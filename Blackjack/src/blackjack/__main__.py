"""
Point d'entrée du jeu.

Lancement :  ``python -m blackjack``
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from .game import Game
from .players import HumanPlayer
from .strategies import STRATEGIES, BasicStrategy, ManualStrategy, Strategy
from .ui import UI
from .utils import configure_logging, load_rules

logger = logging.getLogger(__name__)


def _play_session(ui: UI) -> None:
    """Boucle principale : configure la partie et enchaîne les manches."""
    rules = load_rules()

    # Configuration du joueur.
    ui.header("Configuration du joueur")
    bankroll = ui.ask_float("Solde de départ", default=rules.starting_bankroll,
                            minimum=rules.min_bet)

    # Mode apprentissage : pensé pour les débutants.
    ui.write()
    ui.info("Mode apprentissage : affiche le conseil de la stratégie de base à "
            "chaque tour et explique chaque action la première fois qu'elle apparaît.")
    learning = ui.ask_yes_no("Activer le mode apprentissage ?", default=True)

    if learning:
        strategy: Strategy = BasicStrategy()
        ui.success("Mode apprentissage activé — stratégie de base utilisée comme guide.")
        ui.learning_mode = True
        ui._explained_actions.clear()
        use_advice = True
    else:
        use_advice = ui.ask_yes_no(
            "Voulez-vous afficher l'aide d'une stratégie pendant le jeu ?",
            default=True,
        )
        strategy = ManualStrategy()
        if use_advice:
            _, strategy = ui.choose_strategy()
        ui.learning_mode = False

    # Animations : option indépendante du mode apprentissage.
    ui.write()
    ui.info("Animations : distribution carte par carte et suspense sur les "
            "tirages du croupier. Désactivez-les pour un jeu plus rapide.")
    ui.set_animations(ui.ask_yes_no("Activer les animations ?", default=True))

    player = HumanPlayer(name="Joueur", bankroll=bankroll, strategy=strategy)
    player.show_advice = use_advice and not isinstance(strategy, ManualStrategy)

    game = Game(rules=rules, player=player, strategy=strategy, ui=ui)

    # Mise par défaut suggérée pour un débutant : 1% du solde initial,
    # bornée par les limites min/max de mise du casino.
    beginner_bet = max(rules.min_bet, round(bankroll * 0.01, 2))
    beginner_bet = min(beginner_bet, rules.max_bet)

    # Boucle de jeu.
    while True:
        if player.bankroll < rules.min_bet:
            ui.error("Plus assez d'argent pour miser. Fin de la partie.")
            break

        # En-tête de manche affiché dès que le joueur s'engage, avant la mise.
        manche = game.stats.rounds_played + 1
        ui.show_round_header(manche)
        ui.show_bankroll(player)
        if strategy.counts_cards:
            ui.show_count_status(strategy, game.shoe.decks_remaining)

        suggested = game.suggested_bet() if strategy.counts_cards else beginner_bet
        bet = ui.ask_float(
            f"Votre mise (min {rules.min_bet}, max {min(rules.max_bet, player.bankroll)})",
            default=min(suggested, player.bankroll),
            minimum=rules.min_bet,
            maximum=min(rules.max_bet, player.bankroll),
        )

        try:
            results = game.play_round(bet)
        except ValueError as exc:
            ui.error(str(exc))
            continue

        ui.show_round_results(results)

        if not ui.ask_yes_no("Jouer une autre manche ?", default=True):
            break

    ui.show_stats(game.stats)


def _compare_strategies(ui: UI) -> None:
    """Mode simulation : compare les stratégies sur plusieurs milliers de mains."""
    ui.header("Mode simulation comparative")
    n_rounds = ui.ask_int("Combien de manches simuler par stratégie ?",
                           default=2000, minimum=100, maximum=50000)
    bet_size = ui.ask_float("Taille de la mise (fixe)", default=10.0,
                             minimum=0.5, maximum=1000.0)

    rules = load_rules()
    ui.write()
    ui.write(f"{'Stratégie':<25}{'EV par main':>16}{'Win %':>10}{'BJ %':>10}")
    ui.write("─" * 61)
    for key, cls in STRATEGIES.items():
        if cls is ManualStrategy:
            continue
        # Le joueur de simu utilise la *même* stratégie pour décider.
        strategy = cls()
        sim_player = HumanPlayer(name="SimBot", bankroll=1e9, strategy=strategy)
        sim_player.ui = _SilentUI(strategy)
        game = Game(rules=rules, player=sim_player, strategy=strategy, ui=None)
        for _ in range(n_rounds):
            try:
                game.play_round(bet_size)
            except ValueError:
                break
        ev = game.stats.expected_value * 100
        wr = game.stats.win_rate * 100
        bj = (game.stats.blackjacks / game.stats.hands_played * 100
              if game.stats.hands_played else 0.0)
        ui.write(f"{cls.name:<25}{ev:>+15.3f}%{wr:>9.2f}%{bj:>9.2f}%")
    ui.write()
    ui.info("Lecture : EV = espérance nette par unité misée. "
            "Plus c'est proche de 0, mieux c'est pour le joueur.")


def _about(ui: UI) -> None:
    ui.header("À propos")
    ui.write("""
  Projet pédagogique — NFP01 (CNAM).
  Jeu de Blackjack en Python orienté objet.

  Fonctionnalités :
    • Plusieurs stratégies d'aide à la décision sélectionnables :
        - Stratégie de Base (4-8 jeux, S17, DAS, surrender)
        - Comptages Hi-Lo, KO, Hi-Opt I, Hi-Opt II, Omega II, Zen, Red 7
    • Règles paramétrables via config/default.json
    • Mode simulation comparant les stratégies
    • Journaux dans logs/blackjack.log

  Sources de référence pour les stratégies :
    • E. O. Thorp,    Beat the Dealer
    • S. Wong,        Professional Blackjack
    • D. Schlesinger, Blackjack Attack
    • A. Snyder,      Blackbelt in Blackjack
    • B. Carlson,     Blackjack for Blood
""")


class _SilentUI:
    """Faux UI utilisé en mode simulation : auto-décide selon la stratégie."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy

    def prompt_action(self, player, hand, dealer_up, advice=None, rules=None, hand_index=0):  # noqa: ANN001, ARG002
        action = self.strategy.recommend(hand, dealer_up)
        # Filet de sécurité : si l'action n'est pas faisable, basculer en sécurité.
        if action.name == "DOUBLE" and not hand.can_double:
            return _safe_fallback(action)
        if action.name == "SPLIT" and not hand.can_split:
            return _safe_fallback(action)
        if action.name == "SURRENDER" and not hand.can_surrender:
            return _safe_fallback(action)
        return action

    # Les autres callbacks ne font rien.
    def narrate(self, *a, **k): pass                   # noqa: E704
    def show_pre_deal(self, *a, **k): pass             # noqa: E704
    def show_deal_step(self, *a, **k): pass            # noqa: E704
    def show_initial_deal(self, *a, **k): pass        # noqa: D401, E704
    def show_dealer_reveal(self, *a, **k): pass       # noqa: E704
    def show_dealer_draw(self, *a, **k): pass         # noqa: E704
    def show_action(self, *a, **k): pass              # noqa: E704
    def show_shuffle(self, *a, **k): pass             # noqa: E704
    def show_round_results(self, *a, **k): pass       # noqa: E704


def _safe_fallback(action):  # noqa: ANN001
    from .core import Action
    if action is Action.DOUBLE:
        return Action.HIT
    if action is Action.SPLIT:
        return Action.HIT
    if action is Action.SURRENDER:
        return Action.HIT
    return Action.STAND


def main(argv: Optional[list] = None) -> int:
    """Point d'entrée CLI."""
    configure_logging()
    ui = UI()
    try:
        while True:
            choice = ui.main_menu()
            if choice == "1":
                _play_session(ui)
            elif choice == "2":
                ui.show_rules()
            elif choice == "3":
                _compare_strategies(ui)
            elif choice == "4":
                _about(ui)
            elif choice == "0":
                ui.success("Au revoir !")
                return 0
            else:
                ui.error("Choix invalide.")
    except (KeyboardInterrupt, EOFError):
        ui.write()
        ui.success("Au revoir !")
        return 0


if __name__ == "__main__":
    sys.exit(main())
