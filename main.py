import cv2
import mediapipe as mp
import pyttsx3
import threading
import queue
from gesture import classify_gesture
from actions import execute_action

# --- Voice setup ---
speech_queue = queue.Queue()

def speech_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Voice error: {e}")
        speech_queue.task_done()

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def speak(text):
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
        except:
            pass
    speech_queue.put(text)

# --- MediaPipe setup ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# --- Webcam ---
cap = cv2.VideoCapture(0)
print("GestureOS started!")
print("Gestures:")
print("  ☝️  Index only          → Move mouse / click / double click")
print("  ✌️  Index + Middle      → Drag / Select")
print("  🤟  Three fingers       → Copy Ctrl+C")
print("  🖐️  Four fingers        → Paste Ctrl+V")
print("  🤏  Pinch               → Instant click")
print("  🤘  Rock                → Screenshot")
print("  ✊  Fist                → Win key")
print("  🤙  Pinky               → Escape")
print("  ☝️☝️ Both index          → Double click")
print("  🖐️🖐️ Both four fingers   → Scroll up")
print("  ✊✊ Both fists           → Scroll down")
print("\nPress Q to quit\n")
speak("Gesture OS ready. Show your hand.")

# --- Stability counter ---
STABILITY_FRAMES = 12
gesture_counter = {}
last_stable_gesture = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    current_gesture = "NO_HAND"
    point_count = 0
    four_fingers_count = 0
    fist_count = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw skeleton
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style()
            )

            g = classify_gesture(hand_landmarks)

            # Count gestures across both hands
            if g == "POINT":
                point_count += 1
            if g == "FOUR_FINGERS":
                four_fingers_count += 1
            if g == "FIST":
                fist_count += 1

            # First hand sets the main gesture
            if current_gesture == "NO_HAND":
                current_gesture = g

        # Two hand gesture overrides — checked after all hands processed
        if point_count == 2:
            current_gesture = "DOUBLE_POINT"
        elif four_fingers_count == 2:
            current_gesture = "DOUBLE_PALM"
        elif fist_count == 2:
            current_gesture = "DOUBLE_FIST"

        # Stability counter
        gesture_counter[current_gesture] = gesture_counter.get(current_gesture, 0) + 1
        for g in list(gesture_counter.keys()):
            if g != current_gesture:
                gesture_counter[g] = 0

        # Fire action when stable
        if gesture_counter.get(current_gesture, 0) >= STABILITY_FRAMES:
            try:
                execute_action(current_gesture, results.multi_hand_landmarks[0], w, h, speak)
            except Exception as e:
                print(f"Action error: {e}")

            if current_gesture != last_stable_gesture:
                print(f"Gesture: {current_gesture}")
                last_stable_gesture = current_gesture

    else:
        gesture_counter = {}
        last_stable_gesture = None
        current_gesture = "NO_HAND"

    # Color map
    color_map = {
        "POINT":         (0, 255, 0),
        "PEACE":         (255, 255, 0),
        "THREE_FINGERS": (255, 128, 0),
        "FOUR_FINGERS":  (0, 200, 255),
        "PINCH":         (128, 0, 255),
        "FIST":          (0, 0, 255),
        "ROCK":          (255, 0, 128),
        "PINKY":         (128, 128, 0),
        "DOUBLE_POINT":  (0, 255, 255),
        "DOUBLE_PALM":   (0, 200, 100),
        "DOUBLE_FIST":   (100, 0, 255),
        "NO_HAND":       (100, 100, 100),
        "UNKNOWN":       (50, 50, 50),
    }
    color = color_map.get(current_gesture, (255, 255, 255))

    # Display gesture name
    cv2.putText(frame, f"Gesture: {current_gesture}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, color, 2)

    # Stability bar
    count = gesture_counter.get(current_gesture, 0)
    bar_width = int((count / STABILITY_FRAMES) * 200)
    bar_width = min(bar_width, 200)
    cv2.rectangle(frame, (20, 60), (220, 75), (50, 50, 50), -1)
    cv2.rectangle(frame, (20, 60), (20 + bar_width, 75), color, -1)
    cv2.putText(frame, "Hold steady", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

    cv2.putText(frame, "GestureOS | Press Q to quit",
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (200, 200, 200), 1)

    cv2.imshow("GestureOS", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

speech_queue.put(None)
cap.release()
cv2.destroyAllWindows()
print("GestureOS closed.")