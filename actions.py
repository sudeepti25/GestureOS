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
SMOOTH_FRAMES = 3
x_history = collections.deque(maxlen=SMOOTH_FRAMES)
y_history = collections.deque(maxlen=SMOOTH_FRAMES)
MARGIN = 0.20

# Click tracking
prev_x, prev_y = 0, 0
MOVEMENT_THRESHOLD = 100
still_frame_count = 0
SINGLE_CLICK_FRAMES = 8
click_fired = False

def can_fire(gesture):
    now = time.time()
    last = last_action_time.get(gesture, 0)
    if now - last >= COOLDOWN:
        last_action_time[gesture] = now
        return True
    return False

def move_mouse(hand_landmarks):
    tip = hand_landmarks.landmark[8]
    raw_x = tip.x
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
    pyautogui.moveTo(smooth_x, smooth_y, duration=0.0)
    return smooth_x, smooth_y

def execute_action(gesture, hand_landmarks, frame_w, frame_h, speak):
    global mouse_held, prev_x, prev_y
    global still_frame_count, click_fired

    # POINT — move mouse + hold to click
    if gesture == "POINT":
        if mouse_held:
            pyautogui.mouseUp()
            mouse_held = False
            speak("Selection released")
        curr_x, curr_y = move_mouse(hand_landmarks)
        movement = abs(curr_x - prev_x) + abs(curr_y - prev_y)
        prev_x, prev_y = curr_x, curr_y
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

    # DOUBLE_PALM — both four fingers = scroll up
    if gesture == "DOUBLE_PALM":
        pyautogui.scroll(5)
        speak("Scroll up")
        print("Scroll up!")
        return

    # DOUBLE_FIST — both fists = scroll down
    if gesture == "DOUBLE_FIST":
        pyautogui.scroll(-5)
        speak("Scroll down")
        print("Scroll down!")
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

    # PINCH — instant click
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

    # Release mouse for all remaining gestures
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
        pyautogui.press('q')
        speak("Escape")