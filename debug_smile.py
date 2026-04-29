import cv2
import numpy as np
from PIL import Image
import subprocess

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

def debug_landmarks(image_path, label):
    img = load_image_as_array(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    h, w = gray.shape
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1,
                                        minNeighbors=8, minSize=(w//10, h//10))

    if len(faces) == 0:
        print(f"{label}: No faces detected")
        return

    facemark = cv2.face.createFacemarkLBF()
    facemark.loadModel("lbfmodel.yaml")

    faces_for_lbf = np.array([[x, y, w, h] for (x, y, w, h) in faces])
    ok, landmarks = facemark.fit(gray, faces_for_lbf)

    if not ok or landmarks is None:
        print(f"{label}: Landmark detection failed")
        return

    # Draw on a resized copy for viewing
    display = img.copy()
    h, w = display.shape[:2]
    scale = 800 / max(h, w)
    display = cv2.resize(display, (int(w * scale), int(h * scale)))
    gray_display = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)

    for (x, y, fw, fh) in faces:
        x2, y2, fw2, fh2 = int(x*scale), int(y*scale), int(fw*scale), int(fh*scale)
        cv2.rectangle(display, (x2, y2), (x2+fw2, y2+fh2), (0, 255, 0), 2)

    for face_landmarks in landmarks:
        pts = face_landmarks[0]
        for i, (px, py) in enumerate(pts):
            px2, py2 = int(px * scale), int(py * scale)
            cv2.circle(display, (px2, py2), 2, (0, 0, 255), -1)
            # Highlight mouth corners in blue
            if i in [48, 54]:
                cv2.circle(display, (px2, py2), 6, (255, 0, 0), -1)

        # Print mouth stats
        left_corner  = pts[48]
        right_corner = pts[54]
        left_jaw     = pts[0]
        right_jaw    = pts[16]
        mouth_width  = abs(right_corner[0] - left_corner[0])
        face_width   = abs(right_jaw[0] - left_jaw[0])
        ratio = mouth_width / face_width if face_width > 0 else 0
        print(f"{label}: mouth/face ratio = {ratio:.3f} → score = {min(ratio/0.55, 1.0):.2f}")

    out_path = f"/tmp/debug_{label}.jpg"
    cv2.imwrite(out_path, display)
    print(f"{label}: saved to {out_path} — open to inspect landmarks")

# ── Paste your actual file paths for photos #1 and #3 below ──
debug_landmarks("/Users/shekharkumar/Pictures/Photos Library.photoslibrary/originals/7/7F99F51B-E76D-435D-8777-2D75E31EA221.heic", "photo1")
debug_landmarks("/Users/shekharkumar/Pictures/Photos Library.photoslibrary/originals/8/8A8E7AA5-D841-4217-8379-C84939276D92.heic", "photo3")