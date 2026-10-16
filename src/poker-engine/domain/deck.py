from poker_engine.domain.card import Card, Suit, Value

def create_deck() -> List[Card]:
	deck = []
	for s in Suit:
		for v in Value:
			deck.append(Card(v, s))

	return deck
