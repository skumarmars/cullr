import osxphotos
import cv2
import numpy as np
from PIL import Image
import subprocess
import os

# ── Image loading ──────────────────────────────────────────────────────────────

def load_image_as_array(path):
    try:
        img = Image.open(path).convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception:
        tmp = "/tmp/osxphotos_tmp.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", path, "--out", tmp],
                      capture_output=True)
        img = Image.open(tmp).convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

# ── Scoring functions ──────────────────────────────────────────────────────────

def sharpness_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def exposure_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean = np.mean(gray)
    return 1 - abs(mean - 127) / 127

def face_quality_score(photo):
    faces = photo.face_info
    if not faces:
        return 0
    qualities = [f.quality for f in faces if hasattr(f, 'quality') and f.quality >= 0]
    if not qualities:
        return 0.3
    return max(qualities)

def tilt_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                             threshold=100, minLineLength=100, maxLineGap=10)
    if lines is None:
        return 0.8
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 == 0:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 30:
            angles.append(angle)
    if not angles:
        return 0.8
    median_angle = np.median(angles)
    return round(max(0, 1 - abs(median_angle) / 10), 2)

def smile_score(photo, path):
    """
    Uses Apple Vision VNDetectFaceCaptureQualityRequest via Swift CLI.
    Holistic face quality score — expression, sharpness, pose all at once.
    """
    tmp_jpg = "/tmp/vision_face.jpg"
    tool_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smile_detector")

    subprocess.run(["sips", "-s", "format", "jpeg", path, "--out", tmp_jpg],
                  capture_output=True)

    result = subprocess.run([tool_path, tmp_jpg],
                           capture_output=True, text=True, timeout=15)
    try:
        score = float(result.stdout.strip())
        return round(score, 3)
    except Exception:
        return 0.3


def composite_score(sharpness, face_quality, exposure, tilt, smile):
    sharp_norm = min(sharpness / 1000, 1.0)
    return (
        sharp_norm   * 0.35 +
        smile        * 0.35 +
        face_quality * 0.20 +
        tilt         * 0.05 +
        exposure     * 0.05
    )

# ── Write-back actions ─────────────────────────────────────────────────────────

def favorite_photo(uuid):
    script = f"""
    tell application "Photos"
        set thePhoto to media item id "{uuid}"
        set favorite of thePhoto to true
    end tell
    """
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Could not favorite: {result.stderr.strip()}")
    else:
        print(f"  ✓ Favorited")

def add_to_album(uuid, album_name):
    script = f"""
    tell application "Photos"
        set thePhoto to media item id "{uuid}"
        if not (exists album "{album_name}") then
            make new album named "{album_name}"
        end if
        add {{thePhoto}} to album "{album_name}"
    end tell
    """
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Could not add to album: {result.stderr.strip()}")
    else:
        print(f"  ✓ Added to '{album_name}'")

def apply_picks(picks, album_name):
    output_album = f"{album_name} — AI Picks"
    print(f"\nApplying picks to Photos.app...")
    print(f"Creating album '{output_album}'\n")
    for p in picks:
        print(f"  → {p['filename'][:40]}")
        favorite_photo(p['uuid'])
        add_to_album(p['uuid'], output_album)
    print(f"\n✓ Done. Check Photos.app for '{output_album}'")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    album_name = "DSAIL Project"
    top_n = 1  # best photo from each bucket

    db = osxphotos.PhotosDB()
    albums = db.album_info
    target = next((a for a in albums if a.title == album_name), None)

    if not target:
        print(f"Album '{album_name}' not found.")
        return

    photos = target.photos
    print(f"\nFound {len(photos)} photos in '{album_name}'")
    print("Processing...\n")

    solo, together, skipped = [], [], []

    for i, photo in enumerate(photos):
        path = photo.path
        if not path:
            skipped.append(photo.filename)
            continue

        print(f"  Scoring {i+1}/{len(photos)}: {photo.filename[:30]}...")

        try:
            img = load_image_as_array(path)
        except Exception as e:
            print(f"  ✗ Could not load: {e}")
            skipped.append(photo.filename)
            continue

        # Bucketing by recognized faces only
        recognized = [f for f in photo.face_info if f.name]
        recognized_count = len(recognized)
        total_count = len(photo.face_info)

        sharp  = sharpness_score(img)
        exp    = exposure_score(img)
        fq     = face_quality_score(photo)
        tilt   = tilt_score(img)
        smile = smile_score(photo, path)
        score  = composite_score(sharp, fq, exp, tilt, smile)

        entry = {
            "filename":     photo.filename,
            "uuid":         photo.uuid,
            "score":        score,
            "sharpness":    round(sharp, 1),
            "exposure":     round(exp, 2),
            "face_quality": round(fq, 2),
            "tilt":         tilt,
            "smile":        smile,
            "face_count": recognized_count,
            "total_faces": total_count,
        }

        if recognized_count >= 2:
            together.append(entry)
        elif recognized_count == 1:
            solo.append(entry)
        else:
            pass  # no recognized faces, skip

    solo.sort(key=lambda x: x["score"], reverse=True)
    together.sort(key=lambda x: x["score"], reverse=True)

    def print_bucket(label, bucket):
        print(f"\n{'─'*50}")
        print(f"  {label} ({len(bucket)} photos)")
        print(f"{'─'*50}")
        for i, p in enumerate(bucket, 1):
            star = " ★" if i == 1 else ""
            print(f"{i}. {p['filename'][:40]}{star}")
            print(f"   Score: {p['score']:.3f} | Sharp: {p['sharpness']} | "
                  f"Exp: {p['exposure']} | Face: {p['face_quality']} | "
                  f"Tilt: {p['tilt']} | Smile: {p['smile']} | "
                  f"Faces: {p['face_count']}")

    print_bucket("SOLO SHOTS", solo)
    print_bucket("TOGETHER SHOTS", together)

    if skipped:
        print(f"\nSkipped {len(skipped)} photos (not downloaded from iCloud)")

    # One pick per bucket
    top_picks = []
    if solo:
        top_picks.append(solo[0])
    if together:
        top_picks.append(together[0])

    print(f"\n{'═'*50}")
    print(f"  AI Picks ({len(top_picks)} total — 1 per group):")
    print(f"{'═'*50}")
    for p in top_picks:
        bucket = "Solo" if p['face_count'] < 2 else "Together"
        print(f"  • [{bucket}] {p['filename'][:40]}  (score: {p['score']:.3f})")

    print(f"\nThis will:")
    print(f"  ★  Favorite each selected photo")
    print(f"  📁 Add them to 'DSAIL Project — AI Picks'")
    confirm = input("\nProceed? (yes/no): ").strip().lower()

    if confirm == "yes":
        apply_picks(top_picks, album_name)
    else:
        print("\nCancelled. No changes made to Photos.app.")

main()
