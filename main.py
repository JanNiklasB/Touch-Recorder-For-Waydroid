import UIStuff
from DBusListener import Listener
import sys

if __name__ == "__main__":
	app = UIStuff.pyqt.QApplication(sys.argv)
	
	PosListener = Listener()
	window = UIStuff.MainWindow(PosListener)
	window.show()

	signal = app.exec()

	window.config.save()
	sys.exit(signal)