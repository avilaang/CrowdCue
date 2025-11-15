def emotion_to_engagement(emotion):
    emotion = emotion.lower()

    if emotion in ["happy", "surprise"]:
        return "engaged"

    if emotion == "neutral":
        return "neutral"

    if emotion in ["sad", "angry", "disgust", "fear"]:
        return "bored"

    return "neutral"
