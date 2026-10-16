from poker_engine.domain.card import Card
from poker_engine.domain.player_state import PlaterState
from poker_engine.domain.game_state import GameState

def Game:
	def __init__(self, noPlayers: int, startMoney: int):
		self.state = GameState()
		self.players = []
		for _ in range(noPlayers):
			self.players.append(PlayerState(startMoney))
