"""
Module ``hand`` — représentation d'une main de Blackjack.

Le calcul du total tient compte de la spécificité de l'As (1 ou 11). On parle
de main « soft » lorsqu'au moins un As compte pour 11, et de main « hard »
sinon. Cette distinction est fondamentale pour la stratégie de base.
"""

from __future__ import annotations

from typing import List, Optional

from .card import Card


class Hand:
    """Main d'un joueur ou du croupier.

    Attributs publics et privés illustrent l'encapsulation : la mise et les
    cartes sont protégées et exposées via des propriétés et des méthodes.
    """

    def __init__(self, bet: float = 0.0) -> None:
        self.__cards: List[Card] = []
        self.__bet: float = float(bet)
        self.__doubled: bool = False
        self.__surrendered: bool = False
        self.__stood: bool = False  # Le joueur a-t-il dit « rester » ?
        # Issue d'un split : permet d'appliquer les règles spécifiques
        # (pas de Blackjack naturel sur une main splittée, pas de re-split d'As…)
        self.__from_split: bool = False

    # ------------------------------------------------------------------ #
    # Accesseurs / mutateurs (encapsulation par propriétés)
    # ------------------------------------------------------------------ #
    @property
    def cards(self) -> List[Card]:
        # On renvoie une copie pour empêcher la modification externe.
        return list(self.__cards)

    @property
    def bet(self) -> float:
        return self.__bet

    @bet.setter
    def bet(self, value: float) -> None:
        if value < 0:
            raise ValueError("La mise ne peut pas être négative")
        self.__bet = float(value)

    @property
    def doubled(self) -> bool:
        return self.__doubled

    @property
    def surrendered(self) -> bool:
        return self.__surrendered

    @property
    def stood(self) -> bool:
        return self.__stood

    @property
    def from_split(self) -> bool:
        return self.__from_split

    @from_split.setter
    def from_split(self, value: bool) -> None:
        self.__from_split = bool(value)

    # ------------------------------------------------------------------ #
    # Actions sur la main
    # ------------------------------------------------------------------ #
    def add_card(self, card: Card) -> None:
        self.__cards.append(card)

    def remove_last_card(self) -> Card:
        """Retire la dernière carte (utile pour gérer un split)."""
        return self.__cards.pop()

    def stand(self) -> None:
        self.__stood = True

    def double(self) -> None:
        self.__doubled = True
        self.__bet *= 2
        self.__stood = True  # Après un double on ne tire plus.

    def surrender(self) -> None:
        self.__surrendered = True
        self.__stood = True

    # ------------------------------------------------------------------ #
    # Calculs spécifiques au Blackjack
    # ------------------------------------------------------------------ #
    @property
    def total(self) -> int:
        """Meilleur total possible <= 21 (sinon la valeur la plus basse)."""
        total = sum(c.value for c in self.__cards)
        # Chaque As compté à 11 peut être ramené à 1 (=> -10).
        aces = sum(1 for c in self.__cards if c.is_ace)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    @property
    def is_soft(self) -> bool:
        """True s'il existe un As compté comme 11 dans le total courant."""
        total = sum(c.value for c in self.__cards)
        aces = sum(1 for c in self.__cards if c.is_ace)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        # Si au moins un As compte encore comme 11, la main est « soft ».
        return aces > 0 and total <= 21 and any(c.is_ace for c in self.__cards)

    @property
    def is_blackjack(self) -> bool:
        """Vrai As + 10 sur les deux premières cartes (hors split)."""
        return (
            not self.__from_split
            and len(self.__cards) == 2
            and self.total == 21
        )

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    @property
    def is_pair(self) -> bool:
        """Vrai si la main contient deux cartes splittables.

        Deux cartes de même rang forment toujours une paire. En règle française
        les cartes de valeur 10 (10, V, D, R) sont considérées équivalentes et
        peuvent donc être splittées même si leurs rangs diffèrent.
        """
        if len(self.__cards) != 2:
            return False
        c1, c2 = self.__cards
        return c1.rank is c2.rank or (c1.value == 10 and c2.value == 10)

    @property
    def can_double(self) -> bool:
        return len(self.__cards) == 2 and not self.__doubled

    @property
    def can_split(self) -> bool:
        return self.is_pair and not self.__doubled

    @property
    def can_surrender(self) -> bool:
        """Le surrender n'est autorisé que sur les 2 premières cartes."""
        return len(self.__cards) == 2 and not self.__doubled

    @property
    def is_done(self) -> bool:
        """La main ne peut plus être jouée."""
        return self.is_bust or self.__stood or self.__surrendered or self.total == 21

    # ------------------------------------------------------------------ #
    # Représentation
    # ------------------------------------------------------------------ #
    def describe(self, hide_first: bool = False) -> str:
        """Description lisible. ``hide_first`` masque la 1re carte (croupier)."""
        if not self.__cards:
            return "(vide)"
        if hide_first:
            shown = ["??"] + [str(c) for c in self.__cards[1:]]
            return " ".join(shown)
        return " ".join(str(c) for c in self.__cards) + f"  ({self.total})"

    def __str__(self) -> str:
        return self.describe()

    def __repr__(self) -> str:
        return f"Hand(cards={self.__cards!r}, total={self.total}, bet={self.__bet})"

    def __len__(self) -> int:
        return len(self.__cards)
