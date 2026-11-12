import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from poker_engine.__main__ import main
from poker_engine.engine.game import Game
from poker_engine.engine.match import run_games

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANDOM_BOT = f"{sys.executable} {os.path.join(ROOT, 'bots', 'random_bot.py')}"
CALL_BOT = f"{sys.executable} {os.path.join(ROOT, 'bots', 'call_bot.py')}"


class RunGamesTest(unittest.TestCase):
	def test_multiple_games_summary(self):
		bots = [RANDOM_BOT, RANDOM_BOT, CALL_BOT]
		result = run_games(4, 11, 300, bots, blind=5, verbose=False)
		self.assertEqual(len(result["games"]), 4)
		summary = result["summary"]
		self.assertEqual(sorted(s["seat"] for s in summary), [0, 1, 2])
		self.assertEqual(sum(s["wins"] for s in summary), 4)
		for s in summary:
			self.assertEqual(sum(s["places"]), 4)
		# every place is taken exactly once per game
		for place in range(3):
			self.assertEqual(sum(s["places"][place] for s in summary), 4)

	def test_single_game_matches_plain_game(self):
		bots = [CALL_BOT] * 3
		kwargs = dict(blind=5, max_hands=6, verbose=False)
		single = run_games(1, 5, 300, bots, **kwargs)["games"][0]
		plain = Game(5, 3, 300, bots, **kwargs).run()
		self.assertEqual(single, plain)

	def test_invalid_count(self):
		with self.assertRaises(ValueError):
			run_games(0, 1, 100, [CALL_BOT, CALL_BOT])


RECORDER = '''
import json, os, sys
log = open(sys.argv[1], "a")
for line in sys.stdin:
	msg = json.loads(line)
	if msg["type"] in ("game_start", "game_over", "match_over"):
		log.write(json.dumps({"pid": os.getpid(), "type": msg["type"],
			"game": msg.get("game_number"), "num_games": msg.get("num_games")}) + "\\n")
		log.flush()
	if msg["type"] == "action_request":
		print("call", flush=True)
'''


class PersistentBotsTest(unittest.TestCase):
	def run_recorded(self, persistent):
		with tempfile.TemporaryDirectory() as d:
			script = os.path.join(d, "recorder.py")
			with open(script, "w") as f:
				f.write(RECORDER)
			logs = [os.path.join(d, f"seat{i}.log") for i in range(2)]
			bots = [f"{sys.executable} {script} {log}" for log in logs]
			result = run_games(3, 1, 100, bots, blind=10, max_hands=5,
				persistent_bots=persistent, verbose=False)
			records = []
			for log in logs:
				with open(log) as f:
					records.append([json.loads(l) for l in f])
			return result, records

	def test_persistent_bots_see_every_game(self):
		result, records = self.run_recorded(persistent=True)
		self.assertEqual(len(result["games"]), 3)
		for seat_records in records:
			self.assertEqual(len({r["pid"] for r in seat_records}), 1)
			self.assertEqual([(r["type"], r["game"]) for r in seat_records], [
				("game_start", 1), ("game_over", 1),
				("game_start", 2), ("game_over", 2),
				("game_start", 3), ("game_over", 3),
				("match_over", None)])
			self.assertEqual(seat_records[-1]["num_games"], 3)

	def test_default_restarts_bots(self):
		_, records = self.run_recorded(persistent=False)
		for seat_records in records:
			self.assertEqual(len({r["pid"] for r in seat_records}), 3)
			self.assertNotIn("match_over", [r["type"] for r in seat_records])

	def test_persistent_crashed_bot_stays_out(self):
		with tempfile.TemporaryDirectory() as d:
			crasher = os.path.join(d, "crash.py")
			with open(crasher, "w") as f:
				f.write("import sys; sys.exit(1)\n")
			bots = [f"{sys.executable} {crasher}", CALL_BOT, CALL_BOT]
			result = run_games(2, 3, 100, bots, blind=10, persistent_bots=True,
				timeout=1, verbose=False)
			self.assertEqual(result["summary"][-1]["seat"], 0)
			self.assertEqual(result["summary"][-1]["wins"], 0)


class CliTest(unittest.TestCase):
	def run_cli(self, *args):
		out = io.StringIO()
		with redirect_stdout(out):
			code = main(list(args))
		return code, out.getvalue()

	def test_games_flag(self):
		code, out = self.run_cli("--games", "3", "--seed", "2", "--money", "200",
			"--blind", "5", "--quiet", RANDOM_BOT, CALL_BOT)
		self.assertEqual(code, 0)
		self.assertIn("Summary over 3 games", out)

	def test_default_is_one_game(self):
		code, out = self.run_cli("--seed", "2", "--money", "200", "--blind", "5",
			"--quiet", RANDOM_BOT, CALL_BOT)
		self.assertEqual(code, 0)
		self.assertNotIn("Summary", out)
		self.assertEqual(len(out.strip().splitlines()), 2)

	def test_persistent_flag(self):
		code, out = self.run_cli("--games", "2", "--persistent-bots", "--seed", "4",
			"--money", "200", "--blind", "5", "--quiet", RANDOM_BOT, CALL_BOT)
		self.assertEqual(code, 0)
		self.assertIn("Summary over 2 games", out)

	def test_rejects_zero_games(self):
		code, _ = self.run_cli("--games", "0", CALL_BOT, CALL_BOT)
		self.assertEqual(code, 1)


if __name__ == "__main__":
	unittest.main()
