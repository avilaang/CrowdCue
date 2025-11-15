import cv2
import torch
from models.face_pose_detection import load_yolo_models
from models.emotion_model_loader import load_emotion_model, predict_emotion
from models.engagement_utils import map_emotion_to_engagement, interpret_pose
from models.overlay_utils import draw_face_box


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Using device: {device}")

    # --- choose token ---
    selection = int(input("Choose your HuggingFace token:\n1 = AA\n2 = AZ\n3 = KX\nEnter 1/2/3: "))

    # Load models
    face_model, pose_model = load_yolo_models()
    emotion_model, emotion_processor = load_emotion_model(device, selection)

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Face detection
        face_results = face_model(frame)
        pose_results = pose_model(frame)

        for det in face_results[0].boxes:
            x1, y1, x2, y2 = map(int, det.xyxy[0])
            face_crop = frame[y1:y2, x1:x2]

            # Emotion
            emotion = predict_emotion(emotion_model, emotion_processor, face_crop, device)
            emotion_eng = map_emotion_to_engagement(emotion)

            draw_face_box(frame, (x1, y1, x2, y2), f"{emotion} → {emotion_eng}")

        # Pose (optional)
        if len(pose_results) > 0:
            if len(pose_results[0].keypoints) > 0:
                kp = pose_results[0].keypoints[0].data.cpu().numpy()
                pose_state = interpret_pose(kp)
                cv2.putText(frame, f"Pose: {pose_state}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

        cv2.imshow("CrowdCue", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
