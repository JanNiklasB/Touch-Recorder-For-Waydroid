import PyQt6.QtWidgets as pyqt
import PyQt6.QtCore as qtcore
import PyQt6.QtGui as qtgui
from time import perf_counter, sleep
import os, sys
import configparser
import subprocess

import Listener
import Player

#get current path
from pathlib import Path
PATH = Path(__file__).parent.resolve()

# config file, can be static
CONFIGFILE = str(PATH) + "/WaydroidTouchRecorder.ini"

class Config:
	def __init__(self):
		self.config = configparser.ConfigParser()
		configExists = os.path.exists(CONFIGFILE)
		if configExists:
			self.config.read(CONFIGFILE)
		else:
			self.config["SystemVariables"] = {}
			self.config["UserVariables"] = {}

	def set(self, key:str, val:str, Category="UserVariables"):
		if not Category in self.config:
			self.config[Category] = {}
		self.config[Category][key] = val

	def save(self):
		with open(CONFIGFILE, "w") as conffile:
			self.config.write(conffile)

	def get(self, key:str, Category="UserVariables"):
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
			
	def setIfNotExist(self, key:str, val:str, Catergory="UserVariables"):
		if self.get(str(key), Catergory)=="":
			self.set(str(key), str(val), Catergory)

class MainWindow(pyqt.QMainWindow):
	def __init__(self, PosListener):
		super().__init__()
		self.config = Config()
		self.config.setIfNotExist("InputsToTaps", True, "SystemVariables")
		self.config.setIfNotExist("TimeTolerance", 0.3, "SystemVariables")
		self.config.setIfNotExist("PixelTolerance", 20, "SystemVariables")
		self.config.setIfNotExist("MovementCooldown", 0.1, "SystemVariables")

		# setup timer and timer globals:
		self._timer = qtcore.QTimer(self)
		self._timer.setInterval(100)
		self._timer.timeout.connect(self._updateTimer)
		self._timerRunning = False
		self._timerStart = 0
		self._timerElapsed = 0

		# set main Window options
		self.setWindowTitle("Waydroid Touch Macro Recorder")
		self.setMinimumSize(700, 500)

		# create Window
		mainWidget = pyqt.QWidget()
		self.setCentralWidget(mainWidget)

		# Create HBox inside Window
		layout = pyqt.QHBoxLayout()
		mainWidget.setLayout(layout)

		

		# create status bar
		statusBar = pyqt.QStatusBar()
		self.setStatusBar(statusBar)

		# set status info text
		statusInfoLabelPrefix = pyqt.QLabel("Status: ")
		self.statusInfoLabel = pyqt.QLabel("Idling")
		# set status light
		self.statusLight = pyqt.QLabel()
		self.statusLight.setFixedSize(14, 14)
		self.statusLight.setPixmap(self._getStatusPixmap("gray"))
		# set timer label
		self.timerLabel = pyqt.QLabel("00:00.0")

		statusBar.addWidget(statusInfoLabelPrefix)
		statusBar.addWidget(self.statusInfoLabel)
		statusBar.addPermanentWidget(self.statusLight)
		statusBar.addPermanentWidget(self.timerLabel)



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

		# Add Available Macros
		self.macroList = pyqt.QListWidget()
		self.refresh_macro_list()

		FileOperationsPanel = pyqt.QWidget()
		FileOperationsLayout = pyqt.QHBoxLayout(FileOperationsPanel)

		OpenMacroFileButton = pyqt.QPushButton("Open")
		OpenMacroFileButton.clicked.connect(self.openSelectedMacro)
		FileOperationsLayout.addWidget(OpenMacroFileButton)

		DeleteMacroFileButton = pyqt.QPushButton("Delete")
		DeleteMacroFileButton.clicked.connect(self.deleteSelectedMacro)
		FileOperationsLayout.addWidget(DeleteMacroFileButton)


		leftLayout.addWidget(pyqt.QLabel("Choose Macro Folder:"))
		leftLayout.addWidget(pathPanel)
		leftLayout.addWidget(pyqt.QLabel("Choose a Macro:"))
		leftLayout.addWidget(self.macroList)
		leftLayout.addWidget(FileOperationsPanel)



		# Create right panel for list of buttons
		rightPanel = pyqt.QWidget()
		rightLayout = pyqt.QVBoxLayout(rightPanel)
		rightLayout.setAlignment(qtcore.Qt.AlignmentFlag.AlignTop)

		# Add buttons:
		# Add Pick Window
		QueryPanel = pyqt.QWidget()
		QueryLayout = pyqt.QHBoxLayout(QueryPanel)

		queryButton = pyqt.QPushButton("Pick Window")
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

		# Record Macro:
		RecordPanel = pyqt.QWidget()
		RecordLayout = pyqt.QHBoxLayout(RecordPanel)
		# globals:
		self._RecordingIsRunning = False
		self.Recorder = None
		self.PosListener = PosListener

		StartRecordButton = pyqt.QPushButton("Record")
		StartRecordButton.clicked.connect(self.startRecording)
		RecordLayout.addWidget(StartRecordButton)

		StopRecordButton = pyqt.QPushButton("Stop")
		StopRecordButton.clicked.connect(self.stopRecording)
		RecordLayout.addWidget(StopRecordButton)

		# Replay Macro
		ReplayPanel = pyqt.QWidget()
		ReplayLayout = pyqt.QHBoxLayout(ReplayPanel)
		# globals
		try:
			self._ReplayPlayer = Player.Player(self._askForSudo())
		except Exception as e:
			self.ErrorMessage(str(e))
			exit()

		self._ReplayIsRunning = False
		self._ReplayIsPaused = False
		self._ReplayIsRequeueing = False
		self._ReplayTargetTimeStr = ""

		ReplayStartButton = pyqt.QPushButton("Start")
		ReplayStartButton.clicked.connect(self.ReplayStart)
		ReplayLayout.addWidget(ReplayStartButton)

		self.ReplayPauseButton = pyqt.QPushButton("Pause")
		self.ReplayPauseButton.clicked.connect(self.ReplayPause)
		ReplayLayout.addWidget(self.ReplayPauseButton)

		ReplayStopButton = pyqt.QPushButton("Abort")
		ReplayStopButton.clicked.connect(self.ReplayStop)
		ReplayLayout.addWidget(ReplayStopButton)

		# Loop Options:
		LoopPanel = pyqt.QWidget()
		LoopLayout = pyqt.QHBoxLayout(LoopPanel)
		# globals:
		self._LoopInfinitly = False
		self._LoopCounter = 0
		self._LoopRequeueDelayTime = -1

		LoopInfiniteCheck = pyqt.QCheckBox()
		LoopInfiniteCheck.stateChanged.connect(self._OnLoopInfiniteCheck)
		LoopLayout.addWidget(pyqt.QLabel("Repeat until Abort:"))
		LoopLayout.addWidget(LoopInfiniteCheck)

		self.LoopCountInput = pyqt.QLineEdit()
		self.LoopCountInput.setFixedWidth(40)
		self.LoopCountInput.setAlignment(qtcore.Qt.AlignmentFlag.AlignCenter)
		self.LoopCountInput.setText("1")
		CountValidator = qtgui.QIntValidator(1, 999)
		self.LoopCountInput.setValidator(CountValidator)
		LoopLayout.addWidget(pyqt.QLabel("Count:"))
		LoopLayout.addWidget(self.LoopCountInput)

		self.LoopDelayInput = pyqt.QLineEdit()
		self.LoopDelayInput.setFixedWidth(40)
		self.LoopDelayInput.setAlignment(qtcore.Qt.AlignmentFlag.AlignCenter)
		self.LoopDelayInput.setText("0.0")
		DelayValidator = qtgui.QDoubleValidator(0.0, 999.9, 1)
		DelayValidator.setNotation(qtgui.QDoubleValidator.Notation.StandardNotation)
		self.LoopDelayInput.setValidator(DelayValidator)
		LoopLayout.addWidget(pyqt.QLabel("Delay:"))
		LoopLayout.addWidget(self.LoopDelayInput)


		rightLayout.addWidget(pyqt.QLabel("Configuration:"))
		rightLayout.addWidget(QueryPanel)
		rightLayout.addWidget(DevicesPanel)
		rightLayout.addWidget(pyqt.QLabel("Recording:"))
		rightLayout.addWidget(RecordPanel)
		rightLayout.addWidget(pyqt.QLabel("Replay:"))
		rightLayout.addWidget(ReplayPanel)
		rightLayout.addWidget(pyqt.QLabel("Loop Options:"))
		rightLayout.addWidget(LoopPanel)


		# TODO
		# Fuse Macros Tool -> new ui/popup which should give the followig options:
		# - Only option for two macros, can then be called again for the new one (by user)
		# - give two MacroLists (already implemented) and one option field
		# - add delay between 1 and 2
				
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
			if file.endswith('.txt'):
				self.macroList.addItem(file)

	def openSelectedMacro(self):
		if self.macroList.selectedItems():
			subprocess.Popen(["xdg-open", self.macroPathInfo.text() + "/" + self.macroList.selectedItems()[0].text()])

	def deleteSelectedMacro(self):
		if self.macroList.selectedItems():
			os.remove(self.macroPathInfo.text() + "/" + self.macroList.selectedItems()[0].text())
			self.refresh_macro_list()

	def checkSelection(self) -> str:
		items = self.macroList.selectedItems()
		if items:
			return items[0].text()
		else:
			return ""


	def queryWindow(self):
		self.query = Listener.extractWindowQuery()
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


	def startRecording(self):
		# do nothing if already running or playing:
		if(self._ReplayIsRunning or self._RecordingIsRunning):
			return

		# check requirements:
		queryCheck = self._checkQuery()
		devicesCheck = (self.config.get("devices") != "") and (self.config.get("devices") != "[]")
		if(queryCheck or not devicesCheck):
			WarningMessage = ""
			if not devicesCheck:
				WarningMessage += "You need to pick your Devices!\n"
			
			if queryCheck == 1:
				WarningMessage += "You need to pick a Window!\n"
			elif queryCheck == 2:
				WarningMessage += "Your chosen window does not exist, pick again!"

			self.warningMessage(WarningMessage)
			return

		# get fresh recorder
		print(eval(self.config.get("devices")))
		self.Recorder = Listener.EventListener(eval(self.config.get("devices")), self.query, self.PosListener)

		self._RecordingIsRunning = True
		self.setStatus("recording")
		self.Recorder.start()

	def stopRecording(self):
		# do nothing if Recorder is not running
		if not self._RecordingIsRunning:
			return

		self.Recorder.stop()
		self.setStatus("idling")
		inputs = self.Recorder.getData()

		filename = self._chooseMacroFilename()
		# self.warningMessage(f"You entered {self.macroPathInfo.text() + '/' + filename}")
		if filename:
			Listener.saveInputs(
				self.macroPathInfo.text() + "/" + filename, 
				inputs,
				bool(self.config.get("InputsToTaps", "SystemVariables")),
				float(self.config.get("TimeTolerance", "SystemVariables")),
				float(self.config.get("PixelTolerance", "SystemVariables")),
				float(self.config.get("MovementCooldown", "SystemVariables"))
			)
			self.refresh_macro_list()
		
		self._RecordingIsRunning = False


	def ReplayStart(self):
		# do nothing if already running or playing:
		if(self._ReplayIsRunning or self._RecordingIsRunning or self._ReplayIsRequeueing):
			return
		
		# in case start is pressed while paused, just resume:
		if(self._ReplayIsPaused):
			self.ReplayPause()
			return
		
		# checks
		if not len(self.macroList.selectedItems()):
			self.warningMessage("Please choose a macro first!")
			return

		filename = self.macroPathInfo.text() + "/" + self.macroList.selectedItems()[0].text()
		self._ReplayPlayer.readFile(filename)

		timerElapsed = self._ReplayPlayer.Times[-1]
		secs = int(timerElapsed)
		tenthsecs = int((timerElapsed-secs)*10)
		minutes = secs//60
		secs = secs%60
		self._ReplayTargetTimeStr =f" / {minutes:02d}:{secs:02d}.{tenthsecs}"

		self._ReplayIsRunning = True
		self.setStatus("playing")
		self._ReplayPlayer.start()

	def ReplayPause(self):
		# resume if paused:
		if(self._ReplayIsPaused):
			self._ReplayIsRunning = True
			self._ReplayIsPaused = False
			self._ReplayPlayer.resume()
			self.setStatus("resume")
			return

		# do nothing if already paused or not playing:
		if(not self._ReplayIsRunning or self._ReplayIsPaused):
			return
		
		self._ReplayIsRunning = False
		self._ReplayIsPaused = True
		self._ReplayPlayer.pause()
		self.setStatus("paused")

	def ReplayStop(self):
		# only do something if its running or paused or requeueing
		if(not (self._ReplayIsRunning or self._ReplayIsPaused or self._ReplayIsRequeueing)):
			return
		
		self._ReplayIsRunning = False
		self._ReplayIsPaused = False
		self._ReplayIsRequeueing = False
		self._ReplayPlayer.stop()

		self.setStatus("idle")
		self._LoopCounter = 0

	def _ReplayRequeue(self):
		self._ReplayIsRunning = False
		self._ReplayIsPaused = False
		self._ReplayIsRequeueing = False
		self._ReplayPlayer.stop()

		self._LoopCounter += 1
		if self._LoopInfinitly:
			self._ReplayIsRequeueing = True
			self.setStatus("requeue")
			self._LoopRequeueDelayTime = perf_counter()
		elif self.LoopCountInput.text():
			if self._LoopCounter < int(self.LoopCountInput.text()):
				self._ReplayIsRequeueing = True
				self.setStatus("requeue")
				self._LoopRequeueDelayTime = perf_counter()
			else:
				self.setStatus("idle")
				self._LoopCounter = 0

	def _OnLoopInfiniteCheck(self):
		self._LoopInfinitly = not self._LoopInfinitly


	def warningMessage(self, message):
		errorWin = pyqt.QMessageBox()
		errorWin.setIcon(pyqt.QMessageBox.Icon.Warning)
		errorWin.setWindowTitle("Warning Message")
		errorWin.setText(message)
		errorWin.exec()

	def ErrorMessage(self, message):
		errorWin = pyqt.QMessageBox()
		errorWin.setIcon(pyqt.QMessageBox.Icon.Critical)
		errorWin.setWindowTitle("Error Message")
		errorWin.setText(message)
		errorWin.exec()

	def _getStatusPixmap(self, color, size = 14):
		pixmap = qtgui.QPixmap(size, size)
		pixmap.fill(qtgui.QColor(0, 0, 0, 0))
		
		painter = qtgui.QPainter(pixmap)
		painter.setRenderHint(qtgui.QPainter.RenderHint.Antialiasing)
		painter.setBrush(qtgui.QColor(color))
		painter.setPen(qtgui.QColor(color))
		
		painter.drawEllipse(1, 1, size-2, size-2)
		painter.end()
		return pixmap
	
	def _ReplayIsAlive(self):
		if not self._ReplayPlayer.threads:
			return False
		return self._ReplayPlayer.threads[-1].is_alive()

	def _updateTimer(self):
		if self._LoopRequeueDelayTime>=0:
			if (perf_counter() - self._LoopRequeueDelayTime) >= float(self.LoopDelayInput.text()):
				self._ReplayIsRequeueing = False
				self._LoopRequeueDelayTime = -1
				self.ReplayStart()

		if not self._timerRunning:
			return

		self._timerElapsed = perf_counter() - self._timerStart
		secs = int(self._timerElapsed)
		tenthsecs = int((self._timerElapsed-secs)*10)
		minutes = secs//60
		secs = secs%60
		self.timerLabel.setText(f"{minutes:02d}:{secs:02d}.{tenthsecs}{self._ReplayTargetTimeStr}")

		if self._ReplayIsRunning:
			if not self._ReplayIsAlive():
				self._ReplayRequeue()

		
	def setStatus(self, state:str):
		"""
		Available states = ('idle', 'requeue', 'recording', 'playing', 'paused', 'resume')
		-> use 'resume' to correctly restart a timer (shows 'playing' status)
		"""

		status = state.lower()
		if status == "recording":
			self.statusInfoLabel.setText("Recording...")
			self.statusLight.setPixmap(self._getStatusPixmap("red"))
			self._timerStart = perf_counter()
			self._timerRunning = True
			self._timer.start()
		elif status == "playing":
			if self._LoopInfinitly:
				self.statusInfoLabel.setText(f"Playing {self._LoopCounter}/∞")
			else:
				self.statusInfoLabel.setText(f"Playing {self._LoopCounter}/{self.LoopCountInput.text() if self.LoopCountInput.text() else 1}")
			self.statusLight.setPixmap(self._getStatusPixmap("green"))
			self._timerStart = perf_counter()
			self._timerRunning = True
			self._timer.start()
		elif status == "paused":
			if self._LoopInfinitly:
				self.statusInfoLabel.setText(f"Paused {self._LoopCounter}/∞")
			else:
				self.statusInfoLabel.setText(f"Paused {self._LoopCounter}/{self.LoopCountInput.text() if self.LoopCountInput.text() else 1}")
			self.statusLight.setPixmap(self._getStatusPixmap("yellow"))
			self._timerRunning = False
			self._timerStart = perf_counter() - self._timerStart  # save elapsed time for later
			self._timer.stop()
			self.ReplayPauseButton.setText("Resume")
		elif status == "resume":
			if self._LoopInfinitly:
				self.statusInfoLabel.setText(f"Playing {self._LoopCounter}/∞")
			else:
				self.statusInfoLabel.setText(f"Playing {self._LoopCounter}/{self.LoopCountInput.text() if self.LoopCountInput.text() else 1}")
			self.statusLight.setPixmap(self._getStatusPixmap("green"))
			self._timerStart = perf_counter() - self._timerStart  # offset _timerStart by previous elapsed time
			self._timerRunning = True
			self._timer.start()
			self.ReplayPauseButton.setText("Pause")
		elif status == "requeue":
			if self._LoopInfinitly:
				self.statusInfoLabel.setText(f"Requeueing to {self._LoopCounter}/∞")
			else:
				if self._LoopCounter < int(self.LoopCountInput.text()):
					self.statusInfoLabel.setText(f"Requeueing to {self._LoopCounter}/{self.LoopCountInput.text()}")

			self.statusLight.setPixmap(self._getStatusPixmap("yellow"))

			self._timerRunning = False
			self._timer.stop()
			self._timerElapsed = 0
			
			timerElapsed = float(self.LoopDelayInput.text())
			secs = int(timerElapsed)
			tenthsecs = int((timerElapsed-secs)*10)
			minutes = secs//60
			secs = secs%60
			self._ReplayTargetTimeStr =f" / {minutes:02d}:{secs:02d}.{tenthsecs}"
			self.timerLabel.setText(f"00:00.0{self._ReplayTargetTimeStr}")

			self._timerStart = perf_counter()
			self._timerRunning = True
			self._timer.start()

		elif status == "idling" or status == "idle":
			self.statusInfoLabel.setText("Idling")
			self.statusLight.setPixmap(self._getStatusPixmap("gray"))
			self._ReplayTargetTimeStr = ""
			self._timerRunning = False
			self._timer.stop()
			self._timerElapsed = 0
			self.timerLabel.setText("00:00.0")
			self.ReplayPauseButton.setText("Pause")
		else:
			raise KeyError(f"state not found {state}")

	def _checkQuery(self) -> int:
		if not self.query:
			return 1
		
		self.query = Listener.extractWindowQuery(self.query["uuid"])
		if not self.query:
			return 2
		
		return 0

	def _chooseMacroFilename(self):
		popup = pyqt.QDialog(self)
		popup.setWindowTitle("Choose a Macro Filename")
		popup.setMinimumSize(400, 150)

		layout = pyqt.QVBoxLayout(popup)
		layout.setAlignment(qtcore.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(pyqt.QLabel("Please choose a filename for your Macro:"))

		inputLayout = pyqt.QHBoxLayout()
		filenameInput = pyqt.QLineEdit()
		filenameInput.setPlaceholderText("Endings: None, *.txt")
		inputLayout.addWidget(filenameInput)
		layout.addLayout(inputLayout)

		buttonBox = pyqt.QDialogButtonBox(
			pyqt.QDialogButtonBox.StandardButton.Ok |
			pyqt.QDialogButtonBox.StandardButton.Cancel
		)

		buttonBox.accepted.connect(popup.accept)
		buttonBox.rejected.connect(popup.reject)
		layout.addWidget(buttonBox)

		if popup.exec() == pyqt.QDialog.DialogCode.Accepted:
			filename = filenameInput.text()
			if not filename.endswith('.txt') and filename:
				filename += ".txt"
			return filename
		else:
			return ""
		
	def _askForSudo(self):
		popup = pyqt.QDialog(self)
		popup.setWindowTitle("Password Prompt")
		popup.setMinimumSize(400, 150)

		layout = pyqt.QVBoxLayout(popup)
		layout.setAlignment(qtcore.Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(pyqt.QLabel("This tool needs sudo to start a waydroid shell.\nLeave empty or cancel to use adb shell instead:"))

		inputLayout = pyqt.QHBoxLayout()
		
		PasswordInput = pyqt.QLineEdit()
		PasswordInput.setEchoMode(pyqt.QLineEdit.EchoMode.Password)
		PasswordInput.setPlaceholderText("Enter Password")
		inputLayout.addWidget(PasswordInput)
		
		layout.addLayout(inputLayout)

		buttonBox = pyqt.QDialogButtonBox(
			pyqt.QDialogButtonBox.StandardButton.Ok |
			pyqt.QDialogButtonBox.StandardButton.Cancel
		)

		buttonBox.accepted.connect(popup.accept)
		buttonBox.rejected.connect(popup.reject)
		layout.addWidget(buttonBox)

		if popup.exec() == pyqt.QDialog.DialogCode.Accepted:
			return PasswordInput.text()
		else:
			return ""


if __name__ == "__main__":
	app = pyqt.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	signal = app.exec()
	window.config.save()
	sys.exit(signal)