import unittest

from poker_engine.engine.pots import build_pots


class PotTest(unittest.TestCase):
	def test_single_pot(self):
		self.assertEqual(build_pots({0: 100, 1: 100, 2: 100}, [0, 1, 2]),
			[(300, [0, 1, 2])])

	def test_side_pots(self):
		pots = build_pots({0: 50, 1: 200, 2: 200}, [0, 1, 2])
		self.assertEqual(pots, [(150, [0, 1, 2]), (300, [1, 2])])

	def test_folded_contribution_and_uncalled_bet(self):
		# seat 0 folded after putting in 30; seat 2 bet 300 but seat 1 was all-in for 100
		pots = build_pots({0: 30, 1: 100, 2: 300}, [1, 2])
		self.assertEqual(pots, [(230, [1, 2]), (200, [2])])

	def test_everyone_folds(self):
		self.assertEqual(build_pots({0: 10, 1: 20, 2: 0}, [1]), [(30, [1])])


if __name__ == "__main__":
	unittest.main()
