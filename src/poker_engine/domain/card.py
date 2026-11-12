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

	@property
	def rank(self) -> int:
		"""Numeric rank, 2 (deuce) .. 14 (ace)."""
		return self.value + 1


class Suit(Enum):
	SPADES = 1
	HEARTS = 2
	CLUBS = 3
	DIAMONDS = 4


VALUE_CHARS = "23456789TJQKA"
SUIT_CHARS = "shcd"


class Card:
	"""A playing card. Serialised as two characters, e.g. "As", "Td", "2c"."""

	def __init__(self, value: Value, suit: Suit):
		self.value = value
		self.suit = suit

	@property
	def rank(self) -> int:
		return self.value.rank

	@classmethod
	def from_str(cls, text: str) -> "Card":
		if len(text) != 2:
			raise ValueError(f"Invalid card: {text!r}")
		v = VALUE_CHARS.index(text[0].upper()) + 1
		s = SUIT_CHARS.index(text[1].lower()) + 1
		return cls(Value(v), Suit(s))

	def __str__(self) -> str:
		return VALUE_CHARS[self.value.value - 1] + SUIT_CHARS[self.suit.value - 1]

	def __repr__(self) -> str:
		return f'{self.value.name} {self.suit.name}'

	def __eq__(self, other) -> bool:
		return isinstance(other, Card) and self.value == other.value \
			and self.suit == other.suit

	def __hash__(self) -> int:
		return hash((self.value, self.suit))
