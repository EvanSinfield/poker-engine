from typing import List

from poker_engine.domain.card import Card


class GameState:
	def __init__(self, blind: int = 10):
		self.board: List[Card] = []
		self.pot = 0
		self.current_bet = 0
		self.min_raise = 0
		self.blind = blind	# small blind; big blind is twice this
		self.button_position = 0
		self.hand_number = 0
		self.street = "preflop"
		self.history: List[dict] = []


	@property
	def big_blind(self) -> int:
		return self.blind * 2


	def reset(self):
		self.board = []
		self.pot = 0
		self.current_bet = 0
		self.min_raise = self.big_blind
		self.street = "preflop"
		self.history = []


	def serialize(self) -> dict:
		return {
			"hand_number": self.hand_number,
			"street": self.street,
			"board": [str(c) for c in self.board],
			"pot": self.pot,
			"current_bet": self.current_bet,
			"min_raise": self.min_raise,
			"small_blind": self.blind,
			"big_blind": self.big_blind,
			"button": self.button_position,
			"history": self.history,
		}
