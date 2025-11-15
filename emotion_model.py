from ultralytics import YOLO
import cv2
import torch
from torchvision import transforms

# Load YOLOv8 face detection model
face_model = YOLO('yolov8n-face.pt')

# Load your pretrained emotion classifier (PyTorch example)
emotion_model = torch.load('your_emotion_model.pth')
emotion_model.eval()

# Preprocess transforms for emotion model input
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((48, 48)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# Emotion classes based on your classifier
emotion_labels = ['neutral', 'happy', 'sad', 'angry', 'surprised']

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = face_model(frame)
    annotated_frame = frame.copy()

    for detection in results[0].boxes:
        x1, y1, x2, y2 = map(int, detection.xyxy[0])
        face_crop = frame[y1:y2, x1:x2]

        # Preprocess and predict emotion
        face_tensor = transform(face_crop).unsqueeze(0)
        with torch.no_grad():
            output = emotion_model(face_tensor)
            emotion_idx = torch.argmax(output).item()
        emotion = emotion_labels[emotion_idx]

        # Draw bounding box and label
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated_frame, emotion, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow('Face Detection with Emotion', annotated_frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
