import random

from poker_engine.domain.card import Card
from poker_engine.domain.deck import create_deck
from poker_engine.domain.player_state import PlaterState
from poker_engine.domain.game_state import GameState
from poker_engine.domain.actions import Actions
from poker_engine.player.manager import PlayerManager


def Game:
	def __init__(self, seed: float, noPlayers: int, startMoney: int,
			paths: List[str]):
		if noPlayers < 3:
			print("Error: Must be more than 2 players.")
			return
		if len(paths) != noPlayers:
			print("Error: Mismatch no.Players and Paths.")

		self.game_state = GameState()
		self.player_states = []
		self.player_manager = PlayerManager(paths)
		for _ in range(noPlayers):
			self.player_state.append(PlayerState(startMoney))

		random.seed(seed)


	def update_button(self):
		self.game_state.button_position += 1
		self.game_state.button_position %= len(self.player_states)

		if self.game_state.button_position == 0:
			self.game_state.blind *= 2


	def run_hand(self):
		self.game_state.reset()
		update_button(self.game_state)

		deck = create_deck()
		random.shuffle(deck)

		for p in self.player_states:
			p.deal_hand(deck)

		# set the player blinds
		self.player_states[(button_pos + 1) % 
			len(self.player_states)] = blind
		self.player_states[(button_pos + 2) % 
			len(self.player_states)] = blind * 2

		round()
		# TODO: check player states after each round
		self.game_state.board.append(deck.pop())
		self.game_state.board.append(deck.pop())
		self.game_state.board.append(deck.pop())
		round()
		self.game_state.board.append(deck.pop())
		round()
		self.game_state.board.append(deck.pop())

		# TODO: showdown


	def round(self):
		raise_flag = True
		while raise_flag:
			raise_flag = False
			for i in range(len(self.player_states)):
				if not self.player_states[i].folded:
					state_rep = serialize_state_for_player(self.game_sate,
						self.player_states, i)
					action = self.player_manager.get_action_from_player(i, 
						state_rep)
				# TODO: do something with the action
				if action == Actions.RAISE and not raise_flag:
					raise_flag = True


	def serialize_state_for_player(self, game: GameState,
			players: List[PlaterStates], player_index: int):
		state = '{ "game": ' + self.game_state.serialize() + ', "self": '
		state += self.player_states[player_index].serialize_full()
		state += ', "players": [ ' 
		for i in range(len(self.player_states)):
			if i != player_index:
				state += self.player_states[i].serialize_public()
				state += ', '
		state += '] }'
		# TODO: add legal actions
		return state
