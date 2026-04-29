import cv2
import numpy as np
from PIL import Image
import subprocess
from deepface import DeepFace

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

# Paste your actual paths for photos 1 and 3
paths = {
    "photo1": "/Users/shekharkumar/Pictures/Photos Library.photoslibrary/originals/7/7F99F51B-E76D-435D-8777-2D75E31EA221.heic",
    "photo3": "/Users/shekharkumar/Pictures/Photos Library.photoslibrary/originals/8/8A8E7AA5-D841-4217-8379-C84939276D92.heic",
}

for label, path in paths.items():
    img = load_image_as_array(path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    try:
        result = DeepFace.analyze(img_rgb,
                                   actions=['emotion'],
                                   enforce_detection=False,
                                   detector_backend='retinaface',
                                   silent=True)
        for i, face in enumerate(result):
            print(f"\n{label} — face {i+1}:")
            print(f"  Region: {face['region']}")
            print(f"  Dominant emotion: {face['dominant_emotion']}")
            for emotion, score in sorted(face['emotion'].items(),
                                          key=lambda x: x[1], reverse=True):
                print(f"  {emotion}: {score:.2f}")
    except Exception as e:
        print(f"{label}: Error — {e}")

# ./smile_detector /Users/shekharkumar/Pictures/Photos Library.photoslibrary/originals/8/8A8E7AA5-D841-4217-8379-C84939276D92.heic
