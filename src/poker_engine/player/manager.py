import json
import sys
from typing import List, Optional

from poker_engine.domain.actions import Action, parse_action
from poker_engine.player.player import Player


class PlayerManager:
	def __init__(self, paths: List[str], timeout: float = 10.0):
		self.timeout = timeout
		self.players: List[Player] = []
		try:
			for i, p in enumerate(paths):
				self.players.append(Player(p, name=f"seat {i}: {p}"))
		except OSError:
			self.close()
			raise


	def is_connected(self, position: int) -> bool:
		return self.players[position].connected


	def notify(self, position: int, message: dict):
		"""Send a message that does not expect a reply."""
		self.players[position].send(json.dumps(message))


	def get_action_from_player(self, position: int, state: str) -> Optional[Action]:
		"""Returns the parsed action, or None if the player didn't give a
		valid one (timeout, crash or garbage), in which case the engine
		applies a default action."""
		player = self.players[position]
		output = player.get_action(state, self.timeout)
		if output is None:
			return None
		action = parse_action(output)
		if action is None:
			print(f"[engine] player {player.name!r} sent invalid action: "
				f"{output.strip()!r}", file=sys.stderr)
		return action


	def close(self):
		for p in self.players:
			p.close()
