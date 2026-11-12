from collections import Counter
from itertools import combinations
from typing import Iterable, Tuple

from poker_engine.domain.card import Card

HIGH_CARD = 0
PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8

HAND_NAMES = [
	"high card", "pair", "two pair", "three of a kind", "straight",
	"flush", "full house", "four of a kind", "straight flush",
]

HandRank = Tuple[int, Tuple[int, ...]]


def evaluate_five(cards: Iterable[Card]) -> HandRank:
	"""Rank exactly five cards. Higher tuples beat lower tuples."""
	cards = list(cards)
	ranks = sorted((c.rank for c in cards), reverse=True)
	flush = len({c.suit for c in cards}) == 1

	unique = sorted(set(ranks), reverse=True)
	straight_high = None
	if len(unique) == 5:
		if unique[0] - unique[4] == 4:
			straight_high = unique[0]
		elif unique == [14, 5, 4, 3, 2]:	# the wheel, A-2-3-4-5
			straight_high = 5

	if straight_high and flush:
		return (STRAIGHT_FLUSH, (straight_high,))

	# group by count then rank, e.g. full house KKK22 -> [(3,13),(2,2)]
	groups = sorted(((n, r) for r, n in Counter(ranks).items()), reverse=True)
	counts = [n for n, _ in groups]
	kickers = tuple(r for _, r in groups)

	if counts[0] == 4:
		return (FOUR_OF_A_KIND, kickers)
	if counts == [3, 2]:
		return (FULL_HOUSE, kickers)
	if flush:
		return (FLUSH, tuple(ranks))
	if straight_high:
		return (STRAIGHT, (straight_high,))
	if counts[0] == 3:
		return (THREE_OF_A_KIND, kickers)
	if counts[:2] == [2, 2]:
		return (TWO_PAIR, kickers)
	if counts[0] == 2:
		return (PAIR, kickers)
	return (HIGH_CARD, tuple(ranks))


def evaluate(cards: Iterable[Card]) -> HandRank:
	"""Best five-card rank from 5-7 cards."""
	cards = list(cards)
	if len(cards) < 5:
		raise ValueError("Need at least 5 cards to evaluate a hand")
	return max(evaluate_five(c) for c in combinations(cards, 5))


def hand_name(rank: HandRank) -> str:
	return HAND_NAMES[rank[0]]
