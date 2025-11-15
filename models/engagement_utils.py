def emotion_to_engagement(emotion):
    emotion = emotion.lower()

    if emotion in ["happy", "surprise"]:
        return "engaged"

    if emotion == "neutral":
        return "neutral"

    if emotion in ["sad", "angry", "disgust", "fear"]:
        return "bored"

    return "neutral"


# Per-class confidence thresholds — tuneable
DEFAULT_CONF_THRESH = 0.45
CLASS_CONF_THRESH = {
    # give 'happy' a higher bar to avoid false positives
    'happy': 0.60,
    # neutral can be lower
    'neutral': 0.25,
}


def apply_conf_threshold(label, prob):
    """Return (label, prob) after applying per-class thresholds.

    If the prediction is below the class threshold, fallback to 'neutral'.
    """
    if label is None:
        return 'neutral', 0.0

    l = str(label).lower()
    thresh = CLASS_CONF_THRESH.get(l, DEFAULT_CONF_THRESH)
    if prob < thresh:
        return 'neutral', prob
    return l, prob
