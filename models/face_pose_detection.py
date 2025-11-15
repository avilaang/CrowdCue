from ultralytics import YOLO

def load_yolo_models():
    face_model = YOLO("yolov8n.pt")
    pose_model = YOLO("yolov8n-pose.pt")
    return face_model, pose_model
