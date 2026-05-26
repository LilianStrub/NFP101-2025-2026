"""
Module ``card`` — classe :class:`Card`.

Démonstration des concepts d'encapsulation (attributs privés ``__rank`` /
``__suit`` accessibles uniquement via des propriétés) et de surcharge
d'opérateurs (``__eq__``, ``__hash__``, ``__repr__``, ``__str__``).
"""

from __future__ import annotations

from .enums import Rank, Suit


class Card:
    """Représente une carte à jouer.

    Une carte est immuable : une fois construite, son rang et son enseigne
    ne peuvent plus changer. Cela évite des bugs subtils lorsqu'une même
    carte transite entre la pioche, la main du joueur et la défausse.
    """

    __slots__ = ("__rank", "__suit")

    def __init__(self, rank: Rank, suit: Suit) -> None:
        if not isinstance(rank, Rank):
            raise TypeError(f"rank doit être un Rank, reçu {type(rank).__name__}")
        if not isinstance(suit, Suit):
            raise TypeError(f"suit doit être un Suit, reçu {type(suit).__name__}")
        # Encapsulation : double underscore => name-mangling.
        self.__rank = rank
        self.__suit = suit

    # ------------------------------------------------------------------ #
    # Propriétés (accesseurs en lecture seule)
    # ------------------------------------------------------------------ #
    @property
    def rank(self) -> Rank:
        return self.__rank

    @property
    def suit(self) -> Suit:
        return self.__suit

    @property
    def value(self) -> int:
        """Valeur faciale de la carte (11 pour l'As)."""
        return self.__rank.points

    @property
    def is_ace(self) -> bool:
        return self.__rank.is_ace

    @property
    def is_ten_value(self) -> bool:
        return self.__rank.is_ten_value

    # ------------------------------------------------------------------ #
    # Représentation et égalité
    # ------------------------------------------------------------------ #
    def __str__(self) -> str:
        return f"{self.__rank.label}{self.__suit.symbol}"

    def __repr__(self) -> str:
        return f"Card({self.__rank.name}, {self.__suit.name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.__rank is other.__rank and self.__suit is other.__suit

    def __hash__(self) -> int:
        return hash((self.__rank, self.__suit))
