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

    # PINCH — highest priority
    if pinch_dist < 0.08:
        return "PINCH"

    # Count fingers up
    up_count = sum([index, middle, ring, pinky])

    # 0 fingers — FIST
    if up_count == 0:
        if (lm[8].y  > lm[5].y and
            lm[12].y > lm[9].y and
            lm[16].y > lm[13].y and
            lm[20].y > lm[17].y):
            return "FIST"

    # 1 finger
    if up_count == 1:
        if index:
            return "POINT"
        if pinky:
            return "PINKY"

    # 2 fingers
    if up_count == 2:
        if index and middle:
            return "PEACE"
        if index and pinky:
            return "ROCK"

    # 3 fingers
    if up_count == 3:
        if index and middle and ring:
            return "THREE_FINGERS"

    # 4 fingers
    if up_count == 4:
        if index and middle and ring and pinky:
            return "FOUR_FINGERS"

    return "UNKNOWN"