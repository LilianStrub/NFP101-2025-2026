"""
Module ``human_player`` — le joueur humain.

Le ``HumanPlayer`` délègue la décision à un objet ``UI`` (séparation des
responsabilités : la classe Joueur ne sait pas comment afficher quoi que ce
soit). Cela permet de remplacer la CLI par une interface graphique sans
toucher au reste du code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..core import Action, Card, Hand
from ..strategies import Strategy
from .base_player import BasePlayer

if TYPE_CHECKING:  # pragma: no cover
    from ..ui.cli import UI  # boucle d'imports si on importait directement.


class HumanPlayer(BasePlayer):
    """Joueur humain interagissant via une UI."""

    def __init__(self, name: str, bankroll: float = 100.0,
                 strategy: Optional[Strategy] = None) -> None:
        super().__init__(name, bankroll)
        self.strategy: Optional[Strategy] = strategy
        self.show_advice: bool = strategy is not None and not strategy.__class__.__name__.startswith("Manual")
        self.ui: "Optional[UI]" = None  # injecté après création.

    def decide(self, hand: Hand, dealer_up: Card, rules=None,
               hand_index: int = 0) -> Action:
        if self.ui is None:
            raise RuntimeError(
                "Aucune UI n'a été attachée au joueur — impossible de décider"
            )
        advice = None
        if self.show_advice and self.strategy is not None:
            advice = self.strategy.recommend(hand, dealer_up)
        return self.ui.prompt_action(self, hand, dealer_up, advice=advice,
                                     rules=rules, hand_index=hand_index)
