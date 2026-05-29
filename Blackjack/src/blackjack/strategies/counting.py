"""
Stratégies de comptage de cartes.

Chaque stratégie hérite de :class:`Strategy` et surcharge :meth:`card_value`
pour appliquer son propre barème. La méthode :meth:`recommend` délègue à la
stratégie de base, puis applique d'éventuels « index plays » lorsque le
*true count* dépasse un seuil donné. C'est l'illustration directe du
polymorphisme : le moteur du jeu appelle ``strategy.recommend(...)`` sans
jamais avoir à savoir quel système est utilisé.

Référentiels utilisés :
    * Hi-Lo      — Harvey Dubner, popularisé par E. Thorp ; *Beat the Dealer*.
    * KO         — Vancura & Fuchs, *Knock-Out Blackjack*.
    * Hi-Opt I   — Charles Einstein.
    * Hi-Opt II  — Lance Humble.
    * Omega II   — Bryce Carlson, *Blackjack for Blood*.
    * Zen        — Arnold Snyder, *Blackbelt in Blackjack*.
    * Red 7      — Arnold Snyder.
"""

from __future__ import annotations

from typing import Dict

from ..core import Action, Card, Hand, Rank
from .base_strategy import Strategy
from .basic_strategy import BasicStrategy


# --------------------------------------------------------------------------- #
# Palier de mise commun à tous les comptages — SOURCE UNIQUE.
# Du plus favorable au moins : (true count minimum, multiplicateur de la mise).
# En dessous du dernier seuil, on garde la mise de base (1×).
# --------------------------------------------------------------------------- #
BET_RAMP = (
    (5, 8),
    (4, 6),
    (3, 4),
    (2, 2),
)


def bet_units_for(true_count: float) -> int:
    """Multiplicateur de mise conseillé pour un true count donné."""
    for threshold, units in BET_RAMP:
        if true_count >= threshold:
            return units
    return 1


# Présentation pédagogique du palier (affichée au choix de stratégie).
# (condition, multiplicateur, raison). Construite à partir de BET_RAMP pour
# rester cohérente : on ajoute la ligne « mise de base » sous le plus bas seuil.
def _bet_ramp_guide():
    reasons = {2: "léger avantage pour vous",
               3: "avantage net",
               4: "fort avantage",
               5: "avantage maximal"}
    rows = [("true count ≤ +1", "1× (mise de base)",
             "sabot neutre ou défavorable")]
    for threshold, units in sorted(BET_RAMP):  # du plus bas au plus haut
        label = (f"true count ≥ +{threshold}" if threshold == BET_RAMP[0][0]
                 else f"true count +{threshold}")
        rows.append((label, f"{units}×", reasons.get(threshold, "")))
    return tuple(rows)


BET_RAMP_GUIDE = _bet_ramp_guide()


class _CountingStrategy(Strategy):
    """Classe intermédiaire factorisant le comportement commun.

    Toutes les stratégies de comptage utilisent en pratique la stratégie de
    base pour la décision ; le comptage sert surtout à moduler la mise et
    quelques décisions clés (les « illustrious 18 » par exemple).
    """

    counts_cards = True
    #: Dictionnaire {valeur de rang -> incrément du compte}.
    values: Dict[int, int] = {}

    def __init__(self) -> None:
        super().__init__()
        # On compose plutôt que d'hériter pour pouvoir partager la même
        # implémentation de la stratégie de base entre tous les compteurs.
        self._basic = BasicStrategy()

    # ------------------------------------------------------------------ #
    def card_value(self, card: Card) -> int:
        """Renvoie la valeur de la carte dans le système courant."""
        rank_value = card.rank.points
        # Les figures (V, D, R) sont déjà valorisées 10 dans ``Rank``.
        # On normalise A vers 1 pour clé de dictionnaire (sinon == 11).
        key = 1 if card.is_ace else rank_value
        return self.values.get(key, 0)

    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        # 99 % du temps la stratégie de base est optimale.
        return self._basic.recommend(hand, dealer_up)

    def betting_units(self, decks_remaining: float, min_bet: float,
                       max_bet: float) -> float:
        """Palier de mises standard selon le true count (cf. ``BET_RAMP``)."""
        units = bet_units_for(self.true_count(decks_remaining))
        return min(min_bet * units, max_bet)


# --------------------------------------------------------------------------- #
# Hi-Lo  (système de niveau 1, équilibré)
# --------------------------------------------------------------------------- #
class HiLoStrategy(_CountingStrategy):
    """Comptage Hi-Lo (1963) — le plus enseigné au monde."""

    name = "Hi-Lo"
    description = (
        "Système de niveau 1 équilibré. Le plus simple et le plus populaire des "
        "comptages. Inventé par Harvey Dubner, popularisé par Edward Thorp."
    )
    # 2,3,4,5,6 = +1 ; 7,8,9 = 0 ; 10,V,D,R,A = -1
    values = {
        2: +1, 3: +1, 4: +1, 5: +1, 6: +1,
        7:  0, 8:  0, 9:  0,
        10: -1,
        1: -1,  # As (normalisé)
    }


# --------------------------------------------------------------------------- #
# KO  (Knock-Out, déséquilibré)
# --------------------------------------------------------------------------- #
class KOStrategy(_CountingStrategy):
    """Comptage KO (Knock-Out) — déséquilibré, pas besoin de true count."""

    name = "KO (Knock-Out)"
    description = (
        "Comptage déséquilibré de niveau 1 (Vancura & Fuchs). On compte aussi "
        "le 7 comme +1. L'IRC (compte initial) dépend du nombre de jeux : "
        "IRC = -4 × (n_decks − 1)."
    )
    # 2,3,4,5,6,7 = +1 ; 8,9 = 0 ; 10,V,D,R,A = -1
    values = {
        2: +1, 3: +1, 4: +1, 5: +1, 6: +1, 7: +1,
        8:  0, 9:  0,
        10: -1,
        1: -1,
    }

    def __init__(self, num_decks: int = 6) -> None:
        super().__init__()
        self.__irc = -4 * (num_decks - 1)
        self._running_count = self.__irc

    def reset_count(self) -> None:
        self._running_count = self.__irc

    def true_count(self, decks_remaining: float) -> float:
        # Le KO n'utilise PAS de true count ; on renvoie le running count.
        return float(self._running_count)


# --------------------------------------------------------------------------- #
# Hi-Opt I  (Einstein Count)
# --------------------------------------------------------------------------- #
class HiOptIStrategy(_CountingStrategy):
    """Hi-Opt I (Charles Einstein, 1968)."""

    name = "Hi-Opt I"
    description = (
        "Comptage de niveau 1 équilibré. Charles Einstein (1968). 3-6 valent "
        "+1, 10/V/D/R valent -1, le reste (dont A et 2) est neutre. Aces à "
        "compter à part pour l'assurance."
    )
    # 3,4,5,6 = +1 ; 10,V,D,R = -1 ; A,2,7,8,9 = 0
    values = {
        3: +1, 4: +1, 5: +1, 6: +1,
        2: 0, 7: 0, 8: 0, 9: 0,
        10: -1,
        1: 0,
    }


# --------------------------------------------------------------------------- #
# Hi-Opt II  (Lance Humble)
# --------------------------------------------------------------------------- #
class HiOptIIStrategy(_CountingStrategy):
    """Hi-Opt II (Lance Humble), niveau 2."""

    name = "Hi-Opt II"
    description = (
        "Comptage de niveau 2 équilibré (Humble). Plus précis que Hi-Opt I, "
        "demande un comptage séparé des As pour l'assurance."
    )
    # 2,3,6,7 = +1 ; 4,5 = +2 ; 8,9,A = 0 ; 10,V,D,R = -2
    values = {
        2: +1, 3: +1, 6: +1, 7: +1,
        4: +2, 5: +2,
        8: 0, 9: 0,
        10: -2,
        1: 0,
    }


# --------------------------------------------------------------------------- #
# Omega II  (Bryce Carlson)
# --------------------------------------------------------------------------- #
class OmegaIIStrategy(_CountingStrategy):
    """Omega II (Bryce Carlson, *Blackjack for Blood*)."""

    name = "Omega II"
    description = (
        "Comptage de niveau 2 équilibré (Bryce Carlson). Très efficace mais "
        "demande de la concentration : 5 valeurs différentes (-2 à +2) et "
        "comptage séparé des As recommandé."
    )
    # 2,3,7 = +1 ; 4,5,6 = +2 ; 8,A = 0 ; 9 = -1 ; 10,V,D,R = -2
    values = {
        2: +1, 3: +1, 7: +1,
        4: +2, 5: +2, 6: +2,
        8: 0,
        9: -1,
        10: -2,
        1: 0,
    }


# --------------------------------------------------------------------------- #
# Zen Count  (Arnold Snyder)
# --------------------------------------------------------------------------- #
class ZenStrategy(_CountingStrategy):
    """Zen Count (Arnold Snyder, *Blackbelt in Blackjack*)."""

    name = "Zen Count"
    description = (
        "Comptage de niveau 2 équilibré (Snyder). Bon compromis entre "
        "puissance et complexité : les As sont comptés (-1) au lieu d'être "
        "neutres comme dans Omega II."
    )
    # 2,3,7 = +1 ; 4,5,6 = +2 ; 8,9 = 0 ; 10,V,D,R = -2 ; A = -1
    values = {
        2: +1, 3: +1, 7: +1,
        4: +2, 5: +2, 6: +2,
        8: 0, 9: 0,
        10: -2,
        1: -1,
    }


# --------------------------------------------------------------------------- #
# Red 7  (Arnold Snyder)
# --------------------------------------------------------------------------- #
class Red7Strategy(_CountingStrategy):
    """Red 7 Count (Snyder) — déséquilibré, niveau 1."""

    name = "Red 7"
    description = (
        "Comptage déséquilibré de niveau 1 (Snyder). Spécificité : un 7 rouge "
        "compte +1, un 7 noir compte 0. L'IRC dépend du nombre de jeux : "
        "IRC = -2 × n_decks."
    )
    # 2,3,4,5,6 = +1 ; 7 rouge = +1, 7 noir = 0 ; 8,9 = 0 ; 10/V/D/R,A = -1
    values = {
        2: +1, 3: +1, 4: +1, 5: +1, 6: +1,
        8: 0, 9: 0,
        10: -1,
        1: -1,
    }

    def __init__(self, num_decks: int = 6) -> None:
        super().__init__()
        self.__irc = -2 * num_decks
        self._running_count = self.__irc

    def reset_count(self) -> None:
        self._running_count = self.__irc

    def card_value(self, card: Card) -> int:
        # Cas spécifique du 7 : la couleur de l'enseigne compte.
        if card.rank is Rank.SEVEN:
            return +1 if card.suit.is_red else 0
        return super().card_value(card)

    def true_count(self, decks_remaining: float) -> float:
        # Comme tous les comptages déséquilibrés, pas de conversion en TC.
        return float(self._running_count)
