"""
Module ``solver`` — agent IA n°1 : solveur par recherche/expectiminimax.

Contrairement à une stratégie de base « recopiée » d'un livre (comme
``strategies/basic_strategy.py`` dans ce même projet), ce solveur ne connaît
*aucune* table de décision : il calcule l'espérance de gain (EV) exacte de
chaque action possible en explorant récursivement l'arbre des tirages
futurs, et choisit l'action de plus grande espérance. C'est un
**expectiminimax** à un seul joueur actif : à chaque nœud de décision, on
maximise sur les actions (HIT/STAND/DOUBLE/SPLIT/SURRENDER) ; entre deux
décisions, un nœud de hasard moyenne sur les 13 valeurs de carte possibles
pondérées par leur probabilité (voir ``mdp.py``). La mémoïsation évite de
recalculer un sous-arbre déjà résolu (le nombre d'états atteignables,
(total, soft, carte croupier), est petit — quelques centaines).

Hypothèses et approximations (voir aussi ``mdp.py``) :

* sabot infini (composition-independent) ;
* SPLIT est approximé : chaque main issue du split est traitée comme une
  main indépendante (une carte de la paire + une carte neuve), sans
  ré-autoriser un nouveau split et sans modéliser la corrélation entre les
  deux mains résultantes. C'est l'approximation standard des calculateurs
  d'EV grand public.

Note de portage : ce module vient du projet NFP106 « blackjack-ia », où
``Rules`` vit dans ``core`` ; ici, il vit dans ``game.rules``. L'import n'est
utilisé qu'en type hint (jamais évalué grâce à ``from __future__ import
annotations``) et reste donc sous garde ``TYPE_CHECKING`` pour ne pas créer
de cycle ``ai -> game -> strategies -> ai`` (même précaution que
``players/human_player.py`` pour ``ui.cli.UI``).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Dict

from ..core import Action, Card, Hand
from .dealer_probs import dealer_distribution_from_upcard
from .mdp import CARD_PROBS, add_card_value

if TYPE_CHECKING:  # pragma: no cover
    from ..game.rules import Rules

SURRENDER_EV = -0.5

#: Probabilité qu'une carte tirée soit une carte à 10 (sabot infini — voir
#: mdp.py) : c'est exactement la question que pose l'assurance (le croupier
#: a-t-il un 10 caché sous son As ?).
_P_TEN = dict(CARD_PROBS)[10]

#: Espérance de l'assurance (en unités de la mise d'assurance, payée 2:1) :
#: gagnée (carte à 10 cachée, proba ``_P_TEN``) elle rapporte 2x la mise,
#: perdue elle coûte 1x la mise. Toujours négative sous hypothèse de sabot
#: infini (4/13 ≈ 30,8 % < 1/3) — c'est le résultat classique « ne jamais
#: prendre l'assurance sans compter les cartes ».
INSURANCE_EV = _P_TEN * 2.0 - (1.0 - _P_TEN) * 1.0


@lru_cache(maxsize=None)
def _ev_stand(total: int, dealer_up: int, hit_soft_17: bool) -> float:
    """Espérance (en unités de mise) de rester sur ``total`` sans plus agir."""
    distribution = dealer_distribution_from_upcard(dealer_up, hit_soft_17)
    ev = 0.0
    for outcome, p in distribution.items():
        if outcome == "bust" or outcome < total:
            ev += p * 1.0
        elif outcome == total:
            ev += 0.0
        else:
            ev += p * -1.0
    return ev


@lru_cache(maxsize=None)
def _ev_double(total: int, soft: bool, dealer_up: int, hit_soft_17: bool) -> float:
    """Espérance de doubler : une seule carte tirée, puis arrêt forcé."""
    ev = 0.0
    for card_value, p in CARD_PROBS:
        new_total, _, bust = add_card_value(total, soft, card_value)
        if bust:
            ev += p * -2.0
        else:
            ev += p * 2.0 * _ev_stand(new_total, dealer_up, hit_soft_17)
    return ev


@lru_cache(maxsize=None)
def _best_continuation_value(total: int, soft: bool, dealer_up: int,
                               hit_soft_17: bool) -> float:
    """Valeur de la meilleure suite de jeu (HIT ou STAND) à partir de cet
    état — nœud MAX de l'expectiminimax, sans option de double (déjà
    consommée : le double n'est possible que sur les deux premières
    cartes)."""
    if total > 21:
        return -1.0
    stand_ev = _ev_stand(total, dealer_up, hit_soft_17)
    if total == 21:
        return stand_ev  # 21 = arrêt forcé, rien à maximiser.

    hit_ev = 0.0
    for card_value, p in CARD_PROBS:
        new_total, new_soft, bust = add_card_value(total, soft, card_value)
        if bust:
            hit_ev += p * -1.0
        else:
            hit_ev += p * _best_continuation_value(
                new_total, new_soft, dealer_up, hit_soft_17
            )
    return max(stand_ev, hit_ev)


@lru_cache(maxsize=None)
def _ev_hit(total: int, soft: bool, dealer_up: int, hit_soft_17: bool) -> float:
    """Espérance de tirer une carte puis de continuer à jouer *optimalement*
    (nœud de hasard suivi, à chaque branche, d'un nœud MAX récursif)."""
    ev = 0.0
    for card_value, p in CARD_PROBS:
        new_total, new_soft, bust = add_card_value(total, soft, card_value)
        if bust:
            ev += p * -1.0
        else:
            ev += p * _best_continuation_value(
                new_total, new_soft, dealer_up, hit_soft_17
            )
    return ev


@lru_cache(maxsize=None)
def _ev_split(pair_value: int, is_ace_pair: bool, dealer_up: int,
              hit_soft_17: bool, double_after_split: bool) -> float:
    """Espérance approchée de séparer une paire (voir limitations en tête de
    module) : deux mains indépendantes, chacune démarrant avec une carte de
    la paire plus une carte neuve."""
    ev = 0.0
    for card_value, p in CARD_PROBS:
        if is_ace_pair:
            # Règle standard : une seule carte par As splitté, arrêt forcé.
            new_total, _, bust = add_card_value(11, True, card_value)
            sub_ev = -1.0 if bust else _ev_stand(new_total, dealer_up, hit_soft_17)
        else:
            new_total, new_soft, bust = add_card_value(pair_value, False, card_value)
            if bust:
                sub_ev = -1.0
            elif double_after_split:
                sub_ev = max(
                    _best_continuation_value(new_total, new_soft, dealer_up, hit_soft_17),
                    _ev_double(new_total, new_soft, dealer_up, hit_soft_17),
                )
            else:
                sub_ev = _best_continuation_value(new_total, new_soft, dealer_up, hit_soft_17)
        ev += p * sub_ev
    return 2.0 * ev


@dataclass
class Decision:
    """Résultat d'une consultation du solveur : action recommandée et EV de
    chaque action envisagée — de quoi expliquer le raisonnement."""

    action: Action
    expected_values: Dict[Action, float]


class ExpectiminimaxSolver:
    """Agent IA calculant, par recherche exacte, l'action optimale.

    Contrairement à ``ReinforcementStrategy`` (voir ``rl_agent.py``), rien
    n'est appris à partir de parties simulées : chaque appel recalcule (ou
    relit depuis le cache mémoïsé) l'espérance de chaque action en résolvant
    exactement le sous-arbre de jeu correspondant.
    """

    name = "Solveur (recherche exacte / expectiminimax)"
    description = (
        "Calcule par recherche récursive mémoïsée l'espérance de gain de "
        "chaque action (HIT/STAND/DOUBLE/SPLIT/SURRENDER) sous hypothèse de "
        "sabot infini, et choisit l'action d'espérance maximale. Aucune "
        "table n'est codée en dur : la décision est entièrement dérivée des "
        "règles de la table."
    )

    def __init__(self, rules: "Rules") -> None:
        self.hit_soft_17 = rules.dealer_hits_soft_17
        self.double_after_split = rules.double_after_split
        self.surrender_allowed = rules.surrender_allowed

    # ------------------------------------------------------------------ #
    def evaluate(self, hand: Hand, dealer_up: Card) -> Decision:
        """Calcule l'EV de chaque action disponible et l'action optimale."""
        # ``Rank.points`` code déjà 10 pour V/D/R et 11 pour l'As : la carte
        # visible du croupier porte donc directement sa valeur de référence.
        dealer_val = dealer_up.value
        total, soft = hand.total, hand.is_soft

        evs: Dict[Action, float] = {
            Action.STAND: _ev_stand(total, dealer_val, self.hit_soft_17),
            Action.HIT: _ev_hit(total, soft, dealer_val, self.hit_soft_17),
        }
        if hand.can_double:
            evs[Action.DOUBLE] = _ev_double(total, soft, dealer_val, self.hit_soft_17)
        if hand.can_surrender and self.surrender_allowed:
            evs[Action.SURRENDER] = SURRENDER_EV
        if hand.can_split:
            pair_rank = hand.cards[0].rank
            pair_value = 11 if pair_rank.is_ace else (10 if pair_rank.is_ten_value else pair_rank.points)
            evs[Action.SPLIT] = _ev_split(
                pair_value, pair_rank.is_ace, dealer_val, self.hit_soft_17,
                self.double_after_split,
            )

        best_action = max(evs, key=evs.get)
        return Decision(action=best_action, expected_values=evs)

    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        """Interface compatible avec :class:`~blackjack.strategies.Strategy`."""
        return self.evaluate(hand, dealer_up).action

    def take_insurance(self) -> bool:
        """Faut-il prendre l'assurance ? Calculé, pas deviné (voir
        ``INSURANCE_EV`` ci-dessus) : toujours négative sous hypothèse de
        sabot infini, donc toujours refusée par un agent qui ne compte pas
        les cartes."""
        return INSURANCE_EV > 0
