"""
Paquet ``ai`` — deux agents IA jouant au Blackjack par deux voies
radicalement différentes. Porté depuis le projet NFP106 « blackjack-ia »
(Intelligence Artificielle Libre, CNAM) où ils ont été développés et évalués,
pour venir compléter — sans y toucher — l'interface de jeu animée existante
de ce projet (voir ``strategies/solver_strategy.py`` et
``strategies/reinforcement_strategy.py`` pour le branchement).

Ce paquet ne dépend que de ``core`` (cartes, main) — ni du moteur de jeu
(``game/``), ni des joueurs (``players/``) : il reste ainsi autonome et
testable isolément.

- :mod:`.mdp`            — modèle de transition partagé (sabot infini).
- :mod:`.dealer_probs`   — distribution exacte du total final du croupier.
- :mod:`.solver`         — agent n°1 : recherche exacte (expectiminimax mémoïsé).
- :mod:`.rl_agent`       — agent n°2 : apprentissage par renforcement (Q-learning).
"""

from .dealer_probs import dealer_distribution_from_upcard
from .rl_agent import QLearningAgent
from .solver import Decision, ExpectiminimaxSolver

__all__ = [
    "ExpectiminimaxSolver",
    "Decision",
    "QLearningAgent",
    "dealer_distribution_from_upcard",
]
