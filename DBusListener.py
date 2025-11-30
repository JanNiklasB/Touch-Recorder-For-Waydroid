from PyQt6.QtCore import QObject, pyqtSlot, QCoreApplication, pyqtSignal
from PyQt6.QtDBus import QDBusConnection
from threading import Thread

class CursorReceiver(QObject):
	cursorPosChanged = pyqtSignal(int, int)

	def __init__(self):
		super().__init__()

	@pyqtSlot(int, int)  # sets the expected input parameter for the dbus method
	def Send(self, x, y):  # the method invoced in python
		self.cursorPosChanged.emit(x, y)

class Listener:
	def __init__(self):
		self.receiver = CursorReceiver()
		self.conn = QDBusConnection.sessionBus()
		self.conn.registerService("org.pythonmacro.Cursor")
		self.conn.registerObject("/", self.receiver, QDBusConnection.RegisterOption.ExportAllSlots)

if __name__ == "__main__":
	app = QCoreApplication([])
	receiver = CursorReceiver()
	conn = QDBusConnection.sessionBus()
	conn.registerService("org.pythonmacro.Cursor")
	conn.registerObject("/", receiver, QDBusConnection.RegisterOption.ExportAllSlots)
	app.exec()
