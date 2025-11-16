# crowd_engine.py

from face_pose_detection import get_face_crops, init_yolo_models
from emotion_model_loader import load_emotion_model, predict_emotion
from engagement_utils import emotion_to_engagement
from ocr.ocr_engine import extract_text
from ocr.ai_engine import get_engagement_suggestions
from PIL import Image

def process_camera_frame(frame, emotion_model, emotion_processor, face_model, device):
    """
    Takes a video frame → detects face → classifies emotion → computes engagement level
    Returns:
        emotion (str), engagement_score (float)
    """
    face_crops, boxes = get_face_crops(frame, face_model)
    if not face_crops:
        return None, None

    # Use first face only (demo)
    face_crop = face_crops[0]
    emotion, prob = predict_emotion(emotion_model, emotion_processor, face_crop, device=device)

    engagement = emotion_to_engagement(emotion)
    return emotion, engagement


def generate_combined_feedback(emotion, engagement, screenshot_path):
    """
    Runs OCR on screenshot → gets textual context → generates personalized suggestions
    """
    # Load image from path
    image = Image.open(screenshot_path)
    text = extract_text(image)
    
    # Generate suggestions based on text (emotion/engagement can be incorporated into prompt if needed)
    suggestions = get_engagement_suggestions(text)
    return suggestions
