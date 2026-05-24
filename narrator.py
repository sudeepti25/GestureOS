import threading
import time
import pyautogui
try:
    import pywinauto
    from pywinauto import Desktop
    PYWINAUTO_AVAILABLE = True
except:
    PYWINAUTO_AVAILABLE = False

# --- Narrator state ---
last_spoken_element = ""
last_check_time = 0
CHECK_INTERVAL = 0.5      # check what's under cursor every 0.5 seconds
narrator_running = False
narrator_thread = None

def get_element_under_cursor():
    """
    Gets the name and type of UI element currently under mouse cursor
    Returns a string like "Submit button" or "File menu item"
    """
    if not PYWINAUTO_AVAILABLE:
        return ""

    try:
        # Get current mouse position
        x, y = pyautogui.position()

        # Use Desktop to find element at cursor position
        desktop = Desktop(backend="uia")
        element = desktop.from_point(x, y)

        if element is None:
            return ""

        # Get element properties
        try:
            name = element.window_text()
        except:
            name = ""

        try:
            ctrl_type = element.element_info.control_type
        except:
            ctrl_type = ""

        # Clean up control type name
        type_map = {
            "Button":     "button",
            "MenuItem":   "menu item",
            "Edit":       "text field",
            "Text":       "text",
            "List":       "list",
            "ListItem":   "list item",
            "ComboBox":   "dropdown",
            "CheckBox":   "checkbox",
            "RadioButton":"radio button",
            "Tab":        "tab",
            "TabItem":    "tab",
            "Hyperlink":  "link",
            "Image":      "image",
            "ToolBar":    "toolbar",
            "Menu":       "menu",
            "Window":     "window",
            "Pane":       "pane",
            "Document":   "document",
            "ScrollBar":  "scrollbar",
            "Slider":     "slider",
            "Tree":       "tree",
            "TreeItem":   "tree item",
            "Group":      "group",
            "StatusBar":  "status bar",
        }
        friendly_type = type_map.get(ctrl_type, ctrl_type.lower() if ctrl_type else "")

        # Build spoken string
        if name and friendly_type:
            return f"{name}, {friendly_type}"
        elif name:
            return name
        elif friendly_type:
            return friendly_type
        else:
            return ""

    except Exception:
        return ""

def get_window_title():
    """Gets the title of the currently focused window"""
    try:
        import pywinauto
        app = pywinauto.application.Application(backend="uia")
        desktop = Desktop(backend="uia")
        focused = desktop.from_point(*pyautogui.position())
        # Walk up to find window title
        el = focused
        for _ in range(5):
            try:
                parent = el.parent()
                if parent and parent.window_text():
                    el = parent
                else:
                    break
            except:
                break
        title = el.window_text()
        return title if title else ""
    except:
        return ""

def narrator_loop(speak_fn):
    """
    Runs in background thread
    Continuously checks what element is under cursor
    Speaks it if it changed
    """
    global last_spoken_element, last_check_time, narrator_running

    print("Narrator started — hover over elements to hear them")

    while narrator_running:
        now = time.time()

        # Only check every CHECK_INTERVAL seconds
        if now - last_check_time >= CHECK_INTERVAL:
            last_check_time = now

            element_text = get_element_under_cursor()

            # Only speak if element changed
            if element_text and element_text != last_spoken_element:
                last_spoken_element = element_text
                speak_fn(element_text)

        time.sleep(0.05)  # small sleep to avoid hammering CPU

def start_narrator(speak_fn):
    """Start the narrator background thread"""
    global narrator_running, narrator_thread
    narrator_running = True
    narrator_thread = threading.Thread(
        target=narrator_loop,
        args=(speak_fn,),
        daemon=True
    )
    narrator_thread.start()
    print("Narrator thread started!")

def stop_narrator():
    """Stop the narrator thread"""
    global narrator_running
    narrator_running = False
    print("Narrator stopped")

def narrate_click(speak_fn):
    """Call this when user clicks — speaks what was clicked"""
    element = get_element_under_cursor()
    if element:
        speak_fn(f"Clicked: {element}")
    else:
        speak_fn("Clicked")

def narrate_window_focus(speak_fn):
    """Speaks the current window title"""
    title = get_window_title()
    if title:
        speak_fn(f"Window: {title}")