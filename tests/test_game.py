import os
import sys
import tempfile
import unittest

from poker_engine.domain.actions import Action, Actions, parse_action
from poker_engine.engine.game import Game

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANDOM_BOT = f"{sys.executable} {os.path.join(ROOT, 'bots', 'random_bot.py')}"
CALL_BOT = f"{sys.executable} {os.path.join(ROOT, 'bots', 'call_bot.py')}"


def write_bot(dirname, name, source):
	path = os.path.join(dirname, name)
	with open(path, "w") as f:
		f.write(source)
	return f"{sys.executable} {path}"


class ParseActionTest(unittest.TestCase):
	def test_formats(self):
		self.assertEqual(parse_action('{"action": "raise", "amount": 50}'),
			Action(Actions.RAISE, 50))
		self.assertEqual(parse_action("check\n"), Action(Actions.CALL))
		self.assertEqual(parse_action("RAISE 40"), Action(Actions.RAISE, 40))
		self.assertEqual(parse_action("all-in"), Action(Actions.ALLIN))
		self.assertIsNone(parse_action("dance"))
		self.assertIsNone(parse_action("raise lots"))
		self.assertIsNone(parse_action("[1, 2]"))


class GameTest(unittest.TestCase):
	def test_full_game_conserves_chips(self):
		for seed in range(5):
			bots = [RANDOM_BOT] * 4 + [CALL_BOT]
			game = Game(seed, len(bots), 500, bots, blind=5, verbose=False)
			standings = game.run()
			self.assertEqual(sum(s["money"] for s in standings), 500 * len(bots))
			self.assertEqual(sorted(s["seat"] for s in standings),
				list(range(len(bots))))
			self.assertEqual(standings[0]["money"], 500 * len(bots))
			self.assertEqual(len(game.eliminated), len(bots) - 1)

	def test_heads_up(self):
		game = Game(1, 2, 300, [RANDOM_BOT, RANDOM_BOT], blind=5, verbose=False)
		standings = game.run()
		self.assertEqual(standings[0]["money"], 600)

	def test_max_hands(self):
		game = Game(1, 3, 1000, [CALL_BOT] * 3, max_hands=4, verbose=False)
		game.run()
		self.assertEqual(game.game_state.hand_number, 4)
		self.assertEqual(sum(p.money for p in game.player_states), 3000)

	def test_bad_bots_are_handled(self):
		with tempfile.TemporaryDirectory() as d:
			crasher = write_bot(d, "crash.py", "import sys; sys.exit(1)\n")
			garbage = write_bot(d, "garbage.py",
				"import sys\nfor l in sys.stdin: print('hello', flush=True)\n")
			sleeper = write_bot(d, "sleep.py",
				"import sys, time\nfor l in sys.stdin:\n time.sleep(5)\n")
			bots = [crasher, garbage, sleeper, CALL_BOT]
			game = Game(3, len(bots), 200, bots, blind=5, timeout=0.5,
				verbose=False)
			standings = game.run()
			self.assertEqual(sum(s["money"] for s in standings), 800)
			self.assertEqual(standings[0]["seat"], 3)


if __name__ == "__main__":
	unittest.main()
