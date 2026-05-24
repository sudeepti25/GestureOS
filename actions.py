import pyautogui
import time
from config_loader import load_config, get_settings, get_gestures

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Load config
config = load_config()
settings = get_settings(config)
gesture_map = get_gestures(config)

SCREEN_W, SCREEN_H = pyautogui.size()
last_action_time = {}
COOLDOWN = settings["cooldown"]
mouse_held = False

# Settings
MARGIN = settings["margin"]
MOVEMENT_THRESHOLD = settings["movement_threshold"]
SINGLE_CLICK_FRAMES = settings["single_click_frames"]

# Click tracking
still_frame_count = 0
click_fired = False

# Exponential smoothing
SMOOTH_ALPHA = 0.5
DEAD_ZONE = 8
VELOCITY_SCALE = 1.2
smooth_x = None
smooth_y = None
prev_raw_x = None
prev_raw_y = None

def can_fire(gesture):
    now = time.time()
    last = last_action_time.get(gesture, 0)
    if now - last >= COOLDOWN:
        last_action_time[gesture] = now
        return True
    return False

def move_mouse(hand_landmarks):
    global smooth_x, smooth_y, prev_raw_x, prev_raw_y

    tip = hand_landmarks.landmark[8]
    raw_x = tip.x
    raw_y = tip.y

    mapped_x = (raw_x - MARGIN) / (1 - 2 * MARGIN)
    mapped_y = (raw_y - MARGIN) / (1 - 2 * MARGIN)
    mapped_x = max(0.0, min(1.0, mapped_x))
    mapped_y = max(0.0, min(1.0, mapped_y))

    target_x = int(mapped_x * SCREEN_W)
    target_y = int(mapped_y * SCREEN_H)

    # First frame
    if smooth_x is None:
        smooth_x = target_x
        smooth_y = target_y
        prev_raw_x = target_x
        prev_raw_y = target_y
        return smooth_x, smooth_y

    delta_x = abs(target_x - prev_raw_x)
    delta_y = abs(target_y - prev_raw_y)
    prev_raw_x = target_x
    prev_raw_y = target_y

    # Dead zone
    if delta_x < DEAD_ZONE and delta_y < DEAD_ZONE:
        return smooth_x, smooth_y

    # Dynamic alpha
    movement = delta_x + delta_y
    if movement > 80:
        alpha = min(SMOOTH_ALPHA * VELOCITY_SCALE * 2, 0.8)
    elif movement > 30:
        alpha = SMOOTH_ALPHA * VELOCITY_SCALE
    else:
        alpha = SMOOTH_ALPHA * 0.6

    smooth_x = int(alpha * target_x + (1 - alpha) * smooth_x)
    smooth_y = int(alpha * target_y + (1 - alpha) * smooth_y)

    pyautogui.moveTo(smooth_x, smooth_y, duration=0.0)
    return smooth_x, smooth_y

def fire_from_config(gesture, speak):
    if gesture not in gesture_map:
        return
    cfg = gesture_map[gesture]
    action = cfg.get("action", "")
    keys = cfg.get("keys", "")
    say = cfg.get("say", "")

    try:
        if action == "hotkey":
            key_list = keys.split("+")
            pyautogui.hotkey(*key_list)
        elif action == "key":
            pyautogui.press(keys)
        elif action == "scroll":
            value = cfg.get("value", 5)   # default 5 if not set
            if keys == "up":
                pyautogui.scroll(value)
        elif keys == "down":
            pyautogui.scroll(-value)
    except Exception as e:
        print(f"Config action error: {e}")

    if say:
        speak(say)

def execute_action(gesture, hand_landmarks, frame_w, frame_h, speak):
    global mouse_held, still_frame_count, click_fired

    # POINT — move mouse + hold to click
    if gesture == "POINT":
        if mouse_held:
            pyautogui.mouseUp()
            mouse_held = False
            speak("Selection released")

        curr_x, curr_y = move_mouse(hand_landmarks)
        prev_x = prev_raw_x if prev_raw_x else curr_x
        prev_y = prev_raw_y if prev_raw_y else curr_y
        movement = abs(curr_x - prev_x) + abs(curr_y - prev_y)

        if movement < MOVEMENT_THRESHOLD:
            still_frame_count += 1
            if still_frame_count == SINGLE_CLICK_FRAMES and not click_fired:
                pyautogui.click()
                speak("Click")
                print("Single click!")
                click_fired = True
        else:
            still_frame_count = 0
            click_fired = False
        return

    # DOUBLE_POINT — both index fingers = double click
    if gesture == "DOUBLE_POINT":
        if can_fire("DOUBLE_POINT"):
            pyautogui.doubleClick()
            speak("Double click")
            print("Double click!")
        return

    # PEACE — drag / select
    if gesture == "PEACE":
        if not mouse_held:
            pyautogui.mouseDown(button='left')
            mouse_held = True
            speak("Selecting")
        else:
            move_mouse(hand_landmarks)
        return

    # Release mouse for all other gestures
    if mouse_held:
        pyautogui.mouseUp()
        mouse_held = False

    if not can_fire(gesture):
        return

    fire_from_config(gesture, speak)