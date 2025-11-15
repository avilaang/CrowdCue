from ultralytics import YOLO
import numpy as np


def init_yolo_models():
   face_model = YOLO("yolov8n.pt")          # face/general detector
   pose_model = YOLO("yolov8n-pose.pt")     # keypoint model
   return face_model, pose_model




def get_face_crops(frame, face_model):
   """Returns list of cropped faces from YOLO detection."""
   detections = face_model(frame)[0]
   boxes = detections.boxes.xyxy.cpu().numpy() if detections.boxes is not None else []


   face_crops = []
   out_boxes = []
   for box in boxes:
       x1, y1, x2, y2 = map(int, box)
       crop = frame[y1:y2, x1:x2]
       face_crops.append(crop)
       out_boxes.append((x1, y1, x2, y2))


   return face_crops, out_boxes
