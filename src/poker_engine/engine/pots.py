from typing import Dict, Iterable, List, Tuple

Pot = Tuple[int, List[int]]	# (amount, eligible seats)


def build_pots(contributions: Dict[int, int], contenders: Iterable[int]) -> List[Pot]:
	"""Split the chips put in this hand into a main pot and side pots.

	contributions maps seat -> chips put in this hand (folded players
	included). contenders are the seats still in the hand. Each pot lists
	the contenders who are eligible to win it. An uncalled bet ends up as
	a pot with a single eligible player, i.e. it is returned to them."""
	contenders = sorted(set(contenders))
	levels = sorted({contributions[s] for s in contenders if contributions[s] > 0})

	pots: List[Pot] = []
	prev = 0
	for level in levels:
		amount = sum(min(a, level) - min(a, prev) for a in contributions.values())
		eligible = [s for s in contenders if contributions[s] >= level]
		if pots and pots[-1][1] == eligible:
			pots[-1] = (pots[-1][0] + amount, eligible)
		else:
			pots.append((amount, eligible))
		prev = level

	# chips from folded players above the highest contender's level
	leftover = sum(a - min(a, prev) for a in contributions.values())
	if leftover:
		if pots:
			pots[-1] = (pots[-1][0] + leftover, pots[-1][1])
		else:
			pots.append((leftover, contenders))
	return pots
