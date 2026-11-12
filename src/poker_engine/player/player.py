import queue
import shlex
import subprocess
import sys
import threading
from typing import Optional


class Player:
	"""A bot running as a child process, spoken to with one JSON message per
	line over stdin/stdout. The process stays alive for the whole game.
	The bot's stderr is passed through to the engine's stderr for debugging."""

	def __init__(self, command: str, name: Optional[str] = None):
		self.name = name or command
		self.connected = True
		self.process = subprocess.Popen(
			shlex.split(command),
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			text=True,
			bufsize=1)

		# a reader thread lets us wait for a reply with a timeout
		self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
		self._reader = threading.Thread(target=self._read_loop, daemon=True)
		self._reader.start()


	def _read_loop(self):
		try:
			for line in self.process.stdout:
				self._lines.put(line)
		except (OSError, ValueError):
			pass
		self._lines.put(None)	# EOF


	def send(self, message: str) -> bool:
		if not self.connected:
			return False
		try:
			self.process.stdin.write(message + "\n")
			self.process.stdin.flush()
			return True
		except (BrokenPipeError, OSError, ValueError):
			self.disconnect("stdin closed")
			return False


	def receive(self, timeout: float) -> Optional[str]:
		if not self.connected:
			return None
		try:
			line = self._lines.get(timeout=timeout)
		except queue.Empty:
			# a late reply would desync the protocol, so the bot is dropped
			self.disconnect(f"no response within {timeout}s")
			return None
		if line is None:
			self.disconnect("process exited")
			return None
		return line


	def get_action(self, state: str, timeout: float) -> Optional[str]:
		if not self.send(state):
			return None
		return self.receive(timeout)


	def disconnect(self, reason: str):
		if self.connected:
			print(f"[engine] player {self.name!r} disconnected: {reason}",
				file=sys.stderr)
		self.connected = False
		self.close()


	def close(self):
		try:
			self.process.stdin.close()
		except (OSError, ValueError):
			pass
		try:
			self.process.wait(timeout=1)
		except subprocess.TimeoutExpired:
			self.process.kill()
			self.process.wait()
		self._reader.join(timeout=1)
		if not self._reader.is_alive():
			self.process.stdout.close()
