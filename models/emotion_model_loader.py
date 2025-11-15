import os
import torch
from dotenv import load_dotenv
from transformers import AutoImageProcessor, AutoModelForImageClassification
import numpy as np
import cv2

load_dotenv()

MODEL_NAME = "dima806/facial_emotions_image_detection"

# emotion id → label mapping from HF model
EMOTION_LABELS = {
    0: "angry",
    1: "disgust",
    2: "fear",
    3: "happy",
    4: "sad",
    5: "surprise",
    6: "neutral"
}

def load_emotion_model(device, selection):
    """Loads HuggingFace model using user-selected token."""
    
    token_key = f"TOKEN{selection}"
    token = os.getenv(token_key)

    if token is None:
        raise ValueError(f"Token {token_key} missing from .env")

    print(f"Using HuggingFace token from {token_key}")

    processor = AutoImageProcessor.from_pretrained(
        MODEL_NAME,
        use_auth_token=token,
        cache_dir="hf_cache"
    )

    model = AutoModelForImageClassification.from_pretrained(
        MODEL_NAME,
        use_auth_token=token,
        cache_dir="hf_cache"
    ).to(device)

    return model, processor


def predict_emotion(model, processor, face_img, device="cpu"):
    """Runs emotion inference on a cropped face image."""
    if face_img is None:
        return "neutral", 0.0

    # If the crop is empty or degenerate, return neutral with zero confidence
    try:
        if getattr(face_img, "size", None) == 0:
            return "neutral", 0.0
    except Exception:
        pass

    # Convert BGR (OpenCV) to RGB for the HF processor
    try:
        img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    except Exception:
        img_rgb = face_img

    # Processor -> tensors. Some HF processors return a BatchEncoding with .to()
    inputs = processor(images=img_rgb, return_tensors="pt")
    # Move tensors to device explicitly where possible
    try:
        inputs = {k: v.to(device) for k, v in inputs.items()}
    except Exception:
        try:
            inputs = inputs.to(device)
        except Exception:
            pass

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        top_prob, pred_id = torch.max(probs, dim=-1)
        prob = float(top_prob.cpu().numpy().squeeze())
        pred_idx = int(pred_id.cpu().numpy().squeeze())

    label = EMOTION_LABELS.get(pred_idx, str(pred_idx))
    return label, prob
