import io
import os
import sys
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

	def test_rejects_zero_games(self):
		code, _ = self.run_cli("--games", "0", CALL_BOT, CALL_BOT)
		self.assertEqual(code, 1)


if __name__ == "__main__":
	unittest.main()
