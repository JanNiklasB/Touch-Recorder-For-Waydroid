import subprocess
from time import perf_counter, sleep
import sys, os
import threading

class Player:
	def __init__(self):
		self.Times = []
		self.Commands = []
		self.threads = []
		self.starttime = 0
		self.paused = False
		self.stopped = True

	def readFile(self, filename):
		self.Times = []
		self.Commands = []
		with open(filename, "r") as f:
			for i, line in enumerate(f.readlines()):
				if i==0 or line=="":
					continue
				Time, Command = line.split(",")
				self.Times.append(float(Time))
				self.Commands.append(Command[:-1])


	def singleReplay(self, Time, Command):
		# wait for next command:
		while (Time>(perf_counter()-self.starttime) or self.paused) and not self.stopped:
			sleep(0.01)

		if self.stopped:
			return

		# execute command
		os.system(f"adb shell input {Command}")

	def allReplays(self):
		for Time, Command in zip(self.Times, self.Commands):
			# wait for next command:
			while (Time>(perf_counter()-self.starttime) or self.paused) and not self.stopped:
				sleep(0.01)

			if self.stopped:
				return

			# execute command
			print(Command)
			os.system(f"sudo waydroid shell input {Command}")
			# subprocess.call(["sudo", "waydroid", "shell", "input", f"{Command}"])

	def replayMacro(self):
		self.stopped = False
		self.paused = True

		# the simples solution to timing issues is to start all command executions
		# in seperate threads and time the commands there
		threads = []
		for Time, Command in zip(self.Times, self.Commands):
			threads.append(threading.Thread(target=self.singleReplay, args=[Time, Command]))

		# start all threads:
		for thread in threads:
			thread.start()

		# now start the timer:
		self.starttime = perf_counter()
		self.paused = False

		# wait for all threads:
		for thread in threads:
			thread.join()

		self.stopped = True

	def start(self):
		self.stopped = False

		# first setup all threads
		self.threads = []
		# for Time, Command in zip(self.Times, self.Commands):
		# 	self.threads.append(threading.Thread(target=self.singleReplay, args=[Time, Command]))
		self.threads.append(threading.Thread(target=self.allReplays))

		for thread in self.threads:
			thread.start()

		# then start all threads at the same time
		self.starttime = perf_counter()
		self.paused = False

	def pause(self):
		self.paused = True
		# save elapsed time
		self.starttime = perf_counter() - self.starttime

	def resume(self):
		# correct start time with elapsed time
		self.starttime = perf_counter() - self.starttime
		self.paused = False

	def stop(self):
		self.stopped = True

		for thread in self.threads:
			thread.join()



if __name__ == "__main__":
	filename = "/home/jnb/Documents/PythonMacro/test.txt"

	player = Player()
	player.readFile(filename)
	player.replayMacro()