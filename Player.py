import subprocess
from time import perf_counter, sleep
import sys, os
import threading

def testSudo(pwd=""):
	args = "sudo -S echo OK".split()
	kwargs = dict(stdout=subprocess.PIPE,
				encoding="ascii")
	if pwd:
		kwargs.update(input=pwd)
	cmd = subprocess.run(args, **kwargs)
	return ("OK" in cmd.stdout)

class Player:
	def __init__(self, pswd=""):
		self.Times = []
		self.Commands = []
		self.threads = []
		self.starttime = 0
		self.paused = False
		self.stopped = True

		if pswd=="" and os.geteuid()!=0:
			# connect to adb shell if no password is given (might cause problems along the line)
			self.waydroidShell = subprocess.Popen(
				['adb', 'shell'], 
				stderr=subprocess.PIPE, 
				stdout=subprocess.PIPE, 
				stdin=subprocess.PIPE,
				text=True,
				encoding="utf-8",
				bufsize=1
			)
		elif testSudo(pswd):
			self.waydroidShell = subprocess.Popen(
				['sudo', '-S', 'waydroid', 'shell'], 
				stderr=subprocess.PIPE, 
				stdout=subprocess.PIPE, 
				stdin=subprocess.PIPE,
				text=True,
				encoding="utf-8",
				bufsize=1
			)
		else:
			raise Exception("sudo password was wrong!!!\nYou can enter no password to use 'adb shell' instead of 'sudo waydroid shell'")

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

	def _send_cmd(self, cmd):
		if self.waydroidShell.stdin is None:
			raise Exception("Shell is Closed!")
		self.waydroidShell.stdin.write(cmd + "\n")
		self.waydroidShell.stdin.flush()

	def singleReplay(self, Time, Command):
		# wait for next command:
		while (Time>(perf_counter()-self.starttime) or self.paused) and not self.stopped:
			sleep(0.01)

		if self.stopped:
			return
		
		self._send_cmd(f"input {Command}")

	def allReplays(self):
		for Time, Command in zip(self.Times, self.Commands):
			# wait for next command:
			while (Time>(perf_counter()-self.starttime) or self.paused) and not self.stopped:
				sleep(0.01)

			if self.stopped:
				return

			self._send_cmd(f"input {Command}")

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
		self.paused = True

		# first setup all threads
		self.threads = []
		for Time, Command in zip(self.Times, self.Commands):
			self.threads.append(threading.Thread(target=self.singleReplay, args=[Time, Command]))
		# ordered execution as an alternative, but this might cause delay due to overhead
		# self.threads.append(threading.Thread(target=self.allReplays))

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
