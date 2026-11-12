import argparse
import sys

from poker_engine.engine.game import Game


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
	parser.add_argument("--quiet", action="store_true")
	args = parser.parse_args(argv)

	try:
		game = Game(args.seed, len(args.bots), args.money, args.bots,
			blind=args.blind, timeout=args.timeout,
			max_hands=args.max_hands, verbose=not args.quiet)
	except (ValueError, OSError) as e:
		print(f"Error: {e}", file=sys.stderr)
		return 1

	standings = game.run()
	if args.quiet:
		for s in standings:
			print(f"{s['place']}. seat {s['seat']} ({s['money']} chips)")
	return 0


if __name__ == "__main__":
	sys.exit(main())
