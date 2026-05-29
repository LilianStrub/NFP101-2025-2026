"""
Module ``rules`` — règles paramétrables de la table.

Encapsule l'ensemble des paramètres modifiables d'une partie de Blackjack.
Permet de tester différentes configurations sans toucher au moteur de jeu.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rules:
    """Configuration d'une table de Blackjack."""

    num_decks: int = 6
    """Nombre de jeux dans le sabot (typiquement 4 à 8)."""

    penetration: float = 0.75
    """Profondeur de jeu avant remélange (0.75 = ~25 % du sabot non joué)."""

    blackjack_payout: float = 1.5
    """Multiplicateur du gain pour un blackjack (3:2 = 1.5, 6:5 = 1.2)."""

    dealer_hits_soft_17: bool = False
    """True si le croupier tire sur 17 soft (« H17 »), False = S17."""

    double_after_split: bool = True
    """DAS — autorise de doubler après un split."""

    surrender_allowed: bool = True
    """Late surrender autorisé sur les deux premières cartes."""

    resplit_aces: bool = False
    """True si l'on peut re-split une paire d'As."""

    max_splits: int = 3
    """Nombre maximal de splits par main (3 splits = 4 mains finales)."""

    min_bet: float = 1.0
    max_bet: float = 500.0
    starting_bankroll: float = 100.0

    no_hole_card: bool = True
    """True = règle ENHC (casinos européens/français) : le croupier ne prend
    pas de carte cachée ; sa 2e carte est tirée après le tour du joueur."""

    original_bets_only: bool = True
    """OBO — en ENHC, si le croupier fait Blackjack, le joueur ne perd que sa
    mise d'origine ; la portion ajoutée par un double lui est rendue."""

    insurance_allowed: bool = True
    """Proposer l'assurance quand le croupier montre un As."""

    double_hard_9_to_11_only: bool = True
    """Restreindre le double aux totaux durs 9, 10 et 11 (règle française)."""

    def __post_init__(self) -> None:
        if self.num_decks < 1:
            raise ValueError("num_decks doit être >= 1")
        if not 0.1 <= self.penetration <= 1.0:
            raise ValueError("penetration doit être dans ]0.1 ; 1.0]")
        if self.blackjack_payout <= 0:
            raise ValueError("blackjack_payout doit être > 0")
        if self.min_bet <= 0 or self.max_bet < self.min_bet:
            raise ValueError("min_bet et max_bet incohérents")
