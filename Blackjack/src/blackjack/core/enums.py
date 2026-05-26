"""
Énumérations centrales du jeu.

Utilise le module ``enum`` de la bibliothèque standard pour offrir des
constantes typées, lisibles et impossibles à confondre avec des chaînes
arbitraires.
"""

from __future__ import annotations

from enum import Enum, IntEnum


class Suit(Enum):
    """Les quatre couleurs (enseignes) d'un jeu de 52 cartes."""

    HEARTS = ("Cœur", "♥", "rouge")
    DIAMONDS = ("Carreau", "♦", "rouge")
    CLUBS = ("Trèfle", "♣", "noir")
    SPADES = ("Pique", "♠", "noir")

    def __init__(self, label: str, symbol: str, color: str) -> None:
        self.label = label
        self.symbol = symbol
        self.color = color  # "rouge" ou "noir" — utile pour le Red 7 Count.

    @property
    def is_red(self) -> bool:
        """True si l'enseigne est rouge (cœur ou carreau)."""
        return self.color == "rouge"

    def __str__(self) -> str:
        return self.symbol


class Rank(Enum):
    """Les treize rangs d'un jeu de cartes classique."""

    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("V", 10)
    QUEEN = ("D", 10)
    KING = ("R", 10)
    ACE = ("A", 11)  # Au Blackjack l'As vaut 11 ou 1.

    def __init__(self, label: str, points: int) -> None:
        # « value » étant réservé par enum.Enum, on expose la valeur
        # numérique de la carte via l'attribut ``points``.
        self.label = label
        self.points = points

    @property
    def is_ace(self) -> bool:
        return self is Rank.ACE

    @property
    def is_face(self) -> bool:
        """Vrai pour Valet, Dame, Roi (figures)."""
        return self in (Rank.JACK, Rank.QUEEN, Rank.KING)

    @property
    def is_ten_value(self) -> bool:
        """Vrai si la carte vaut 10 (10, V, D, R)."""
        return self.points == 10

    def __str__(self) -> str:
        return self.label


class Action(IntEnum):
    """Décisions possibles pour un joueur de Blackjack."""

    HIT = 1        # Tirer
    STAND = 2      # Rester
    DOUBLE = 3     # Doubler la mise puis tirer une seule carte
    SPLIT = 4      # Séparer une paire en deux mains
    SURRENDER = 5  # Abandonner et récupérer la moitié de la mise

    @property
    def label(self) -> str:
        return {
            Action.HIT: "Tirer",
            Action.STAND: "Rester",
            Action.DOUBLE: "Doubler",
            Action.SPLIT: "Séparer",
            Action.SURRENDER: "Abandonner",
        }[self]

    @property
    def short(self) -> str:
        """Code court utilisé dans les tableaux de stratégie."""
        return {
            Action.HIT: "H",
            Action.STAND: "S",
            Action.DOUBLE: "D",
            Action.SPLIT: "P",          # P comme « Pair split »
            Action.SURRENDER: "R",      # R comme « Rendition »
        }[self]


class Outcome(Enum):
    """Résultat d'une main pour le joueur (par rapport au croupier)."""

    BLACKJACK = "Blackjack !"
    WIN = "Gagné"
    PUSH = "Égalité"
    LOSS = "Perdu"
    SURRENDER = "Abandon"
    BUST = "Brûlé"
