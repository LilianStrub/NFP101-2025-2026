"""
Module ``dealer`` — le croupier (la banque).

Le croupier suit des règles fixes (pas de choix stratégique). En règle S17
(« stand on soft 17 »), il s'arrête dès que son total atteint 17, y compris
quand cet 17 contient un As compté 11.
"""

from __future__ import annotations

from ..core import Action, Card, Hand
from .base_player import BasePlayer


class Dealer(BasePlayer):
    """Le croupier, joueur automatique."""

    def __init__(self, name: str = "Croupier", hit_soft_17: bool = False) -> None:
        # Le croupier n'a pas vraiment de bankroll dans notre modèle.
        super().__init__(name, bankroll=0.0)
        self.hit_soft_17 = hit_soft_17

    @property
    def hand(self) -> Hand:
        """Le croupier n'a toujours qu'une seule main."""
        if not self._hands:
            self._hands.append(Hand())
        return self._hands[0]

    @property
    def up_card(self) -> Card:
        """Carte visible du croupier.

        En mode américain (hole card) : la 2e carte (la 1re est cachée).
        En mode ENHC : la 1re (et seule) carte pendant le tour du joueur.
        Dans les deux cas, cards[0] suffit quand le croupier n'a qu'une carte.
        """
        cards = self.hand.cards
        if not cards:
            raise RuntimeError("Le croupier n'a pas encore de carte")
        if len(cards) == 1:
            # ENHC : la seule carte est la carte visible.
            return cards[0]
        # Américain : la 1re carte est la hole card, la 2e est la carte visible.
        return cards[1]

    @property
    def hole_card(self) -> Card:
        """Carte cachée (la première donnée, mode américain uniquement)."""
        cards = self.hand.cards
        if not cards:
            raise RuntimeError("Le croupier n'a pas encore de carte cachée")
        return cards[0]

    # ------------------------------------------------------------------ #
    # Décision : règle fixe
    # ------------------------------------------------------------------ #
    def decide(self, hand: Hand, dealer_up: Card) -> Action:  # noqa: ARG002
        total = hand.total
        if total < 17:
            return Action.HIT
        if total == 17 and hand.is_soft and self.hit_soft_17:
            return Action.HIT  # règle « H17 »
        return Action.STAND
