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
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from ..core import Action, Card, Hand, Outcome
from ..players import Dealer, HumanPlayer
from ..strategies import STRATEGIES, Strategy
from ..strategies.counting import BET_RAMP_GUIDE


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
# Aide contextuelle sur les actions (affichée en mode didacticiel)
# --------------------------------------------------------------------------- #
_ACTION_HELP = {
    Action.HIT: "prendre une carte de plus (risque de dépasser 21).",
    Action.STAND: "garder votre main et laisser jouer le croupier.",
    Action.DOUBLE: "doubler votre mise, tirer UNE seule carte, puis rester.",
    Action.SPLIT: "séparer votre paire en deux mains (mise doublée).",
    Action.SURRENDER: "abandonner la main et récupérer la moitié de la mise.",
}


# Valeurs des jetons de casino (en €), du plus petit au plus grand.
CHIP_VALUES = (1, 5, 25, 100, 500)


# --------------------------------------------------------------------------- #
# Guide « grand public » des stratégies (menu de choix de l'aide)
# Pour chaque clé du registre STRATEGIES : (niveau, explication en clair).
# --------------------------------------------------------------------------- #
_STRATEGY_GUIDE = {
    "manuelle":  ("—",            "Aucun conseil : vous décidez tout seul."),
    "basique":   ("Débutant ⭐",  "Indique toujours le meilleur coup, calculé "
                                   "mathématiquement. Rien à mémoriser : idéale "
                                   "pour apprendre."),
    "hi-lo":     ("Intermédiaire", "Comptage de cartes le plus connu : suit les "
                                    "cartes hautes/basses déjà sorties pour repérer "
                                    "les moments favorables."),
    "ko":        ("Intermédiaire", "Comptage simplifié : pas de calcul de "
                                    "conversion à faire dans sa tête."),
    "red-7":     ("Intermédiaire", "Comptage simplifié où même la couleur du 7 "
                                    "entre en compte."),
    "hi-opt-i":  ("Avancé",       "Comptage plus fin que le Hi-Lo (les As se "
                                   "suivent à part)."),
    "hi-opt-ii": ("Expert",       "Comptage très précis mais exigeant (plusieurs "
                                   "valeurs à retenir)."),
    "omega-ii":  ("Expert",       "Parmi les comptages les plus puissants ; "
                                   "demande beaucoup de concentration."),
    "zen":       ("Expert",       "Comptage avancé, bon compromis entre puissance "
                                   "et difficulté."),
}


# --------------------------------------------------------------------------- #
# Rendu des cartes : mini-boîtes Unicode 5 × 7
# --------------------------------------------------------------------------- #
def _card_lines(card: Card) -> Tuple[List[str], str]:
    """Renvoie les 5 lignes de la boîte Unicode d'une carte et son style."""
    rank = card.rank.label
    suit = card.suit.symbol
    lines = [
        "┌─────┐",
        f"│{rank.ljust(5)}│",
        f"│  {suit}  │",
        f"│{rank.rjust(5)}│",
        "└─────┘",
    ]
    return lines, ("heart" if card.suit.is_red else "spade")


def _hand_renderable(hand: Hand, hide_first: bool = False,
                     add_hidden: bool = False, pad_to: int = 0,
                     up_card_first: bool = False) -> Text:
    """Combine plusieurs cartes côte à côte dans un seul ``Text`` multi-ligne.

    ``pad_to`` garantit un minimum de blocs pour que les panneaux gardent une
    largeur fixe pendant l'animation. Les emplacements non encore distribués
    sont laissés *vides* (et non en cartes face cachée, pour ne pas laisser
    croire qu'une carte a déjà été donnée).
    ``up_card_first`` place l'up card (cards[1]) à gauche de la hole card
    (cards[0]) après révélation, pour conserver un ordre visuel cohérent.
    """
    raw = hand.cards
    if up_card_first and len(raw) >= 2:
        cards = [raw[1], raw[0]] + list(raw[2:])
    else:
        cards = raw
    _hidden = (["┌─────┐", "│▒▒▒▒▒│", "│▒▒▒▒▒│", "│▒▒▒▒▒│", "└─────┘"], "back")
    _blank = (["       ", "       ", "       ", "       ", "       "], "back")
    card_blocks: List[Tuple[List[str], str]] = []

    if hide_first:
        # Cartes visibles (up card et suivantes) à gauche, hole card cachée à droite.
        for card in cards[1:]:
            card_blocks.append(_card_lines(card))
        # La hole card n'est représentée que si elle a réellement été distribuée.
        if cards:
            card_blocks.append(_hidden)
    else:
        for card in cards:
            card_blocks.append(_card_lines(card))

    if add_hidden:
        card_blocks.append(_hidden)

    # Remplissage : emplacements vides (espaces) pour garder une largeur fixe.
    while len(card_blocks) < pad_to:
        card_blocks.append(_blank)

    if not card_blocks:
        return Text("(vide)", style="dim")

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
                add_hidden: bool = False, pad_to: int = 0,
                up_card_first: bool = False,
                show_bet: bool = False, border: str = "felt") -> Panel:
    """Encapsule une main dans un ``Panel`` Rich (cartes + total)."""
    cards = _hand_renderable(hand, hide_first=hide_first,
                             add_hidden=add_hidden, pad_to=pad_to,
                             up_card_first=up_card_first)
    if hide_first:
        visible = hand.cards[1:]
        if visible:
            visible_hand = Hand()
            for c in visible:
                visible_hand.add_card(c)
            body: Group = Group(cards, Text(""), _hand_footer(visible_hand))
        else:
            body = Group(cards)
    elif hand.cards:
        body = Group(cards, Text(""), _hand_footer(hand, show_bet=show_bet))
    elif show_bet and hand.bet > 0:
        # Main vide mais mise connue : affiche seulement la mise.
        bet_line = Text()
        bet_line.append("Mise : ", style="dim")
        bet_line.append(f"{hand.bet:.2f}", style="gold")
        body = Group(cards, Text(""), bet_line)
    else:
        body = Group(cards)
    title_text = Text(f" {title} ", style="gold")
    return Panel(body, title=title_text, border_style=border, padding=(0, 1),
                 expand=False)


def _figlet(text: str, style: str = "gold", font: str = "slant") -> Text:
    """Rend un titre en grosses lettres ASCII via pyfiglet."""
    art = pyfiglet.figlet_format(text, font=font)
    return Text(art.rstrip("\n"), style=style)


# --------------------------------------------------------------------------- #
# Classe UI
# --------------------------------------------------------------------------- #
class UI:
    """Interface utilisateur en ligne de commande, rendu Rich."""

    # Délais de suspense quand les animations sont activées (en secondes).
    DEAL_DELAY: float = 2.0
    DRAW_DELAY: float = 2.0

    def __init__(self, stream=sys.stdout) -> None:  # noqa: ANN001
        self.console = Console(theme=THEME, file=stream, highlight=False)
        self.round_number: int = 0
        self.tour_number: int = 0
        # Didacticiel (menu « 2 ») : conseil + explications + narration. L'attribut
        # interne reste nommé ``learning_mode`` mais correspond au Didacticiel.
        self.learning_mode: bool = False
        # Animations activées par défaut ; pilotent les délais de suspense.
        self.animations_enabled: bool = True
        # Délai entre chaque carte à la distribution initiale.
        self.deal_delay: float = self.DEAL_DELAY
        # Pause de suspense entre les tirages du croupier en cours de jeu.
        self.draw_delay: float = self.DRAW_DELAY
        # Pause de lecture après une ligne de narration (mode didacticiel).
        self.narration_delay: float = 1.0
        # Live display pour l'animation de distribution (mis à jour en place).
        self._deal_live: Optional[Live] = None
        # Légendes d'aide affichées une seule fois par session.
        self._yesno_help_shown: bool = False
        self._bet_help_shown: bool = False
        self._num_help_shown: bool = False

    # ------------------------------------------------------------------ #
    # Sorties basiques (compatibles avec l'ancienne API)
    # ------------------------------------------------------------------ #
    def write(self, text: str = "") -> None:
        self.console.print(text)

    def header(self, text: str) -> None:
        self.console.print()
        self.console.print(
            Panel(Text(text, style="bold gold", justify="center"),
                  border_style="felt", padding=(0, 2))
        )

    def info(self, text: str) -> None:
        self.console.print(Text(f"ℹ  {text}", style="info"))

    def warn(self, text: str) -> None:
        self.console.print(Text(f"⚠  {text}", style="warn"))

    def error(self, text: str) -> None:
        self.console.print(Text(f"✗  {text}", style="danger"))

    def success(self, text: str) -> None:
        self.console.print(Text(f"✓  {text}", style="good"))

    def set_animations(self, enabled: bool) -> None:
        """Active ou désactive les animations (délais de distribution/suspense)."""
        self.animations_enabled = enabled
        self.deal_delay = self.DEAL_DELAY if enabled else 0.0
        self.draw_delay = self.DRAW_DELAY if enabled else 0.0

    def pause_suspense(self) -> None:
        """Petit délai de suspense (si les animations sont activées)."""
        if self.draw_delay:
            time.sleep(self.draw_delay)

    def narrate(self, text: str, pause: bool = True) -> None:
        """Commente une action de la table — uniquement en mode didacticiel.

        ``pause`` ajoute un court temps de lecture. On le met à ``False`` quand
        un délai existant suit immédiatement (ex. révélation d'une carte).
        """
        if not self.learning_mode:
            return
        self.console.print(Text(f"🗣  {text}", style="italic cyan"))
        if pause and self.narration_delay:
            time.sleep(self.narration_delay)

    # ------------------------------------------------------------------ #
    # Écrans de menus
    # ------------------------------------------------------------------ #
    def main_menu(self, music_on: bool = False, music_available: bool = True) -> str:
        """Affiche le menu principal et renvoie le choix saisi."""
        self.console.print()
        self.console.print(_figlet("BLACKJACK", style="gold", font="slant"))
        subtitle = Text("Casino  —  règles internationales", style="felt", justify="center")
        self.console.print(subtitle)

        if not music_available:
            music_line = "   Musique d'ambiance (aucun lecteur audio)\n"
        else:
            music_line = (f"   Musique d'ambiance : "
                          f"{'activée' if music_on else 'désactivée'}\n")

        options = Text()
        options.append("  1", style="gold"); options.append("   Démarrer une nouvelle partie\n")
        options.append("  2", style="gold"); options.append("   Didacticiel — apprendre en jouant\n")
        options.append("  3", style="gold"); options.append("   Règles du jeu\n")
        options.append("  4", style="gold"); options.append("   Comparer les stratégies (simulation)\n")
        options.append("  5", style="gold"); options.append("   À propos / aide\n")
        options.append("  6", style="gold"); options.append(music_line)
        options.append("  0", style="gold"); options.append("   Quitter")

        self.console.print(Panel(options, title=Text(" Menu principal ", style="gold"),
                                 border_style="felt", padding=(1, 2)))
        return input("Tapez le numéro de votre choix (0 à 6) puis Entrée : ").strip()

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
        act.add_row("Tirer",      "(t, tirer)",      "Prendre une carte supplémentaire.")
        act.add_row("Rester",     "(r, rester)",     "Garder votre main et passer au croupier.")
        act.add_row("Doubler",    "(d, doubler)",    "Doubler votre mise, tirer UNE seule carte, puis rester.")
        act.add_row("Séparer",    "(s, séparer)",    "Séparer une paire en deux mains (mise doublée).")
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

        # Règles spécifiques de la table
        table_lines = [
            "• Le croupier reste sur 17 'soft' (S17).",
            "• Doubler est limité aux totaux durs de 9, 10 ou 11.",
            "• Pas d'abandon (surrender) autorisé.",
            "• 6 jeux de cartes mélangés (sabot).",
        ]
        table_rules = Text("\n".join(table_lines))
        self.console.print(Panel(table_rules,
                                 title=Text(" 📋 Règles de la table ", style="gold"),
                                 border_style="felt", padding=(0, 2)))

        self.console.print()
        self.info("Astuce débutant : choisissez « 2 Didacticiel — apprendre en jouant » "
                  "au menu principal pour des conseils et des explications à chaque tour.")
        self.console.print()
        input("Appuyez sur Entrée pour revenir au menu...")

    def choose_strategy(self) -> Tuple[str, Strategy]:
        """Affiche la liste des stratégies et fait choisir le joueur."""
        self.header("Choix de la stratégie d'aide à la décision")

        # Explication du concept, avant le tableau.
        intro = Text()
        intro.append("Une « stratégie d'aide » est un coach : à chaque tour, "
                     "elle vous suggère le meilleur coup à jouer.\n\n", style="white")
        intro.append("Deux familles :\n", style="white")
        intro.append("• La Stratégie de Base", style="good")
        intro.append(" conseille toujours le coup mathématiquement optimal. "
                     "Rien à retenir, parfaite pour débuter.\n", style="white")
        intro.append("• Les comptages de cartes", style="advice")
        intro.append(" (Hi-Lo, KO…) suivent en plus les cartes déjà sorties "
                     "pour affiner conseils et mises — réservés aux joueurs "
                     "avertis.\n", style="white")
        intro.append("\n👉 Débutant ? Choisissez la Stratégie de Base "
                     "(ou appuyez sur Entrée).", style="gold")
        self.console.print(Panel(intro, title=Text(" 💡 C'est quoi ? ", style="gold"),
                                 border_style="felt", padding=(1, 2)))

        recommended_key = "basique"

        # Tri par niveau croissant : — / Débutant / Intermédiaire / Avancé /
        # Expert (tri stable → l'ordre du registre est conservé à niveau égal).
        def _level_rank(key: str) -> int:
            niveau = _STRATEGY_GUIDE.get(key, ("",))[0]
            if niveau == "—":
                return 0
            if niveau.startswith("Débutant"):
                return 1
            if niveau.startswith("Intermédiaire"):
                return 2
            if niveau.startswith("Avancé"):
                return 3
            return 4  # Expert (et tout niveau inconnu en dernier)

        keys = sorted(STRATEGIES.keys(), key=_level_rank)

        tbl = Table(show_header=True, header_style="gold", border_style="felt",
                    show_lines=True, padding=(0, 1))
        tbl.add_column("#", style="gold", justify="right", no_wrap=True)
        tbl.add_column("Stratégie", style="info", no_wrap=True)
        tbl.add_column("Niveau", justify="center", no_wrap=True)
        tbl.add_column("En clair", style="white")

        for i, key in enumerate(keys, start=1):
            cls = STRATEGIES[key]
            niveau, en_clair = _STRATEGY_GUIDE.get(
                key, ("—", cls.description.replace("\n", " ")))
            nom = cls.name + ("  (conseillé)" if key == recommended_key else "")
            nom_style = "good" if key == recommended_key else "info"
            niv_style = "good" if niveau.startswith("Débutant") else (
                "dim" if niveau == "—" else "advice")
            tbl.add_row(str(i), Text(nom, style=nom_style),
                        Text(niveau, style=niv_style), en_clair)
        self.console.print(tbl)

        # Quand / de combien / pourquoi augmenter sa mise (comptages).
        self._show_bet_ramp_help()

        rec_index = keys.index(recommended_key) + 1
        while True:
            choice = input(f"\nVotre choix (numéro, ou Entrée = {rec_index}. "
                           "Stratégie de Base) : ").strip()
            if not choice:
                key = recommended_key
            elif choice.isdigit() and 1 <= int(choice) <= len(keys):
                key = keys[int(choice) - 1]
            else:
                self.error("Choix invalide. Recommencez.")
                continue
            cls = STRATEGIES[key]
            strat = cls()
            self.success(f"Stratégie sélectionnée : {strat.name}")
            return key, strat

    def _show_bet_ramp_help(self) -> None:
        """Explique, pour les comptages, quand/de combien/pourquoi miser plus."""
        why = Text()
        why.append("Réservé aux stratégies de comptage. ", style="advice")
        why.append("Le « true count » mesure combien de grosses cartes "
                    "(10 et As) restent dans le sabot, ajusté au nombre de jeux "
                    "restants.\n", style="white")
        why.append("Plus il est élevé, plus le sabot vous est favorable "
                   "(davantage de blackjacks et de croupiers qui sautent) : "
                   "vous augmentez alors votre mise pour gagner plus quand "
                   "l'avantage est de votre côté.\n", style="white")
        why.append("Quand il est bas ou négatif, vous revenez à la mise de base.",
                   style="dim")
        self.console.print(Panel(
            why, title=Text(" 📈 Quand augmenter sa mise ? ", style="gold"),
            border_style="advice", padding=(1, 2)))

        ramp = Table(show_header=True, header_style="gold", border_style="advice",
                     padding=(0, 1))
        ramp.add_column("Si le true count est…", style="info", no_wrap=True)
        ramp.add_column("Misez", style="good", justify="center", no_wrap=True)
        ramp.add_column("Pourquoi", style="white")
        for condition, mult, reason in BET_RAMP_GUIDE:
            ramp.add_row(condition, mult, reason)
        self.console.print(ramp)
        self.console.print(Text(
            "« Misez 4× » = quatre fois votre mise de base (votre mise de la "
            "1re manche). Note : KO et Red 7 se basent sur le compte courant, "
            "sans conversion.", style="dim"))

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        # Légende affichée une fois : explique les réponses possibles et le défaut.
        if not self._yesno_help_shown:
            self.console.print(Text(
                "Réponses : « o » pour oui, « n » pour non. La lettre en "
                "MAJUSCULE est choisie si vous appuyez juste sur Entrée.",
                style="dim"))
            self._yesno_help_shown = True
        suffix = " [O/n] " if default else " [o/N] "
        ans = input(question + suffix).strip().lower()
        if not ans:
            return default
        return ans in ("o", "oui", "y", "yes")

    def _num_help(self) -> None:
        """Explique une fois la convention [valeur par défaut] + Entrée."""
        if not self._num_help_shown:
            self.console.print(Text(
                "La valeur entre crochets [ ] est proposée par défaut : appuyez "
                "sur Entrée pour l'accepter, ou tapez votre propre valeur.",
                style="dim"))
            self._num_help_shown = True

    def ask_int(self, question: str, default: int, minimum: int = 1,
                maximum: int = 100) -> int:
        self._num_help()
        while True:
            ans = input(f"{question} [{default}] : ").strip()
            if not ans:
                return default
            if ans.isdigit() and minimum <= int(ans) <= maximum:
                return int(ans)
            self.error(f"Entrez un nombre entier entre {minimum} et {maximum}.")

    def ask_float(self, question: str, default: float, minimum: float = 0.0,
                  maximum: float = 1e9) -> float:
        self._num_help()
        while True:
            ans = input(f"{question} [{default}] : ").strip()
            if not ans:
                return default
            try:
                v = float(ans.replace(",", "."))
                if minimum <= v <= maximum:
                    return v
            except ValueError:
                pass
            self.error(f"Entrez un nombre entre {minimum:g} et {maximum:g}.")

    def ask_bet(self, default: float, minimum: float, maximum: float) -> float:
        """Mise façon casino : on tape le montant, Entrée lance la manche.

        La mise est arrondie à un montant « en jetons » (multiple du plus petit
        jeton) : impossible de miser au centime. Entrée sans rien saisir reprend
        la mise conseillée. ``tapis`` mise tout le solde.
        """
        step = min(CHIP_VALUES)  # plus petit jeton → granularité (pas de centime)

        def snap(x: float) -> float:
            v = round(x / step) * step
            return float(min(max(v, minimum), maximum))

        suggested = snap(default)
        # On ne propose que les jetons jouables (≤ solde / mise max).
        chips = [c for c in CHIP_VALUES if c <= maximum] or [CHIP_VALUES[0]]
        chip_line = Text("Jetons : ", style="white")
        for c in chips:
            chip_line.append(f"[{c}] ", style="gold")
        self.console.print(chip_line)
        # Légende affichée une fois : explique le défaut entre crochets.
        if not self._bet_help_shown:
            self.console.print(Text(
                "Le montant entre crochets [ ] est la mise par défaut : appuyez "
                "sur Entrée pour la valider, ou tapez un autre montant.",
                style="dim"))
            self._bet_help_shown = True

        while True:
            ans = input(f"Votre mise en € (min {minimum:.0f}, max {maximum:.0f}, "
                        f"« tapis ») [{suggested:.0f}] : ").strip().lower()
            if not ans:
                return suggested
            if ans in ("tapis", "max", "all-in"):
                return snap(maximum)
            try:
                v = float(ans.replace(",", "."))
            except ValueError:
                self.error("Entrez un montant (ex. 25), « tapis », ou Entrée.")
                continue
            if v < minimum or v > maximum:
                self.warn(f"Misez entre {minimum:.0f} et {maximum:.0f} €.")
                continue
            snapped = snap(v)
            if snapped != v:
                self.info(f"Mise arrondie à {snapped:.0f} € (jetons, pas de centime).")
            return snapped

    # ------------------------------------------------------------------ #
    # Affichage d'une manche
    # ------------------------------------------------------------------ #
    def _stop_deal_live(self) -> None:
        """Termine l'animation Live de distribution si elle est encore active."""
        if self._deal_live is not None:
            self._deal_live.stop()
            self._deal_live = None

    def show_initial_deal(self, player: HumanPlayer, dealer: Dealer) -> None:
        self.round_number += 1
        self.tour_number = 0
        # On NE stoppe PAS le Live ici : le tableau reste épinglé à l'écran
        # pendant le peek et l'assurance (les narrations s'affichent au-dessus).
        # Il sera stoppé par la prochaine méthode qui dessine (prompt_action,
        # prompt_insurance, show_showdown, show_deal_state…).

    def show_round_header(self, number: int) -> None:
        """Bandeau proéminent de début de manche (unité de jeu de haut niveau)."""
        self.round_number = number - 1  # show_initial_deal incrémentera à `number`.
        self.tour_number = 0
        self.console.print()
        self.console.print()
        self.console.rule(
            Text(f"  ♠  MANCHE {number}  ♠  ", style="bold gold"),
            characters="═", style="gold",
        )

    def show_pre_deal(self, player: HumanPlayer, dealer: Dealer,
                      hide_hole: bool = False) -> None:
        """Affiche les cadres vides avant la distribution (positions fixes dès le départ)."""
        self.console.print()
        player_hand = player.hands[0] if player.hands else Hand()
        dealer_pad = 2 if hide_hole else 1
        dealer_panel = _hand_panel(Hand(), "Croupier",
                                   hide_first=hide_hole, pad_to=dealer_pad, border="felt")
        player_panel = _hand_panel(player_hand, "Votre main",
                                   pad_to=2, show_bet=True, border="gold")
        renderable = Group(dealer_panel, Text(""), player_panel)
        self._deal_live = Live(renderable, console=self.console,
                               refresh_per_second=4, transient=True)
        self._deal_live.start()

    def show_deal_step(self, player: HumanPlayer, dealer: Dealer,
                       hide_hole: bool = False) -> None:
        """Met à jour la zone de distribution en place (même case, pas de scroll).

        La carte apparaît immédiatement (synchronisée avec le texte de
        narration) ; la pause vient *après*, avant l'étape suivante.
        """
        player_hand = player.hands[0] if player.hands else Hand()
        dealer_pad = 2 if hide_hole else 1
        dealer_panel = _hand_panel(dealer.hand, "Croupier",
                                   hide_first=hide_hole, pad_to=dealer_pad, border="felt")
        player_panel = _hand_panel(player_hand, "Votre main",
                                   pad_to=2, show_bet=True, border="gold")
        renderable = Group(dealer_panel, Text(""), player_panel)
        if self._deal_live is None:
            self._deal_live = Live(renderable, console=self.console,
                                   refresh_per_second=4, transient=True)
            self._deal_live.start()
        else:
            self._deal_live.update(renderable)
        if self.deal_delay:
            time.sleep(self.deal_delay)

    def show_split_step(self, player: HumanPlayer) -> None:
        """Anime la séparation : affiche les mains issues du split, en place.

        Réutilise la zone Live de distribution (stoppée par la prochaine
        méthode qui dessine, ex. prompt_action).
        """
        panels = [
            _hand_panel(h, f"Main {i + 1}", pad_to=2, show_bet=True, border="gold")
            for i, h in enumerate(player.hands)
        ]
        renderable = Columns(panels, padding=(0, 2), expand=False)
        if self._deal_live is None:
            self._deal_live = Live(renderable, console=self.console,
                                   refresh_per_second=4, transient=True)
            self._deal_live.start()
        else:
            self._deal_live.update(renderable)
        if self.deal_delay:
            time.sleep(self.deal_delay)

    def show_deal_state(self, player: HumanPlayer, dealer: Dealer) -> None:
        """Affiche les deux panneaux (croupier + joueur) sans demander d'action."""
        self._stop_deal_live()
        self.tour_number += 1
        label = f"Tour {self.tour_number}"
        self.console.print()
        self.console.rule(Text(label, style="cyan"), characters="─", style="dim")

        dealer_hand_shown = Hand()
        dealer_hand_shown.add_card(dealer.up_card)

        hand = player.hands[0] if player.hands else Hand()
        # Empilé (croupier au-dessus / main en dessous), comme partout ailleurs.
        self.console.print(Group(
            _hand_panel(dealer_hand_shown, "Croupier", add_hidden=True, border="felt"),
            Text(""),
            _hand_panel(hand, "Votre main", show_bet=True, border="gold"),
        ))

    def show_showdown(self, player: HumanPlayer, dealer: Dealer) -> None:
        """Affiche les deux mains avec le jeu complet du croupier révélé.

        Utilisé notamment quand le croupier a un Blackjack : on montre la main
        du joueur ET celle du croupier (carte cachée dévoilée), sans action.
        """
        self._stop_deal_live()
        hand = player.hands[0] if player.hands else Hand()
        self.console.print()
        self.console.print(Group(
            _hand_panel(dealer.hand, "Croupier", up_card_first=True, border="felt"),
            Text(""),
            _hand_panel(hand, "Votre main", show_bet=True, border="gold"),
        ))
        if self.draw_delay:
            time.sleep(self.draw_delay)

    def show_dealer_reveal(self, dealer: Dealer,
                           revealed: Optional[Card] = None) -> None:
        self._stop_deal_live()
        self.console.print()
        # En didacticiel, la narration annonce déjà la révélation : on évite
        # le doublon en n'imprimant le libellé que hors mode didacticiel.
        if not self.learning_mode:
            label = "révèle sa carte cachée" if revealed is not None else "tire sa 2e carte"
            self.console.print(Text(f"Croupier {label} :", style="info"))
        self.console.print(Padding(
            _hand_panel(dealer.hand, "Croupier", up_card_first=True), (1, 0, 0, 2)
        ))
        if self.draw_delay:
            time.sleep(self.draw_delay)

    def show_insurance_result(self, dealer_blackjack: bool,
                              insurance_bet: float) -> None:
        self.console.print()
        if dealer_blackjack:
            self.success(f"Assurance gagnée ! (+{insurance_bet * 2:.2f})")
        else:
            self.warn(f"Assurance perdue (-{insurance_bet:.2f})")

    def show_dealer_draw(self, dealer: Dealer) -> None:
        self._stop_deal_live()
        self.console.print()
        # En didacticiel, la narration annonce déjà le tirage : on évite le doublon.
        if not self.learning_mode:
            n = len(dealer.hand.cards)
            self.console.print(Text(f"Croupier tire sa {n}e carte :", style="info"))
        self.console.print(Padding(
            _hand_panel(dealer.hand, "Croupier", up_card_first=True), (1, 0, 0, 2)
        ))
        if self.draw_delay:
            time.sleep(self.draw_delay)

    def show_dealer_bust(self, dealer: Dealer) -> None:
        # La pause de calcul a déjà eu lieu après l'affichage de la carte (show_dealer_draw).
        self.console.print()
        self.console.print(_figlet("BUST !", style="danger", font="small"))

    def show_action(self, player: HumanPlayer, hand: Hand, action: Action) -> None:
        line = Text()
        line.append("▸ ", style="gold")
        line.append(f"{player.name} : ", style="white")
        line.append(action.label, style="warn")
        self.console.print(line)

    def show_player_hand(self, player: HumanPlayer, hand: Hand) -> None:
        """Affiche la main du joueur (ex. après un tirage qui la termine)."""
        self._stop_deal_live()
        self.console.print()
        self.console.print(Padding(
            _hand_panel(hand, "Votre main", show_bet=True, border="gold"), (1, 0, 0, 2)
        ))
        if self.draw_delay:
            time.sleep(self.draw_delay)

    def show_shuffle(self) -> None:
        self.console.print()
        self.info("Carte de coupe atteinte — le sabot est remélangé.")

    def show_round_results(self, results: List[Tuple[Hand, Outcome, float]]) -> None:
        self._stop_deal_live()
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
        if stats.surrenders:  # masquée quand l'abandon est désactivé/inutilisé
            tbl.add_row("Abandons",        f"{stats.surrenders}")
        tbl.add_row("Total misé",          f"{stats.total_bet:.2f}")
        net_color = "good" if stats.total_won >= 0 else "danger"
        tbl.add_row("Bilan net",
                    Text(f"{stats.total_won:+.2f}", style=net_color))
        tbl.add_row("Espérance par mise",
                    Text(f"{stats.expected_value*100:+.2f} %", style=net_color))
        self.console.print(Panel(tbl, border_style="felt", padding=(1, 2)))

    def show_streak(self, streak: int) -> None:
        """Affiche la série de victoires en cours (à partir de 2)."""
        if streak < 2:
            return
        self.console.print(
            Text(f"🔥 {streak} victoires d'affilée !", style="gold")
        )

    def show_records(self, profile) -> None:  # noqa: ANN001
        """Affiche les records et le cumul « à vie » du profil sauvegardé."""
        self.header("Vos records")
        tbl = Table.grid(padding=(0, 2))
        tbl.add_column(style="info", no_wrap=True)
        tbl.add_column(style="gold", justify="right")
        tbl.add_row("Meilleur solde atteint",   f"{profile.best_bankroll:.2f}")
        tbl.add_row("Plus longue série",         f"{profile.longest_win_streak}")
        tbl.add_row("Plus gros gain (1 main)",   f"{profile.biggest_win:+.2f}")
        tbl.add_row("Blackjacks (total)",        f"{profile.blackjacks}")
        tbl.add_row("Manches jouées (total)",    f"{profile.rounds_played}")
        if profile.rebuys:
            tbl.add_row("Re-caves",              f"{profile.rebuys}")
        self.console.print(Panel(tbl, title=Text(" 🏆 Records ", style="gold"),
                                 border_style="gold", padding=(1, 2)))
        self.console.print(Text(f"💰 Solde sauvegardé : {profile.bankroll:.2f}",
                                style="white"))

    # ------------------------------------------------------------------ #
    # Prompt d'assurance — appelé par Round
    # ------------------------------------------------------------------ #
    def prompt_insurance(self, player: HumanPlayer, dealer: Dealer,
                         max_insurance: float) -> float:
        """Propose l'assurance ; renvoie la mise prise (0.0 si refus)."""
        self._stop_deal_live()
        self.console.print()

        # Rappel des mains pour décider en connaissance de cause.
        dealer_hand_shown = Hand()
        dealer_hand_shown.add_card(dealer.up_card)
        hand = player.hands[0] if player.hands else Hand()
        self.console.print(Group(
            _hand_panel(dealer_hand_shown, "Croupier", add_hidden=True, border="felt"),
            Text(""),
            _hand_panel(hand, "Votre main", show_bet=True, border="gold"),
        ))

        ins = Text()
        ins.append("Le croupier montre un As.\n\n", style="warn")
        ins.append("L'assurance est un pari à part : vous misez la moitié de "
                   "votre mise ", style="white")
        ins.append(f"({max_insurance:.2f} €)", style="gold")
        ins.append(". Si le croupier a un Blackjack, elle rapporte 2:1 (vous ne "
                   "perdez alors rien) ; sinon, elle est perdue.\n", style="white")
        ins.append("Conseil : rarement rentable — en cas de doute, refusez.",
                   style="dim")
        self.console.print(Panel(
            ins, title=Text(" 🛡  Assurance ? ", style="warn"),
            border_style="warn", padding=(1, 2),
        ))
        if self.ask_yes_no("Prendre l'assurance ?", default=False):
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
        self._stop_deal_live()
        self.tour_number += 1

        if len(player.hands) > 1:
            label = f"Tour {self.tour_number} — Main {hand_index + 1}/{len(player.hands)}"
        else:
            label = f"Tour {self.tour_number}"

        self.console.print()
        self.console.rule(Text(label, style="cyan"), characters="─", style="dim")

        # Main du croupier virtuelle : uniquement la carte visible + hole card cachée.
        dealer_hand_shown = Hand()
        dealer_hand_shown.add_card(dealer_up)

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
            ("t", Action.HIT),      # Tirer
            ("r", Action.STAND),    # Rester
        ]
        if can_double and player.bankroll >= hand.bet:
            options.append(("d", Action.DOUBLE))   # Doubler
        if hand.can_split and player.bankroll >= hand.bet:
            options.append(("s", Action.SPLIT))    # Séparer
        if can_surrender:
            options.append(("a", Action.SURRENDER))  # Abandonner

        # Le conseil doit porter sur une action réellement disponible : si la
        # stratégie recommande un double/split/abandon non autorisé (ex. double
        # d'une main « soft » en règle française), on retombe sur le repli usuel
        # (tirer si on aurait doublé/abandonné, sinon rester).
        allowed_actions = {a for _, a in options}
        if advice is not None and advice not in allowed_actions:
            if advice in (Action.DOUBLE, Action.SPLIT, Action.SURRENDER):
                advice = Action.HIT
            else:
                advice = Action.STAND

        # Table d'actions (colonne de droite).
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
            act_tbl.add_row(*row)

        right_parts: list = [act_tbl]
        if advice is not None:
            advice_panel = Panel(
                Text(f"💡 Conseil : {advice.label}  ({advice.short})",
                     style="advice"),
                border_style="advice", padding=(0, 2),
            )
            right_parts.extend([Text(""), advice_panel])

        # Mise en page : mains empilées à gauche, actions à droite.
        left = Group(
            _hand_panel(dealer_hand_shown, "Croupier", add_hidden=True, border="felt"),
            Text(""),
            _hand_panel(hand, "Votre main", show_bet=True, border="gold"),
        )
        self.console.print(Columns([left, Group(*right_parts)],
                                   padding=(0, 2), expand=False))

        valid_keys = {k: a for k, a in options}
        word_aliases = {
            "tirer": Action.HIT, "hit": Action.HIT,
            "rester": Action.STAND, "stand": Action.STAND,
            "doubler": Action.DOUBLE, "double": Action.DOUBLE,
            "separer": Action.SPLIT, "séparer": Action.SPLIT, "split": Action.SPLIT,
            "abandonner": Action.SURRENDER, "surrender": Action.SURRENDER,
        }
        allowed = {a for _, a in options}
        # Exemple concret tiré des actions réellement disponibles ce tour.
        sample_key, sample_action = options[0]
        prompt = (f"Votre action — tapez la touche (ex. « {sample_key} » pour "
                  f"{sample_action.label}) ou le mot entier : ")
        while True:
            choice = input(prompt).strip().lower()
            if choice in valid_keys:
                return valid_keys[choice]
            if choice in word_aliases and word_aliases[choice] in allowed:
                return word_aliases[choice]
            self.error(f"Action invalide. Tapez une touche ({'/'.join(valid_keys)}) "
                       f"ou le nom complet ({', '.join(a.label.lower() for _, a in options)}).")
