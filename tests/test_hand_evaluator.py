import unittest

from poker_engine.domain.card import Card
from poker_engine.domain.hand_evaluator import evaluate, hand_name


def cards(text):
	return [Card.from_str(c) for c in text.split()]


def rank(text):
	return evaluate(cards(text))


class HandEvaluatorTest(unittest.TestCase):
	def test_categories(self):
		cases = {
			"As Ks Qs Js Ts 2d 3c": "straight flush",
			"9c 9d 9h 9s Kd 2c 3c": "four of a kind",
			"9c 9d 9h Ks Kd 2c 3c": "full house",
			"2h 7h 9h Jh Kh Ad Qc": "flush",
			"Ah 2d 3c 4s 5h Kd Kc": "straight",
			"7c 7d 7h As Kd 2c 3c": "three of a kind",
			"7c 7d 4h 4s Kd 2c 3c": "two pair",
			"7c 7d 4h As Kd 2c 3c": "pair",
			"7c 9d 4h As Kd 2c 3c": "high card",
		}
		for hand, name in cases.items():
			self.assertEqual(hand_name(rank(hand)), name, hand)

	def test_ordering(self):
		self.assertGreater(rank("As Ad Kc Qh Js"), rank("Ks Kd Ac Qh Js"))
		self.assertGreater(rank("As Ad Kc Qh Js"), rank("As Ad Kc Qh Ts"))
		self.assertGreater(rank("2s 3d 4c 5h 6s"), rank("As 2d 3c 4h 5s"))
		self.assertGreater(rank("Ks Kd 2c 2h As"), rank("Qs Qd Jc Jh As"))
		self.assertGreater(rank("3s 3d 3c 2h 2s"), rank("2s 2d 2c Ah As"))

	def test_ties(self):
		self.assertEqual(rank("As Kd Qc Jh Ts 2c 3c"), rank("Ad Kc Qh Js Tc 4c 5d"))

	def test_card_round_trip(self):
		for c in ["As", "Td", "2c", "Jh"]:
			self.assertEqual(str(Card.from_str(c)), c)


if __name__ == "__main__":
	unittest.main()
