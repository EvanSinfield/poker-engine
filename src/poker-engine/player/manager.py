from poker_engine.player.player import Player

class PlayerManager:
	def __init__(self, paths: List[str]):
		self.players = []
		for p in paths:
			self.players.append(Player(p))


	def get_action_from_player(self, position: int, state: str):
		self.players[position].get_action(state)
		# TODO: parse output
