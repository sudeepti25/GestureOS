import mediapipe as mp
import math
import pickle
import os
import numpy as np

mp_hands = mp.solutions.hands

# --- Try to load ML model ---
MODEL_FILE = "ml/model.pkl"
ENCODER_FILE = "ml/encoder.pkl"

ml_model = None
ml_encoder = None

if os.path.exists(MODEL_FILE) and os.path.exists(ENCODER_FILE):
    try:
        with open(MODEL_FILE, "rb") as f:
            ml_model = pickle.load(f)
        with open(ENCODER_FILE, "rb") as f:
            ml_encoder = pickle.load(f)
        print("✅ ML model loaded — using trained classifier")
    except Exception as e:
        print(f"ML model load failed: {e} — using rule-based")
else:
    print("No ML model found — using rule-based classifier")

def get_landmark_features(hand_landmarks):
    """Extract 63 features (21 landmarks * x,y,z) for ML model"""
    features = []
    for lm in hand_landmarks.landmark:
        features.extend([lm.x, lm.y, lm.z])
    return np.array(features).reshape(1, -1)

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

def classify_gesture_rules(hand_landmarks):
    """Original rule-based classifier — fallback"""
    f = get_finger_states(hand_landmarks)
    pinch_dist = get_pinch_distance(hand_landmarks)
    lm = hand_landmarks.landmark

    index  = f["index"]
    middle = f["middle"]
    ring   = f["ring"]
    pinky  = f["pinky"]

    if pinch_dist < 0.08:
        return "PINCH"

    up_count = sum([index, middle, ring, pinky])

    if up_count == 0:
        if (lm[8].y > lm[5].y and lm[12].y > lm[9].y and
            lm[16].y > lm[13].y and lm[20].y > lm[17].y):
            return "FIST"

    if up_count == 1:
        if index: return "POINT"
        if pinky: return "PINKY"

    if up_count == 2:
        if index and middle: return "PEACE"
        if index and pinky:  return "ROCK"

    if up_count == 3:
        if index and middle and ring: return "THREE_FINGERS"

    if up_count == 4:
        if index and middle and ring and pinky: return "FOUR_FINGERS"

    return "UNKNOWN"

# def classify_gesture_ml(hand_landmarks):
#     """ML-based classifier"""
#     try:
#         features = get_landmark_features(hand_landmarks)
#         prediction = ml_model.predict(features)[0]
#         gesture = ml_encoder.inverse_transform([prediction])[0]

#         # Still use pinch distance check — ML is less reliable for pinch
#         pinch_dist = get_pinch_distance(hand_landmarks)
#         if pinch_dist < 0.08:
#             return "PINCH"

#         return gesture
#     except Exception as e:
#         print(f"ML prediction error: {e}")
#         return classify_gesture_rules(hand_landmarks)
def classify_gesture_ml(hand_landmarks):
    try:
        features = get_landmark_features(hand_landmarks)
        prediction = ml_model.predict(features)[0]
        gesture = ml_encoder.inverse_transform([prediction])[0]
        
        # DEBUG — print prediction confidence
        proba = ml_model.predict_proba(features)[0]
        max_conf = max(proba)
        print(f"ML: {gesture} ({max_conf*100:.0f}% confident)")
        
        return gesture
    except Exception as e:
        print(f"ML prediction error: {e}")
        return classify_gesture_rules(hand_landmarks)

def classify_gesture(hand_landmarks):
    """
    Main classifier — uses ML if available, falls back to rules
    """
    
    return classify_gesture_rules(hand_landmarks)