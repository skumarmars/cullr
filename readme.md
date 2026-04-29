# Cullr - an AI Photo Culling System

An on-device AI tool for macOS that automatically selects the best photos from a batch in your Apple Photos library — no uploads, no cloud, no coding required to use.

Built as a final project for the DSAIL course at Harvard Business School.

---

## What It Does

When you shoot a batch of photos at an event, you often end up with 10–20 similar shots and need to pick the best 1–2. This tool automates that process by:

1. Reading a named album directly from your Photos.app library
2. Grouping photos into **solo shots** (one recognized person) and **together shots** (two or more recognized people)
3. Scoring each photo across five quality signals: sharpness, face capture quality, exposure, camera tilt, and facial expression
4. Selecting the top photo from each group
5. Favoriting the picks and adding them to a new **"[Album] — AI Picks"** album in Photos.app

The AI proposes — you dispose. All selections can be reviewed before anything is written back to your library.

---

## How It Works

The scoring engine combines five signals into a weighted composite score:

| Signal | Weight | Method |
|--------|--------|--------|
| Face capture quality | 35% | Apple Vision (`VNDetectFaceCaptureQualityRequest`) |
| Sharpness | 35% | OpenCV Laplacian variance |
| Face quality | 20% | Apple Photos.app face quality score via osxphotos |
| Camera tilt | 5% | OpenCV Hough line transform |
| Exposure | 5% | Histogram mean deviation |

Photos are bucketed by the number of **recognized** faces (people you have named in Photos.app), not total detected faces. This means group shots with strangers are handled gracefully, and solo vs. together shots are ranked independently.

---

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.8 or higher
- Xcode Command Line Tools
- Apple Photos.app with at least one album containing photos of named people

---

## Setup

### 1. Install Xcode Command Line Tools
If you don't already have them:
```bash
xcode-select --install
```

### 2. Clone the repository
```bash
git clone https://github.com/skumarmars/cullr.git
cd cullr
```

### 3. Create a virtual environment and install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Compile the Swift face quality tool
This is a one-time step. The Swift tool uses Apple's Vision framework to assess face quality:
```bash
swiftc smile_detector.swift -o smile_detector
```

### 5. Train Photos.app to recognize people
Open Photos.app and navigate to the **People** album. Make sure the people in your photos are named. The system uses these names to bucket photos correctly — this is a one-time setup per person.

---

## Usage

Run the tool on any album in your Photos library:

```bash
source venv/bin/activate
python score.py --album "Your Album Name"
```

To select the top 2 photos per group instead of 1:
```bash
python score.py --album "Your Album Name" --picks 2
```

The tool will:
1. Score all photos in the album
2. Print a ranked list for each group (solo and together)
3. Show you the proposed picks and ask for confirmation
4. Write favorites and create an AI Picks album in Photos.app — **only after you confirm**

### Example output
```
Found 12 photos in 'Summer Trip'
Processing...

──────────────────────────────────────────
  SOLO SHOTS (3 photos)
──────────────────────────────────────────
1. IMG_4821.heic ★
   Score: 0.746 | Sharp: 442.6 | Exp: 1.0 | Face: 0.71 | Tilt: 1.0 | Smile: 0.755

──────────────────────────────────────────
  TOGETHER SHOTS (9 photos)
──────────────────────────────────────────
1. IMG_4835.heic ★
   Score: 0.603 | Sharp: 415.6 | Exp: 0.94 | Face: 0.66 | Tilt: 0.79 | Smile: 0.683

AI Picks (2 total — 1 per group):
  • [Solo]    IMG_4821.heic  (score: 0.746)
  • [Together] IMG_4835.heic  (score: 0.603)

Proceed? (yes/no):
```

---

## Important Notes

- **Photos must be downloaded locally.** If you use iCloud with "Optimize Mac Storage", ensure the album photos are downloaded before running. Photos not available locally are skipped automatically.
- **Face training is required.** The system relies on Photos.app having named the people in your photos. Unrecognized faces are ignored for bucketing purposes.
- **Nothing is changed until you confirm.** The tool always asks before writing anything to your Photos library.

---

## Project Background

This tool was built as a final project for the DSAIL (Data Science and AI for Leaders) course at Harvard Business School. The goal was to explore how AI can augment creative workflows — specifically, how a system can combine objective quality signals (sharpness, exposure) with subjective ones (expression, composition) to replicate the judgment of an experienced photographer.

A key design insight: photos of different compositional intent shouldn't compete with each other. A solo portrait and a group shot serve different purposes, so they're ranked independently. The AI handles computation; the human handles meaning.

---

## Tech Stack

- **[osxphotos](https://github.com/RhetTbull/osxphotos)** — Apple Photos library access and face recognition data
- **[OpenCV](https://opencv.org/)** — sharpness and tilt analysis
- **[Pillow](https://python-pillow.org/)** — image loading and HEIC handling
- **Apple Vision framework** — face capture quality scoring (via Swift CLI)
- **AppleScript** — writing favorites and albums back to Photos.app

---

## License

MIT
