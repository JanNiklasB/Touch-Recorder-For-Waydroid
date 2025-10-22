import PyQt6.QtWidgets as pyqt
from PyQt6.QtCore import Qt as qtcore
import os, sys
import configparser
import subprocess

import Listener
import Player


# config file, can be static
CONFIGFILE = "WaydroidTouchRecorder.ini"

class Config:
	def __init__(self):
		self.config = configparser.ConfigParser()
		configExists = os.path.exists(CONFIGFILE)
		if configExists:
			self.config.read(CONFIGFILE)
		else:
			self.config["SystemVariables"] = {}
			self.config["UserVariables"] = {}

	def set(self, key, val, Category="UserVariables"):
		if not Category in self.config:
			self.config[Category] = {}
		self.config[Category][key] = val

	def save(self):
		with open(CONFIGFILE, "w") as conffile:
			self.config.write(conffile)

	def get(self, key, Category="UserVariables"):
		if(Category==""):
			for category in self.config.keys():
				if key in self.config[category]:
					return self.config[category][key]
			return ""
		else:
			if key in self.config[Category].keys():
				return self.config[Category][key]
			else:
				return ""

class MainWindow(pyqt.QMainWindow):
	def __init__(self):
		super().__init__()
		self.config = Config()

		self.setWindowTitle("Waydroid Touch Macro Recorder")
		self.setMinimumSize(700, 500)

		# create Window
		mainWidget = pyqt.QWidget()
		self.setCentralWidget(mainWidget)

		# Create HBox inside Window
		layout = pyqt.QHBoxLayout()
		mainWidget.setLayout(layout)



		# Panel For List of Macros
		leftPanel = pyqt.QWidget()
		leftLayout = pyqt.QVBoxLayout(leftPanel)

		pathPanel = pyqt.QWidget()
		pathLayout = pyqt.QHBoxLayout(pathPanel)

		self.macroPathInfo = pyqt.QLineEdit()
		self.macroPathInfo.setReadOnly(True)
		# getcwd returns current directory
		if self.config.get("macropath") == "":
			self.macroPathInfo.setText(os.getcwd())
		else:
			self.macroPathInfo.setText(self.config.get("macropath"))
		pathLayout.addWidget(self.macroPathInfo)

		browseButton = pyqt.QPushButton("Browse")
		browseButton.clicked.connect(self.browseMacroPath)
		pathLayout.addWidget(browseButton)

		# Add Available Macros (currently only this Dir)
		self.macroList = pyqt.QListWidget()
		self.refresh_macro_list()
		
		leftLayout.addWidget(pyqt.QLabel("Choose Macro Folder:"))
		leftLayout.addWidget(pathPanel)
		leftLayout.addWidget(pyqt.QLabel("Choose a Macro:"))
		leftLayout.addWidget(self.macroList)



		# Create right panel for list of buttons
		rightPanel = pyqt.QWidget()
		rightLayout = pyqt.QVBoxLayout(rightPanel)
		rightLayout.setAlignment(qtcore.AlignmentFlag.AlignTop)

		# Add buttons:
		# Add Pick Window
		QueryPanel = pyqt.QWidget()
		QueryLayout = pyqt.QHBoxLayout(QueryPanel)

		queryButton = pyqt.QPushButton("Pick Window")
		self.uuid = ""
		self.query = {}
		queryButton.clicked.connect(self.queryWindow)
		QueryLayout.addWidget(queryButton)

		self.queryInfo = pyqt.QLineEdit()
		self.queryInfo.setReadOnly(True)
		self.queryInfo.setPlaceholderText("Window Name")
		QueryLayout.addWidget(self.queryInfo)
		

		# Choose Devices:
		DevicesPanel = pyqt.QWidget()
		DevicesLayout = pyqt.QHBoxLayout(DevicesPanel)

		DevicesButton = pyqt.QPushButton("Pick Devices")
		DevicesButton.clicked.connect(self.chooseDevices)
		DevicesLayout.addWidget(DevicesButton)

		self.DevicesInfo = pyqt.QLineEdit()
		self.DevicesInfo.setReadOnly(True)
		if self.config.get("devices") == "":
			self.DevicesInfo.setPlaceholderText("Devices")
		else:
			self.DevicesInfo.setText(self.config.get("devices"))
		DevicesLayout.addWidget(self.DevicesInfo)


		rightLayout.addWidget(QueryPanel)
		rightLayout.addWidget(DevicesPanel)

		# TODO
		# Choose Device Field
		# Record Macro Button (Check if other options are set) (threaded)
		# -> start recording directly
		# -> stop recording with button
		# -> make prompt for macro name after recording
		# Play Macro Field (will probably take about half the right panel) (threaded)
		# -> read out chosen file for macro
		# Global:
		# - For Record/Play Macro: Signal recording with some icon and a running timer
		
		
		# Add panels to global layout
		layout.addWidget(leftPanel)
		layout.addWidget(rightPanel)

	def browseMacroPath(self):
		dialog = pyqt.QFileDialog()
		dialog.setFileMode(pyqt.QFileDialog.FileMode.Directory)
		if dialog.exec():
			dir = dialog.selectedFiles()[0]
			self.macroPathInfo.setText(dir)
			self.config.set("macropath", dir)
			self.refresh_macro_list()			

	def refresh_macro_list(self):
		self.macroList.clear()
		path = self.config.get("macropath")
		if path=="":
			path = "."
		for file in os.listdir(path):
			if file.endswith('.txt') or file.endswith('.csv'):
				self.macroList.addItem(file)

	def checkSelection(self) -> str:
		items = self.macroList.selectedItems()
		if items:
			return items[0].text()
		else:
			return ""

	def queryWindow(self):
		self.query = Listener.extractWindowQuery(self.uuid)
		self.uuid = self.query["uuid"]
		self.queryInfo.setText(self.query["desktopFile"])

	def chooseDevices(self):
		popup = pyqt.QDialog(self)
		popup.setWindowTitle("Choose Input Devices")
		popup.setMinimumSize(600, 400)

		layout = pyqt.QVBoxLayout(popup)

		outputArea = pyqt.QListWidget()
		outputArea.setSelectionMode(pyqt.QAbstractItemView.SelectionMode.MultiSelection)

		try:
			Devices = subprocess.run("libinput list-devices | grep -e 'Device'", shell=True, capture_output=True)
			Kernel = subprocess.run("libinput list-devices | grep -e 'Kernel'", shell=True, capture_output=True)
			DevicesList = Devices.stdout.decode().split("\n")
			KernelList = Kernel.stdout.decode().split("\n")

			DevicesList = [device for device in DevicesList if device]
			KernelList = [kernel for kernel in KernelList if kernel]

			outputArea.addItems(DevicesList)

			for i in range(len(KernelList)):
				tmp = KernelList[i].split("/dev/input/event")
				if len(tmp)>1:
					KernelList[i] = int(tmp[1])
				else:
					KernelList[i] = -1

			previousDevices = eval(self.config.get("devices"))
			for device in previousDevices:
				if device in KernelList:
					outputArea.item(KernelList.index(device)).setSelected(True)

		except Exception as e:
			outputArea = pyqt.QTextEdit()
			outputArea.setText(f"Error getting devices: {str(e)}")

		layout.addWidget(pyqt.QLabel("Choose devices and press OK:"))
		layout.addWidget(outputArea)

		buttonBox = pyqt.QDialogButtonBox(
			pyqt.QDialogButtonBox.StandardButton.Ok |
			pyqt.QDialogButtonBox.StandardButton.Cancel
		)

		buttonBox.accepted.connect(popup.accept)
		buttonBox.rejected.connect(popup.reject)
		layout.addWidget(buttonBox)

		if popup.exec() == pyqt.QDialog.DialogCode.Accepted:
			devices = []
			for item in outputArea.selectedItems():
				index = DevicesList.index(item.text())
				devices.append(KernelList[index])
			self.config.set("devices", str(devices))
			self.DevicesInfo.setText(str(devices))

	def warningMessage(self, message):
		errorWin = pyqt.QMessageBox()
		errorWin.setIcon(pyqt.QMessageBox.Icon.Critical)
		errorWin.setWindowTitle("Warning Message")
		errorWin.setText(message)
		errorWin.exec()



if __name__ == "__main__":
	app = pyqt.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	signal = app.exec()
	window.config.save()
	sys.exit(signal)