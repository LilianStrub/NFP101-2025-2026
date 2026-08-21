"""Adapte :class:`~blackjack.ai.solver.ExpectiminimaxSolver` à l'interface
:class:`~.base_strategy.Strategy` attendue par le moteur de jeu (``game/``).

Porté du projet NFP106 « blackjack-ia ». Le constructeur accepte des règles
optionnelles (chargées via ``utils.load_rules()`` si omises) afin de rester
instanciable sans argument, comme l'exige le registre ``STRATEGIES``
(``STRATEGIES[key]()`` — voir ``strategies/__init__.py`` et ``CLAUDE.md``).
Le chargement de ``load_rules`` se fait à l'intérieur de ``__init__`` (import
différé) plutôt qu'en tête de module : ``utils`` importe ``game``, qui importe
``strategies`` (ce module même) — un import en tête de fichier créerait un
cycle. Différer l'import jusqu'à l'appel réel évite le problème, puisqu'à ce
moment tous les paquets sont déjà pleinement chargés.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..ai.solver import Decision, ExpectiminimaxSolver
from ..core import Action, Card, Hand
from .base_strategy import Strategy

if TYPE_CHECKING:  # pragma: no cover
    from ..game.rules import Rules


class SolverStrategy(Strategy):
    """Agent IA n°1 : recherche exacte (voir ``ai/solver.py``)."""

    name = "Solveur (recherche exacte)"
    description = ExpectiminimaxSolver.description

    def __init__(self, rules: Optional["Rules"] = None) -> None:
        super().__init__()
        if rules is None:
            from ..utils import load_rules
            rules = load_rules()
        self._solver = ExpectiminimaxSolver(rules)

    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        return self._solver.recommend(hand, dealer_up)

    def explain(self, hand: Hand, dealer_up: Card) -> Decision:
        """Renvoie le détail des EV par action (utile pour une future UI
        d'explication de la décision)."""
        return self._solver.evaluate(hand, dealer_up)

    def take_insurance(self) -> bool:
        return self._solver.take_insurance()
