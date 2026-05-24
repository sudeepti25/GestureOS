import cv2
import mediapipe as mp
import csv
import os
import time

# --- Setup ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# --- Gestures to collect ---
GESTURES = [
    "POINT",
    "PEACE",
    "THREE_FINGERS",
    "FOUR_FINGERS",
    "FIST",
    "ROCK",
    "PINKY",
    
    "UNKNOWN"
]

# --- Config ---
SAMPLES_PER_GESTURE = 300    # collect 300 samples per gesture
DATA_FILE = "ml/data.csv"
os.makedirs("ml", exist_ok=True)

# --- CSV setup ---
# Each row = 21 landmarks * 3 values (x,y,z) + label = 64 columns
def get_landmark_row(hand_landmarks, label):
    row = []
    for lm in hand_landmarks.landmark:
        row.extend([lm.x, lm.y, lm.z])
    row.append(label)
    return row

# --- Write header if file doesn't exist ---
file_exists = os.path.exists(DATA_FILE)
csv_file = open(DATA_FILE, "a", newline="")
writer = csv.writer(csv_file)

if not file_exists:
    # Write header
    header = []
    for i in range(21):
        header.extend([f"x{i}", f"y{i}", f"z{i}"])
    header.append("label")
    writer.writerow(header)

# --- Webcam ---
cap = cv2.VideoCapture(0)

print("=" * 50)
print("GestureOS — Data Collection")
print("=" * 50)
print(f"Collecting {SAMPLES_PER_GESTURE} samples per gesture")
print(f"Saving to: {DATA_FILE}")
print()

current_gesture_idx = 0
collecting = False
sample_count = 0
countdown = 0
countdown_start = 0

print(f"Ready to collect: {GESTURES[current_gesture_idx]}")
print("Press SPACE to start collecting, N for next gesture, Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Draw landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Collect sample if active
            if collecting and sample_count < SAMPLES_PER_GESTURE:
                gesture_name = GESTURES[current_gesture_idx]
                row = get_landmark_row(hand_landmarks, gesture_name)
                writer.writerow(row)
                sample_count += 1

    # Check if done collecting
    if collecting and sample_count >= SAMPLES_PER_GESTURE:
        collecting = False
        print(f"✅ {GESTURES[current_gesture_idx]} — {SAMPLES_PER_GESTURE} samples collected!")

        # Move to next gesture automatically
        current_gesture_idx += 1
        sample_count = 0

        if current_gesture_idx >= len(GESTURES):
            print("\n🎉 All gestures collected! Run train.py next.")
            break
        else:
            print(f"\nNext: {GESTURES[current_gesture_idx]}")
            print("Press SPACE to start collecting")

    # --- Display ---
    gesture_name = GESTURES[current_gesture_idx] if current_gesture_idx < len(GESTURES) else "DONE"

    # Background box
    cv2.rectangle(frame, (0, 0), (w, 110), (0, 0, 0), -1)

    # Current gesture
    cv2.putText(frame, f"Gesture: {gesture_name}",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, (0, 255, 0), 2)

    # Sample count progress bar
    if SAMPLES_PER_GESTURE > 0:
        bar = int((sample_count / SAMPLES_PER_GESTURE) * (w - 40))
        cv2.rectangle(frame, (20, 50), (w - 20, 70), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 50), (20 + bar, 70), (0, 255, 0), -1)
        cv2.putText(frame, f"{sample_count}/{SAMPLES_PER_GESTURE}",
                    (20, 95), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (200, 200, 200), 1)

    # Status
    status = "COLLECTING..." if collecting else "Press SPACE to collect"
    color = (0, 255, 0) if collecting else (0, 200, 255)
    cv2.putText(frame, status,
                (w - 280, 95), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, color, 1)

    # Instructions
    cv2.putText(frame, "SPACE=collect  N=skip  Q=quit",
                (20, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                0.45, (150, 150, 150), 1)

    cv2.imshow("GestureOS - Data Collection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord(' '):
        # Start collecting
        collecting = True
        sample_count = 0
        print(f"Collecting {GESTURES[current_gesture_idx]}... hold the gesture!")
    elif key == ord('n'):
        # Skip this gesture
        print(f"Skipped: {GESTURES[current_gesture_idx]}")
        current_gesture_idx += 1
        sample_count = 0
        collecting = False
        if current_gesture_idx >= len(GESTURES):
            print("All gestures done!")
            break
        print(f"Next: {GESTURES[current_gesture_idx]}")

csv_file.close()
cap.release()
cv2.destroyAllWindows()
print(f"\nData saved to {DATA_FILE}")
print("Now run: python train.py")