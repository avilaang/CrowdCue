from collections import deque
import math


def iou(boxA, boxB):
    # boxes are (x1,y1,x2,y2)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    if interArea == 0:
        return 0.0
    boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)


class Track:
    def __init__(self, tid, box, label, prob, max_history=5):
        self.id = tid
        self.box = box
        self.history = deque(maxlen=max_history)
        self.probs = deque(maxlen=max_history)
        self.update(label, prob)

    def update(self, label, prob):
        self.history.append(label)
        self.probs.append(prob)

    def majority_label(self):
        if not self.history:
            return None
        # simple majority
        counts = {}
        for l in self.history:
            counts[l] = counts.get(l, 0) + 1
        return max(counts.items(), key=lambda x: x[1])[0]

    def avg_prob(self):
        if not self.probs:
            return 0.0
        return sum(self.probs) / len(self.probs)


class SimpleTracker:
    """Lightweight IoU tracker maintaining short label history per face.

    Usage:
      tracker = SimpleTracker(iou_thresh=0.3, max_history=5)
      tracks = tracker.update(detected_boxes, predicted_labels_and_probs)
      # tracks is a list of Track objects
    """

    def __init__(self, iou_thresh=0.3, max_history=5, max_missing=10):
        self.iou_thresh = iou_thresh
        self.max_history = max_history
        self.max_missing = max_missing
        self.next_id = 1
        self.tracks = {}  # id -> Track
        self.missing = {}  # id -> frames missing

    def update(self, boxes, preds):
        """Update tracker with current detections.

        boxes: list of (x1,y1,x2,y2)
        preds: list of (label, prob) corresponding to boxes
        Returns list of Track objects (updated/created)
        """
        assigned = set()
        # Greedy match: for each detection, find best track by IoU
        for i, box in enumerate(boxes):
            best_id = None
            best_iou = 0.0
            for tid, tr in self.tracks.items():
                val = iou(box, tr.box)
                if val > best_iou:
                    best_iou = val
                    best_id = tid

            if best_id is not None and best_iou >= self.iou_thresh and best_id not in assigned:
                # assign
                tr = self.tracks[best_id]
                label, prob = preds[i]
                tr.box = box
                tr.update(label, prob)
                assigned.add(best_id)
                self.missing[best_id] = 0
            else:
                # create new track
                tid = self.next_id
                self.next_id += 1
                label, prob = preds[i]
                self.tracks[tid] = Track(tid, box, label, prob, max_history=self.max_history)
                self.missing[tid] = 0

        # Increment missing counters for unassigned tracks and remove stale ones
        for tid in list(self.tracks.keys()):
            if tid not in assigned:
                self.missing[tid] = self.missing.get(tid, 0) + 1
                if self.missing[tid] > self.max_missing:
                    del self.tracks[tid]
                    del self.missing[tid]

        return list(self.tracks.values())