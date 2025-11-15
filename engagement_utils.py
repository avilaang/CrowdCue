def combine_engagement(emotion_engagement, pose_state):
    # Pose overrides emotion
    if pose_state == "confused":
        return "confused"
    if pose_state == "looking away":
        return "bored"
    return emotion_engagement


def suggestion_for(engagement):
    if engagement == "engaged":
        return "Continue 👍"
    if engagement == "neutral":
        return "Add example or statistic 📘"
    if engagement == "bored":
        return "Increase energy / tell a joke 🔥"
    if engagement == "confused":
        return "Clarify / Slow down ❓"
    return ""


def color_for(engagement):
    if engagement == "engaged":
        return (0, 255, 0)     # green
    if engagement == "neutral":
        return (255, 255, 0)   # yellow
    if engagement == "bored":
        return (0, 140, 255)   # orange
    if engagement == "confused":
        return (0, 0, 255)     # red
    return (255, 255, 255)
