"""
Module ``rl_agent`` — agent IA n°2 : apprentissage par renforcement (Q-learning).

Contrairement au solveur (``solver.py``), qui *calcule* l'espérance exacte
de chaque action par recherche récursive, cet agent l'*apprend* par
essais/erreurs, en appliquant l'algorithme **Q-learning** : le Blackjack y
est formalisé comme un **MDP** (états, actions, récompenses), et la table
Q(état, action) y est mise à jour selon la règle temporal-difference :

    Q(s, a) <- Q(s, a) + alpha * [ r + gamma * max_a' Q(s', a') - Q(s, a) ]

où ``alpha`` est le taux d'apprentissage, ``gamma`` le facteur d'actualisation
(1.0 ici : tâche épisodique non actualisée, cohérent avec un gain qui ne se
réalise qu'à la fin de la main) et ``max_a' Q(s', a')`` le meilleur Q connu de
l'état suivant — c'est la caractéristique *off-policy* du Q-learning : on
amorce (« bootstrap ») sur la meilleure action possible, pas sur celle
réellement tirée par la politique d'exploration.

Aucune table de stratégie n'est fournie a priori : au départ, l'agent ne
sait littéralement rien jouer (Q-table vide, politique aléatoire). Toute sa
compétence de jeu émerge des parties simulées pendant l'entraînement
(``train()``).

Espace d'actions appris : HIT / STAND / DOUBLE (sur les deux premières
cartes uniquement). SPLIT et SURRENDER ne sont pas appris — décisions plus
rares, combinatoirement plus complexes à intégrer au même espace d'états ;
l'agent délègue alors au solveur exact (voir ``recommend()``).

Note de portage : voir l'en-tête de ``solver.py`` au sujet de l'import
``Rules`` sous garde ``TYPE_CHECKING`` (évite un cycle d'import avec
``game``/``strategies``).
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

from ..core import Action, Card, Hand
from .mdp import CARD_PROBS, add_card_value
from .solver import Decision, ExpectiminimaxSolver

if TYPE_CHECKING:  # pragma: no cover
    from ..game.rules import Rules

State = Tuple[int, bool, int]  # (total du joueur, main soft ?, carte visible croupier)


def _sample_card_value(rng: random.Random) -> int:
    """Tire une valeur de carte selon la distribution ``CARD_PROBS``
    (hypothèse de sabot infini, cohérente avec le solveur — voir ``mdp.py``,
    ce qui rend la comparaison agent-appris / agent-calculé équitable)."""
    r = rng.random()
    cumulative = 0.0
    for value, p in CARD_PROBS:
        cumulative += p
        if r <= cumulative:
            return value
    return CARD_PROBS[-1][0]  # filet de sécurité contre les arrondis flottants


def _play_dealer(up_value: int, hit_soft_17: bool, rng: random.Random) -> int:
    """Simule le tour du croupier (règle fixe) ; renvoie son total final
    (> 21 signifie qu'il a brûlé).

    Quand la carte visible est un As ou une carte à 10, on exclut donc, sur
    le premier tirage seulement, la valeur qui compléterait un Blackjack
    (par rejet) — sans quoi le croupier serait entraîné/évalué comme
    artificiellement plus fort qu'il ne l'est réellement à ce point de la
    manche (voir la même correction, plus détaillée, dans
    ``dealer_probs.dealer_distribution_from_upcard``)."""
    total, soft = up_value, up_value == 11
    excluded = 10 if up_value == 11 else (11 if up_value == 10 else None)
    while total < 17 or (total == 17 and soft and hit_soft_17):
        card = _sample_card_value(rng)
        if excluded is not None:
            while card == excluded:
                card = _sample_card_value(rng)
            excluded = None  # ne s'applique qu'au tout premier tirage.
        total, soft, bust = add_card_value(total, soft, card)
        if bust:
            return total
    return total


def _settle(player_total: int, dealer_total: int, unit: float) -> float:
    """Gain net en unités de mise (``unit`` = 2.0 après un double, sinon 1.0)."""
    if dealer_total > 21 or player_total > dealer_total:
        return unit
    if player_total == dealer_total:
        return 0.0
    return -unit


@dataclass
class TrainingCurve:
    """Historique de la courbe d'apprentissage (récompense moyenne par
    fenêtre d'épisodes)."""

    episodes: List[int] = field(default_factory=list)
    average_reward: List[float] = field(default_factory=list)


class QLearningAgent:
    """Agent IA apprenant à jouer par renforcement (Q-learning, off-policy,
    politique d'exploration epsilon-greedy)."""

    name = "Agent par renforcement (Q-learning)"
    description = (
        "Apprend à jouer par essais/erreurs : simule des centaines de "
        "milliers de mains, explore selon une politique epsilon-greedy, et "
        "met à jour Q(état, action) par différence temporelle (Q-learning). "
        "Aucune table de stratégie n'est fournie a priori."
    )

    def __init__(self, rules: "Rules", seed: int = 42, gamma: float = 1.0) -> None:
        self.hit_soft_17 = rules.dealer_hits_soft_17
        self.gamma = gamma
        self._rng = random.Random(seed)
        self._q: Dict[State, Dict[Action, float]] = {}
        # SPLIT / SURRENDER : hors du champ appris, délégués au solveur.
        self._fallback = ExpectiminimaxSolver(rules)
        self.trained_episodes = 0
        self.curve = TrainingCurve()

    @property
    def known_states(self) -> int:
        """Nombre d'états (total, soft, carte croupier) déjà rencontrés à
        l'entraînement — indicateur de couverture de la Q-table."""
        return len(self._q)

    # ------------------------------------------------------------------ #
    # Entraînement
    # ------------------------------------------------------------------ #
    def train(self, episodes: int, *,
              epsilon_start: float = 1.0, epsilon_end: float = 0.05,
              epsilon_decay_episodes: Optional[int] = None,
              alpha_start: float = 0.10, alpha_end: float = 0.01,
              checkpoint_every: int = 5000,
              on_checkpoint: Optional[Callable[[int, float], None]] = None) -> None:
        """Entraîne l'agent sur ``episodes`` mains simulées en auto-jeu.

        ``epsilon`` (exploration) et ``alpha`` (taux d'apprentissage)
        décroissent tous deux linéairement, comme il est d'usage en
        Q-learning : on explore beaucoup et on apprend vite au début, puis
        on se stabilise progressivement sur la politique apprise.
        """
        decay_span = epsilon_decay_episodes or episodes
        reward_window: List[float] = []

        for ep in range(1, episodes + 1):
            epsilon = self._decay(ep, epsilon_start, epsilon_end, decay_span)
            alpha = self._decay(ep, alpha_start, alpha_end, decay_span)
            reward = self._train_one_episode(epsilon, alpha)

            reward_window.append(reward)
            self.trained_episodes += 1
            if ep % checkpoint_every == 0 or ep == episodes:
                avg = sum(reward_window) / len(reward_window)
                self.curve.episodes.append(ep)
                self.curve.average_reward.append(avg)
                reward_window = []
                if on_checkpoint is not None:
                    on_checkpoint(ep, avg)

    @staticmethod
    def _decay(ep: int, start: float, end: float, span: int) -> float:
        if ep >= span:
            return end
        return start + (end - start) * (ep / span)

    def _train_one_episode(self, epsilon: float, alpha: float) -> float:
        """Joue une main complète en auto-jeu, en appliquant la mise à jour
        Q-learning à chaque décision, et renvoie le gain net de la main.

        Simplification assumée : paiement 1:1 partout, y compris sur un
        Blackjack naturel (pas de bonus 3:2) et pas d'assurance — l'objectif
        de cette boucle est d'apprendre la politique HIT/STAND/DOUBLE, pas
        de reproduire la comptabilité d'une vraie table.
        """
        rng = self._rng
        total, soft, _ = add_card_value(0, False, _sample_card_value(rng))
        total, soft, _ = add_card_value(total, soft, _sample_card_value(rng))
        dealer_up = _sample_card_value(rng)

        if total == 21:
            # Blackjack naturel : aucune décision à prendre, rien à mettre à jour.
            dealer_total = _play_dealer(dealer_up, self.hit_soft_17, rng)
            return _settle(total, dealer_total, unit=1.0)

        first_decision = True
        while True:
            state = (total, soft, dealer_up)
            available = [Action.STAND, Action.HIT]
            if first_decision:
                available.append(Action.DOUBLE)
            action = self._epsilon_greedy(state, available, epsilon)

            if action is Action.STAND:
                dealer_total = _play_dealer(dealer_up, self.hit_soft_17, rng)
                reward = _settle(total, dealer_total, unit=1.0)
                self._td_update(state, action, reward, None, alpha)
                return reward

            card = _sample_card_value(rng)
            new_total, new_soft, bust = add_card_value(total, soft, card)
            unit = 2.0 if action is Action.DOUBLE else 1.0

            if bust:
                reward = -unit
                self._td_update(state, action, reward, None, alpha)
                return reward

            if action is Action.DOUBLE or new_total == 21:
                # Arrêt forcé : après un double (une seule carte) ou à 21.
                dealer_total = _play_dealer(dealer_up, self.hit_soft_17, rng)
                reward = _settle(new_total, dealer_total, unit=unit)
                self._td_update(state, action, reward, None, alpha)
                return reward

            # HIT non terminal : récompense nulle, on amorce (bootstrap) sur
            # la meilleure valeur connue de l'état suivant.
            next_state = (new_total, new_soft, dealer_up)
            self._td_update(state, action, 0.0, next_state, alpha)
            total, soft, first_decision = new_total, new_soft, False

    def _td_update(self, state: State, action: Action, reward: float,
                    next_state: Optional[State], alpha: float) -> None:
        """Règle de mise à jour du Q-learning : ``Q(s,a) += alpha * (cible - Q(s,a))``,
        où la cible est la récompense immédiate, plus — si l'épisode continue
        — le meilleur Q connu de l'état suivant, actualisé par ``gamma``."""
        q_state = self._q.setdefault(state, {})
        current = q_state.get(action, 0.0)
        if next_state is None:
            target = reward
        else:
            next_values = self._q.get(next_state)
            best_next = max(next_values.values()) if next_values else 0.0
            target = reward + self.gamma * best_next
        q_state[action] = current + alpha * (target - current)

    def _epsilon_greedy(self, state: State, available: List[Action], epsilon: float) -> Action:
        if self._rng.random() < epsilon:
            return self._rng.choice(available)
        q = self._q.get(state, {})
        return max(available, key=lambda a: q.get(a, 0.0))

    # ------------------------------------------------------------------ #
    # Utilisation (une fois entraîné)
    # ------------------------------------------------------------------ #
    def recommend(self, hand: Hand, dealer_up: Card) -> Action:
        """Interface compatible avec :class:`~blackjack.strategies.Strategy`."""
        if hand.can_split:
            decision = self._fallback.evaluate(hand, dealer_up)
            if decision.action is Action.SPLIT:
                return Action.SPLIT
        if hand.can_surrender:
            decision = self._fallback.evaluate(hand, dealer_up)
            if decision.action is Action.SURRENDER:
                return Action.SURRENDER

        state = (hand.total, hand.is_soft, dealer_up.value)
        available = [Action.STAND, Action.HIT]
        if hand.can_double:
            available.append(Action.DOUBLE)

        q = self._q.get(state, {})
        known = [(a, q[a]) for a in available if a in q]
        if not known:
            # État jamais rencontré à l'entraînement : repli sur le solveur
            # plutôt qu'un choix arbitraire.
            return self._fallback.evaluate(hand, dealer_up).action
        return max(known, key=lambda pair: pair[1])[0]

    def take_insurance(self) -> bool:
        """L'assurance n'a jamais été apprise (hors du champ de
        l'entraînement, voir en-tête de module) : délègue au solveur exact,
        comme pour SPLIT/SURRENDER."""
        return self._fallback.take_insurance()

    def explain(self, hand: Hand, dealer_up: Card) -> Decision:
        """Comme ``recommend()``, mais renvoie le détail (les Q-values
        connues pour cet état, ou le repli sur le solveur) au lieu de la
        seule action — pour une UI qui veut montrer *pourquoi* l'agent a
        choisi ce coup plutôt qu'un autre."""
        if hand.can_split or hand.can_surrender:
            fallback = self._fallback.evaluate(hand, dealer_up)
            if (hand.can_split and fallback.action is Action.SPLIT) or \
               (hand.can_surrender and fallback.action is Action.SURRENDER):
                return fallback

        state = (hand.total, hand.is_soft, dealer_up.value)
        available = [Action.STAND, Action.HIT]
        if hand.can_double:
            available.append(Action.DOUBLE)

        q = self._q.get(state, {})
        known = {a: q[a] for a in available if a in q}
        if not known:
            # État jamais rencontré à l'entraînement : le solveur explique
            # à sa place (voir recommend(), même repli).
            return self._fallback.evaluate(hand, dealer_up)
        best_action = max(known, key=known.get)
        return Decision(action=best_action, expected_values=known)

    # ------------------------------------------------------------------ #
    # Persistance (entraînement long -> fichier JSON réutilisable)
    # ------------------------------------------------------------------ #
    def save(self, path: Path) -> None:
        payload = {
            "trained_episodes": self.trained_episodes,
            "hit_soft_17": self.hit_soft_17,
            "gamma": self.gamma,
            "q_table": [
                {"total": total, "soft": soft, "dealer_up": dealer_up,
                 "values": {action.name: value for action, value in actions.items()}}
                for (total, soft, dealer_up), actions in self._q.items()
            ],
            "training_curve": {
                "episodes": self.curve.episodes,
                "average_reward": self.curve.average_reward,
            },
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, rules: "Rules", seed: int = 42) -> "QLearningAgent":
        payload = json.loads(path.read_text(encoding="utf-8"))
        agent = cls(rules, seed=seed, gamma=payload.get("gamma", 1.0))
        agent.trained_episodes = payload.get("trained_episodes", 0)
        for entry in payload.get("q_table", []):
            state = (entry["total"], entry["soft"], entry["dealer_up"])
            agent._q[state] = {Action[name]: value for name, value in entry["values"].items()}
        curve = payload.get("training_curve", {})
        agent.curve.episodes = curve.get("episodes", [])
        agent.curve.average_reward = curve.get("average_reward", [])
        return agent
