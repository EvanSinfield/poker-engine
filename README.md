# poker-engine

A no-limit Texas hold'em tournament engine for bots. Each bot runs as a child
process; the engine talks to it with **one JSON object per line** over the
bot's stdin/stdout. Bots can be written in any language.

## Running

```bash
PYTHONPATH=src python3 -m poker_engine --seed 42 --money 1000 --blind 10 \
    "python3 bots/random_bot.py" "python3 bots/random_bot.py" "./my_bot"
```

Or `pip install -e .` and use the `poker-engine` command.

| Option | Default | Meaning |
| --- | --- | --- |
| `--seed` | random | seed for shuffling (games are reproducible for deterministic bots) |
| `--money` | 1000 | starting chips per player |
| `--blind` | 10 | starting small blind (big blind is 2x); doubles every orbit of the button |
| `--timeout` | 10 | seconds a bot has to answer an action request |
| `--max-hands` | none | stop after this many hands (per game) |
| `--games` | 1 | number of games to play; with more than one, a summary of wins, average place and finishing positions per seat is printed at the end |
| `--persistent-bots` | off | keep each bot process running across all `--games` (see below) |
| `--quiet` | off | only print final standings |

Each bot argument is a command line (split with shell rules), so arguments are allowed.
Players are eliminated at 0 chips; the game ends when one player remains.

With `--games N`, every game starts fresh bot processes by default, so bots keep no state
between games. Add `--persistent-bots` to start each bot once and keep it running for the
whole run, e.g. so a reinforcement-learning bot can update its policy from game to game. With `--seed S`, game *i* (counting from 0) is seeded with `S + i`, so the first
game is the same as a single-game run with that seed.

Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`

## Bot protocol

The engine sends these messages. **Only `action_request` expects a reply**;
bots must still read (and may ignore) the others. Write debug output to stderr,
never stdout. Cards are two-character strings: rank `23456789TJQKA` + suit `shcd`, e.g. `"As"`, `"Td"`.

- `game_start` — `game_number` (from 1), `num_games`, `seat`, `num_players`, `starting_money`, `small_blind`
- `hand_start` — `hand_number`, `seat`, `hand` (your two cards), `button`, `small_blind`, `big_blind`, `players`
- `action_request` — see below; reply with one line
- `hand_result` — `board`, `pots` (`[{amount, winners}]`), `showdown` (seat → `{hand, rank}` for hands shown), `history`, `players`
- `game_over` — `game_number`, `standings` (`[{place, seat, money}]`)
- `match_over` — only with `--persistent-bots`, after the last game: `num_games`, `seat`,
  `summary` (`[{seat, bot, wins, average_place, places}]`). Stdin is closed right after,
  so save any model/checkpoint when you get this message or on EOF.

### `action_request`

```json
{
  "type": "action_request",
  "game": {"hand_number": 3, "street": "flop", "board": ["8s", "Qh", "Kc"],
           "pot": 60, "current_bet": 20, "min_raise": 20,
           "small_blind": 10, "big_blind": 20, "button": 0,
           "history": [{"seat": 1, "street": "preflop", "action": "small_blind", "amount": 10, "bet": 10}]},
  "self": {"seat": 2, "hand": ["5s", "6s"], "money": 940, "bet": 0, "total_bet": 20,
           "folded": false, "all_in": false, "in_hand": true},
  "players": [{"seat": 0, "money": 960, "bet": 20, "total_bet": 40, "folded": false, "all_in": false, "in_hand": true}],
  "legal_actions": {"fold": true, "call": 20, "raise": {"min": 40, "max": 940}, "allin": 940}
}
```

`players` lists every seat (including yours). `bet` is chips put in on the current
street, `total_bet` chips put in this hand. In `legal_actions`, `call` is the amount
needed to call (0 means check), `raise` is `null` when raising isn't allowed,
and `allin` is `null` when going all-in would be an illegal raise.

### Replies

Either JSON or plain text:

```
{"action": "raise", "amount": 120}      raise 120
{"action": "call"}                      call      (or check)
{"action": "fold"}                      fold
{"action": "allin"}                     allin
```

Raise amounts are **"raise to"**: the total bet for this street, not the increment.
They are clamped to `[raise.min, raise.max]`. An illegal raise/all-in becomes a call.
An unparseable reply checks if possible, otherwise folds.
A bot that crashes or misses the timeout is disconnected and auto-checks/folds for
the rest of the game.

### Persistent bots and training

With `--persistent-bots` a bot sees `game_start ... game_over` once per game in the same
process, then `match_over`. Your seat stays the same in every game. A bot that crashes or
times out stays disconnected (auto check/fold) for the rest of the run; it is not restarted.

The `--timeout` clock starts when an `action_request` is sent. If your bot trains after
`hand_result` or `game_over`, the next request waits in its stdin while it trains, and that
time counts against it. Keep per-message work short or raise `--timeout`.

## Rules implemented

Standard no-limit hold'em: blinds (heads-up the button posts the small blind and acts
first preflop), burn cards, minimum raise equal to the previous raise, short all-in
raises do not re-open betting, side pots, split pots (odd chips go to the first winner
left of the button), and best-five-of-seven hand evaluation.
