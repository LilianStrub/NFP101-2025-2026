"""
Module ``cli`` — interface en ligne de commande.

Rendu basé sur ``rich`` (panneaux, tables, couleurs RGB) et ``pyfiglet``
pour les grands titres ASCII. L'API publique de la classe :class:`UI` est
conservée pour rester compatible avec ``__main__.py`` et les UI factices
utilisées par les tests.
"""

from __future__ import annotations

import sys
import time
from typing import List, Optional, Tuple

import pyfiglet
from rich.columns import Columns
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from ..core import Action, Card, Hand, Outcome
from ..players import Dealer, HumanPlayer
from ..strategies import STRATEGIES, Strategy


# --------------------------------------------------------------------------- #
# Thème casino (couleurs RGB)
# --------------------------------------------------------------------------- #
THEME = Theme({
    "felt":   "rgb(0,130,80)",        # vert tapis casino
    "gold":   "rgb(212,175,55) bold", # doré (gains / blackjack)
    "heart":  "rgb(220,50,50) bold",  # cœurs et carreaux
    "spade":  "white bold",           # piques et trèfles
    "back":   "grey39",               # dos de carte
    "info":   "cyan",
    "warn":   "yellow",
    "danger": "red bold",
    "good":   "green bold",
    "dim":    "grey50",
    "advice": "magenta bold",
})


# --------------------------------------------------------------------------- #
# Aide contextuelle sur les actions (mode apprentissage)
# --------------------------------------------------------------------------- #
_ACTION_HELP = {
    Action.HIT: "prendre une carte de plus (risque de dépasser 21).",
    Action.STAND: "garder votre main et laisser jouer le croupier.",
    Action.DOUBLE: "doubler votre mise, tirer UNE seule carte, puis rester.",
    Action.SPLIT: "séparer votre paire en deux mains (mise doublée).",
    Action.SURRENDER: "abandonner la main et récupérer la moitié de la mise.",
}


# --------------------------------------------------------------------------- #
# Rendu des cartes : mini-boîtes Unicode 5 × 7
# --------------------------------------------------------------------------- #
def _card_text(card: Card) -> Text:
    """Rend une carte sous forme d'une petite boîte Unicode colorée."""
    rank = card.rank.label
    suit = card.suit.symbol
    style = "heart" if card.suit.is_red else "spade"
    body = (
        "┌─────┐\n"
        f"│{rank.ljust(5)}│\n"
        f"│  {suit}  │\n"
        f"│{rank.rjust(5)}│\n"
        "└─────┘"
    )
    return Text(body, style=style)


def _hidden_card_text() -> Text:
    """Carte face cachée."""
    body = (
        "┌─────┐\n"
        "│▒▒▒▒▒│\n"
        "│▒▒▒▒▒│\n"
        "│▒▒▒▒▒│\n"
        "└─────┘"
    )
    return Text(body, style="back")


def _hand_renderable(hand: Hand, hide_first: bool = False) -> Text:
    """Combine plusieurs cartes côte à côte dans un seul ``Text`` multi-ligne."""
    cards = hand.cards
    if not cards:
        return Text("(vide)", style="dim")

    card_blocks: List[Tuple[List[str], str]] = []
    for i, card in enumerate(cards):
        if hide_first and i == 0:
            lines = ["┌─────┐", "│▒▒▒▒▒│", "│▒▒▒▒▒│", "│▒▒▒▒▒│", "└─────┘"]
            card_blocks.append((lines, "back"))
        else:
            rank = card.rank.label
            suit = card.suit.symbol
            lines = [
                "┌─────┐",
                f"│{rank.ljust(5)}│",
                f"│  {suit}  │",
                f"│{rank.rjust(5)}│",
                "└─────┘",
            ]
            style = "heart" if card.suit.is_red else "spade"
            card_blocks.append((lines, style))

    out = Text()
    for row in range(5):
        if row > 0:
            out.append("\n")
        for i, (lines, style) in enumerate(card_blocks):
            if i > 0:
                out.append(" ")
            out.append(lines[row], style=style)
    return out


def _hand_footer(hand: Hand, show_bet: bool = False) -> Text:
    """Pied de panneau : total coloré (+ mise optionnelle)."""
    total = hand.total
    if hand.is_bust:
        style = "danger"
    elif total == 21:
        style = "gold"
    else:
        style = "good"
    foot = Text()
    foot.append("Total : ", style="dim")
    foot.append(f"{total}", style=style)
    if show_bet:
        foot.append("   Mise : ", style="dim")
        foot.append(f"{hand.bet:.2f}", style="gold")
    return foot


def _hand_panel(hand: Hand, title: str, hide_first: bool = False,
                show_bet: bool = False, border: str = "felt") -> Panel:
    """Encapsule une main dans un ``Panel`` Rich (cartes + total)."""
    cards = _hand_renderable(hand, hide_first=hide_first)
    if hide_first:
        # Masquer le total quand on cache la 1re carte du croupier.
        body: Group = Group(cards)
    else:
        body = Group(cards, Text(""), _hand_footer(hand, show_bet=show_bet))
    title_text = Text(f" {title} ", style="gold")
    return Panel(body, title=title_text, border_style=border, padding=(0, 1))


def _figlet(text: str, style: str = "gold", font: str = "slant") -> Text:
    """Rend un titre en grosses lettres ASCII via pyfiglet."""
    art = pyfiglet.figlet_format(text, font=font)
    return Text(art.rstrip("\n"), style=style)


# --------------------------------------------------------------------------- #
# Classe UI
# --------------------------------------------------------------------------- #
class UI:
    """Interface utilisateur en ligne de commande, rendu Rich."""

    def __init__(self, stream=sys.stdout) -> None:  # noqa: ANN001
        self.console = Console(theme=THEME, file=stream, highlight=False)
        self.round_number: int = 0
        self.tour_number: int = 0
        # Mode apprentissage : explique chaque action la 1re fois.
        self.learning_mode: bool = False
        self._explained_actions: set = set()
        # Petite pause pour le suspense entre 2 cartes du croupier.
        self.draw_delay: float = 0.35

    # ------------------------------------------------------------------ #
    # Sorties basiques (compatibles avec l'ancienne API)
    # ------------------------------------------------------------------ #
    def write(self, text: str = "") -> None:
        self.console.print(text)

    def header(self, text: str) -> None:
        self.console.print()
        self.console.print(
            Panel(Text(text, style="bold cyan", justify="center"),
                  border_style="cyan", padding=(0, 2))
        )

    def info(self, text: str) -> None:
        self.console.print(Text(f"ℹ  {text}", style="info"))

    def warn(self, text: str) -> None:
        self.console.print(Text(f"⚠  {text}", style="warn"))

    def error(self, text: str) -> None:
        self.console.print(Text(f"✗  {text}", style="danger"))

    def success(self, text: str) -> None:
        self.console.print(Text(f"✓  {text}", style="good"))

    # ------------------------------------------------------------------ #
    # Écrans de menus
    # ------------------------------------------------------------------ #
    def main_menu(self) -> str:
        """Affiche le menu principal et renvoie le choix saisi."""
        self.console.print()
        self.console.print(_figlet("BLACKJACK", style="gold", font="slant"))
        subtitle = Text("Casino  —  règles françaises", style="felt", justify="center")
        self.console.print(subtitle)

        options = Text()
        options.append("  1", style="gold"); options.append("   Démarrer une nouvelle partie\n")
        options.append("  2", style="gold"); options.append("   Règles du jeu\n")
        options.append("  3", style="gold"); options.append("   Comparer les stratégies (simulation)\n")
        options.append("  4", style="gold"); options.append("   À propos / aide\n")
        options.append("  0", style="gold"); options.append("   Quitter")

        self.console.print(Panel(options, title=Text(" Menu principal ", style="gold"),
                                 border_style="felt", padding=(1, 2)))
        return input("Votre choix : ").strip()

    def show_rules(self) -> None:
        """Affiche les règles du Blackjack pour les débutants."""
        self.console.print()
        self.console.print(_figlet("Regles", style="gold", font="small"))

        # Objectif
        obj = Text("Battre le croupier en s'approchant de 21 sans le dépasser.\n"
                   "Au-delà de 21 : votre main est ", style="white")
        obj.append("brûlée", style="danger")
        obj.append(" et vous perdez immédiatement.", style="white")
        self.console.print(Panel(obj, title=Text(" 🎯 Objectif ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        # Valeur des cartes
        cards_tbl = Table.grid(padding=(0, 2))
        cards_tbl.add_column(style="gold")
        cards_tbl.add_column(style="white")
        cards_tbl.add_row("2 à 10", "leur valeur affichée")
        cards_tbl.add_row("Valet, Dame, Roi", "10 points")
        cards_tbl.add_row("As", "1 ou 11 (la valeur la plus avantageuse)")
        self.console.print(Panel(cards_tbl, title=Text(" 🃏 Valeur des cartes ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        # Déroulement
        flow_steps = [
            "1. Vous misez puis recevez 2 cartes (visibles).",
            "2. Le croupier reçoit 2 cartes (l'une visible, l'autre cachée).",
            "3. Si le croupier montre un As, l'assurance vous est proposée.",
            "4. À votre tour : choisissez parmi les actions disponibles.",
            "5. Le croupier joue : il tire tant que son total est < 17,",
            "   puis s'arrête (S17 : il reste sur un 17 'soft' aussi).",
            "6. Comparaison des totaux : le plus proche de 21 gagne.",
        ]
        flow = Text("\n".join(flow_steps))
        self.console.print(Panel(flow,
                                 title=Text(" 🎲 Déroulement d'une manche ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        # Actions
        act = Table.grid(padding=(0, 2))
        act.add_column(style="warn", no_wrap=True)
        act.add_column(style="dim", no_wrap=True)
        act.add_column(style="white")
        act.add_row("Tirer",      "(h, tirer)",      "Prendre une carte supplémentaire.")
        act.add_row("Rester",     "(s, rester)",     "Garder votre main et passer au croupier.")
        act.add_row("Doubler",    "(d, doubler)",    "Doubler votre mise, tirer UNE seule carte, puis rester.")
        act.add_row("Séparer",    "(p, separer)",    "Séparer une paire en deux mains (mise doublée).")
        self.console.print(Panel(act, title=Text(" ⚡ Actions possibles ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        # Paiements
        pay = Table.grid(padding=(0, 2))
        pay.add_column(style="gold", no_wrap=True)
        pay.add_column(style="white")
        pay.add_row("Gain normal",        "1:1 (vous gagnez le montant de votre mise)")
        pay.add_row("Blackjack naturel",  "3:2 (As + 10/figure sur les 2 premières cartes)")
        pay.add_row("Égalité (push)",     "votre mise vous est rendue")
        pay.add_row("Assurance",          "2:1 si le croupier a un Blackjack")
        self.console.print(Panel(pay, title=Text(" 💰 Paiements ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        # Règles françaises spécifiques
        fr_lines = [
            "• Le croupier reste sur 17 'soft' (S17).",
            "• Doubler est limité aux totaux durs de 9, 10 ou 11.",
            "• Pas d'abandon (surrender) autorisé.",
            "• 6 jeux de cartes mélangés (sabot).",
        ]
        fr = Text("\n".join(fr_lines))
        self.console.print(Panel(fr,
                                 title=Text(" 🇫🇷 Règles françaises ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        self.console.print()
        self.info("Astuce débutant : activez le « Mode apprentissage » au lancement "
                  "d'une partie pour obtenir des conseils à chaque tour.")
        self.console.print()
        input("Appuyez sur Entrée pour revenir au menu...")

    def choose_strategy(self) -> Tuple[str, Strategy]:
        """Affiche la liste des stratégies et fait choisir le joueur."""
        self.header("Choix de la stratégie d'aide à la décision")
        keys = list(STRATEGIES.keys())

        tbl = Table(show_header=True, header_style="gold", border_style="felt",
                    show_lines=False, padding=(0, 1))
        tbl.add_column("#", style="gold", justify="right", no_wrap=True)
        tbl.add_column("Stratégie", style="info", no_wrap=True)
        tbl.add_column("Type", justify="center", no_wrap=True)
        tbl.add_column("Description", style="white")

        for i, key in enumerate(keys, start=1):
            cls = STRATEGIES[key]
            tag = Text("comptage", style="advice") if cls.counts_cards else Text("—", style="dim")
            tbl.add_row(str(i), cls.name, tag, cls.description.replace("\n", " "))
        self.console.print(tbl)

        while True:
            choice = input("\nVotre choix (numéro) : ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(keys):
                key = keys[int(choice) - 1]
                cls = STRATEGIES[key]
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
        self.round_number += 1
        self.tour_number = 0

    def show_dealer_reveal(self, dealer: Dealer,
                           revealed: Optional[Card] = None) -> None:
        if self.draw_delay:
            time.sleep(self.draw_delay)
        self.console.print()
        label = "révèle sa carte cachée" if revealed is not None else "tire sa 2e carte"
        self.console.print(Text(f"Croupier {label} :", style="info"))
        self.console.print(Padding(_hand_panel(dealer.hand, "Croupier"), (0, 0, 0, 2)))

    def show_insurance_result(self, dealer_blackjack: bool,
                              insurance_bet: float) -> None:
        self.console.print()
        if dealer_blackjack:
            self.success(f"Assurance gagnée ! (+{insurance_bet * 2:.2f})")
        else:
            self.warn(f"Assurance perdue (-{insurance_bet:.2f})")

    def show_dealer_draw(self, dealer: Dealer) -> None:
        if self.draw_delay:
            time.sleep(self.draw_delay)
        n = len(dealer.hand.cards)
        self.console.print()
        self.console.print(Text(f"Croupier tire sa {n}e carte :", style="info"))
        self.console.print(Padding(_hand_panel(dealer.hand, "Croupier"), (0, 0, 0, 2)))

    def show_dealer_bust(self, dealer: Dealer) -> None:
        self.console.print()
        self.console.print(_figlet("BUST !", style="danger", font="small"))

    def show_action(self, player: HumanPlayer, hand: Hand, action: Action) -> None:
        line = Text()
        line.append("▸ ", style="gold")
        line.append(f"{player.name} : ", style="white")
        line.append(action.label, style="warn")
        self.console.print(line)

    def show_shuffle(self) -> None:
        self.console.print()
        self.info("Carte de coupe atteinte — le sabot est remélangé.")

    def show_round_results(self, results: List[Tuple[Hand, Outcome, float]]) -> None:
        self.console.print()

        # Évènements spectaculaires : BLACKJACK ou BUST sur une main joueur.
        for hand, outcome, _ in results:
            if outcome is Outcome.BLACKJACK:
                self.console.print(_figlet("BLACKJACK !", style="gold", font="small"))
                break
            if outcome is Outcome.BUST:
                self.console.print(_figlet("BUST !", style="danger", font="small"))
                break

        tbl = Table(title=Text("Résultat de la manche", style="gold"),
                    border_style="felt", show_header=True, header_style="gold",
                    padding=(0, 1))
        tbl.add_column("Main", style="white")
        tbl.add_column("Résultat", justify="center")
        tbl.add_column("Gain", justify="right")

        for hand, outcome, net in results:
            if net > 0:
                color = "good"
            elif net == 0:
                color = "warn"
            else:
                color = "danger"
            cards_str = " ".join(
                f"{c.rank.label}{c.suit.symbol}" for c in hand.cards
            )
            hand_text = Text()
            hand_text.append(cards_str, style="heart" if any(c.suit.is_red for c in hand.cards) else "spade")
            hand_text.append(f"  ({hand.total})", style="dim")
            sign = "+" if net >= 0 else ""
            tbl.add_row(
                hand_text,
                Text(outcome.value, style=color),
                Text(f"{sign}{net:.2f}", style=color),
            )
        self.console.print(tbl)

    def show_bankroll(self, player: HumanPlayer) -> None:
        line = Text()
        line.append("💰 Solde : ", style="white")
        line.append(f"{player.bankroll:.2f}", style="gold")
        self.console.print(line)

    def show_count_status(self, strategy: Strategy, decks_remaining: float) -> None:
        if not strategy.counts_cards:
            return
        rc = strategy.running_count
        tc = strategy.true_count(decks_remaining)
        text = Text()
        text.append("running count = ", style="dim")
        text.append(f"{rc:+d}", style="advice")
        text.append("    true count = ", style="dim")
        text.append(f"{tc:+.2f}", style="advice")
        self.console.print(text)

    def show_stats(self, stats) -> None:  # noqa: ANN001
        self.header("Statistiques de la session")
        tbl = Table.grid(padding=(0, 2))
        tbl.add_column(style="info", no_wrap=True)
        tbl.add_column(style="white", justify="right")
        tbl.add_row("Manches jouées",      f"{stats.rounds_played}")
        tbl.add_row("Mains jouées",        f"{stats.hands_played}")
        tbl.add_row("Victoires",           f"{stats.wins} ({stats.win_rate*100:.1f} %)")
        tbl.add_row("Égalités",            f"{stats.pushes}")
        tbl.add_row("Défaites",            f"{stats.losses}")
        tbl.add_row("Blackjacks naturels", f"{stats.blackjacks}")
        tbl.add_row("Mains brûlées",       f"{stats.busts}")
        tbl.add_row("Abandons",            f"{stats.surrenders}")
        tbl.add_row("Total misé",          f"{stats.total_bet:.2f}")
        net_color = "good" if stats.total_won >= 0 else "danger"
        tbl.add_row("Bilan net",
                    Text(f"{stats.total_won:+.2f}", style=net_color))
        tbl.add_row("Espérance par mise",
                    Text(f"{stats.expected_value*100:+.2f} %", style=net_color))
        self.console.print(Panel(tbl, border_style="felt", padding=(1, 2)))

    # ------------------------------------------------------------------ #
    # Prompt d'assurance — appelé par Round
    # ------------------------------------------------------------------ #
    def prompt_insurance(self, player: HumanPlayer, max_insurance: float) -> float:
        """Propose l'assurance ; renvoie la mise prise (0.0 si refus)."""
        self.console.print()
        self.console.print(Panel(
            Text(f"Le croupier montre un As — Prendre l'assurance ({max_insurance:.2f}) ?",
                 style="warn"),
            border_style="warn", padding=(0, 2),
        ))
        if self.ask_yes_no("Assurance", default=False):
            return max_insurance
        return 0.0

    # ------------------------------------------------------------------ #
    # Prompt d'action — appelé par HumanPlayer
    # ------------------------------------------------------------------ #
    def prompt_action(self, player: HumanPlayer, hand: Hand, dealer_up: Card,
                      advice: Optional[Action] = None,
                      rules: Optional[object] = None,
                      hand_index: int = 0) -> Action:
        """Demande au joueur quelle action effectuer sur la main courante."""
        self.tour_number += 1

        if len(player.hands) > 1:
            label = f"Tour {self.tour_number} — Main {hand_index + 1}/{len(player.hands)}"
        else:
            label = f"Tour {self.tour_number}"

        self.console.print()
        self.console.rule(Text(label, style="gold"), style="felt")

        # Construit une "main du croupier" virtuelle avec uniquement la carte visible.
        dealer_hand_shown = Hand()
        dealer_hand_shown.add_card(dealer_up)

        # Panneaux côte à côte : croupier + joueur.
        cols = Columns(
            [
                _hand_panel(dealer_hand_shown, "Croupier", border="felt"),
                _hand_panel(hand, f"Votre main", show_bet=True, border="gold"),
            ],
            padding=(0, 2),
            expand=False,
        )
        self.console.print(cols)

        # Actions autorisées selon les règles.
        can_double = hand.can_double and (
            rules is None
            or not getattr(rules, "double_hard_9_to_11_only", False)
            or (not hand.is_soft and hand.total in (9, 10, 11))
        )
        can_surrender = hand.can_surrender and (
            rules is None or getattr(rules, "surrender_allowed", True)
        )

        options: List[Tuple[str, Action]] = [
            ("h", Action.HIT),
            ("s", Action.STAND),
        ]
        if can_double and player.bankroll >= hand.bet:
            options.append(("d", Action.DOUBLE))
        if hand.can_split and player.bankroll >= hand.bet:
            options.append(("p", Action.SPLIT))
        if can_surrender:
            options.append(("r", Action.SURRENDER))

        # Table d'actions.
        act_tbl = Table(show_header=True, header_style="gold", border_style="felt",
                        padding=(0, 1))
        act_tbl.add_column("Touche", style="gold", justify="center", no_wrap=True)
        act_tbl.add_column("Action", style="warn", no_wrap=True)
        if self.learning_mode:
            act_tbl.add_column("Description", style="dim")
        for key, action in options:
            row = [key, action.label]
            if self.learning_mode:
                row.append(_ACTION_HELP[action])
                self._explained_actions.add(action)
            act_tbl.add_row(*row)
        self.console.print(act_tbl)

        if advice is not None:
            advice_panel = Panel(
                Text(f"💡 Conseil : {advice.label}  ({advice.short})",
                     style="advice"),
                border_style="advice", padding=(0, 2),
            )
            self.console.print(advice_panel)

        valid_keys = {k: a for k, a in options}
        word_aliases = {
            "tirer": Action.HIT, "hit": Action.HIT,
            "rester": Action.STAND, "stand": Action.STAND,
            "doubler": Action.DOUBLE, "double": Action.DOUBLE,
            "separer": Action.SPLIT, "séparer": Action.SPLIT, "split": Action.SPLIT,
            "abandonner": Action.SURRENDER, "surrender": Action.SURRENDER,
        }
        allowed = {a for _, a in options}
        while True:
            choice = input("Votre action : ").strip().lower()
            if choice in valid_keys:
                return valid_keys[choice]
            if choice in word_aliases and word_aliases[choice] in allowed:
                return word_aliases[choice]
            self.error(f"Action invalide. Tapez {'/'.join(valid_keys)} "
                       f"ou le nom complet ({', '.join(a.label.lower() for _, a in options)}).")
