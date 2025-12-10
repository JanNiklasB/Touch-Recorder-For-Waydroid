# Touch Recorder For Waydroid

This tool is designed to record and replay touch events and key presses in Waydroid.
It is based on `python-libevdev`, `PyQt6`, and the kde plasma wayland desktop.
It utilized `qdbus` to get the cursor positions, so it won't work only any DE that does not work with `qdbus`.

## Notes:
- The tool is equipped with a UI to easily record and replay macros.
- You are asked to give the tool sudo access for the Waydroid shell, but it will also work with `adb`, just decline
  > `adb` might introduce some input lag, but should work fine.
  > You can choose to not be asked again, in that case `adb` is used in the future, make sure to install it!
- Movement inputs are reduced ATM and only recognized during pressed down mouse (to recognize touch movement events). The Cooldown for this behavior can be adjusted to `WaydroidTouchRecorder.ini` where 0 means all movement event are played during pressed mouse button.
  > There might be a better way to send movement inputs then directly over the Waydroid shell or `adb` shell, if found nothing speaks against full cursor movement support. 

## Advanced Configuration:
The tool creates the `WaydroidTouchRecorder.ini` file in its install directory after its first launch. You can modify this file to change some options, but only modify the file while the tool is not running, otherwise the settings might not be applied correctly and are overridden after closing.

### Option Explanations:
- `inputstotaps`: If True converts inputs in a defined threshold to taps (might increase precision) and reduces movement inputs (less accurate movement paths but much better performance)
- `timetolerance`: If any movement action (DOWN -> MOVEMENT -> UP) is <= `timetolerance` convert to tap if other threshold is also True
- `pixeltolerance`: If movement is in box with side length `pixeltolerance` convert action to tap if other threshold is also True
- `movementcooldown`: Cooldown for movement input, set to 0 to disable this function while keeping the above

## Installation:
- Install Requirements:
  - python
  - `pip install libevdev PyQt6`
- Download Repository and start `main.py`

## GUI Example:
![Example GUI](./GUIExample.png?raw=true "GUI")

## Small GUI Example:
![Example Small GUI](./GUIExampleSmall.png?raw=true "SmallGUI")

## Motivation
I programmed this tool to work with games like FGO.
I changed from Windows to GNU/Linux and was used to the macro behavior in emulators like LDPlayer,
but on Linux I wanted to use Waydroid, so I needed a macro tool that works with specifically that usecase.
This tool is easily expandable to more demanding macros for other games (I read Roblox users would want that, but I never played it), however right now it only supports touch events and the ESC button to go back to the previous menu fast.