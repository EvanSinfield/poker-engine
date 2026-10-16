import subprocess

class Player:
	def __init__(self, path: str):
		self.process = subprocess.Popen(
			[path],
    		stdin=subprocess.PIPE,
    		stdout=subprocess.PIPE,
    		text=True)


	def get_action(self, state: str):
		print(state)
		output, _ = self.process.communicate(timeout = 10)
		# TODO: deal with timeouts
		return output
