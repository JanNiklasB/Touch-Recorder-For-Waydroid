from time import perf_counter
import signal
import os, sys
import subprocess
import libevdev
import configparser
import threading
import select

CONFIGFILE = "WaydroidTouchRecorder.ini"

# ADB functions
def TouchDown(x, y) -> str:
	return f"motionevent DOWN {x} {y}"

def TouchMove(x, y) -> str:
	return f"motionevent MOVE {x} {y}"

def TouchUp(x, y) -> str:
	return f"motionevent UP {x} {y}"

def TouchCancel() -> str:
	return "motionevent CANCEL"

def ESCKey() -> str:
	return "keyevent 4"

def extractWindowQuery(uuid = "") -> dict:
	if uuid:
		WindowQueryCommandOutput = subprocess.run(f"qdbus org.kde.KWin /KWin getWindowInfo {uuid}", shell=True, capture_output=True)
	else:
		# print("Select a window with the cursor, if you close the Window you need to restart this tool!")
		WindowQueryCommandOutput = subprocess.run("qdbus org.kde.KWin /KWin queryWindowInfo", shell=True, capture_output=True)

	WindowQuery = {}
	for query_entry in WindowQueryCommandOutput.stdout.decode().split("\n"):
		entries = query_entry.split(": ")
		if len(entries)<2:
			continue
		WindowQuery[entries[0]] = entries[1]
	return WindowQuery

def saveInputs(File, Inputs):
	Lines = ["Time,Command\n"]
	for input in Inputs:
		if input["type"]=="Touch":
			if input["value"]==1:
				Lines.append(f"{input['time']},{TouchDown(input['x'], input['y'])}\n")
			else:
				Lines.append(f"{input['time']},{TouchUp(input['x'], input['y'])}\n")
		elif input["type"]=="Movement":
			Lines.append(f"{input['time']},{TouchMove(input['x'], input['y'])}\n")
		elif input["type"]=="ESC":
			Lines.append(f"{input['time']},{ESCKey()}\n")

	with open(File, "w") as f:
		f.writelines(Lines)

def getpos()->tuple:
	posInput = subprocess.run("findCursor.sh", shell=True, capture_output=True)
	posInput = posInput.stdout.decode().split("_")
	return (int(posInput[1]), int(posInput[2]))

class EventListener:
	def __init__(self, Devices, query):
		self.query = query
		self.Devices = []
		self.Threads = []
		for i in Devices:
			fd = open(f"/dev/input/event{i}")
			# os.set_blocking(fd.fileno(), False)  # important to not block threads, we only read, so ok
			device = libevdev.Device(fd)
			self.Devices.append(device)
			self.Threads.append(threading.Thread(target=self.threadFunc, args=[device]))

		self.container = []
		self.StopSignal = True
		self.ListenOnEV_REL = False

	def signal_handler(self, sig, frame):
		self.StopSignal = True

	def start(self):
		self.StopSignal = False
		for thread in self.Threads:
			thread.start()

	def stop(self):
		self.StopSignal = True

		# wait on thread to finish
		for thread in self.Threads:
			thread.join()

		for device in self.Devices:
			device.fd.close()

	# runs until disrupted
	def run(self):

		old_handler = signal.signal(signal.SIGINT, self.signal_handler)
		print("Press CTRL + C to stop recording, do not resize window while recording!")
		self.Thread.start()

		self.Thread.join()
		signal.signal(signal.SIGINT, old_handler)
		self.StopSignal = False

	def getData(self):
		return self.container

	def threadFunc(self, device):
		start = perf_counter()
		self.query = extractWindowQuery(self.query["uuid"])
		fd = device.fd.fileno()

		while not self.StopSignal:
			try:
				r, _, _ = select.select([fd], [], [], 0.3)
				if not r:
					continue

				for event in device.events():
					if self.StopSignal:
						return
					if event.matches(libevdev.EV_REL) or event.matches(libevdev.EV_KEY):
						self.on_event(event, start)
			except InterruptedError:
				print("Recording Stopped!")
				break
			except Exception as e:
				print(f"Warning: An exception was encountered in EventListener.threadFunc: {str(e)}")

	def on_event(self, event:libevdev.InputEvent, time):
		if event.matches(libevdev.EV_KEY.BTN_LEFT):
			pos = getpos()
			self.on_BTN_LEFT(*pos, time, event.value)
			if(event.value==1):
				self.ListenOnEV_REL = True
			else:
				self.ListenOnEV_REL = False

		# # For now disable Movement, since the amount of inputs is to much for adb.
		
		# elif event.matches(libevdev.EV_REL.REL_X) and self.ListenOnEV_REL:
		# 	pos = (self.container[-1]["x"]+event.value, self.container[-1]["y"])
		# 	self.on_Movement(*pos, time)

		# elif event.matches(libevdev.EV_REL.REL_Y) and self.ListenOnEV_REL:
		# 	pos = (self.container[-1]["x"], self.container[-1]["y"]+event.value)
		# 	self.on_Movement(*pos, time)

		elif event.matches(libevdev.EV_KEY.KEY_ESC):
			self.on_ESC(time, event.value)

	def on_BTN_LEFT(self, x, y, time, value):
		X = int(float(self.query["x"]))
		Y = int(float(self.query["y"]))
		if x>=X and x<=(X+int(float(self.query["width"]))):
			if y>=Y and y<=(Y+int(float(self.query["height"]))):
				self.container.append({
					"x" : x-X,
					"y" : y-Y,
					"time" : perf_counter()-time,
					"value" : value,
					"type" : "Touch"
				})

	def on_Movement(self, x, y, time):
		X = int(float(self.query["width"]))
		Y = int(float(self.query["height"]))
		self.container.append({
			"x" : min(x,X) if (x>0) else 0,
			"y" : min(y,Y) if (y>0) else 0,
			"time" : perf_counter()-time,
			"value" : 0,
			"type" : "Movement"
		})

	def on_ESC(self,time, value):
		if(value==1):
			self.container.append({
				"x" : 0,
				"y" : 0,
				"time" : perf_counter()-time,
				"value" : 1,
				"type" : "ESC"
			})
