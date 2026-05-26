"""
Module ``base_player`` — classe mère de tous les joueurs.

Encapsulation : le solde (bankroll) et le nom sont protégés. Le polymorphisme
intervient sur :meth:`play_hand` que ``Dealer`` et ``HumanPlayer`` implémentent
différemment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..core import Action, Hand


class BasePlayer(ABC):
    """Classe abstraite : un participant assis à la table."""

    def __init__(self, name: str, bankroll: float = 0.0) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("name doit être une chaîne non vide")
        self.__name = name
        self.__bankroll = float(bankroll)
        self._hands: List[Hand] = []

    # ------------------------------------------------------------------ #
    # Encapsulation : propriétés
    # ------------------------------------------------------------------ #
    @property
    def name(self) -> str:
        return self.__name

    @property
    def bankroll(self) -> float:
        return self.__bankroll

    @property
    def hands(self) -> List[Hand]:
        return list(self._hands)

    # ------------------------------------------------------------------ #
    # Mutateurs contrôlés
    # ------------------------------------------------------------------ #
    def credit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Impossible de créditer un montant négatif")
        self.__bankroll += amount

    def debit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Impossible de débiter un montant négatif")
        if amount > self.__bankroll:
            raise ValueError("Solde insuffisant")
        self.__bankroll -= amount

    def reset_hands(self) -> None:
        self._hands.clear()

    def add_hand(self, hand: Hand) -> None:
        self._hands.append(hand)

    # ------------------------------------------------------------------ #
    # Comportement (polymorphisme : à implémenter)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def decide(self, hand: Hand, dealer_up) -> Action:  # noqa: ANN001
        """Décide de l'action à effectuer sur la main donnée."""

    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.__name!r}, bankroll={self.__bankroll})"
