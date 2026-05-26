"""
Module ``cli`` — interface en ligne de commande.

Sans dépendance externe : utilise les codes ANSI standards (compatibles
tous terminaux modernes, Windows 10+, Linux, macOS).
"""

from __future__ import annotations

import sys
from typing import List, Optional, Tuple

from ..core import Action, Card, Hand, Outcome
from ..players import Dealer, HumanPlayer
from ..strategies import STRATEGIES, Strategy


# --------------------------------------------------------------------------- #
# Couleurs ANSI
# --------------------------------------------------------------------------- #
class _Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{_Color.RESET}"


def _card_str(card: Card) -> str:
    color = _Color.RED if card.suit.is_red else _Color.WHITE
    return _c(f"[{card.rank.label}{card.suit.symbol}]", color)


def _hand_str(hand: Hand, hide_first: bool = False) -> str:
    if not hand.cards:
        return _c("(vide)", _Color.DIM)
    if hide_first:
        parts = [_c("[??]", _Color.GREY)] + [_card_str(c) for c in hand.cards[1:]]
        return " ".join(parts)
    cards_str = " ".join(_card_str(c) for c in hand.cards)
    soft_str = "soft" if hand.is_soft else "hard"
    total_color = (
        _Color.RED if hand.is_bust
        else _Color.YELLOW if hand.total == 21
        else _Color.GREEN
    )
    return f"{cards_str}  {_c(f'({soft_str} {hand.total})', total_color)}"


# --------------------------------------------------------------------------- #
# Classe UI
# --------------------------------------------------------------------------- #
class UI:
    """Interface utilisateur en ligne de commande."""

    def __init__(self, stream=sys.stdout) -> None:  # noqa: ANN001
        self.out = stream

    # ------------------------------------------------------------------ #
    # Sorties basiques
    # ------------------------------------------------------------------ #
    def write(self, text: str = "") -> None:
        print(text, file=self.out)

    def header(self, text: str) -> None:
        line = "═" * (len(text) + 4)
        self.write()
        self.write(_c(f"╔{line}╗", _Color.CYAN))
        self.write(_c(f"║  {text}  ║", _Color.CYAN))
        self.write(_c(f"╚{line}╝", _Color.CYAN))

    def info(self, text: str) -> None:
        self.write(_c("ℹ  " + text, _Color.BLUE))

    def warn(self, text: str) -> None:
        self.write(_c("⚠  " + text, _Color.YELLOW))

    def error(self, text: str) -> None:
        self.write(_c("✗  " + text, _Color.RED))

    def success(self, text: str) -> None:
        self.write(_c("✓  " + text, _Color.GREEN))

    # ------------------------------------------------------------------ #
    # Écrans de menus
    # ------------------------------------------------------------------ #
    def main_menu(self) -> str:
        """Affiche le menu principal et renvoie le choix saisi."""
        self.header("BLACKJACK — Menu Principal")
        self.write(f"  {_c('1', _Color.BOLD)}. Démarrer une nouvelle partie")
        self.write(f"  {_c('2', _Color.BOLD)}. Comparer les stratégies (simulation)")
        self.write(f"  {_c('3', _Color.BOLD)}. À propos / aide")
        self.write(f"  {_c('0', _Color.BOLD)}. Quitter")
        return input("\nVotre choix : ").strip()

    def choose_strategy(self) -> Tuple[str, Strategy]:
        """Affiche la liste des stratégies et fait choisir le joueur.

        C'est la fonctionnalité demandée par l'énoncé : « afficher le choix
        possible de toutes les méthodes qui existent pour prendre des
        décisions ».
        """
        self.header("Choix de la stratégie d'aide à la décision")
        keys = list(STRATEGIES.keys())
        for i, key in enumerate(keys, start=1):
            cls = STRATEGIES[key]
            tag = _c("[comptage]", _Color.MAGENTA) if cls.counts_cards else ""
            self.write(f"  {_c(str(i), _Color.BOLD)}. {_c(cls.name, _Color.CYAN)} {tag}")
            # Affiche la description sur deux lignes max.
            desc = cls.description.replace("\n", " ")
            self.write(_c(f"     {desc}", _Color.DIM))
            self.write()

        while True:
            choice = input("Votre choix (numéro) : ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(keys):
                key = keys[int(choice) - 1]
                cls = STRATEGIES[key]
                # Quelques stratégies ont besoin du nombre de jeux à l'init.
                try:
                    strat = cls()  # par défaut 6 jeux pour KO/Red7.
                except TypeError:
                    strat = cls()
                self.success(f"Stratégie sélectionnée : {strat.name}")
                return key, strat
            self.error("Choix invalide. Recommencez.")

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        suffix = " [O/n] " if default else " [o/N] "
        ans = input(question + suffix).strip().lower()
        if not ans:
            return default
        return ans in ("o", "oui", "y", "yes")

    def ask_int(self, question: str, default: int, minimum: int = 1,
                maximum: int = 100) -> int:
        while True:
            ans = input(f"{question} [{default}] : ").strip()
            if not ans:
                return default
            if ans.isdigit() and minimum <= int(ans) <= maximum:
                return int(ans)
            self.error(f"Entrez un entier entre {minimum} et {maximum}.")

    def ask_float(self, question: str, default: float, minimum: float = 0.0,
                  maximum: float = 1e9) -> float:
        while True:
            ans = input(f"{question} [{default}] : ").strip()
            if not ans:
                return default
            try:
                v = float(ans)
                if minimum <= v <= maximum:
                    return v
            except ValueError:
                pass
            self.error(f"Entrez un nombre entre {minimum} et {maximum}.")

    # ------------------------------------------------------------------ #
    # Affichage d'une manche
    # ------------------------------------------------------------------ #
    def show_initial_deal(self, player: HumanPlayer, dealer: Dealer) -> None:
        self.write()
        self.write(_c("── Distribution initiale ──", _Color.CYAN))
        self.write(f"  Croupier : {_hand_str(dealer.hand, hide_first=True)}")
        for i, h in enumerate(player.hands, start=1):
            self.write(f"  {player.name} (main {i}) : {_hand_str(h)}  -  "
                       f"mise {h.bet:.2f}")

    def show_dealer_reveal(self, dealer: Dealer) -> None:
        self.write()
        self.write(f"  Croupier dévoile : {_hand_str(dealer.hand)}")

    def show_dealer_draw(self, dealer: Dealer) -> None:
        self.write(f"  Croupier tire   : {_hand_str(dealer.hand)}")

    def show_action(self, player: HumanPlayer, hand: Hand, action: Action) -> None:
        self.write(f"  → {player.name} : {_c(action.label, _Color.YELLOW)}  "
                   f"({_hand_str(hand)})")

    def show_shuffle(self) -> None:
        self.write()
        self.info("Carte de coupe atteinte — le sabot est remélangé.")

    def show_round_results(self, results: List[Tuple[Hand, Outcome, float]]) -> None:
        self.write()
        self.write(_c("── Résultat de la manche ──", _Color.CYAN))
        for hand, outcome, net in results:
            color = (
                _Color.GREEN if net > 0
                else _Color.YELLOW if net == 0
                else _Color.RED
            )
            sign = "+" if net >= 0 else ""
            self.write(f"  {_hand_str(hand)}  →  "
                       f"{_c(outcome.value, color)}  ({sign}{net:.2f})")

    def show_bankroll(self, player: HumanPlayer) -> None:
        self.write(f"  Solde actuel : {_c(f'{player.bankroll:.2f}', _Color.GREEN)}")

    def show_count_status(self, strategy: Strategy, decks_remaining: float) -> None:
        if not strategy.counts_cards:
            return
        rc = strategy.running_count
        tc = strategy.true_count(decks_remaining)
        self.write(_c(f"  [running count = {rc:+d}  |  true count = {tc:+.2f}]",
                       _Color.MAGENTA))

    def show_stats(self, stats) -> None:  # noqa: ANN001
        self.header("Statistiques de la session")
        self.write(f"  Manches jouées       : {stats.rounds_played}")
        self.write(f"  Mains jouées         : {stats.hands_played}")
        self.write(f"  Victoires            : {stats.wins} "
                   f"({stats.win_rate*100:.1f} %)")
        self.write(f"  Égalités             : {stats.pushes}")
        self.write(f"  Défaites             : {stats.losses}")
        self.write(f"  Blackjacks naturels  : {stats.blackjacks}")
        self.write(f"  Mains brûlées        : {stats.busts}")
        self.write(f"  Abandons             : {stats.surrenders}")
        self.write(f"  Total misé           : {stats.total_bet:.2f}")
        self.write(f"  Bilan net            : {stats.total_won:+.2f}")
        self.write(f"  Espérance par mise   : {stats.expected_value*100:+.2f} %")

    # ------------------------------------------------------------------ #
    # Prompt d'action — appelé par HumanPlayer
    # ------------------------------------------------------------------ #
    def prompt_action(self, player: HumanPlayer, hand: Hand, dealer_up: Card,
                      advice: Optional[Action] = None) -> Action:
        """Demande au joueur quelle action effectuer sur la main courante."""
        self.write()
        self.write(_c(f"  → Au tour de {player.name}", _Color.CYAN))
        self.write(f"    Croupier visible : {_card_str(dealer_up)}")
        self.write(f"    Main             : {_hand_str(hand)}  (mise {hand.bet:.2f})")

        # Construit la liste des actions autorisées.
        options: List[Tuple[str, Action]] = [
            ("h", Action.HIT),
            ("s", Action.STAND),
        ]
        if hand.can_double and player.bankroll >= hand.bet:
            options.append(("d", Action.DOUBLE))
        if hand.can_split and player.bankroll >= hand.bet:
            options.append(("p", Action.SPLIT))
        if hand.can_surrender:
            options.append(("r", Action.SURRENDER))

        legend = "  ".join(f"[{k}] {a.label}" for k, a in options)
        self.write(f"    Actions          : {legend}")

        if advice is not None:
            self.write(_c(f"    💡 Conseil       : {advice.label} "
                          f"({advice.short})",
                          _Color.MAGENTA))

        valid_keys = {k: a for k, a in options}
        while True:
            choice = input("    Votre action : ").strip().lower()
            if choice in valid_keys:
                return valid_keys[choice]
            self.error(f"Action invalide. Tapez {'/'.join(valid_keys)}.")
