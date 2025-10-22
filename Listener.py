from time import perf_counter
import signal
import os, sys
import subprocess
import libevdev
import configparser
import threading

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

def on_BTN_LEFT(x, y, time, container, query, value):
	X = int(float(query["x"]))
	Y = int(float(query["y"]))
	if x>=X and x<=(X+int(float(query["width"]))):
		if y>=Y and y<=(Y+int(float(query["height"]))):
			container.append({
				"x" : x-X,
				"y" : y-Y,
				"time" : perf_counter()-time,
				"value" : value,
				"type" : "Touch"
			})

def on_Movement(x, y, time, container, query):
	X = int(float(query["width"]))
	Y = int(float(query["height"]))
	container.append({
		"x" : min(x,X) if (x>0) else 0,
		"y" : min(y,Y) if (y>0) else 0,
		"time" : perf_counter()-time,
		"value" : 0,
		"type" : "Movement"
	})

def on_ESC(time, container, value):
	if(value==1):
		container.append({
			"x" : 0,
			"y" : 0,
			"time" : perf_counter()-time,
			"value" : 1,
			"type" : "ESC"
		})

ListenOnEV_REL = False
def on_event(event:libevdev.InputEvent, time, container, query):
	global ListenOnEV_REL

	if event.matches(libevdev.EV_KEY.BTN_LEFT):
		pos = getpos()
		on_BTN_LEFT(*pos, time, container, query, event.value)
		if(event.value==1):
			ListenOnEV_REL = True
		else:
			ListenOnEV_REL = False
		
	elif event.matches(libevdev.EV_REL.REL_X) and ListenOnEV_REL:
		pos = (container[-1]["x"]+event.value, container[-1]["y"])
		on_Movement(*pos, time, container)
	elif event.matches(libevdev.EV_REL.REL_Y) and ListenOnEV_REL:
		pos = (container[-1]["x"], container[-1]["y"]+event.value)
		on_Movement(*pos, time, container)

	elif event.matches(libevdev.EV_KEY.KEY_ESC):
		on_ESC(time, container, event.value)

class EventListener:
	def __init__(self, Devices, query):
		self.query = query
		self.Devices = []
		for i in Devices:
			self.Devices.append(libevdev.Device(open(f"/dev/input/event{i}")))

		self.container = []
		self.StopSignal = False
		self.Thread = threading.Thread(target=self.threadFunc)

	def signal_handler(self, sig, frame):
		self.StopSignal = True

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

	def threadFunc(self):
		start = perf_counter()
		self.query = extractWindowQuery(self.query["uuid"])

		while not self.StopSignal:
			try:
				for device in Devices:
					for event in device.events():
						if event.matches(libevdev.EV_REL) or event.matches(libevdev.EV_KEY):
							on_event(event, start, self.container, self.query)
			except InterruptedError:
				print("Recording Stopped!")
				break
			except:
				pass


if __name__ == "__main__":
	config = configparser.ConfigParser()
	configExists = os.path.exists(CONFIGFILE)
	if configExists:
		config.read(CONFIGFILE)
	else:
		config["SystemVariables"] = {}
		config["UserVariables"] = {}

	Devices = []
	if not "Devices" in config["UserVariables"]:
		subprocess.run("libinput list-devices | grep -e 'Device' -e 'Kernel'", shell=True)
		userDeviceInfo = "None"
		while userDeviceInfo:
			userDeviceInfo = input("Specify a valid device to add, leave empty if done: ")
			try:
				Devices.append(int(userDeviceInfo))
			except:
				print("Please only enter Integers!")
			print(f"Current Devices monitored: {Devices}")
		
		question = input("Do you wish to save your devices for next time? y/n: ")
		
		if question=="y" or question=="yes":
			config["UserVariables"]["Devices"] = str(Devices)

	else:
		Devices = eval(config["UserVariables"]["Devices"])

	WindowQuery = extractWindowQuery()
	
	if len(sys.argv)==1:
		RecordingFile = input("Enter a filename for recording: ")
	else:
		RecordingFile = sys.argv[1]
	input("Press Enter to start recording: ")

	LibevdevDevices = []
	for i in Devices:
		LibevdevDevices.append(libevdev.Device(open(f"/dev/input/event{i}")))

	Listener = EventListener(LibevdevDevices, WindowQuery)
	Listener.run()
	Inputs = Listener.getData()

	saveInputs(RecordingFile, Inputs)

	with open(CONFIGFILE, "w") as conffile:
		config.write(conffile)
