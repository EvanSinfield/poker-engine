import argparse
import os
import random
import shlex
import shutil
import sys
from datetime import datetime
from typing import List, Optional

from poker_engine.engine.log import EngineLog
from poker_engine.engine.match import run_games


def format_seed(seed: float) -> str:
	return f"{seed:g}" if isinstance(seed, float) else str(seed)


def resolve_command(command: str) -> str:
	"""The bot command with its executable and any file arguments turned
	into absolute paths, so the log records exactly what was run."""
	parts = shlex.split(command)
	if not parts:
		return command
	resolved = []
	for k, part in enumerate(parts):
		if k == 0 and os.sep not in part:
			resolved.append(shutil.which(part) or part)
		elif os.path.exists(part):
			resolved.append(os.path.abspath(part))
		else:
			resolved.append(part)
	return shlex.join(resolved)


def log_header(log: EngineLog, args, argv: List[str], seed_was_random: bool,
		started: datetime):
	seed = format_seed(args.seed)
	if seed_was_random:
		seed += " (chosen at random; pass --seed to reproduce)"
	max_hands = args.max_hands if args.max_hands is not None else "none"
	lines = [
		"# poker-engine log",
		f"started:          {started.isoformat(timespec='seconds')}",
		f"command:          {shlex.join(['python3', '-m', 'poker_engine'] + argv)}",
		f"working dir:      {os.getcwd()}",
		"",
		"settings:",
		f"  seed:           {seed}",
		f"  games:          {args.games}",
		f"  starting money: {args.money}",
		f"  small blind:    {args.blind} (big blind {args.blind * 2}, doubles every orbit)",
		f"  timeout:        {args.timeout:g}s",
		f"  max hands:      {max_hands}",
		f"  persistent bots: {'yes' if args.persistent_bots else 'no'}",
		"",
		"bots:",
	]
	for seat, command in enumerate(args.bots):
		lines.append(f"  seat {seat}: {command}")
		resolved = resolve_command(command)
		if resolved != command:
			lines.append(f"          resolved: {resolved}")
	lines.append("")
	for line in lines:
		log.file_only(line)


def main(argv: Optional[List[str]] = None) -> int:
	if argv is None:
		argv = sys.argv[1:]
	parser = argparse.ArgumentParser(
		prog="poker_engine",
		description="Run a no-limit hold'em tournament between bot programs "
			"that communicate over stdin/stdout.")
	parser.add_argument("bots", nargs="+",
		help="command to start each bot, e.g. 'python3 bots/random_bot.py'")
	parser.add_argument("--seed", type=float, default=None,
		help="random seed (default: chosen at random and shown in the log)")
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
	parser.add_argument("--persistent-bots", action="store_true",
		help="start each bot once and keep it running across all games "
			"(e.g. for training); by default bots are restarted every game")
	parser.add_argument("--log-file", metavar="PATH", default=None,
		help="write a log with the settings, bot commands and every hand to "
			"PATH (written in full even with --quiet)")
	parser.add_argument("--quiet", action="store_true")
	args = parser.parse_args(argv)

	if args.games < 1:
		print("Error: --games must be at least 1", file=sys.stderr)
		return 1

	# always use a concrete seed so a logged run can be replayed
	seed_was_random = args.seed is None
	if seed_was_random:
		args.seed = random.SystemRandom().randrange(2 ** 32)

	log_file = None
	if args.log_file:
		try:
			parent = os.path.dirname(os.path.abspath(args.log_file))
			os.makedirs(parent, exist_ok=True)
			log_file = open(args.log_file, "w", encoding="utf-8")
		except OSError as e:
			print(f"Error: can't open log file: {e}", file=sys.stderr)
			return 1

	try:
		log = EngineLog(verbose=not args.quiet, file=log_file)
		started = datetime.now()
		log_header(log, args, argv, seed_was_random, started)
		return run(args, log, started)
	finally:
		if log_file is not None:
			log_file.close()


def run(args, log: EngineLog, started: datetime) -> int:
	def announce(i: int):
		if args.games > 1:
			log.info(f"##### Game {i + 1}/{args.games} #####")

	try:
		result = run_games(args.games, args.seed, args.money, args.bots,
			on_game_start=announce, persistent_bots=args.persistent_bots,
			blind=args.blind, timeout=args.timeout, max_hands=args.max_hands,
			logger=log)
	except (ValueError, OSError) as e:
		log.warn(f"Error: {e}")
		return 1

	if args.games == 1:
		# the game already logged its standings when verbose
		if args.quiet:
			for s in result["games"][0]:
				print(f"{s['place']}. seat {s['seat']} ({s['money']} chips)")
	else:
		log.result(f"Summary over {args.games} games:")
		log.result(f"  {'seat':>4}  {'wins':>5}  {'avg place':>9}  "
			f"{'finishes 1st,2nd..':<18}  bot")
		for s in result["summary"]:
			places = " ".join(str(c) for c in s["places"])
			log.result(f"  {s['seat']:>4}  {s['wins']:>5}  {s['average_place']:>9.2f}"
				f"  {places:<18}  {s['bot']}")

	finished = datetime.now()
	elapsed = (finished - started).total_seconds()
	log.file_only("")
	log.file_only(f"finished:         {finished.isoformat(timespec='seconds')}"
		f" ({elapsed:.1f}s)")
	return 0


if __name__ == "__main__":
	sys.exit(main())
