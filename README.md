GestureOS — Touchless Laptop Control
=====================================
Requirements:
- Windows 10 or 11
- Webcam (built-in or USB)
- Visual C++ Redistributable (download from Microsoft if needed)

How to run:
1. Extract this folder
2. Double click GestureOS.exe
3. Show your hand to the webcam

Gestures:
☝️  Index finger     → Move mouse
✌️  Peace sign       → Select/drag
🤟  3 fingers        → Copy
🖐️  4 fingers        → Paste
🤏  Pinch            → Click
🤘  Rock sign        → Screenshot
✊  Fist             → Start menu
🤙  Pinky            → Escape
☝️☝️ Both index      → Double click
🖐️🖐️ Both 4 fingers → Scroll up
✊✊ Both fists       → Scroll down

To customize gestures — edit config.json in this folder.



if .exe crashes run this on terminal
pyinstaller --onefile --noconsole --name GestureOS \
  --collect-data mediapipe \
  --collect-data cv2 \
  main.py