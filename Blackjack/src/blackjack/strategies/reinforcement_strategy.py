"""Adapte :class:`~blackjack.ai.rl_agent.QLearningAgent` à l'interface
:class:`~.base_strategy.Strategy` attendue par le moteur de jeu (``game/``).

Porté du projet NFP106 « blackjack-ia », avec sa Q-table pré-entraînée
(3 000 000 d'épisodes, voir ``data/q_table.json``). Comme
:class:`~.solver_strategy.SolverStrategy`, le constructeur accepte des règles
optionnelles et reste instanciable sans argument pour respecter la
convention du registre ``STRATEGIES`` (``STRATEGIES[key]()``) ; voir ce
module pour le détail de l'import différé qui évite un cycle avec ``game``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..ai.rl_agent import QLearningAgent
from ..core import Action, Card, Hand
from .base_strategy import Strategy

if TYPE_CHECKING:  # pragma: no cover
    from ..game.rules import Rules

#: Q-table pré-entraînée, livrée avec le projet (voir data/q_table.json).
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
Q_TABLE_PATH = DATA_DIR / "q_table.json"


class ReinforcementStrategy(Strategy):
    """Agent IA n°2 : apprentissage par renforcement (voir ``ai/rl_agent.py``).

    Charge par défaut la Q-table pré-entraînée livrée avec le projet
    (``data/q_table.json``). Utiliser :meth:`from_file` pour recharger une
    autre Q-table (par ex. ré-entraînée via ``scripts/train_rl.py``).
    """

    name = "Agent par renforcement (Q-learning)"
    description = QLearningAgent.description

    def __init__(self, rules: Optional["Rules"] = None, *, path: Path = Q_TABLE_PATH) -> None:
        super().__init__()
        if rules is None:
            from ..utils import load_rules
            rules = load_rules()
        self._agent = QLearningAgent.load(path, rules)

    @classmethod
    def from_file(cls, path: Path, rules: "Rules") -> "ReinforcementStrategy":
        return cls(rules, path=path)

    @property
    def trained_episodes(self) -> int:
        return self._agent.trained_episodes

    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        return self._agent.recommend(hand, dealer_up)
