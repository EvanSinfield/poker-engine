from poker_engine.domain import Card


class PlayerState:
	def __init__(self, money: int):
		self.hand = hand
		self.money = money
		self.bet = 0
		self.folded = False


	def deal_hand(self, deck: List[Card]):
		self.hand.append(deck.pop())
		self.hand.append(deck.pop())


	def serialize_full(self) -> str:
		return f'\{ \"hand\": {self.hand}, \"money\": {self.money}\", \"bet\": {self.bet}, \"folded\": {self.folded} \}' 


	def serialize_public(self) -> str:
		return f'\{ \"bet\": {self.bet}, \"folded\": {self.folded} \}' 
