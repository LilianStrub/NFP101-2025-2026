"""
Module ``deck`` — gestion du sabot.

Un sabot (``Shoe``) contient *n* paquets de 52 cartes. La méthode
:py:meth:`Shoe.draw` retire la carte du dessus. Lorsque la « carte de coupe »
(penetration) est atteinte, le sabot est mélangé au début de la main
suivante — comme dans les casinos réels.
"""

from __future__ import annotations

import random
from typing import Iterator, List, Optional

from .card import Card
from .enums import Rank, Suit


class Shoe:
    """Sabot composé d'un ou plusieurs jeux de 52 cartes."""

    def __init__(self, num_decks: int = 6, penetration: float = 0.75,
                 seed: Optional[int] = None) -> None:
        if num_decks < 1:
            raise ValueError("num_decks doit être >= 1")
        if not 0.1 <= penetration <= 1.0:
            raise ValueError("penetration doit être dans ]0.1 ; 1.0]")
        self.__num_decks = num_decks
        self.__penetration = penetration
        self.__rng = random.Random(seed)
        self.__cards: List[Card] = []
        self.__discard: List[Card] = []
        self.__needs_shuffle = True  # Force le mélange au premier tirage.

    # ------------------------------------------------------------------ #
    # Propriétés
    # ------------------------------------------------------------------ #
    @property
    def num_decks(self) -> int:
        return self.__num_decks

    @property
    def cards_remaining(self) -> int:
        return len(self.__cards)

    @property
    def decks_remaining(self) -> float:
        """Estimation flottante du nombre de jeux restants (utile pour le true count)."""
        return self.cards_remaining / 52.0

    @property
    def needs_shuffle(self) -> bool:
        """Indique si le sabot doit être remélangé avant la prochaine donne."""
        return self.__needs_shuffle

    # ------------------------------------------------------------------ #
    # Mécanique du sabot
    # ------------------------------------------------------------------ #
    def shuffle(self) -> None:
        """Reconstruit le sabot complet et le mélange."""
        self.__cards = [
            Card(rank, suit)
            for _ in range(self.__num_decks)
            for suit in Suit
            for rank in Rank
        ]
        self.__rng.shuffle(self.__cards)
        self.__discard.clear()
        self.__needs_shuffle = False

    def burn(self) -> Optional[Card]:
        """Brûle (défausse) la carte du dessus, comme au casino.

        La carte est écartée sans être jouée ni révélée — elle n'est donc
        pas observée par les compteurs. Renvoie ``None`` si le sabot est vide.
        """
        if not self.__cards:
            return None
        card = self.__cards.pop()
        self.__discard.append(card)
        return card

    def draw(self) -> Card:
        """Tire la carte du dessus du sabot.

        Le remélange dû à la carte de coupe est géré en début de manche par
        ``Game`` (jamais en plein milieu d'une main) : ici on ne remélange
        qu'en dernier recours, si le sabot est réellement vide.
        """
        if not self.__cards:
            self.shuffle()
        card = self.__cards.pop()
        self.__discard.append(card)
        # Carte de coupe : si la pénétration est dépassée, on signalera un
        # mélange au début du prochain coup (jamais en plein milieu d'une main).
        total = 52 * self.__num_decks
        if (total - len(self.__cards)) / total >= self.__penetration:
            self.__needs_shuffle = True
        return card

    # ------------------------------------------------------------------ #
    # Itérabilité (utile pour les tests)
    # ------------------------------------------------------------------ #
    def __iter__(self) -> Iterator[Card]:
        return iter(self.__cards)

    def __len__(self) -> int:
        return len(self.__cards)

    def __repr__(self) -> str:
        return (f"Shoe(num_decks={self.__num_decks}, "
                f"remaining={self.cards_remaining})")
