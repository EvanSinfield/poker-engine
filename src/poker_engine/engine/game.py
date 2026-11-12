import json
import random
from typing import List, Optional

from poker_engine.domain.actions import Action, Actions
from poker_engine.domain.deck import create_deck
from poker_engine.domain.game_state import GameState
from poker_engine.domain.hand_evaluator import evaluate, hand_name
from poker_engine.domain.player_state import PlayerState
from poker_engine.engine.pots import build_pots
from poker_engine.player.manager import PlayerManager


class Game:
	"""No-limit Texas hold'em tournament between bots.

	Every player starts with startMoney chips. The small blind starts at
	`blind` and doubles every time the button completes an orbit. Players
	are eliminated when they run out of chips; the game ends when one
	player is left (or after max_hands hands)."""

	def __init__(self, seed: float, noPlayers: int, startMoney: int,
			paths: List[str], blind: int = 10, timeout: float = 10.0,
			max_hands: Optional[int] = None, verbose: bool = True):
		if noPlayers < 2:
			raise ValueError("Must be at least 2 players.")
		if len(paths) != noPlayers:
			raise ValueError("Mismatch no.Players and Paths.")
		if startMoney <= 0 or blind <= 0:
			raise ValueError("Starting money and blind must be positive.")

		self.rng = random.Random(seed)
		self.max_hands = max_hands
		self.verbose = verbose
		self.start_money = startMoney

		self.game_state = GameState(blind)
		self.player_states = [PlayerState(startMoney) for _ in range(noPlayers)]
		self.eliminated: List[int] = []	# seats, in order of elimination
		self.player_manager = PlayerManager(paths, timeout)


	def log(self, msg: str):
		if self.verbose:
			print(msg, flush=True)


	# ---------------------------------------------------------------- game

	def run(self) -> List[dict]:
		"""Play the whole game. Returns the standings, winner first."""
		try:
			for i in range(len(self.player_states)):
				self.player_manager.notify(i, {
					"type": "game_start",
					"seat": i,
					"num_players": len(self.player_states),
					"starting_money": self.start_money,
					"small_blind": self.game_state.blind,
				})

			while len(self.seats_with_money()) > 1:
				if self.max_hands is not None and \
						self.game_state.hand_number >= self.max_hands:
					break
				self.run_hand()

			standings = self.standings()
			self.log("Final standings:")
			for s in standings:
				self.log(f"  {s['place']}. seat {s['seat']} ({s['money']} chips)")
			for i in range(len(self.player_states)):
				self.player_manager.notify(i, {
					"type": "game_over", "standings": standings})
			return standings
		finally:
			self.player_manager.close()


	def standings(self) -> List[dict]:
		alive = sorted(self.seats_with_money(),
			key=lambda s: -self.player_states[s].money)
		order = alive + list(reversed(self.eliminated))
		return [{"place": place + 1, "seat": s,
				"money": self.player_states[s].money}
			for place, s in enumerate(order)]


	def seats_with_money(self) -> List[int]:
		return [i for i, p in enumerate(self.player_states) if p.money > 0]


	def next_seat(self, seat: int, seats: List[int]) -> int:
		"""The first seat in `seats` clockwise after `seat`."""
		n = len(self.player_states)
		for k in range(1, n + 1):
			s = (seat + k) % n
			if s in seats:
				return s
		raise ValueError("No seats available")


	def update_button(self):
		seats = self.seats_with_money()
		if self.game_state.hand_number == 1:
			self.game_state.button_position = seats[0]
			return

		old = self.game_state.button_position
		new = self.next_seat(old, seats)
		self.game_state.button_position = new

		# the button wrapped past seat 0: an orbit has finished
		if new <= old:
			self.game_state.blind *= 2
			self.log(f"Blinds up: {self.game_state.blind}/"
				f"{self.game_state.big_blind}")


	# ---------------------------------------------------------------- hand

	def run_hand(self):
		gs = self.game_state
		gs.reset()
		gs.hand_number += 1
		self.update_button()
		gs.min_raise = gs.big_blind

		for p in self.player_states:
			p.reset_for_hand()
		seats = self.seats_with_money()
		button = gs.button_position
		start_money = {s: self.player_states[s].money for s in seats}

		deck = create_deck()
		self.rng.shuffle(deck)
		for s in seats:
			self.player_states[s].deal_hand(deck)

		self.log(f"=== Hand {gs.hand_number}: button seat {button}, "
			f"blinds {gs.blind}/{gs.big_blind} ===")
		for s in seats:
			self.player_manager.notify(s, {
				"type": "hand_start",
				"hand_number": gs.hand_number,
				"seat": s,
				"hand": [str(c) for c in self.player_states[s].hand],
				"button": button,
				"small_blind": gs.blind,
				"big_blind": gs.big_blind,
				"players": self.public_players(),
			})

		# heads-up the button posts the small blind and acts first preflop
		if len(seats) == 2:
			sb = button
		else:
			sb = self.next_seat(button, seats)
		bb = self.next_seat(sb, seats)
		self.post_blind(sb, gs.blind, "small_blind")
		self.post_blind(bb, gs.big_blind, "big_blind")
		gs.current_bet = max(self.player_states[sb].bet,
			self.player_states[bb].bet, gs.big_blind)

		self.round(self.next_seat(bb, seats))

		for street, count in (("flop", 3), ("turn", 1), ("river", 1)):
			if len(self.contenders()) <= 1:
				break
			deck.pop()	# burn
			for _ in range(count):
				gs.board.append(deck.pop())
			self.start_street(street)
			self.round(self.next_seat(button, seats))

		self.showdown()

		for s in sorted(seats, key=lambda s: -start_money[s]):
			if self.player_states[s].money == 0:
				self.eliminated.append(s)
				self.log(f"Seat {s} is eliminated")


	def post_blind(self, seat: int, amount: int, name: str):
		paid = self.put_chips(seat, amount)
		self.record(seat, name, paid)


	def start_street(self, street: str):
		gs = self.game_state
		gs.street = street
		gs.current_bet = 0
		gs.min_raise = gs.big_blind
		for p in self.player_states:
			p.reset_for_street()
		self.log(f"--- {street}: {' '.join(str(c) for c in gs.board)} "
			f"(pot {gs.pot}) ---")


	def contenders(self) -> List[int]:
		return [i for i, p in enumerate(self.player_states)
			if p.in_hand and not p.folded]


	def needs_to_act(self, seat: int) -> bool:
		p = self.player_states[seat]
		if not p.can_act:
			return False
		if p.has_acted and p.bet >= self.game_state.current_bet:
			return False
		# nobody left to bet against and nothing to call
		others = [i for i, q in enumerate(self.player_states)
			if i != seat and q.can_act]
		if not others and p.bet >= self.game_state.current_bet:
			return False
		return True


	def round(self, first: int):
		"""Run one betting round, starting with seat `first`."""
		n = len(self.player_states)
		seat = first
		while len(self.contenders()) > 1:
			for k in range(n):
				if self.needs_to_act((seat + k) % n):
					seat = (seat + k) % n
					break
			else:
				return
			self.act(seat)
			seat = (seat + 1) % n


	# -------------------------------------------------------------- actions

	def legal_actions(self, seat: int) -> dict:
		gs = self.game_state
		p = self.player_states[seat]
		to_call = min(gs.current_bet - p.bet, p.money)
		max_to = p.bet + p.money

		others_can_act = any(q.can_act for i, q in enumerate(self.player_states)
			if i != seat)
		# a short all-in raise doesn't re-open betting for players who
		# have already acted
		can_raise = p.money > to_call and not p.has_acted and others_can_act

		legal = {"fold": True, "call": to_call, "raise": None, "allin": None}
		if can_raise:
			legal["raise"] = {
				"min": min(gs.current_bet + gs.min_raise, max_to),
				"max": max_to,
			}
		if can_raise or p.money <= to_call:
			legal["allin"] = p.money
		return legal


	def resolve_action(self, seat: int, action: Optional[Action],
			legal: dict) -> Action:
		"""Turn whatever the player sent into a legal action.
		Invalid/missing actions check if possible, otherwise fold. An illegal
		raise/all-in becomes a call, and raise amounts are clamped."""
		p = self.player_states[seat]
		if action is None:
			return Action(Actions.CALL if legal["call"] == 0 else Actions.FOLD)

		if action.type == Actions.ALLIN:
			if legal["allin"] is None:
				return Action(Actions.CALL)
			return Action(Actions.RAISE, p.bet + p.money)

		if action.type == Actions.RAISE:
			bounds = legal["raise"]
			if bounds is None:
				return Action(Actions.CALL)
			amount = action.amount if action.amount is not None else bounds["min"]
			return Action(Actions.RAISE,
				max(bounds["min"], min(amount, bounds["max"])))

		return Action(action.type)


	def act(self, seat: int):
		gs = self.game_state
		p = self.player_states[seat]
		legal = self.legal_actions(seat)

		action = None
		if self.player_manager.is_connected(seat):
			state = self.serialize_state_for_player(seat, legal)
			action = self.player_manager.get_action_from_player(seat, state)
		action = self.resolve_action(seat, action, legal)

		if action.type == Actions.FOLD:
			p.folded = True
			self.record(seat, "fold", 0)

		elif action.type == Actions.CALL:
			paid = self.put_chips(seat, gs.current_bet - p.bet)
			self.record(seat, "call" if paid else "check", paid)

		elif action.type == Actions.RAISE:
			raise_to = action.amount
			paid = self.put_chips(seat, raise_to - p.bet)
			if p.bet > gs.current_bet:
				increase = p.bet - gs.current_bet
				if increase >= gs.min_raise:
					# full raise: everyone gets to act again
					gs.min_raise = increase
					for q in self.player_states:
						q.has_acted = False
				gs.current_bet = p.bet
				self.record(seat, "allin" if p.all_in else "raise", paid)
			else:
				self.record(seat, "allin" if p.all_in else "call", paid)

		p.has_acted = True


	def put_chips(self, seat: int, amount: int) -> int:
		p = self.player_states[seat]
		amount = max(0, min(amount, p.money))
		p.money -= amount
		p.bet += amount
		p.total_bet += amount
		self.game_state.pot += amount
		if p.money == 0:
			p.all_in = True
		return amount


	def record(self, seat: int, action: str, amount: int):
		p = self.player_states[seat]
		entry = {"seat": seat, "street": self.game_state.street,
			"action": action, "amount": amount, "bet": p.bet}
		self.game_state.history.append(entry)
		text = f"Seat {seat} {action}"
		if amount:
			text += f" {amount}"
		if action in ("raise", "allin"):
			text += f" (to {p.bet})"
		self.log(text)


	# ------------------------------------------------------------- showdown

	def showdown(self):
		gs = self.game_state
		contenders = self.contenders()
		contributions = {i: p.total_bet for i, p in enumerate(self.player_states)}
		pots = build_pots(contributions, contenders)
		n = len(self.player_states)

		shown = {}
		ranks = {}
		if len(contenders) > 1:
			for s in contenders:
				p = self.player_states[s]
				ranks[s] = evaluate(p.hand + gs.board)
				shown[s] = {"hand": [str(c) for c in p.hand],
					"rank": hand_name(ranks[s])}
				self.log(f"Seat {s} shows {' '.join(str(c) for c in p.hand)}"
					f" ({hand_name(ranks[s])})")

		results = []
		winnings = {s: 0 for s in contenders}
		for amount, eligible in pots:
			if len(eligible) == 1:
				winners = eligible
			else:
				best = max(ranks[s] for s in eligible)
				winners = [s for s in eligible if ranks[s] == best]
			# odd chips go to the first winners clockwise from the button
			winners.sort(key=lambda s: (s - gs.button_position - 1) % n)
			share, rem = divmod(amount, len(winners))
			for k, s in enumerate(winners):
				won = share + (1 if k < rem else 0)
				winnings[s] += won
				self.player_states[s].money += won
			results.append({"amount": amount, "winners": winners})

		for s, won in winnings.items():
			if won:
				self.log(f"Seat {s} wins {won}")
		gs.pot = 0

		message = {
			"type": "hand_result",
			"hand_number": gs.hand_number,
			"board": [str(c) for c in gs.board],
			"pots": results,
			"showdown": {str(s): v for s, v in shown.items()},
			"history": gs.history,
			"players": self.public_players(),
		}
		for i in range(n):
			self.player_manager.notify(i, message)


	# ------------------------------------------------------- serialization

	def public_players(self) -> List[dict]:
		players = []
		for i, p in enumerate(self.player_states):
			state = p.serialize_public()
			state["seat"] = i
			players.append(state)
		return players


	def serialize_state_for_player(self, player_index: int, legal: dict) -> str:
		me = self.player_states[player_index].serialize_full()
		me["seat"] = player_index
		return json.dumps({
			"type": "action_request",
			"game": self.game_state.serialize(),
			"self": me,
			"players": self.public_players(),
			"legal_actions": legal,
		})
