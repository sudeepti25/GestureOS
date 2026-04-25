import pyautogui
import time
import collections

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

SCREEN_W, SCREEN_H = pyautogui.size()
last_action_time = {}
COOLDOWN = 1.5
mouse_held = False

# Smoothing
SMOOTH_FRAMES = 5
x_history = collections.deque(maxlen=SMOOTH_FRAMES)
y_history = collections.deque(maxlen=SMOOTH_FRAMES)
MARGIN = 0.20

# Hold duration tracking
# Click / double click tracking
prev_x, prev_y = 0, 0
MOVEMENT_THRESHOLD = 100
still_frame_count = 0
SINGLE_CLICK_FRAMES = 8
click_fired = False

# Double tap tracking — raise/lower finger twice
last_point_gone_time = 0    # when finger was last lowered
last_point_seen_time = 0    # when finger was last raised
DOUBLE_TAP_GAP = 0.6        # max seconds between tap and re-tap
tap_stage = 0               # 0=idle, 1=first tap done, waiting for second       # so click only fires once per stop

def can_fire(gesture):
    now = time.time()
    last = last_action_time.get(gesture, 0)
    if now - last >= COOLDOWN:
        last_action_time[gesture] = now
        return True
    return False

def move_mouse(hand_landmarks):
    tip = hand_landmarks.landmark[8]
    raw_x = 1 - tip.x
    raw_y = tip.y
    mapped_x = (raw_x - MARGIN) / (1 - 2 * MARGIN)
    mapped_y = (raw_y - MARGIN) / (1 - 2 * MARGIN)
    mapped_x = max(0.0, min(1.0, mapped_x))
    mapped_y = max(0.0, min(1.0, mapped_y))
    screen_x = int(mapped_x * SCREEN_W)
    screen_y = int(mapped_y * SCREEN_H)
    x_history.append(screen_x)
    y_history.append(screen_y)
    smooth_x = int(sum(x_history) / len(x_history))
    smooth_y = int(sum(y_history) / len(y_history))
    pyautogui.moveTo(smooth_x, smooth_y, duration=0.08)
    return smooth_x, smooth_y

def execute_action(gesture, hand_landmarks, frame_w, frame_h, speak):
    global mouse_held, prev_x, prev_y, still_frame_count, click_fired
    global tap_stage, last_point_gone_time, last_point_seen_time
    # POINT — move mouse + hold to click / double click
    if gesture == "POINT":
        if mouse_held:
            pyautogui.mouseUp()
            mouse_held = False
            speak("Selection released")

        curr_x, curr_y = move_mouse(hand_landmarks)
        movement = abs(curr_x - prev_x) + abs(curr_y - prev_y)
        prev_x, prev_y = curr_x, curr_y
        now = time.time()

        if movement < MOVEMENT_THRESHOLD:
            still_frame_count += 1

            # Single click on short hold
            if still_frame_count == SINGLE_CLICK_FRAMES and not click_fired:
                # Check if this is second tap within gap window
                if tap_stage == 1 and (now - last_point_gone_time) < DOUBLE_TAP_GAP:
                    # Second tap — double click!
                    pyautogui.doubleClick()
                    speak("Double click")
                    print("Double click!")
                    tap_stage = 0
                    click_fired = True
                else:
                    # First tap — single click
                    pyautogui.click()
                    speak("Click")
                    print("Single click — tap again quickly for double click")
                    tap_stage = 1
                    last_point_seen_time = now
                    click_fired = True
        else:
            still_frame_count = 0
            click_fired = False

        return
    
    # Track when POINT gesture disappears
    # This runs for ANY non-POINT gesture
    if gesture != "POINT":
        now = time.time()
        if tap_stage == 1:
            # Finger was lowered after first tap
            last_point_gone_time = now
            # If too much time passed since first tap — reset
            if now - last_point_seen_time > DOUBLE_TAP_GAP:
                tap_stage = 0
                print("Double tap window expired")
        still_frame_count = 0
        click_fired = False
    # PEACE — start selecting / drag
    if gesture == "PEACE":
        if not mouse_held:
            pyautogui.mouseDown(button='left')
            mouse_held = True
            speak("Selecting")
        else:
            move_mouse(hand_landmarks)
        return

    # PINCH — instant click without waiting
    if gesture == "PINCH":
        if mouse_held:
            pyautogui.mouseUp()
            mouse_held = False
            speak("Released")
            return
        if can_fire("PINCH"):
            try:
                pyautogui.click()
                speak("Click")
            except Exception as e:
                print(f"Click error: {e}")
        return

    # Release mouse for all other gestures
    if mouse_held:
        pyautogui.mouseUp()
        mouse_held = False

    if not can_fire(gesture):
        return

    if gesture == "THREE_FINGERS":
        pyautogui.hotkey('ctrl', 'c')
        speak("Copied")

    elif gesture == "FOUR_FINGERS":
        pyautogui.hotkey('ctrl', 'v')
        speak("Pasted")

    elif gesture == "ROCK":
        pyautogui.hotkey('win', 'printscreen')
        speak("Screenshot saved")

    elif gesture == "FIST":
        pyautogui.press('win')
        speak("Start menu")

    elif gesture == "PINKY":
        pyautogui.press('esc')
        speak("Escape")

    elif gesture == "OPEN_PALM":
        pyautogui.scroll(3)
        speak("Scrolling up")