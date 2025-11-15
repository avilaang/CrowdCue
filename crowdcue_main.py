import cv2
import torch

from emotion_model_loader import load_emotion_model, predict_emotion
from engagement_utils import emotion_to_engagement
from face_pose_detection import init_yolo_models, get_face_crops
from overlay_utils import draw_label
from simple_tracker import SimpleTracker

def list_available_cameras(max_tested=5):
    available = []
    for i in range(max_tested):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera index {i} is available")
            available.append(i)
            cap.release()
    if not available:
        print("No cameras detected.")
    return available


def main():

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    cams = list_available_cameras()

    print("\nSelect a camera index:")
    for c in cams:
        print(f"  {c}")

    cam_index = int(input("Enter camera index: "))

    selection = int(input("Choose your HF token:\n1 = AA\n2 = AZ 1\n3 = KX\nEnter 1/2/3: "))

    # Ask whether to enable debug (prints top-3 and saves low-conf crops)
    dbg_input = input("Enable debug output and low-confidence crop saving? (y/N): ").strip().lower()
    debug_mode = dbg_input == 'y'
    debug_dir = 'debug_crops' if debug_mode else None

    # Load emotion model
    model, processor = load_emotion_model(device, selection)

    # Load YOLO models
    face_model, pose_model = init_yolo_models()

    # Initialize a simple tracker for temporal smoothing
    # Slightly more smoothing and a bit more tolerant IoU matching
    tracker = SimpleTracker(iou_thresh=0.25, max_history=7, max_missing=8)

    cap = cv2.VideoCapture(cam_index)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        face_crops, boxes = get_face_crops(frame, face_model)

        preds = []
        for crop in face_crops:
            # predict_emotion now returns (label, prob)
            label, prob = predict_emotion(model, processor, crop, device, debug=debug_mode, save_low_conf_dir=debug_dir)
            # Apply per-class confidence thresholding before smoothing
            from engagement_utils import apply_conf_threshold
            adj_label, adj_prob = apply_conf_threshold(label, prob)
            preds.append((adj_label, adj_prob))

        # Update tracker with current detections and predictions
        tracks = tracker.update(boxes, preds)

        # Draw tracks (smoothed labels/probs)
        from overlay_utils import draw_confidence_bar
        for tr in tracks:
            x1, y1, x2, y2 = tr.box
            sm_label = tr.majority_label() or "neutral"
            sm_prob = tr.avg_prob()
            engagement = emotion_to_engagement(sm_label)
            label_text = f"{sm_label} {sm_prob:.2f} → {engagement}"
            color = (0, 200, 0) if engagement == "engaged" else (0, 200, 200) if engagement == "neutral" else (0, 100, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            draw_label(frame, label_text, x1 + 5, y1 - 5, color)
            draw_confidence_bar(frame, x1 + 5, y1 + 5, min(100, x2 - x1), 8, sm_prob, bar_color=color)

        cv2.imshow("CrowdCue - Real-time Emotion + Engagement", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()