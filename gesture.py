import mediapipe as mp
import math

mp_hands = mp.solutions.hands

def get_finger_states(hand_landmarks):
    lm = hand_landmarks.landmark
    fingers = {
        "index":  lm[8].y  < lm[6].y,
        "middle": lm[12].y < lm[10].y,
        "ring":   lm[16].y < lm[14].y,
        "pinky":  lm[20].y < lm[18].y,
    }
    return fingers

def get_pinch_distance(hand_landmarks):
    lm = hand_landmarks.landmark
    thumb = lm[4]
    index = lm[8]
    return math.sqrt((thumb.x - index.x)**2 + (thumb.y - index.y)**2)

def classify_gesture(hand_landmarks):
    f = get_finger_states(hand_landmarks)
    pinch_dist = get_pinch_distance(hand_landmarks)
    lm = hand_landmarks.landmark

    index  = f["index"]
    middle = f["middle"]
    ring   = f["ring"]
    pinky  = f["pinky"]

    # PINCH — click (thumb + index touch)
    

    # POINT — only index up → move mouse
    if index and not middle and not ring and not pinky:
        return "POINT"

    # PEACE — index + middle → start selecting (mouseDown + drag)
    if index and middle and not ring and not pinky:
        return "PEACE"

    # THREE_FINGERS — index + middle + ring → copy Ctrl+C
    if index and middle and ring and not pinky:
        return "THREE_FINGERS"

    # FOUR_FINGERS — index + middle + ring + pinky (no thumb) → paste Ctrl+V
    if index and middle and ring and pinky:
        return "FOUR_FINGERS"

    # FIST — all down → Win key
    if not index and not middle and not ring and not pinky:
        return "FIST"

    # ROCK — index + pinky up → screenshot
    if index and not middle and not ring and pinky:
        return "ROCK"

    # PINKY only → escape
    if pinky and not index and not middle and not ring:
        return "PINKY"

    return "UNKNOWN"