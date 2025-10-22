import subprocess
from time import perf_counter
import sys
import threading

def readFile(filename):
	Times = []
	Commands = []
	with open(filename, "r") as f:
		for i, line in enumerate(f.readlines()):
			if i==0 or line=="":
				continue
			Time, Command = line.split(",")
			Times.append(float(Time))
			Commands.append(Command)
	return Times, Commands

def singleReplay(Time, Command, start):
	# wait for next command:
	while Time>(perf_counter()-start):
		pass

	# execute command
	subprocess.run(f"adb shell cmd input {Command}", shell=True)	

def replayMacro(Times, Commands):
	input("Press Enter to start Macro: ")
	# to synchronize all container give them all one second:
	start = perf_counter() + 1

	# the simples solution to timing issues is to start all command executions
	# in seperate threads and time the commands there
	threads = []
	for Time, Command in zip(Times, Commands):
		threads.append(threading.Thread(target=singleReplay, args=(Time, Command, start)))

	# start all threads:
	for thread in threads:
		thread.start()

	# wait for all threads:
	for thread in threads:
		thread.join()


if __name__ == "__main__":
	if len(sys.argv)==1:
		filename = input("Input a Macro File: ")
	else:
		filename = sys.argv[1]

	Times, Commands = readFile(filename)
	replayMacro(Times, Commands)