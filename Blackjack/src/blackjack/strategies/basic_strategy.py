"""
Stratégie de base (« Basic Strategy »).

Cette stratégie est mathématiquement optimale en l'absence de comptage. Les
trois tableaux ci-dessous correspondent aux règles standard les plus
répandues dans les casinos :

* 4 à 8 jeux ;
* le croupier reste sur 17 « soft » (« S17 ») ;
* double permis après split (« DAS ») ;
* abandon (« late surrender ») autorisé ;
* split jusqu'à 4 mains.

Sources de référence consultées pour ces tables :
- *Beat the Dealer* — Edward O. Thorp (1962, éd. révisées) ;
- *Professional Blackjack* — Stanford Wong ;
- *Blackjack Attack* — Don Schlesinger.

Légende des actions :
    H = HIT (tirer)
    S = STAND (rester)
    D = DOUBLE si possible, sinon HIT
    Ds = DOUBLE si possible, sinon STAND
    P = SPLIT
    Ph = SPLIT si DAS autorisé, sinon HIT
    R = SURRENDER (abandon) si possible, sinon HIT
    Rs = SURRENDER si possible, sinon STAND
"""

from __future__ import annotations

from typing import Dict, Tuple

from ..core import Action, Card, Hand, Rank
from .base_strategy import Strategy


# --------------------------------------------------------------------------- #
# Tableaux de stratégie (clé : (total joueur, total croupier 2..11))
# --------------------------------------------------------------------------- #
# Codes utilisés dans les tableaux ci-dessous :
#   "H"  = HIT,  "S"  = STAND,  "D"  = DOUBLE/HIT,  "Ds" = DOUBLE/STAND,
#   "P"  = SPLIT, "Ph" = SPLIT si DAS sinon HIT,
#   "R"  = SURRENDER/HIT, "Rs" = SURRENDER/STAND
_HARD_TABLE: Dict[int, Dict[int, str]] = {
    # Carte croupier ->  2    3    4    5    6    7    8    9   10    A(11)
    5:  {2: "H", 3: "H", 4: "H",  5: "H",  6: "H",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    6:  {2: "H", 3: "H", 4: "H",  5: "H",  6: "H",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    7:  {2: "H", 3: "H", 4: "H",  5: "H",  6: "H",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    8:  {2: "H", 3: "H", 4: "H",  5: "H",  6: "H",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    9:  {2: "H", 3: "D", 4: "D",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    10: {2: "D", 3: "D", 4: "D",  5: "D",  6: "D",  7: "D", 8: "D", 9: "D", 10: "H", 11: "H"},
    11: {2: "D", 3: "D", 4: "D",  5: "D",  6: "D",  7: "D", 8: "D", 9: "D", 10: "D", 11: "H"},
    12: {2: "H", 3: "H", 4: "S",  5: "S",  6: "S",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    13: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    14: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    15: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "H", 8: "H", 9: "H", 10: "R", 11: "H"},
    16: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "H", 8: "H", 9: "R", 10: "R", 11: "R"},
    17: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    18: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    19: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    20: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    21: {2: "S", 3: "S", 4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
}

# Mains soft : la clé est le total (l'As compté 11 + l'autre carte).
_SOFT_TABLE: Dict[int, Dict[int, str]] = {
    13: {2: "H", 3: "H",  4: "H",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    14: {2: "H", 3: "H",  4: "H",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    15: {2: "H", 3: "H",  4: "D",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    16: {2: "H", 3: "H",  4: "D",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    17: {2: "H", 3: "D",  4: "D",  5: "D",  6: "D",  7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    18: {2: "S", 3: "Ds", 4: "Ds", 5: "Ds", 6: "Ds", 7: "S", 8: "S", 9: "H", 10: "H", 11: "H"},
    19: {2: "S", 3: "S",  4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    20: {2: "S", 3: "S",  4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    21: {2: "S", 3: "S",  4: "S",  5: "S",  6: "S",  7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
}

# Tableau des paires (clé = valeur d'une des deux cartes).
# 11 = paire d'As ; 10 = paire ten-value (10/V/D/R).
_PAIR_TABLE: Dict[int, Dict[int, str]] = {
    2:  {2: "Ph", 3: "Ph", 4: "P",  5: "P", 6: "P", 7: "P", 8: "H", 9: "H", 10: "H", 11: "H"},
    3:  {2: "Ph", 3: "Ph", 4: "P",  5: "P", 6: "P", 7: "P", 8: "H", 9: "H", 10: "H", 11: "H"},
    4:  {2: "H",  3: "H",  4: "H",  5: "Ph",6: "Ph",7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    5:  {2: "D",  3: "D",  4: "D",  5: "D", 6: "D", 7: "D", 8: "D", 9: "D", 10: "H", 11: "H"},
    6:  {2: "Ph", 3: "P",  4: "P",  5: "P", 6: "P", 7: "H", 8: "H", 9: "H", 10: "H", 11: "H"},
    7:  {2: "P",  3: "P",  4: "P",  5: "P", 6: "P", 7: "P", 8: "H", 9: "H", 10: "H", 11: "H"},
    8:  {2: "P",  3: "P",  4: "P",  5: "P", 6: "P", 7: "P", 8: "P", 9: "P", 10: "P", 11: "P"},
    9:  {2: "P",  3: "P",  4: "P",  5: "P", 6: "P", 7: "S", 8: "P", 9: "P", 10: "S", 11: "S"},
    10: {2: "S",  3: "S",  4: "S",  5: "S", 6: "S", 7: "S", 8: "S", 9: "S", 10: "S", 11: "S"},
    11: {2: "P",  3: "P",  4: "P",  5: "P", 6: "P", 7: "P", 8: "P", 9: "P", 10: "P", 11: "P"},
}


def _resolve_code(code: str, hand: Hand, das_allowed: bool = True) -> Action:
    """Traduit un code de tableau (« H », « D », « Ph », « R »…) en :class:`Action`."""
    if code == "H":
        return Action.HIT
    if code == "S":
        return Action.STAND
    if code == "P":
        return Action.SPLIT if hand.can_split else Action.HIT
    if code == "Ph":  # Split si DAS autorisé, sinon hit
        if hand.can_split and das_allowed:
            return Action.SPLIT
        return Action.HIT
    if code == "D":  # Double, sinon hit
        return Action.DOUBLE if hand.can_double else Action.HIT
    if code == "Ds":  # Double, sinon stand
        return Action.DOUBLE if hand.can_double else Action.STAND
    if code == "R":  # Surrender, sinon hit
        return Action.SURRENDER if hand.can_surrender else Action.HIT
    if code == "Rs":  # Surrender, sinon stand
        return Action.SURRENDER if hand.can_surrender else Action.STAND
    # Fallback défensif — ne devrait jamais arriver.
    return Action.STAND


class BasicStrategy(Strategy):
    """Stratégie de base — décision optimale sans comptage."""

    name = "Stratégie de Base"
    description = (
        "Décision mathématiquement optimale en l'absence de comptage. Conçue "
        "pour 4-8 jeux, croupier stand sur 17 soft, double après split autorisé "
        "(DAS), surrender tardif autorisé. Réduit l'avantage maison à ~0,5 %."
    )
    counts_cards = False

    def __init__(self, das_allowed: bool = True) -> None:
        super().__init__()
        self.das_allowed = das_allowed

    # ------------------------------------------------------------------ #
    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        dealer_val = 11 if dealer_up.is_ace else min(dealer_up.value, 10)

        # Cas 1 : paire « splittable »
        if hand.can_split:
            pair_rank: Rank = hand.cards[0].rank
            key = 11 if pair_rank.is_ace else (10 if pair_rank.is_ten_value else pair_rank.points)
            code = _PAIR_TABLE[key][dealer_val]
            return _resolve_code(code, hand, self.das_allowed)

        # Cas 2 : main soft (au moins un As compté 11)
        if hand.is_soft:
            total = hand.total
            # Sous 13 ou au-dessus de 21 le tableau ne s'applique pas.
            if total in _SOFT_TABLE:
                code = _SOFT_TABLE[total][dealer_val]
                return _resolve_code(code, hand, self.das_allowed)

        # Cas 3 : main hard
        total = hand.total
        if total <= 4:
            return Action.HIT
        if total >= 21:
            return Action.STAND
        code = _HARD_TABLE[total][dealer_val]
        return _resolve_code(code, hand, self.das_allowed)
