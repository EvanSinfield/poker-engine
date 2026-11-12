import sys
from typing import Optional, TextIO


class EngineLog:
	"""Routes engine output to the console and, optionally, a log file.
	The log file always receives everything, even when not verbose."""

	def __init__(self, verbose: bool = True, file: Optional[TextIO] = None):
		self.verbose = verbose
		self.file = file


	def _write_file(self, msg: str):
		if self.file is not None:
			self.file.write(msg + "\n")
			self.file.flush()


	def info(self, msg: str):
		"""Game progress: stdout when verbose, always to the log file."""
		if self.verbose:
			print(msg, flush=True)
		self._write_file(msg)


	def warn(self, msg: str):
		"""Problems such as bot timeouts: always stderr and the log file."""
		print(msg, file=sys.stderr, flush=True)
		self._write_file(msg)


	def result(self, msg: str):
		"""Final results: always stdout and the log file."""
		print(msg, flush=True)
		self._write_file(msg)


	def file_only(self, msg: str):
		self._write_file(msg)
