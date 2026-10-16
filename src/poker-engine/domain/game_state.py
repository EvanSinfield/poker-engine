from poker_engine.domain.card import Card


class GameState:
	def __init__(self):
		self.board = []
		self.pot = 0
		self.current_bet = 0
		self.blind = 0
		self.button_position = 0


	def reset(self):
		self.board = []
		self.pot = 0
		self.current_bet = 0


	def serialize(self):
		return f'\{ \"board\": {self.board}, \"pot\": {self.pot}, \"current bet\": {self.current_bet} \}'
