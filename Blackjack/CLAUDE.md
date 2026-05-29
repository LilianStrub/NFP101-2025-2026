# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (runtime deps: rich + pyfiglet for the CLI; engine itself is stdlib)
pip install -e .
pip install -e ".[dev]"   # adds pytest

# Run the game
python -m blackjack
blackjack                  # after pip install -e .

# Tests (stdlib unittest runner; requires the package installed, i.e. rich + pyfiglet)
python -m unittest discover -s tests -v

# Run a single test file
python -m unittest tests.test_strategies -v

# With pytest (if installed)
pytest -v
pytest tests/test_strategies.py -v
```

## Architecture

The project is split into five sub-packages under `src/blackjack/`:

| Package | Role |
|---|---|
| `core/` | Immutable primitives: `Card`, `Hand`, `Shoe` (multi-deck with cut card), and enums (`Rank`, `Suit`, `Action`, `Outcome`) |
| `players/` | `BasePlayer` → `Dealer` and `HumanPlayer`. Players own a list of `Hand` objects and call `Strategy.recommend()` internally via `decide()` |
| `strategies/` | `Strategy` (ABC) → `BasicStrategy`, `ManualStrategy`, seven `_CountingStrategy` subclasses. The `STRATEGIES` dict in `__init__.py` is the central registry — add an entry there to expose a new strategy in the UI |
| `game/` | `Rules` (dataclass), `Round` (one-hand orchestration), `Game` (session loop + `Statistics`), `Profile` (persistent save/resume + records). `Round._play_peek` handles the hole-card counting correction manually (un-observe then re-observe the hole card) |
| `ui/` | CLI rendering (`cli.py`) using `rich` + `pyfiglet`; optional ambient music (`audio.py`) via a system audio player |

### Key design decisions

- **Strategy pattern**: `Game`/`Round` hold a `Strategy` reference and call `observe(card)` on every revealed card and `recommend(hand, up_card)` for advice. Counting strategies accumulate `_running_count` via `observe`; non-counting strategies leave it 0.
- **Counting composition**: `_CountingStrategy` (in `counting.py`) *contains* a `BasicStrategy` instance rather than inheriting from it. It delegates `recommend()` to it, overriding only `card_value()` and `betting_units()`.
- **Hole card correction**: `Round._deal_card` observes every card immediately. The hole card is un-observed on the next line (`_running_count -= card_value(...)`) and re-observed when revealed. This is the only place the count is mutated outside `observe()`.
- **Configuration**: `config/default.json` drives all rule parameters loaded by `utils/config.py` into a `Rules` dataclass. Change rules there, not in code.
- **Adding a strategy**: subclass `Strategy` (or `_CountingStrategy`), implement `card_value()` and optionally `betting_units()`, then register it in `strategies/__init__.py`'s `STRATEGIES` dict.
