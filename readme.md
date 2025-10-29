# Touch Recorder For Waydroid

This tool is designed to record and replay touch events and key presses in waydroid.
It is based on `python-libevdev`, `PyQt6`, and the kde plasma wayland desktop.

## Notes:
- The tool is equipped with a UI to easily record and replay macros.
- You are asked to give the tool sudo access for the waydroid shell, but it will also work with adb, just decline
  > adb might introduce some input lag, but should work fine
- Currently no movement is recorded, only presses, this is because the amount of inputs that are generated from replaying accurate movement is causing massive delays
  > I only needed the `DOWN` and `UP` events in my case, if you know a way to send movement to waydroid without input delay, then please contribute

## Advanced Configuration:
The tool creates the `WaydroidTouchRecorder.ini` file in its install directory after its first launch. You can modify this file to change some options, but only modify the file while the tool is not running, otherwise the settings might not be applied correctly.

### Option Explanations:
- `inputstotaps`: If True converts inputs in a defined threshold to taps (might increase precision) and reduces movement inputs (less accurate movement paths but much better performance)
- `timetolerance`: If any movement action (DOWN -> MOVEMENT -> UP) is <= `timetolerance` convert to tap if other threshold is also True
- `pixeltolerance`: If movement is in box with sidelength `pixeltolerance` convert action to tap if other threshold is also True
- `movementcooldown`: Cooldown for movement input, set to 0 to disable this function while keeping the above

## Installation:
- Install Requirements:
  - python
  - `pip install libevdev PyQt6`
- Download Repository and start `main.py`

## GUI Example:
![Example GUI](./GUIExample.png?raw=true "GUI")