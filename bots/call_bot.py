#!/usr/bin/env python3
"""Example bot: always checks or calls, using the plain-text reply format."""
import json
import sys

for line in sys.stdin:
	if json.loads(line)["type"] == "action_request":
		print("call", flush=True)
