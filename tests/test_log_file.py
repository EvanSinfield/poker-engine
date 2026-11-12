import io
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from poker_engine.__main__ import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALL_BOT = f"{sys.executable} {os.path.join(ROOT, 'bots', 'call_bot.py')}"


def run_cli(*args):
	out, err = io.StringIO(), io.StringIO()
	with redirect_stdout(out), redirect_stderr(err):
		code = main(list(args))
	return code, out.getvalue(), err.getvalue()


def game_body(log_text):
	"""The results block and the hand log: the parts that depend only on
	the seed and settings, not on when or how the run was started."""
	results = log_text.split("\n\n", 1)[1].split("\ncommand:", 1)[0]
	return results, log_text.split("hand log", 1)[1]


class LogFileTest(unittest.TestCase):
	def setUp(self):
		self.dir = tempfile.TemporaryDirectory()
		self.addCleanup(self.dir.cleanup)

	def read(self, path):
		with open(path, encoding="utf-8") as f:
			return f.read()

	def test_header_settings_and_hands(self):
		path = os.path.join(self.dir.name, "nested", "run.log")
		code, out, _ = run_cli("--seed", "3", "--money", "200", "--blind", "5",
			"--games", "2", "--max-hands", "10", "--timeout", "2.5",
			"--persistent-bots", "--quiet", "--log-file", path,
			CALL_BOT, CALL_BOT, CALL_BOT)
		self.assertEqual(code, 0)
		self.assertNotIn("=== Hand", out)	# quiet console

		log = self.read(path)
		for expected in ["started:", "command:", "seed:           3\n",
				"games:          2", "starting money: 200", "small blind:    5",
				"timeout:        2.5s", "max hands:      10",
				"persistent bots: yes", f"seat 2: {CALL_BOT}",
				"##### Game 2/2 #####", "=== Hand 1:", "Final standings:",
				"summary over 2 games:", "finished:"]:
			self.assertIn(expected, log)
		self.assertIn(os.path.join(ROOT, "bots", "call_bot.py"), log)
		self.assertIn("game 2 (seed 4, ", log)

		# results and run data come before the hand log
		top, hands = log.split("hand log", 1)
		self.assertTrue(top.startswith("# poker-engine log\nstatus:           completed\n"))
		order = [top.index(x) for x in ["finished:", "summary over 2 games:",
			"games (finishing order", "command:", "settings:", "bots:"]]
		self.assertEqual(order, sorted(order))
		self.assertIn("=== Hand 1:", hands)
		self.assertNotIn("=== Hand", top)

	def test_single_game_standings_at_top(self):
		path = os.path.join(self.dir.name, "one.log")
		code, _, _ = run_cli("--seed", "2", "--money", "200", "--blind", "5",
			"--quiet", "--log-file", path, CALL_BOT, CALL_BOT)
		self.assertEqual(code, 0)
		top = self.read(path).split("hand log", 1)[0]
		self.assertRegex(top, r"final standings \(\d+ hands\):\n  1\. seat \d")
		self.assertIn(f"chips  {CALL_BOT}", top)
		self.assertFalse(os.path.exists(path + ".tmp"))

	def test_random_seed_is_logged_and_replays(self):
		first = os.path.join(self.dir.name, "first.log")
		run_cli("--money", "200", "--blind", "5", "--max-hands", "8",
			"--quiet", "--log-file", first, CALL_BOT, CALL_BOT, CALL_BOT)
		log = self.read(first)
		seed = re.search(r"seed:\s+(\d+) \(chosen at random", log).group(1)

		second = os.path.join(self.dir.name, "second.log")
		run_cli("--seed", seed, "--money", "200", "--blind", "5", "--max-hands",
			"8", "--quiet", "--log-file", second, CALL_BOT, CALL_BOT, CALL_BOT)
		self.assertEqual(game_body(log), game_body(self.read(second)))

	def test_warnings_go_to_log(self):
		path = os.path.join(self.dir.name, "warn.log")
		missing = f"{sys.executable} -c 'import sys; sys.exit(0)'"
		code, _, err = run_cli("--seed", "1", "--money", "100", "--blind", "10",
			"--quiet", "--log-file", path, missing, CALL_BOT)
		self.assertEqual(code, 0)
		self.assertIn("disconnected", err)
		self.assertIn("disconnected", self.read(path))

	def test_unwritable_path(self):
		path = os.path.join(self.dir.name, "file")
		open(path, "w").close()
		code, _, err = run_cli("--log-file", os.path.join(path, "x.log"),
			CALL_BOT, CALL_BOT)
		self.assertEqual(code, 1)
		self.assertIn("can't open log file", err)


if __name__ == "__main__":
	unittest.main()
