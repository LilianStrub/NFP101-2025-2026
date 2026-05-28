"""
Module ``game`` — boucle principale et statistiques.

C'est la classe ``Game`` qui orchestre les manches successives, surveille
le sabot, applique les remélanges, et tient les statistiques.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from ..core import Outcome, Shoe
from ..players import Dealer, HumanPlayer
from ..strategies import Strategy
from .round import Round
from .rules import Rules

logger = logging.getLogger(__name__)


@dataclass
class Statistics:
    """Statistiques cumulées d'une session."""

    rounds_played: int = 0
    hands_played: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    blackjacks: int = 0
    surrenders: int = 0
    busts: int = 0
    total_bet: float = 0.0
    total_won: float = 0.0  # net positif/négatif

    def record(self, outcome: Outcome, net: float, bet: float) -> None:
        self.hands_played += 1
        self.total_bet += bet
        self.total_won += net
        if outcome is Outcome.BLACKJACK:
            self.blackjacks += 1
            self.wins += 1
        elif outcome is Outcome.WIN:
            self.wins += 1
        elif outcome is Outcome.PUSH:
            self.pushes += 1
        elif outcome is Outcome.SURRENDER:
            self.surrenders += 1
            self.losses += 1
        elif outcome is Outcome.BUST:
            self.busts += 1
            self.losses += 1
        elif outcome is Outcome.LOSS:
            self.losses += 1

    @property
    def win_rate(self) -> float:
        if self.hands_played == 0:
            return 0.0
        return self.wins / self.hands_played

    @property
    def expected_value(self) -> float:
        """Espérance par main (en unités de mise)."""
        if self.total_bet == 0:
            return 0.0
        return self.total_won / self.total_bet


class Game:
    """Contrôleur d'une session de Blackjack."""

    def __init__(self, rules: Rules, player: HumanPlayer, strategy: Strategy,
                 ui=None, seed: int = None) -> None:  # noqa: ANN001
        self.rules = rules
        self.player = player
        self.strategy = strategy
        self.ui = ui
        self.shoe = Shoe(num_decks=rules.num_decks,
                         penetration=rules.penetration,
                         seed=seed)
        self.shoe.shuffle()  # sabot prêt dès le départ, pas de message parasite
        self.shoe.burn()     # brûlage de la 1re carte, comme au casino (silencieux)
        self.dealer = Dealer(hit_soft_17=rules.dealer_hits_soft_17)
        self.stats = Statistics()
        # On attache l'UI au joueur (rétro-injection), sans écraser une UI
        # qui aurait déjà été assignée manuellement (utile pour les tests).
        if ui is not None:
            self.player.ui = ui

    # ------------------------------------------------------------------ #
    def play_round(self, bet: float) -> List:
        # Le sabot signale-t-il qu'il faut mélanger ?
        if self.shoe.needs_shuffle:
            if self.ui is not None:
                self.ui.show_shuffle()
            self.shoe.shuffle()
            burned = self.shoe.burn()
            if self.ui is not None:
                self.ui.narrate(
                    "La carte de coupe a été atteinte : le croupier remélange "
                    "tout le sabot pour éviter que les cartes soient prévisibles."
                )
                if burned is not None:
                    self.ui.narrate(
                        "Il brûle ensuite la première carte (écartée sans la "
                        "montrer), comme le veut l'usage des casinos."
                    )
            self.strategy.reset_count()

        rnd = Round(self.rules, self.shoe, self.dealer, self.player,
                    self.strategy, ui=self.ui)
        results = rnd.play(bet)
        self.stats.rounds_played += 1
        for hand, outcome, net in results:
            self.stats.record(outcome, net, hand.bet)
            logger.info("Manche %d : %s — main %s, net=%.2f",
                        self.stats.rounds_played, outcome.value, hand, net)
        return results

    # ------------------------------------------------------------------ #
    def suggested_bet(self) -> float:
        """Mise conseillée par la stratégie courante."""
        return self.strategy.betting_units(
            self.shoe.decks_remaining,
            self.rules.min_bet,
            self.rules.max_bet,
        )
