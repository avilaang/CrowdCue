"""
Engagement Score Computation Module

Computes aggregate audience engagement metrics from tracked faces.
"""

from engagement_utils import emotion_to_engagement
from typing import List, Dict, Any, Tuple


class EngagementMetrics:
    """Container for aggregated engagement data."""
    
    def __init__(self):
        self.score: float = 0.0  # 0-100
        self.engaged_pct: float = 0.0
        self.neutral_pct: float = 0.0
        self.bored_pct: float = 0.0
        self.confused_pct: float = 0.0
        self.total_faces: int = 0
        self.suggestion: str = ""
        self.emotion_counts: Dict[str, int] = {}
        # Dominant engagement label (engaged/neutral/bored/confused/none)
        self.dominant_engagement: str = "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            'score': self.score,
            'engaged_pct': self.engaged_pct,
            'neutral_pct': self.neutral_pct,
            'bored_pct': self.bored_pct,
            'confused_pct': self.confused_pct,
            'total_faces': self.total_faces,
            'suggestion': self.suggestion,
            'emotion_counts': self.emotion_counts,
            'dominant_engagement': self.dominant_engagement,
        }
    
    def __repr__(self) -> str:
        return (
            f"EngagementMetrics(score={self.score:.1f}, "
            f"engaged={self.engaged_pct:.0f}%, neutral={self.neutral_pct:.0f}%, "
            f"bored={self.bored_pct:.0f}%, confused={self.confused_pct:.0f}%, "
            f"total_faces={self.total_faces})"
        )


class EngagementScoreComputer:
    """Compute engagement score from tracked faces."""
    
    def __init__(
        self,
        attention_weight: float = 0.4,
        posture_weight: float = 0.3,
        consistency_weight: float = 0.2,
        density_weight: float = 0.1,
        target_audience_size: int = 30,
    ):
        """
        Initialize engagement score computer.
        
        Args:
            attention_weight: Weight for attention factor (default 0.4).
            posture_weight: Weight for posture factor (default 0.3).
            consistency_weight: Weight for consistency factor (default 0.2).
            density_weight: Weight for density factor (default 0.1).
            target_audience_size: Expected audience size for density normalization (default 30).
        """
        self.attention_weight = attention_weight
        self.posture_weight = posture_weight
        self.consistency_weight = consistency_weight
        self.density_weight = density_weight
        self.target_audience_size = target_audience_size
        
        # For consistency tracking across frames
        self.frame_count = 0
        self.emotion_history: Dict[int, List[str]] = {}  # track_id -> [emotions]
        self.max_history = 100  # frames to track for consistency
    
    def compute(self, tracks: List[Any], frame_shape: Tuple[int, int, int] = None) -> EngagementMetrics:
        """
        Compute engagement score from a list of Track objects.
        
        Args:
            tracks: List of Track objects from SimpleTracker.
            frame_shape: Frame dimensions (height, width, channels) for posture estimation.
        
        Returns:
            EngagementMetrics object with score and breakdown.
        """
        self.frame_count += 1
        metrics = EngagementMetrics()
        
        if not tracks or len(tracks) == 0:
            # No faces detected
            metrics.suggestion = "No audience detected. Check camera setup."
            return metrics
        
        # Count faces by engagement state
        engagement_counts = {
            'engaged': 0,
            'neutral': 0,
            'bored': 0,
            'confused': 0,
        }
        
        total_confidence = 0.0
        total_frontality = 0.0
        
        for track in tracks:
            # Get majority label and probability
            label = track.majority_label()
            prob = track.avg_prob() if hasattr(track, 'avg_prob') else 0.5
            
            # Map to engagement state
            engagement = emotion_to_engagement(label)
            engagement_counts[engagement] += 1
            
            # Track emotion history for consistency
            # Support both `track_id` (used in some mock/test tracks) and `id` (used by SimpleTracker.Track)
            tid = getattr(track, 'track_id', None)
            if tid is None:
                tid = getattr(track, 'id', None)
            # only record if we have an identifier
            if tid is not None:
                if tid not in self.emotion_history:
                    self.emotion_history[tid] = []
                self.emotion_history[tid].append(label)
                if len(self.emotion_history[tid]) > self.max_history:
                    self.emotion_history[tid].pop(0)
            
            total_confidence += prob
            
            # Estimate posture (frontality) from bounding box
            if hasattr(track, 'box') and frame_shape:
                frontality = self._estimate_frontality(track.box, frame_shape)
                total_frontality += frontality
        
        total_faces = len(tracks)
        metrics.total_faces = total_faces
        
        # Compute percentages
        metrics.engaged_pct = (engagement_counts['engaged'] / total_faces) * 100
        metrics.neutral_pct = (engagement_counts['neutral'] / total_faces) * 100
        metrics.bored_pct = (engagement_counts['bored'] / total_faces) * 100
        metrics.confused_pct = (engagement_counts['confused'] / total_faces) * 100
        metrics.emotion_counts = engagement_counts
        
        # Determine dominant engagement (most-occurring label)
        if total_faces == 0:
            metrics.dominant_engagement = 'none'
        else:
            dominant = max(engagement_counts.items(), key=lambda x: x[1])[0]
            metrics.dominant_engagement = dominant
        
        # Compute score components
        attention = (engagement_counts['engaged'] + engagement_counts['neutral']) / total_faces
        
        posture = (total_frontality / total_faces) if total_faces > 0 else 0.0
        
        consistency = self._compute_consistency()
        
        density = min(total_faces / self.target_audience_size, 1.0)
        
        # Weighted score (0-100 scale)
        metrics.score = (
            self.attention_weight * attention * 100 +
            self.posture_weight * posture * 100 +
            self.consistency_weight * consistency * 100 +
            self.density_weight * density * 100
        )
        
        # Cap score at 100
        metrics.score = min(max(metrics.score, 0.0), 100.0)
        
        # Generate suggestion
        metrics.suggestion = self._generate_suggestion(metrics)
        
        return metrics
    
    def _estimate_frontality(self, box: Tuple[int, int, int, int], frame_shape: Tuple[int, int, int]) -> float:
        """
        Estimate face frontality (how much face is turned toward camera).
        
        A face is "frontal" if its bounding box is centered horizontally in the frame.
        This is a simple heuristic; ideally use face landmarks (yaw angle).
        
        Args:
            box: (x1, y1, x2, y2) bounding box.
            frame_shape: (height, width, channels).
        
        Returns:
            Frontality score (0-1), where 1 is perfectly frontal.
        """
        x1, y1, x2, y2 = box
        frame_height, frame_width, _ = frame_shape if frame_shape else (480, 640, 3)
        
        # Box center
        box_center_x = (x1 + x2) / 2
        frame_center_x = frame_width / 2
        
        # Distance from center as fraction of frame width
        distance_ratio = abs(box_center_x - frame_center_x) / (frame_width / 2)
        
        # Frontality: 1 if at center, decreases with distance
        frontality = max(0.0, 1.0 - distance_ratio)
        
        return frontality
    
    def _compute_consistency(self) -> float:
        """
        Compute emotion consistency (low emotion switching indicates stability).
        
        Returns:
            Consistency score (0-1), where 1 is perfect consistency.
        """
        if not self.emotion_history:
            return 0.5  # No history yet
        
        total_switches = 0
        total_comparisons = 0
        
        for track_id, emotions in self.emotion_history.items():
            if len(emotions) < 2:
                continue
            for i in range(1, len(emotions)):
                total_comparisons += 1
                if emotions[i] != emotions[i - 1]:
                    total_switches += 1
        
        if total_comparisons == 0:
            return 1.0
        
        switch_rate = total_switches / total_comparisons
        # Consistency is inverse of switch rate
        consistency = max(0.0, 1.0 - switch_rate)
        
        return consistency
    
    def _generate_suggestion(self, metrics: EngagementMetrics) -> str:
        """
        Generate a suggestion based on engagement metrics.
        
        Args:
            metrics: EngagementMetrics object.
        
        Returns:
            Suggestion string.
        """
        if metrics.total_faces == 0:
            return "No audience detected. Check camera."
        
        if metrics.score >= 80:
            return "Excellent! Keep the momentum going."
        elif metrics.score >= 60:
            return "Good engagement. Consider adding interactive elements."
        elif metrics.score >= 40:
            return "Moderate engagement. Try changing pace or asking questions."
        else:
            suggestions = []
            if metrics.bored_pct > 30:
                suggestions.append("audience seems bored")
            if metrics.confused_pct > 20:
                suggestions.append("some audience confused")
            if metrics.engaged_pct < 20:
                suggestions.append("low engagement detected")
            
            if suggestions:
                return "⚠ " + " | ".join(suggestions)
            else:
                return "Low engagement. Increase energy and interact with audience."
    
    def reset_history(self):
        """Clear emotion history (useful for new sessions)."""
        self.emotion_history.clear()
        self.frame_count = 0


def compute_engagement_score(
    tracks: List[Any],
    frame_shape: Tuple[int, int, int] = None,
    **kwargs
) -> EngagementMetrics:
    """
    Convenience function to compute engagement score from tracks.
    
    Args:
        tracks: List of Track objects from SimpleTracker.
        frame_shape: Frame dimensions (height, width, channels).
        **kwargs: Additional arguments for EngagementScoreComputer (e.g., target_audience_size).
    
    Returns:
        EngagementMetrics object.
    """
    computer = EngagementScoreComputer(**kwargs)
    return computer.compute(tracks, frame_shape)
