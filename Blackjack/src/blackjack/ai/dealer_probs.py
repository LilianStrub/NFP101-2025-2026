"""
Module ``dealer_probs`` — distribution exacte du total final du croupier.

Le croupier ne « décide » jamais rien (règle fixe : tirer sous 17, s'arrêter
à 17+, éventuellement tirer sur 17 « soft » selon la variante H17). Calculer
la probabilité de chacun de ses totaux finaux (17, 18, 19, 20, 21 ou buste)
est donc un pur calcul combinatoire, exploré récursivement et mémoïsé
(``functools.lru_cache``) pour ne jamais recalculer deux fois le même
sous-arbre.

C'est le premier étage de l'**expectiminimax** utilisé par le solveur
(``solver.py``) : un arbre de décision où le croupier ne joue pas contre le
joueur (ce n'est pas un adversaire qui minimise) mais où chaque tirage de
carte est un nœud de hasard pondéré par sa probabilité — d'où « expecti- »
(espérance) plutôt que « mini- » (minimum).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Union

from .mdp import CARD_PROBS, add_card_value

_CARD_PROB_BY_VALUE = dict(CARD_PROBS)

#: Clé d'issue pour un croupier brûlé (dépassement de 21).
BUST = "bust"

DealerOutcome = Dict[Union[int, str], float]


@lru_cache(maxsize=None)
def dealer_final_distribution(total: int, soft: bool, hit_soft_17: bool) -> DealerOutcome:
    """Distribution de probabilité du total final du croupier, en partant
    d'un état ``(total, soft)`` donné et en appliquant sa règle de jeu fixe.

    :param total:         Total courant du croupier.
    :param soft:          Main actuelle « soft » (As compté 11) ou non.
    :param hit_soft_17:   True si le croupier tire sur 17 « soft » (règle H17).
    :return: dict associant chaque issue (17, 18, 19, 20, 21 ou ``BUST``) à
             sa probabilité ; les probabilités somment à 1.0.
    """
    if total > 21:
        return {BUST: 1.0}

    must_stand = total >= 18 or (total == 17 and not (soft and hit_soft_17))
    if must_stand:
        return {total: 1.0}

    distribution: DealerOutcome = {}
    for card_value, p in CARD_PROBS:
        new_total, new_soft, bust = add_card_value(total, soft, card_value)
        if bust:
            distribution[BUST] = distribution.get(BUST, 0.0) + p
            continue
        sub = dealer_final_distribution(new_total, new_soft, hit_soft_17)
        for outcome, sub_p in sub.items():
            distribution[outcome] = distribution.get(outcome, 0.0) + p * sub_p
    return distribution


@lru_cache(maxsize=None)
def dealer_distribution_from_upcard(up_value: int, hit_soft_17: bool) -> DealerOutcome:
    """Distribution du total final du croupier connaissant seulement sa
    carte visible, **au moment où le joueur doit décider**.

    Point important, facile à rater : à cet instant précis, on sait déjà
    que le croupier n'a *pas* de Blackjack naturel — sinon la manche se
    serait terminée avant même que le joueur n'ait à agir. Quand la carte
    visible est un As ou une carte à 10, il faut donc exclure la carte
    cachée qui aurait complété un Blackjack, et renormaliser sur les 12
    valeurs restantes — sans quoi le croupier est artificiellement modélisé
    plus fort qu'il ne l'est réellement à ce point de la manche.
    """
    if up_value not in (10, 11):
        return dealer_final_distribution(up_value, up_value == 11, hit_soft_17)

    excluded_value = 10 if up_value == 11 else 11
    remaining_mass = 1.0 - _CARD_PROB_BY_VALUE[excluded_value]

    distribution: DealerOutcome = {}
    for card_value, p in CARD_PROBS:
        if card_value == excluded_value:
            continue
        weight = p / remaining_mass
        new_total, new_soft, bust = add_card_value(up_value, up_value == 11, card_value)
        if bust:
            distribution[BUST] = distribution.get(BUST, 0.0) + weight
            continue
        sub = dealer_final_distribution(new_total, new_soft, hit_soft_17)
        for outcome, sub_p in sub.items():
            distribution[outcome] = distribution.get(outcome, 0.0) + weight * sub_p
    return distribution
