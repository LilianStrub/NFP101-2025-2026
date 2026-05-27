"""
Module ``cli`` — interface en ligne de commande.

Hybride entre rendu *scroll* (menus, écran règles, statistiques) et rendu
*TUI à zone fixe* (pendant une manche, via ``rich.live.Live`` + ``Layout``).
L'API publique de :class:`UI` reste compatible avec ``__main__.py`` et les
UI factices des tests.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Deque, List, Optional, Tuple

import pyfiglet
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
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


def _hand_footer(hand: Hand, show_bet: bool = False,
                 hidden: bool = False) -> Text:
    """Pied de panneau : total coloré (+ mise optionnelle)."""
    foot = Text()
    if hidden:
        foot.append("Total : ", style="dim")
        foot.append("?", style="dim")
        return foot
    total = hand.total
    if hand.is_bust:
        style = "danger"
    elif total == 21:
        style = "gold"
    else:
        style = "good"
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
    body: Group = Group(
        cards,
        Text(""),
        _hand_footer(hand, show_bet=show_bet, hidden=hide_first),
    )
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
    """Interface utilisateur en ligne de commande.

    Rendu hybride : *scroll* hors manche et *TUI fixe* pendant une manche
    via ``rich.live.Live``.
    """

    def __init__(self, stream=sys.stdout) -> None:  # noqa: ANN001
        self.console = Console(theme=THEME, file=stream, highlight=False)
        self.round_number: int = 0
        self.tour_number: int = 0
        # Mode apprentissage : explique chaque action la 1re fois.
        self.learning_mode: bool = False
        self._explained_actions: set = set()
        self.draw_delay: float = 0.45

        # État pour le rendu Live (rempli à chaque manche).
        self.layout: Optional[Layout] = None
        self.live: Optional[Live] = None
        self.log_buffer: Deque[Text] = deque(maxlen=6)
        self._cur_player: Optional[HumanPlayer] = None
        self._cur_dealer: Optional[Dealer] = None
        self._cur_hand_index: int = 0
        self._cur_advice: Optional[Action] = None
        self._cur_options: List[Tuple[str, Action]] = []
        self._dealer_hide_hole: bool = True

    # ------------------------------------------------------------------ #
    # Sorties basiques (mode scroll, compatibles avec l'ancienne API)
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
    # Écrans de menus (rendu scroll)
    # ------------------------------------------------------------------ #
    def main_menu(self) -> str:
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
        self.console.print()
        self.console.print(_figlet("Regles", style="gold", font="small"))

        obj = Text("Battre le croupier en s'approchant de 21 sans le dépasser.\n"
                   "Au-delà de 21 : votre main est ", style="white")
        obj.append("brûlée", style="danger")
        obj.append(" et vous perdez immédiatement.", style="white")
        self.console.print(Panel(obj, title=Text(" 🎯 Objectif ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        cards_tbl = Table.grid(padding=(0, 2))
        cards_tbl.add_column(style="gold")
        cards_tbl.add_column(style="white")
        cards_tbl.add_row("2 à 10", "leur valeur affichée")
        cards_tbl.add_row("Valet, Dame, Roi", "10 points")
        cards_tbl.add_row("As", "1 ou 11 (la valeur la plus avantageuse)")
        self.console.print(Panel(cards_tbl, title=Text(" 🃏 Valeur des cartes ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        flow_steps = [
            "1. Vous misez puis recevez 2 cartes (visibles).",
            "2. Le croupier reçoit 2 cartes (l'une visible, l'autre cachée).",
            "3. Si le croupier montre un As, l'assurance vous est proposée.",
            "4. À votre tour : choisissez parmi les actions disponibles.",
            "5. Le croupier joue : il tire tant que son total est < 17,",
            "   puis s'arrête (S17 : il reste sur un 17 'soft' aussi).",
            "6. Comparaison des totaux : le plus proche de 21 gagne.",
        ]
        self.console.print(Panel(Text("\n".join(flow_steps)),
                                 title=Text(" 🎲 Déroulement d'une manche ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

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

        pay = Table.grid(padding=(0, 2))
        pay.add_column(style="gold", no_wrap=True)
        pay.add_column(style="white")
        pay.add_row("Gain normal",        "1:1 (vous gagnez le montant de votre mise)")
        pay.add_row("Blackjack naturel",  "3:2 (As + 10/figure sur les 2 premières cartes)")
        pay.add_row("Égalité (push)",     "votre mise vous est rendue")
        pay.add_row("Assurance",          "2:1 si le croupier a un Blackjack")
        self.console.print(Panel(pay, title=Text(" 💰 Paiements ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        fr_lines = [
            "• Le croupier reste sur 17 'soft' (S17).",
            "• Doubler est limité aux totaux durs de 9, 10 ou 11.",
            "• Pas d'abandon (surrender) autorisé.",
            "• 6 jeux de cartes mélangés (sabot).",
        ]
        self.console.print(Panel(Text("\n".join(fr_lines)),
                                 title=Text(" 🇫🇷 Règles françaises ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        self.console.print()
        self.info("Astuce débutant : activez le « Mode apprentissage » au lancement "
                  "d'une partie pour obtenir des conseils à chaque tour.")
        self.console.print()
        input("Appuyez sur Entrée pour revenir au menu...")

    def choose_strategy(self) -> Tuple[str, Strategy]:
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
    # Affichages hors manche
    # ------------------------------------------------------------------ #
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

    # ================================================================== #
    # Rendu TUI à zone fixe (pendant une manche)
    # ================================================================== #

    def _build_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="top",     size=3),
            Layout(name="dealer",  size=9),
            Layout(name="player",  size=11),
            Layout(name="actions", size=7),
            Layout(name="log",     size=8),
        )
        return layout

    def _start_live(self) -> None:
        """Initialise et démarre l'écran TUI fixe pour une manche."""
        self.layout = self._build_layout()
        self.live = Live(self.layout, console=self.console,
                         refresh_per_second=8, screen=False, transient=False)
        self.live.start(refresh=True)

    def _stop_live(self) -> None:
        """Arrête proprement l'écran TUI fixe (idempotent)."""
        if self.live is not None:
            try:
                self.live.stop()
            finally:
                self.live = None
                self.layout = None

    def _refresh(self) -> None:
        """Recalcule chaque zone et redessine le layout."""
        if self.live is None or self.layout is None:
            return
        self.layout["top"].update(self._render_top())
        self.layout["dealer"].update(self._render_dealer())
        self.layout["player"].update(self._render_player())
        self.layout["actions"].update(self._render_actions())
        self.layout["log"].update(self._render_log())
        self.live.refresh()

    def _add_log(self, message: str, style: str = "white",
                 prefix: str = "▸") -> None:
        line = Text()
        line.append(f"{prefix} ", style="gold")
        line.append(message, style=style)
        self.log_buffer.append(line)

    def _input_paused(self, prompt: str) -> str:
        """Suspend Live le temps de lire une entrée utilisateur."""
        was_live = self.live is not None
        if was_live:
            self.live.stop()
        try:
            return input(prompt)
        finally:
            if was_live and self.live is not None:
                self.live.start(refresh=True)
                self._refresh()

    # ---- Renderers des 5 zones ---------------------------------------- #

    def _render_top(self) -> Panel:
        player = self._cur_player
        text = Text()
        text.append("Manche ", style="dim")
        text.append(f"{self.round_number}", style="gold")
        if player is not None:
            text.append("    💰 Solde : ", style="dim")
            text.append(f"{player.bankroll:.2f}", style="gold")
            if player.strategy is not None:
                text.append("    Stratégie : ", style="dim")
                text.append(player.strategy.name, style="info")
        return Panel(text, border_style="felt", padding=(0, 2),
                     title=Text(" 🎰 BLACKJACK ", style="gold"))

    def _render_dealer(self) -> Panel:
        dealer = self._cur_dealer
        if dealer is None or not dealer.hand.cards:
            return Panel(Text("(en attente)", style="dim"),
                         title=Text(" Croupier ", style="gold"),
                         border_style="felt", padding=(0, 1))
        hide = self._dealer_hide_hole and len(dealer.hand.cards) >= 2
        return _hand_panel(dealer.hand, "Croupier", hide_first=hide,
                           border="felt")

    def _render_player(self) -> Panel:
        player = self._cur_player
        if player is None or not player.hands:
            return Panel(Text("(en attente)", style="dim"),
                         title=Text(" Votre main ", style="gold"),
                         border_style="gold", padding=(0, 1))

        hands = player.hands
        idx = min(self._cur_hand_index, len(hands) - 1)
        current = hands[idx]

        # Cartes + total + mise de la main courante.
        cards = _hand_renderable(current)
        footer = _hand_footer(current, show_bet=True)

        # Si splits : petite ligne récapitulative des autres mains.
        parts: List = [cards, Text(""), footer]
        if len(hands) > 1:
            recap = Text()
            for i, h in enumerate(hands):
                if i > 0:
                    recap.append("  |  ", style="dim")
                style = "gold" if i == idx else "dim"
                marker = "▶ " if i == idx else "  "
                cards_short = " ".join(
                    f"{c.rank.label}{c.suit.symbol}" for c in h.cards
                ) or "—"
                recap.append(f"{marker}Main {i + 1}: {cards_short} ({h.total})",
                             style=style)
            parts.append(Text(""))
            parts.append(recap)

        title = f"Votre main"
        if len(hands) > 1:
            title += f" — {idx + 1}/{len(hands)}"
        return Panel(Group(*parts), title=Text(f" {title} ", style="gold"),
                     border_style="gold", padding=(0, 1))

    def _render_actions(self) -> Panel:
        # En-tête : numéro de tour.
        header = Text()
        if self.tour_number == 0:
            header.append("(en attente d'action)", style="dim")
        else:
            header.append(f"Tour {self.tour_number}", style="gold")

        # Table des actions disponibles.
        body_parts: List = [header]
        if self._cur_options:
            act_tbl = Table.grid(padding=(0, 2))
            act_tbl.add_column(style="gold", no_wrap=True)
            act_tbl.add_column(style="warn", no_wrap=True)
            if self.learning_mode:
                act_tbl.add_column(style="dim")
            for key, action in self._cur_options:
                row = [f"[{key}]", action.label]
                if self.learning_mode:
                    row.append(_ACTION_HELP[action])
                act_tbl.add_row(*row)
            body_parts.append(act_tbl)

        # Conseil de la stratégie.
        if self._cur_advice is not None:
            advice = Text()
            advice.append("💡 Conseil : ", style="dim")
            advice.append(self._cur_advice.label, style="advice")
            advice.append(f"  ({self._cur_advice.short})", style="dim")
            body_parts.append(advice)

        return Panel(Group(*body_parts), title=Text(" Actions ", style="gold"),
                     border_style="felt", padding=(0, 1))

    def _render_log(self) -> Panel:
        if not self.log_buffer:
            body = Text("(début de manche)", style="dim")
        else:
            body = Group(*list(self.log_buffer))
        return Panel(body, title=Text(" Journal ", style="gold"),
                     border_style="felt", padding=(0, 1))

    # ---- Callbacks pendant la manche ---------------------------------- #

    def show_initial_deal(self, player: HumanPlayer, dealer: Dealer) -> None:
        self.round_number += 1
        self.tour_number = 0
        self._cur_player = player
        self._cur_dealer = dealer
        self._cur_hand_index = 0
        self._cur_advice = None
        self._cur_options = []
        self._dealer_hide_hole = True
        self.log_buffer.clear()
        self._add_log("Cartes distribuées", style="info")
        self._start_live()
        self._refresh()

    def show_dealer_reveal(self, dealer: Dealer,
                           revealed: Optional[Card] = None) -> None:
        if self.draw_delay:
            time.sleep(self.draw_delay)
        self._dealer_hide_hole = False
        if revealed is not None:
            msg = f"Croupier révèle sa carte cachée : {revealed.rank.label}{revealed.suit.symbol}"
        else:
            n = len(dealer.hand.cards)
            msg = (f"Croupier tire sa {n}e carte : "
                   f"{dealer.hand.cards[-1].rank.label}{dealer.hand.cards[-1].suit.symbol}")
        self._add_log(msg, style="info")
        self._refresh()

    def show_dealer_draw(self, dealer: Dealer) -> None:
        if self.draw_delay:
            time.sleep(self.draw_delay)
        n = len(dealer.hand.cards)
        card = dealer.hand.cards[-1]
        self._add_log(f"Croupier tire sa {n}e carte : "
                      f"{card.rank.label}{card.suit.symbol} → total {dealer.hand.total}",
                      style="info")
        self._refresh()

    def show_dealer_bust(self, dealer: Dealer) -> None:
        self._add_log("💥 BUST du croupier !", style="danger")
        self._refresh()

    def show_insurance_result(self, dealer_blackjack: bool,
                              insurance_bet: float) -> None:
        if dealer_blackjack:
            self._add_log(f"Assurance GAGNÉE (+{insurance_bet * 2:.2f})",
                          style="good")
        else:
            self._add_log(f"Assurance perdue (-{insurance_bet:.2f})",
                          style="danger")
        self._refresh()

    def show_action(self, player: HumanPlayer, hand: Hand, action: Action) -> None:
        # Décrire ce qui s'est passé.
        if action is Action.HIT and hand.cards:
            card = hand.cards[-1]
            msg = (f"{player.name} : Tirer → {card.rank.label}{card.suit.symbol} "
                   f"(total {hand.total})")
        else:
            msg = f"{player.name} : {action.label}"
        style = "danger" if hand.is_bust else "warn"
        self._add_log(msg, style=style)
        self._refresh()

    def show_shuffle(self) -> None:
        if self.live is not None:
            self._add_log("🔀 Sabot remélangé", style="advice")
            self._refresh()
        else:
            self.console.print()
            self.info("Carte de coupe atteinte — le sabot est remélangé.")

    def show_round_results(self, results: List[Tuple[Hand, Outcome, float]]) -> None:
        # Résume dans le journal.
        for hand, outcome, net in results:
            sign = "+" if net >= 0 else ""
            if net > 0:
                style = "good"
            elif net == 0:
                style = "warn"
            else:
                style = "danger"
            self._add_log(f"Résultat : {outcome.value}  ({sign}{net:.2f})",
                          style=style)
        self._refresh()
        # Ferme l'écran TUI avant de rendre en mode scroll.
        self._stop_live()

        # Évènements spectaculaires (pyfiglet).
        for hand, outcome, _ in results:
            if outcome is Outcome.BLACKJACK:
                self.console.print(_figlet("BLACKJACK !", style="gold", font="small"))
                break
            if outcome is Outcome.BUST:
                self.console.print(_figlet("BUST !", style="danger", font="small"))
                break

        # Table récapitulative de la manche.
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
            hand_text.append(cards_str, style="white")
            hand_text.append(f"  ({hand.total})", style="dim")
            sign = "+" if net >= 0 else ""
            tbl.add_row(
                hand_text,
                Text(outcome.value, style=color),
                Text(f"{sign}{net:.2f}", style=color),
            )
        self.console.print(tbl)

    # ---- Prompts pendant la manche ------------------------------------ #

    def prompt_insurance(self, player: HumanPlayer, max_insurance: float) -> float:
        """Propose l'assurance ; renvoie la mise prise (0.0 si refus)."""
        self._add_log(f"⚠ Le croupier montre un As — assurance ? (max {max_insurance:.2f})",
                      style="warn")
        self._refresh()
        ans = self._input_paused(
            f"Prendre l'assurance pour {max_insurance:.2f} ? [o/N] : "
        ).strip().lower()
        took = ans in ("o", "oui", "y", "yes")
        if took:
            self._add_log(f"Assurance prise : {max_insurance:.2f}", style="advice")
        else:
            self._add_log("Assurance refusée", style="dim")
        self._refresh()
        return max_insurance if took else 0.0

    def prompt_action(self, player: HumanPlayer, hand: Hand, dealer_up: Card,
                      advice: Optional[Action] = None,
                      rules: Optional[object] = None,
                      hand_index: int = 0) -> Action:
        """Demande au joueur quelle action effectuer sur la main courante."""
        self.tour_number += 1
        self._cur_hand_index = hand_index
        self._cur_advice = advice

        # Calcule les actions autorisées.
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
        self._cur_options = options

        if self.learning_mode:
            for _, a in options:
                self._explained_actions.add(a)

        self._refresh()

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
            choice = self._input_paused("Votre action : ").strip().lower()
            if choice in valid_keys:
                return valid_keys[choice]
            if choice in word_aliases and word_aliases[choice] in allowed:
                return word_aliases[choice]
            self._add_log(
                f"Action invalide « {choice} » — tapez {'/'.join(valid_keys)}",
                style="danger",
            )
            self._refresh()
