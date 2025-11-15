import cv2
import torch

from models.emotion_model_loader import load_emotion_model, predict_emotion
from models.engagement_utils import emotion_to_engagement
from models.face_pose_detection import init_yolo_models, get_face_crops
from models.overlay_utils import draw_label


def main():

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    selection = int(input("Choose your HF token:\n1 = You\n2 = Friend 1\n3 = Friend 2\nEnter 1/2/3: "))

    # Load emotion model
    model, processor = load_emotion_model(device, selection)

    # Load YOLO models
    face_model, pose_model = init_yolo_models()

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        face_crops = get_face_crops(frame, face_model)

        if len(face_crops) > 0:
            # face_crops corresponds to detected boxes in same order; get boxes too
            # We re-run detection with boxes to draw labels at correct positions
            detections = face_model(frame)[0]
            boxes = detections.boxes.xyxy.cpu().numpy() if detections.boxes is not None else []

            for crop, box in zip(face_crops, boxes):
                x1, y1, x2, y2 = map(int, box)
                emotion, prob = predict_emotion(model, processor, crop, device)
                engagement = emotion_to_engagement(emotion)

                label_text = f"{emotion} {prob:.2f} → {engagement}"
                # choose color by engagement
                color = (0, 200, 0) if engagement == "engaged" else (0, 200, 200) if engagement == "neutral" else (0, 100, 255)

                # Draw bounding box and label at top-left of the box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                draw_label(frame, label_text, x1 + 5, y1 - 5, color)
                # Draw a small confidence bar under the label
                from models.overlay_utils import draw_confidence_bar
                draw_confidence_bar(frame, x1 + 5, y1 + 5, min(100, x2-x1), 8, prob, bar_color=color)

        cv2.imshow("CrowdCue - Real-time Emotion + Engagement", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
