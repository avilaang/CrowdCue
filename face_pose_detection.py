from ultralytics import YOLO
import cv2

def main():
    # Load the YOLOv8 pose model (pretrained, auto-downloads if needed)
    model = YOLO("yolov8n-pose.pt")  # 'n' is nano, fast and good for demos
    
    cap = cv2.VideoCapture(0)  # Use webcam (or replace with video file path)

    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # Predict poses on the frame
        results = model(frame)
        
        # results[0].plot() draws keypoints and connections on the frame, including face, hands, body
        annotated_frame = results[0].plot()
        
        # Display
        cv2.imshow("YOLOv8 Multi-Person Face + Pose Detection", annotated_frame)
        
        # Press ESC to exit
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
