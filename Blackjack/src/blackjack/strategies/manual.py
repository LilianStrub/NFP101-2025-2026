"""
Stratégie ``Manual`` — pas d'aide à la décision.

Sert de valeur par défaut : le joueur joue sans assistance. La méthode
:py:meth:`recommend` n'est jamais utilisée par le moteur car l'option
« aide » est désactivée, mais elle reste implémentée par contrat pour
respecter le polymorphisme.
"""

from __future__ import annotations

from ..core import Action, Card, Hand
from .base_strategy import Strategy


class ManualStrategy(Strategy):
    """Stratégie nulle : « débrouille-toi tout seul »."""

    name = "Manuelle (aucune aide)"
    description = (
        "Aucune assistance n'est affichée. Le joueur prend ses propres décisions, "
        "sans suggestion ni comptage."
    )
    counts_cards = False

    def recommend(self, hand: Hand, dealer_up: Card) -> Action:  # noqa: ARG002
        # Par convention on renvoie STAND. Cette valeur n'est jamais
        # affichée au joueur en mode manuel.
        return Action.STAND
