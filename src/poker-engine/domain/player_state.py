from poker_engine.domain import Card

class PlayerState:
	def __init__(self, hand: Tuple(Card), money: int):
		self.hand = hand
		self.money = money
		self.bet = 0
		self.folded = False
