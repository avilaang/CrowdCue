import os
import torch
from dotenv import load_dotenv
from transformers import BeitImageProcessor, BeitForImageClassification

# Load .env from the project root
load_dotenv()

def get_token_by_selection(selection: int) -> str:
    token_map = {
        1: os.getenv("TOKEN1"),
        2: os.getenv("TOKEN2"),
        3: os.getenv("TOKEN3"),
    }
    token = token_map.get(selection)

    if token is None or token.strip() == "":
        raise ValueError(f"No HuggingFace token found for selection {selection}")
    return token


def load_emotion_model(device: str, selection: int):
    token = get_token_by_selection(selection)

    print(f"Loading HuggingFace BEiT emotion model on device: {device}...")

    processor = BeitImageProcessor.from_pretrained(
        "Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large",
        use_auth_token=token,
    )

    model = BeitForImageClassification.from_pretrained(
        "Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large",
        use_auth_token=token,
    ).to(device)

    return model, processor


def predict_emotion(model, processor, face_img, device: str):
    inputs = processor(images=face_img, return_tensors="pt").to(device)
    outputs = model(**inputs)
    pred_idx = outputs.logits.argmax(-1).item()
    label = model.config.id2label[pred_idx]
    return label
