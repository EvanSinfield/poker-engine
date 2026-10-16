from enum import Enum

class Value(Enum):
	TWO = 1
	THREE = 2
	FOUR = 3
	FIVE = 4
	SIX = 5
	SEVEN = 6
	EIGHT = 7
	NINE = 8
	TEN = 9
	JACK = 10
	QUEEN = 11
	KING = 12
	ACE = 13


class Suit(Enum):
	SPADES = 1
	HEARTS = 2
	CLUBS = 3
	DIAMONDS = 4


class Card:
	def __init__(self, value: Value, suit: Suit):
		self.value = value
		self.suit = suit
