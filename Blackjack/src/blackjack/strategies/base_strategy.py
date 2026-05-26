"""
Module ``base_strategy`` — interface commune à toutes les stratégies.

Toutes les stratégies (de base, Hi-Lo, KO, Hi-Opt I/II, Omega II, Zen, Red 7)
héritent de :class:`Strategy`. C'est l'illustration directe du polymorphisme
enseigné en cours : le moteur du jeu manipule des ``Strategy`` sans rien
savoir de leur implémentation concrète.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..core import Action, Card, Hand


class Strategy(ABC):
    """Classe mère abstraite pour toute stratégie d'aide à la décision."""

    #: Nom court (affichage menu).
    name: str = "Stratégie"
    #: Description longue (affichage détaillé).
    description: str = ""
    #: True si la stratégie tient un comptage de cartes.
    counts_cards: bool = False

    def __init__(self) -> None:
        self._running_count: int = 0

    # ------------------------------------------------------------------ #
    # Comptage de cartes (polymorphisme : surchargé par les sous-classes)
    # ------------------------------------------------------------------ #
    @property
    def running_count(self) -> int:
        """Compte courant (running count) — 0 si la stratégie ne compte pas."""
        return self._running_count

    def reset_count(self) -> None:
        self._running_count = 0

    def observe(self, card: Card) -> None:
        """Notifie la stratégie qu'une carte vient d'être révélée.

        Implémentation par défaut : ne rien faire (utile pour la stratégie
        de base qui n'a pas besoin de compter).
        """
        if self.counts_cards:
            self._running_count += self.card_value(card)

    def observe_many(self, cards: List[Card]) -> None:
        for c in cards:
            self.observe(c)

    def card_value(self, card: Card) -> int:  # noqa: ARG002 — surchargé.
        """Valeur attribuée à une carte dans le comptage. À surcharger."""
        return 0

    def true_count(self, decks_remaining: float) -> float:
        """Conversion du running count en true count (par pondération)."""
        if decks_remaining <= 0:
            return 0.0
        return self._running_count / decks_remaining

    # ------------------------------------------------------------------ #
    # Décision principale (polymorphisme : à implémenter)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        """Recommande l'action optimale selon la stratégie.

        :param hand:        Main du joueur.
        :param dealer_up:   Carte visible du croupier.
        :return:            L'action conseillée.
        """

    # ------------------------------------------------------------------ #
    # Conseil de mise (pour les comptages — par défaut : mise minimale)
    # ------------------------------------------------------------------ #
    def betting_units(self, decks_remaining: float, min_bet: float,
                       max_bet: float) -> float:
        """Renvoie une mise conseillée d'après le true count.

        Implémentation par défaut : mise minimale (utilisée par les
        stratégies non-comptantes).
        """
        return min_bet

    # ------------------------------------------------------------------ #
    # Représentation
    # ------------------------------------------------------------------ #
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<{type(self).__name__} count={self._running_count}>"
