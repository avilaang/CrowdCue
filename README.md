# CrowdCue - Quick Start Guide

## Running the App

```bash
cd /Users/avilaang/Documents/CrowdCue
./venv/bin/python crowdcue_main.py
```

**Press ESC to exit**

---

## System Status

✅ **Emotion Model** - Loads successfully (untrained + heuristic detection)  
✅ **Face Detection** - YOLOv8 general detector (fallback from face-specific)  
✅ **Pose Detection** - YOLOv8 pose model downloads automatically  
✅ **Engagement Analysis** - Maps emotion + pose → engagement state  
✅ **Real-time Overlay** - Shows engagement | emotion | pose for each person  

---

## What You'll See

For each detected person:
- **Green bounding box** around the face
- **Black info box** above showing: `Engagement | Raw Emotion | Pose State`

### Example Labels:
- `Engaged | Happy | Neutral` - Person is smiling, head neutral
- `Neutral | Neutral | Neutral` - Normal, neutral expression  
- `Bored | Sad | Looking Away` - Person looking away or sad
- `Confused | Surprise | Confused` - Head tilted, confused expression

---

## Emotion Detection

The system uses:

1. **Heuristic Image Analysis** (for untrained model)
   - Bright pixels in mouth region → "Happy"
   - Low brightness + edges → "Angry"  
   - Very low brightness → "Sad"
   - High edge density → "Surprise"
   - Default → "Neutral"

2. **Pose Analysis**
   - Eyes far apart horizontally → "Looking Away"
   - Significant head tilt → "Confused"
   - Otherwise → "Neutral"

3. **Engagement Mapping**
   - Pose overrides emotion
   - Looking Away or Confused → "Bored" or "Confused"
   - Happy/Surprise → "Engaged"
   - Sad/Angry/etc → "Bored"
   - Neutral → "Neutral"

---

## Improving Accuracy

To use a trained emotion model:

1. Download from: https://github.com/oarriaga/face_classification/releases
2. Extract and place weights in `checkpoint/weights_epoch_75.pth.tar`
3. The app will automatically load them

---

## Troubleshooting

**"yolov8n-face.pt not found"** → App falls back to general detector ✓  
**"Camera failed to initialize"** → Grant camera permissions in macOS Settings  
**"No persons detected"** → Make sure face is visible and well-lit  

---

## Architecture Overview

```
crowdcue_main.py
├── Load emotion model
├── Open webcam
└── Main loop:
    ├── detect_faces() → YOLO face detection
    ├── detect_pose() → YOLO pose keypoints
    ├── For each face:
    │   ├── Crop face
    │   ├── predict_emotion() → emotion label
    │   ├── interpret_pose() → pose state
    │   ├── resolve_final_engagement() → engagement
    │   └── draw_engagement_box() → overlay
    └── Display frame
```

---

**Ready to go!** 🎬
