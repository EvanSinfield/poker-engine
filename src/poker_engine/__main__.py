import argparse
import os
import random
import shlex
import shutil
import sys
from datetime import datetime
from typing import List, Optional

from poker_engine.engine.log import EngineLog
from poker_engine.engine.match import game_seed, run_games


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


HAND_LOG_MARKER = "==================== hand log ===================="


def run_info_lines(args, argv: List[str], seed_was_random: bool) -> List[str]:
	"""Command line, settings and bots: everything needed to rerun."""
	seed = format_seed(args.seed)
	if seed_was_random:
		seed += " (chosen at random; pass --seed to reproduce)"
	max_hands = args.max_hands if args.max_hands is not None else "none"
	lines = [
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
	return lines


def summary_table(summary: List[dict]) -> List[str]:
	lines = [f"  {'seat':>4}  {'wins':>5}  {'avg place':>9}  "
		f"{'finishes 1st,2nd..':<18}  bot"]
	for s in summary:
		places = " ".join(str(c) for c in s["places"])
		lines.append(f"  {s['seat']:>4}  {s['wins']:>5}  {s['average_place']:>9.2f}"
			f"  {places:<18}  {s['bot']}")
	return lines


def result_lines(args, result: Optional[dict]) -> List[str]:
	if result is None:
		return ["results:          none"]
	bots = args.bots
	if args.games == 1:
		standings = result["games"][0]
		lines = [f"final standings ({result['hands'][0]} hands):"]
		width = max(len(str(s["money"])) for s in standings)
		for s in standings:
			lines.append(f"  {s['place']}. seat {s['seat']}  "
				f"{s['money']:>{width}} chips  {bots[s['seat']]}")
		return lines

	lines = [f"summary over {args.games} games:"] + summary_table(result["summary"])
	lines += ["", "games (finishing order by seat):"]
	for i, (standings, hands) in enumerate(zip(result["games"], result["hands"])):
		order = ", ".join(str(s["seat"]) for s in standings)
		lines.append(f"  game {i + 1:>{len(str(args.games))}} "
			f"(seed {format_seed(game_seed(args.seed, i))}, {hands} hands): {order}")
	return lines


def header_text(status: str, started: datetime, finished: Optional[datetime],
		results: List[str], run_info: List[str]) -> str:
	lines = ["# poker-engine log", f"status:           {status}",
		f"started:          {started.isoformat(timespec='seconds')}"]
	if finished is not None:
		elapsed = (finished - started).total_seconds()
		lines.append(f"finished:         {finished.isoformat(timespec='seconds')}"
			f" ({elapsed:.1f}s)")
	lines += [""] + results + [""] + run_info + ["", HAND_LOG_MARKER, ""]
	return "\n".join(lines) + "\n"


def finalize_log(path: str, provisional: str, final: str):
	"""Swap the provisional header for the final one (results first),
	keeping the hand log that was streamed to the file during the run."""
	with open(path, encoding="utf-8") as f:
		body = f.read()[len(provisional):]
	tmp = path + ".tmp"
	with open(tmp, "w", encoding="utf-8") as f:
		f.write(final + body)
	os.replace(tmp, path)


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
		help="write a log to PATH: results and settings at the top, then "
			"every hand (written in full even with --quiet)")
	parser.add_argument("--quiet", action="store_true")
	args = parser.parse_args(argv)

	if args.games < 1:
		print("Error: --games must be at least 1", file=sys.stderr)
		return 1

	# always use a concrete seed so a logged run can be replayed
	seed_was_random = args.seed is None
	if seed_was_random:
		args.seed = random.SystemRandom().randrange(2 ** 32)

	started = datetime.now()
	run_info = run_info_lines(args, argv, seed_was_random)
	provisional = header_text("running (incomplete)", started, None,
		["results:          not available yet"], run_info)

	log_file = None
	if args.log_file:
		try:
			parent = os.path.dirname(os.path.abspath(args.log_file))
			os.makedirs(parent, exist_ok=True)
			log_file = open(args.log_file, "w", encoding="utf-8")
			log_file.write(provisional)
			log_file.flush()
		except OSError as e:
			print(f"Error: can't open log file: {e}", file=sys.stderr)
			return 1

	log = EngineLog(verbose=not args.quiet, file=log_file)
	status, result, code = "interrupted", None, 1
	try:
		result, error = run(args, log)
		status = "completed" if error is None else f"failed: {error}"
		code = 0 if error is None else 1
	finally:
		if log_file is not None:
			log_file.close()
			final = header_text(status, started, datetime.now(),
				result_lines(args, result), run_info)
			finalize_log(args.log_file, provisional, final)
	return code


def run(args, log: EngineLog):
	"""Play the games. Returns (result, None) or (None, error message)."""
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
		return None, str(e)

	# console only: the log file gets these at the top when it's finalized
	if args.games == 1:
		if args.quiet:
			for s in result["games"][0]:
				print(f"{s['place']}. seat {s['seat']} ({s['money']} chips)")
	else:
		print(f"Summary over {args.games} games:")
		for line in summary_table(result["summary"]):
			print(line)
	return result, None


if __name__ == "__main__":
	sys.exit(main())
