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

The project is split into six sub-packages under `src/blackjack/`:

| Package | Role |
|---|---|
| `core/` | Immutable primitives: `Card`, `Hand`, `Shoe` (multi-deck with cut card), and enums (`Rank`, `Suit`, `Action`, `Outcome`) |
| `players/` | `BasePlayer` → `Dealer` and `HumanPlayer`. Players own a list of `Hand` objects and call `Strategy.recommend()` internally via `decide()` |
| `strategies/` | `Strategy` (ABC) → `BasicStrategy`, `ManualStrategy`, seven `_CountingStrategy` subclasses, plus `SolverStrategy`/`ReinforcementStrategy` (thin adapters over `ai/`). The `STRATEGIES` dict in `__init__.py` is the central registry — add an entry there to expose a new strategy in the UI |
| `ai/` | Ported from the NFP106 "blackjack-ia" project: `ExpectiminimaxSolver` (exact EV search, memoized) and `QLearningAgent` (self-play reinforcement learning). Depends only on `core` — never on `game`/`strategies` at runtime, to avoid an import cycle (see below) |
| `game/` | `Rules` (dataclass), `Round` (one-hand orchestration), `Game` (session loop + `Statistics`), `Profile` (persistent save/resume + records). `Round._play_peek` handles the hole-card counting correction manually (un-observe then re-observe the hole card) |
| `ui/` | CLI rendering (`cli.py`) using `rich` + `pyfiglet`; optional ambient music (`audio.py`) via a system audio player |

### Key design decisions

- **Strategy pattern**: `Game`/`Round` hold a `Strategy` reference and call `observe(card)` on every revealed card and `recommend(hand, up_card)` for advice. Counting strategies accumulate `_running_count` via `observe`; non-counting strategies leave it 0.
- **Counting composition**: `_CountingStrategy` (in `counting.py`) *contains* a `BasicStrategy` instance rather than inheriting from it. It delegates `recommend()` to it, overriding only `card_value()` and `betting_units()`.
- **Hole card correction**: `Round._deal_card` observes every card immediately. The hole card is un-observed on the next line (`_running_count -= card_value(...)`) and re-observed when revealed. This is the only place the count is mutated outside `observe()`.
- **Configuration**: `config/default.json` drives all rule parameters loaded by `utils/config.py` into a `Rules` dataclass. Change rules there, not in code.
- **Adding a strategy**: subclass `Strategy` (or `_CountingStrategy`), implement `card_value()` and optionally `betting_units()`, then register it in `strategies/__init__.py`'s `STRATEGIES` dict. Every entry in `STRATEGIES` must stay instantiable with **no arguments** (`STRATEGIES[key]()`) — `SolverStrategy`/`ReinforcementStrategy` accept an optional `rules` and load `utils.load_rules()` by default to satisfy this.
- **`ai/` import cycle avoidance**: `game` imports `strategies` (`game/game.py` imports `Strategy`), and `strategies` imports `ai` (`solver_strategy.py`/`reinforcement_strategy.py`). `Rules` lives in `game/rules.py`, so `ai/solver.py` and `ai/rl_agent.py` only reference it under `if TYPE_CHECKING` (never imported at runtime — same trick already used by `players/human_player.py` for `ui.cli.UI`); `SolverStrategy`/`ReinforcementStrategy` load `utils.load_rules` with a **deferred import inside `__init__`**, not at module top level, for the same reason. Don't add a top-level `from ..game...` import anywhere under `ai/` or `strategies/*_strategy.py` — it will reintroduce the cycle.
- **Watching an AI agent play** (menu 7, `_watch_ai_session` in `__main__.py`): reuses the exact same `Game`/`Round`/`UI` used for human play — the only difference is `_AutoPlayUI` (in `__main__.py`, next to `_SilentUI`), which delegates every display/animation/narration call to the real `UI` via `__getattr__` and overrides `prompt_action` (answers with `strategy.recommend()`) and `prompt_insurance` (answers with `strategy.take_insurance()`) instead of prompting the keyboard. Both overrides matter: `Round._offer_insurance` calls `ui.prompt_insurance()` whenever the dealer shows an Ace, and without this override it would silently fall through to `_SilentUI`/real `UI`'s keyboard prompt and hang the auto-play session.
- **Insurance is part of the `Strategy` interface**: `Strategy.take_insurance() -> bool` defaults to `False` (correct for any non-counting strategy — negative EV under a random shoe). `SolverStrategy` computes it for real (`ai/solver.py`'s `INSURANCE_EV`, from the same `CARD_PROBS` the rest of the solver uses); `ReinforcementStrategy` delegates to the solver, same as it already does for SPLIT/SURRENDER (insurance was never part of its training either). The human-facing flow (`ui.prompt_insurance`) is untouched — still asks the human directly, regardless of any strategy chosen for advice.
- **Explaining an AI decision, not just taking it**: `SolverStrategy.explain()`/`ReinforcementStrategy.explain()` (→ `ai/solver.py`'s `ExpectiminimaxSolver.evaluate()` / `ai/rl_agent.py`'s new `QLearningAgent.explain()`) return a `Decision` (chosen action + EV/Q-value per action considered) instead of just the action. `QLearningAgent.explain()` mirrors `recommend()`'s exact logic (SPLIT/SURRENDER fallback to the solver, then Q-table lookup) so the two never disagree. `_AutoPlayUI.prompt_action` calls `explain()` when the strategy has it and derives `action` from `decision.action` — never a separate `recommend()` call — so the displayed reasoning (`ui.show_ai_decision`, in `ui/cli.py`) always matches the action actually taken, by construction.
- **Solver/RL agents are an approximation for this table's exact rules**: `ai/` was ported from NFP106 "blackjack-ia", built with `surrender_allowed=True` and no double-total restriction, whereas this game's `config/default.json` has `surrender_allowed=False` and `double_hard_9_to_11_only=True`. `Round._can_double`/`_apply_action` already convert any now-illegal action into a legal one (double → hit, surrender → hit), so nothing breaks — the two AI agents just aren't a perfect solve for this exact rule set. See README § Limites for the adaptation/retraining path if exact parity is ever needed.
