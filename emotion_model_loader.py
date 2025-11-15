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

    # Derive EMOTION_LABELS from the model's config if available. This
    # prevents hard-coded index/order mismatches when switching models.
    try:
        cfg_labels = getattr(model.config, "id2label", None)
        if cfg_labels:
            # Normalize labels to lowercase and ensure integer keys
            normalized = {int(k): str(v).lower() for k, v in cfg_labels.items()}
            # assign to the module-level EMOTION_LABELS
            global EMOTION_LABELS
            EMOTION_LABELS = normalized
    except Exception:
        # If anything goes wrong, keep the existing EMOTION_LABELS hard-coded map
        pass

    return model, processor


def predict_emotion(model, processor, face_img, device="cpu", conf_thresh: float = 0.45, debug: bool = False, save_low_conf_dir: str = None):
    """Runs emotion inference on a cropped face image.

    Args:
      model, processor: HF model + processor
      face_img: OpenCV BGR numpy array
      device: torch device string
      conf_thresh: minimum probability to consider prediction reliable
      debug: if True, print top-3 predictions
      save_low_conf_dir: if provided and prediction prob < conf_thresh, save crop there

    Returns:
      (label, prob)
    """

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
        # flatten
        probs_np = probs.cpu().numpy().squeeze()
        # top-3 for debug
        import numpy as _np
        topk_idx = _np.argsort(probs_np)[::-1][:3]
        topk = [(int(i), float(probs_np[int(i)])) for i in topk_idx]
        pred_idx = int(topk[0][0])
        prob = float(topk[0][1])

    label = EMOTION_LABELS.get(pred_idx, str(pred_idx))

    if debug:
        # Print top-3 with readable labels
        try:
            topk_strs = []
            for idx, p in topk:
                lbl = EMOTION_LABELS.get(int(idx), str(idx))
                topk_strs.append(f"{lbl}:{p:.3f}")
            print("[emotion_debug] top3:", ", ".join(topk_strs))
        except Exception:
            print("[emotion_debug] predicted", label, prob)

    # Save low-confidence crops if requested
    if save_low_conf_dir and prob < conf_thresh:
        try:
            import time
            os.makedirs(save_low_conf_dir, exist_ok=True)
            ts = int(time.time() * 1000)
            fname = os.path.join(save_low_conf_dir, f"lowconf_{label}_{prob:.2f}_{ts}.jpg")
            # face_img is BGR; save as-is
            cv2.imwrite(fname, face_img)
        except Exception:
            pass

    return label, prob