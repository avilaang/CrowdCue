import threading
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock

import cv2

# Ensure the repository root is on sys.path so local modules import reliably
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from emotion_model_loader import load_emotion_model, predict_emotion
from face_pose_detection import init_yolo_models, get_face_crops
from simple_tracker import SimpleTracker
from engagement_score import EngagementScoreComputer, EngagementMetrics
from engagement_utils import apply_conf_threshold


@dataclass
class SimpleMetrics:
    score: float = 0.0
    engaged_pct: float = 0.0
    neutral_pct: float = 0.0
    bored_pct: float = 0.0
    confused_pct: float = 0.0
    total_faces: int = 0
    suggestion: str = ""
    dominant: str = "none"  # Most-occurring engagement state


class DetectionEngine:
    def __init__(self, device: str = "cpu", hf_token_selection: int = 1, cam_index: int = 0, debug: bool = False):
        self.device = device
        self.hf_token_selection = hf_token_selection
        self.cam_index = cam_index
        self.debug = debug

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = Lock()
        self._latest_metrics = SimpleMetrics()

        # resources to be initialized in thread
        self.model = None
        self.processor = None
        self.face_model = None
        self.pose_model = None
        self.tracker = None
        self.engagement_computer = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_latest(self) -> SimpleMetrics:
        with self._lock:
            return SimpleMetrics(**self._latest_metrics.__dict__)

    def _run(self):
        # Load models (do this in thread to avoid blocking UI)
        try:
            self.model, self.processor = load_emotion_model(self.device, self.hf_token_selection)
        except Exception as e:
            print(f"Error loading emotion model: {e}")
            return

        try:
            self.face_model, self.pose_model = init_yolo_models()
        except Exception as e:
            print(f"Error loading YOLO models: {e}")
            return

        self.tracker = SimpleTracker(iou_thresh=0.25, max_history=7, max_missing=8)
        self.engagement_computer = EngagementScoreComputer()

        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            print(f"Camera {self.cam_index} not available")
            return

        frame_skip = 10  # Update metrics every N frames (~333ms at 30fps)
        frame_counter = 0

        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            face_crops, boxes = get_face_crops(frame, self.face_model)
            preds = []
            for crop in face_crops:
                label, prob = predict_emotion(self.model, self.processor, crop, device=self.device, debug=self.debug)
                adj_label, adj_prob = apply_conf_threshold(label, prob)
                preds.append((adj_label, adj_prob))

            tracks = self.tracker.update(boxes, preds)

            # Compute metrics via EngagementScoreComputer
            metrics = self.engagement_computer.compute(tracks, frame_shape=(frame.shape[0], frame.shape[1], frame.shape[2] if frame.ndim==3 else 3))

            # Update _latest_metrics only every N frames to avoid thrashing
            frame_counter += 1
            if frame_counter >= frame_skip:
                frame_counter = 0
                with self._lock:
                    self._latest_metrics.score = metrics.score
                    self._latest_metrics.engaged_pct = metrics.engaged_pct
                    self._latest_metrics.neutral_pct = metrics.neutral_pct
                    self._latest_metrics.bored_pct = metrics.bored_pct
                    self._latest_metrics.confused_pct = metrics.confused_pct
                    self._latest_metrics.total_faces = metrics.total_faces
                    self._latest_metrics.suggestion = metrics.suggestion
                    self._latest_metrics.dominant = metrics.dominant_engagement

            # Small sleep to avoid maxing CPU; real loop rate controlled by camera
            time.sleep(0.01)

        cap.release()


# Global engine instance and simple provider
_engine: Optional[DetectionEngine] = None


class SimplifiedMetricsProvider:
    def __init__(self, engine: DetectionEngine):
        self._engine = engine

    def get_engagement_percentage(self) -> int:
        m = self._engine.get_latest()
        return int(m.score)

    def get_suggested_action(self) -> str:
        m = self._engine.get_latest()
        return m.suggestion or "Analyzing..."

    def get_audience_breakdown(self) -> Dict[str, Any]:
        m = self._engine.get_latest()
        return {
            'engaged': m.engaged_pct,
            'neutral': m.neutral_pct,
            'bored': m.bored_pct,
            'confused': m.confused_pct,
            'total_faces': m.total_faces,
        }

    def get_dominant_engagement(self) -> str:
        """Return the dominant engagement state: engaged, neutral, bored, confused, or 'none'."""
        m = self._engine.get_latest()
        return m.dominant


def initialize_detection(device: str = "cpu", hf_token_selection: int = 1, cam_index: int = 0, debug: bool = False) -> SimplifiedMetricsProvider:
    global _engine
    if _engine is not None:
        return SimplifiedMetricsProvider(_engine)

    _engine = DetectionEngine(device=device, hf_token_selection=hf_token_selection, cam_index=cam_index, debug=debug)
    _engine.start()
    return SimplifiedMetricsProvider(_engine)


def shutdown_detection():
    global _engine
    if _engine is not None:
        _engine.stop()
        _engine = None
