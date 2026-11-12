#!/usr/bin/env python3
"""Example bot: picks a random legal action.

Protocol: the engine writes one JSON object per line to stdin. Only messages
with "type": "action_request" expect a reply, which is a single line on
stdout, e.g. {"action": "raise", "amount": 120}. Ignore other message types
you don't care about. Use stderr for debug output, never stdout."""
import json
import random
import sys


def choose(legal):
	options = ["call", "call", "call", "fold"]
	if legal["call"] == 0:
		options.remove("fold")
	if legal["raise"]:
		options.append("raise")
	if legal["allin"] is not None and random.random() < 0.05:
		return {"action": "allin"}

	action = random.choice(options)
	if action == "raise":
		lo, hi = legal["raise"]["min"], legal["raise"]["max"]
		return {"action": "raise", "amount": random.randint(lo, min(hi, lo * 3))}
	return {"action": action}


for line in sys.stdin:
	msg = json.loads(line)
	if msg["type"] == "action_request":
		print(json.dumps(choose(msg["legal_actions"])), flush=True)
