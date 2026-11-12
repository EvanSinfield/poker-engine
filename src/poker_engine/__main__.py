import argparse
import sys

from poker_engine.engine.match import run_games


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(
		prog="poker_engine",
		description="Run a no-limit hold'em tournament between bot programs "
			"that communicate over stdin/stdout.")
	parser.add_argument("bots", nargs="+",
		help="command to start each bot, e.g. 'python3 bots/random_bot.py'")
	parser.add_argument("--seed", type=float, default=None)
	parser.add_argument("--money", type=int, default=1000,
		help="starting chips per player (default 1000)")
	parser.add_argument("--blind", type=int, default=10,
		help="starting small blind, doubles every orbit (default 10)")
	parser.add_argument("--timeout", type=float, default=10.0,
		help="seconds a bot has to respond (default 10)")
	parser.add_argument("--max-hands", type=int, default=None)
	parser.add_argument("--games", type=int, default=1,
		help="number of games to play, each with fresh bot processes "
			"(default 1). With --seed, game i uses seed + i")
	parser.add_argument("--quiet", action="store_true")
	args = parser.parse_args(argv)

	if args.games < 1:
		print("Error: --games must be at least 1", file=sys.stderr)
		return 1

	def announce(i: int):
		if not args.quiet and args.games > 1:
			print(f"##### Game {i + 1}/{args.games} #####", flush=True)

	try:
		result = run_games(args.games, args.seed, args.money, args.bots,
			on_game_start=announce, blind=args.blind, timeout=args.timeout,
			max_hands=args.max_hands, verbose=not args.quiet)
	except (ValueError, OSError) as e:
		print(f"Error: {e}", file=sys.stderr)
		return 1

	if args.games == 1:
		if args.quiet:
			for s in result["games"][0]:
				print(f"{s['place']}. seat {s['seat']} ({s['money']} chips)")
		return 0

	print(f"Summary over {args.games} games:")
	print(f"  {'seat':>4}  {'wins':>5}  {'avg place':>9}  {'finishes 1st,2nd..':<18}  bot")
	for s in result["summary"]:
		places = " ".join(str(c) for c in s["places"])
		print(f"  {s['seat']:>4}  {s['wins']:>5}  {s['average_place']:>9.2f}"
			f"  {places:<18}  {s['bot']}")
	return 0

if __name__ == "__main__":
	sys.exit(main())
