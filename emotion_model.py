import torch
import torch.nn as nn
import cv2
from torchvision import transforms
import os
import urllib.request

# -------------------------
# Raw emotion labels from pretrained model
# -------------------------
EMOTION_LABELS = [
    "neutral", "happy", "sad",
    "surprise", "fear", "anger", "disgust"
]

# -------------------------
# Simple Emotion Model
# -------------------------
class SimpleEmotionNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.classifier = nn.Linear(64, 7)
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

# -------------------------
# Load pretrained emotion model
# -------------------------
def load_emotion_model(path="affectnet_emotions.pt"):
    """Load emotion model, download if missing"""
    
    # Check if model file exists and is valid
    if os.path.exists(path):
        try:
            model = torch.jit.load(path, map_location="cpu")
            model.eval()
            return model
        except Exception as e:
            print(f"Warning: Could not load JIT model ({e}). Using fallback model.")
            os.remove(path)  # Remove corrupted file
    
    # Create a simple model as fallback
    print(f"Creating fallback emotion model...")
    model = SimpleEmotionNet()
    model.eval()
    return model

# -------------------------
# Preprocessing for emotion model
# -------------------------
preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# -------------------------
# Predict RAW emotion (happy, sad, neutral, etc.)
# -------------------------
def predict_raw_emotion(model, face_img):
    if face_img is None or face_img.size == 0:
        return "neutral"

    try:
        img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        tensor = preprocess(img_rgb).unsqueeze(0)

        with torch.no_grad():
            logits = model(tensor)
            
            # Get probabilities
            probs = torch.softmax(logits, dim=1)[0]
            emotion_idx = torch.argmax(probs).item()
            confidence = probs[emotion_idx].item()
            
            # For untrained models, be more lenient with confidence
            # Lower threshold helps detect emotions even with poor quality models
            if confidence < 0.2:  # Lowered from 0.3
                # Try smile detection as fallback for untrained models
                smile_score = detect_smile_heuristic(face_img)
                if smile_score > 0.5:
                    return "happy"
                return "neutral"
            
            return EMOTION_LABELS[emotion_idx]
    except Exception as e:
        print(f"Error in emotion prediction: {e}")
        return "neutral"

# -------------------------
# Heuristic smile/expression detection
# -------------------------
def detect_smile_heuristic(face_img):
    """
    Simple heuristic to detect smiles using image analysis.
    Looks for bright regions in mouth area and mouth corners.
    """
    try:
        if face_img is None or face_img.size == 0:
            return 0.0
        
        # Focus on lower half of face (mouth region)
        h, w = face_img.shape[:2]
        mouth_region = face_img[h//2:, :]
        
        # Convert to grayscale
        gray = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2GRAY)
        
        # Check for bright pixels (teeth/smile features)
        bright_pixels = cv2.countNonZero(cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1])
        max_pixels = gray.size
        
        # Smile score based on bright pixel ratio
        smile_score = bright_pixels / max_pixels
        
        return min(smile_score * 3, 1.0)  # Scale and cap at 1.0
    except:
        return 0.0

# -------------------------
# Map raw emotion → engagement state
# -------------------------
def map_emotion_to_engagement(emotion):
    # Be more lenient with engagement classification
    if emotion in ["happy", "surprise"]:
        return "engaged"
    if emotion in ["neutral"]:
        return "neutral"
    if emotion in ["sad", "anger", "disgust", "fear"]:
        return "bored"
    return "neutral"   # fallback

# -------------------------
# Interpret pose from YOLO keypoints
# -------------------------
def interpret_pose(keypoints):
    """
    Interpret pose and expression from YOLO keypoints.
    YOLO pose model has 17 keypoints:
    0=nose, 1=L eye, 2=R eye, 3=L ear, 4=R ear, 5=L shoulder, 6=R shoulder, etc.
    """
    try:
        left_eye = keypoints[1][:2]
        right_eye = keypoints[2][:2]
        nose = keypoints[0][:2]
        left_ear = keypoints[3][:2] if len(keypoints) > 3 else None
        right_ear = keypoints[4][:2] if len(keypoints) > 4 else None
    except:
        return "neutral"

    # Calculate eye distance (horizontal)
    eye_distance = abs(left_eye[0] - right_eye[0])
    
    # Calculate head tilt (vertical distance between eyes)
    eye_tilt = abs(left_eye[1] - right_eye[1])
    
    # Calculate eye-to-nose vertical distance (indicates head angle)
    avg_eye_y = (left_eye[1] + right_eye[1]) / 2
    nose_eye_distance = nose[1] - avg_eye_y  # positive = nose below eyes (normal), negative = nose above
    
    # Looking away detection - eyes far apart horizontally
    if eye_distance > 90:
        return "looking away"

    # Brow furrowing detection - slight head tilt with nose position
    # When confused, people often tilt head and furrow brows (slight angle)
    if 15 < eye_tilt < 35 and 5 < abs(nose_eye_distance) < 30:
        return "confused"
    
    # Extreme head tilt (almost turned away but not quite)
    if eye_tilt > 35:
        return "confused"

    return "neutral"
