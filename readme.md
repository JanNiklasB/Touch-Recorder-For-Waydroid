# Waydroid Touch Recorder

This tool is designed to record and replay touch events and key presses in waydroid.
It is based on `python-libevdev`, `PyQt6`, and the kde plasma wayland desktop.

## Notes:
- The tool is equipped with a UI to easily record and replay macros.
- You are asked to give the tool sudo access for the waydroid shell, but it will also work with adb, just decline
  > adb might introduce some input lag, but should work fine
- Currently no movement is recorded, only presses, this is because the amount of inputs that are generated from replaying accurate movement is causing massive delays
  > I only needed the `DOWN` and `UP` events in my case, if you know a way to send movement to waydroid without input delay, then please contribute


## Installation:
- Install Requirements:
  - python
  - `pip install libevdev PyQt6`
- Download Repository and start `main.py`

## GUI Example:
![Example GUI](./GUIExample.png?raw=true "GUI")