import Xlib
from Xlib import X, display
import numpy as np

display = display.Display()
root = display.screen().root
windowIDs = root.get_full_property(display.intern_atom("_NET_CLIENT_LIST"), Xlib.X.AnyPropertyType).value
window = display.create_resource_object("window", windowIDs)
window_title_property = window.get_full_property(int(display.intern_atom("_NET_WM_NAME")), int(0))

for windowID in windowIDs:
        window = display.create_resource_object('window', windowID)
        window_title_property = window.get_full_property(display.intern_atom('_NET_WM_NAME'), 0)
        searching_window_title = "albion online"

        if window_title_property and searching_window_title.lower() in window_title_property.value.decode('utf-8').lower():
            geometry = window.get_geometry()
            width, height = geometry.width, geometry.height

            pixmap = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)
            data = pixmap.data
            final_image = np.frombuffer(data, dtype='uint8').reshape((height, width, 4))
