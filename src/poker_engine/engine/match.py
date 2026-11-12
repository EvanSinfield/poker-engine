from typing import Callable, List, Optional

from poker_engine.engine.game import Game


def game_seed(seed: Optional[float], index: int) -> Optional[float]:
	"""Seed for the index-th game (0-based). Game 0 uses the seed as given,
	so a single game is reproduced exactly; later games get seed + index."""
	return None if seed is None else seed + index


def run_games(num_games: int, seed: Optional[float], start_money: int,
		paths: List[str], on_game_start: Optional[Callable[[int], None]] = None,
		**game_kwargs) -> dict:
	"""Play num_games independent games with fresh bot processes for each.

	Returns {"games": [standings, ...], "summary": [per-seat stats]}, with
	the summary sorted best first (most wins, then best average place)."""
	if num_games < 1:
		raise ValueError("Number of games must be at least 1.")

	n = len(paths)
	all_standings = []
	for i in range(num_games):
		if on_game_start:
			on_game_start(i)
		game = Game(game_seed(seed, i), n, start_money, paths, **game_kwargs)
		all_standings.append(game.run())

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
	return {"games": all_standings, "summary": summary}
