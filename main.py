import UIStuff
import sys

if __name__ == "__main__":
	app = UIStuff.pyqt.QApplication(sys.argv)
	window = UIStuff.MainWindow()
	window.show()
	signal = app.exec()
	window.config.save()
	sys.exit(signal)