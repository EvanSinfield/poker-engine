from typing import Callable, List, Optional

from poker_engine.engine.game import Game
from poker_engine.engine.log import EngineLog
from poker_engine.player.manager import PlayerManager


def game_seed(seed: Optional[float], index: int) -> Optional[float]:
	"""Seed for the index-th game (0-based). Game 0 uses the seed as given,
	so a single game is reproduced exactly; later games get seed + index."""
	return None if seed is None else seed + index


def summarize(all_standings: List[List[dict]], paths: List[str]) -> List[dict]:
	"""Per-seat stats, best first (most wins, then best average place)."""
	n = len(paths)
	summary = []
	for seat in range(n):
		places = [next(s["place"] for s in standings if s["seat"] == seat)
			for standings in all_standings]
		summary.append({
			"seat": seat,
			"bot": paths[seat],
			"wins": places.count(1),
			"average_place": sum(places) / len(places),
			"places": [places.count(p) for p in range(1, n + 1)],
		})
	summary.sort(key=lambda s: (-s["wins"], s["average_place"], s["seat"]))
	return summary


def run_games(num_games: int, seed: Optional[float], start_money: int,
		paths: List[str], on_game_start: Optional[Callable[[int], None]] = None,
		persistent_bots: bool = False, timeout: float = 10.0,
		logger: Optional[EngineLog] = None, **game_kwargs) -> dict:
	"""Play num_games games between the same bots.

	By default every game starts fresh bot processes. With persistent_bots
	each bot is started once and kept running for all games, so it can learn
	across games (e.g. reinforcement learning); after the last game it is
	sent a "match_over" message and its stdin is closed.

	Returns {"games": [standings, ...], "hands": [hands played per game],
	"summary": [per-seat stats]}."""
	if num_games < 1:
		raise ValueError("Number of games must be at least 1.")

	warn = logger.warn if logger else None
	manager = PlayerManager(paths, timeout, warn=warn) if persistent_bots else None
	all_standings = []
	hands = []
	try:
		for i in range(num_games):
			if on_game_start:
				on_game_start(i)
			game = Game(game_seed(seed, i), len(paths), start_money, paths,
				timeout=timeout, player_manager=manager, game_number=i + 1,
				num_games=num_games, logger=logger, **game_kwargs)
			all_standings.append(game.run())
			hands.append(game.game_state.hand_number)

		summary = summarize(all_standings, paths)
		if manager is not None:
			for seat in range(len(paths)):
				manager.notify(seat, {
					"type": "match_over",
					"num_games": num_games,
					"seat": seat,
					"summary": summary,
				})
		return {"games": all_standings, "hands": hands, "summary": summary}
	finally:
		if manager is not None:
			manager.close()
