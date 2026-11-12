from typing import List

from poker_engine.domain.card import Card


class PlayerState:
	def __init__(self, money: int):
		self.hand: List[Card] = []
		self.money = money
		self.bet = 0		# chips put in during the current street
		self.total_bet = 0	# chips put in during the whole hand
		self.folded = False
		self.all_in = False
		self.has_acted = False	# acted since the last full raise this street
		self.in_hand = False	# dealt into the current hand


	def reset_for_hand(self):
		self.hand = []
		self.bet = 0
		self.total_bet = 0
		self.all_in = False
		self.has_acted = False
		self.in_hand = self.money > 0
		self.folded = not self.in_hand


	def reset_for_street(self):
		self.bet = 0
		self.has_acted = False


	def deal_hand(self, deck: List[Card]):
		self.hand.append(deck.pop())
		self.hand.append(deck.pop())


	@property
	def can_act(self) -> bool:
		return self.in_hand and not self.folded and not self.all_in


	def serialize_full(self) -> dict:
		state = self.serialize_public()
		state["hand"] = [str(c) for c in self.hand]
		return state


	def serialize_public(self) -> dict:
		return {
			"money": self.money,
			"bet": self.bet,
			"total_bet": self.total_bet,
			"folded": self.folded,
			"all_in": self.all_in,
			"in_hand": self.in_hand,
		}
