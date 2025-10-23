### Steps I did so far:

- Installed python3-libevdev
- Installed above with pip (might both do the same)
- Installed findCursor in ~/bin
- Installed adb
- Installed PyQt6

### TODO:
- find way to execute `waydroid shell input` instead of `adb shell input`
  > requires sudo rights, user can of course start window with sudo, but then roots window settings are used
  > -> find way to start in `sudo waydroid shell`  environment and ask user for sudo rights