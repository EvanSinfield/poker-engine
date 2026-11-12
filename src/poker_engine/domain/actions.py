import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Actions(Enum):
	CALL = 1	# also used for "check" when there is nothing to call
	RAISE = 2	# amount is the total bet for the street ("raise to")
	FOLD = 3
	ALLIN = 4


ACTION_NAMES = {
	"call": Actions.CALL,
	"check": Actions.CALL,
	"raise": Actions.RAISE,
	"bet": Actions.RAISE,
	"fold": Actions.FOLD,
	"allin": Actions.ALLIN,
	"all-in": Actions.ALLIN,
	"all_in": Actions.ALLIN,
}


@dataclass
class Action:
	type: Actions
	amount: Optional[int] = None


def parse_action(text: Optional[str]) -> Optional[Action]:
	"""Parse a bot's reply. Accepts either JSON such as
	{"action": "raise", "amount": 120} or plain text such as "raise 120".
	Returns None if the reply can't be understood."""
	if text is None:
		return None
	text = text.strip()
	if not text:
		return None

	name, amount = None, None
	if text.startswith("{"):
		try:
			data = json.loads(text)
		except json.JSONDecodeError:
			return None
		if not isinstance(data, dict):
			return None
		name = data.get("action")
		amount = data.get("amount")
	else:
		parts = text.split()
		name = parts[0]
		if len(parts) > 1:
			amount = parts[1]

	if not isinstance(name, str) or name.lower() not in ACTION_NAMES:
		return None
	if amount is not None:
		try:
			amount = int(amount)
		except (TypeError, ValueError):
			return None

	return Action(ACTION_NAMES[name.lower()], amount)
