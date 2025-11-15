def map_emotion_to_engagement(emotion):
    if emotion == "happy":
        return "engaged"
    if emotion in ["neutral", "surprise"]:
        return "neutral"
    if emotion in ["anger", "disgust", "fear", "sad"]:
        return "bored"
    return "neutral"


def interpret_pose(keypoints):
    """
    keypoints shape varies; YOLO sometimes gives very few.
    We handle all edge cases safely.
    """
    if keypoints is None or len(keypoints) < 3:
        return "neutral"

    # Extract what we can
    try:
        left_eye = keypoints[1][:2]
        right_eye = keypoints[2][:2]
        nose = keypoints[0][:2]
    except:
        return "neutral"

    # Looking away
    if abs(left_eye[0] - right_eye[0]) > 90:
        return "looking_away"

    # Tilted head
    if abs(left_eye[1] - right_eye[1]) > 25:
        return "confused"

    return "neutral"
