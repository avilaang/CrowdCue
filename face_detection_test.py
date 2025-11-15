import cv2
import mediapipe as mp

# Initialize MediaPipe face detection and drawing utils
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # Access webcam
with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # Convert image to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Detect faces
        results = face_detection.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Draw bounding boxes and extract landmarks
        if results.detections:
            for detection in results.detections:
                mp_drawing.draw_detection(image, detection)
                print("Detection:", detection.location_data)  # Each detection's box & keypoints

        cv2.imshow('MediaPipe Face Detection', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
cv2.destroyAllWindows()
