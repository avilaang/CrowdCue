from ultralytics import YOLO
import cv2
from emotion_model import (
    load_emotion_model,
    predict_raw_emotion,
    map_emotion_to_engagement,
    interpret_pose
)
from engagement_utils import combine_engagement, suggestion_for, color_for


def main():
    # Load models - use face-specific detector
    try:
        face_model = YOLO("yolov8n-face.pt")  # Specialized face detector
    except:
        print("Warning: yolov8n-face.pt not found, using general detector")
        face_model = YOLO("yolov8n.pt")  # Fallback to general detector
    
    pose_model = YOLO("yolov8n-pose.pt")
    emotion_model = load_emotion_model("affectnet_emotions.pt")

    cap = cv2.VideoCapture(0)
    
    # Track engagement history per face for smoothing
    engagement_history = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        annotated = frame.copy()

        face_results = face_model(frame)
        pose_results = pose_model(frame)

        # Initialize engagement (default when no faces detected)
        engagement = None

        # Process faces
        for idx, box in enumerate(face_results[0].boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width = x2 - x1
            height = y2 - y1
            
            # Skip if bounding box is too small (likely not a face)
            if width < 20 or height < 20:
                continue
            
            # Skip if aspect ratio is too extreme (likely not a face)
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                continue
                
            face_crop = frame[y1:y2, x1:x2]
            
            # Skip if crop is empty or invalid
            if face_crop is None or face_crop.size == 0:
                continue

            raw_emotion = predict_raw_emotion(emotion_model, face_crop)
            emotion_engagement = map_emotion_to_engagement(raw_emotion)

            # Get pose keypoints (only if same person)
            pose_keypoints = None
            if len(pose_results[0].keypoints) > 0:
                pose_keypoints = pose_results[0].keypoints[0].xy

            pose_state = interpret_pose(pose_keypoints) if pose_keypoints is not None else "neutral"

            # Combine engagement with smoothing
            engagement = combine_engagement(emotion_engagement, pose_state)
            
            # Apply temporal smoothing (average last 3 predictions)
            if idx not in engagement_history:
                engagement_history[idx] = []
            engagement_history[idx].append(engagement)
            if len(engagement_history[idx]) > 3:
                engagement_history[idx].pop(0)
            
            # Use most common engagement in recent history
            most_common = max(set(engagement_history[idx]), key=engagement_history[idx].count)
            engagement = most_common
            
            color = color_for(engagement)

            # Draw bounding box + label
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Display engagement + raw emotion for debugging
            label_text = f"{engagement}"
            if raw_emotion != "neutral":
                label_text += f" ({raw_emotion})"
            
            cv2.putText(
                annotated,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        # Display suggestion at top-left
        if engagement:
            cv2.putText(
                annotated,
                suggestion_for(engagement),
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                3
            )

        cv2.imshow("CrowdCue", annotated)

        if cv2.waitKey(1) == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
