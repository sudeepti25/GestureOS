import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """Load config.json — creates default if not found"""
    if not os.path.exists(CONFIG_PATH):
        print("config.json not found — using defaults")
        return get_defaults()
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            print("Config loaded successfully")
            return config
    except Exception as e:
        print(f"Config error: {e} — using defaults")
        return get_defaults()

def get_defaults():
    return {
        "gestures": {
            "THREE_FINGERS": {"action": "hotkey", "keys": "ctrl+c", "say": "Copied"},
            "FOUR_FINGERS":  {"action": "hotkey", "keys": "ctrl+v", "say": "Pasted"},
           
            "ROCK":          {"action": "hotkey", "keys": "win+printscreen", "say": "Screenshot saved"},
            "PINKY":         {"action": "key",    "keys": "q",    "say": "Escape"},
            "DOUBLE_PALM":   {"action": "scroll", "keys": "up",     "say": "Scroll up"},
            "DOUBLE_FIST":   {"action": "scroll", "keys": "down",   "say": "Scroll down"}
        },
        "settings": {
            "stability_frames": 12,
            "smooth_frames": 3,
            "margin": 0.20,
            "movement_threshold": 100,
            "single_click_frames": 8,
            "narrator_interval": 0.5,
            "speech_rate": 150,
            "cooldown": 1.5
        }
    }

def get_settings(config):
    return config.get("settings", get_defaults()["settings"])

def get_gestures(config):
    return config.get("gestures", get_defaults()["gestures"])