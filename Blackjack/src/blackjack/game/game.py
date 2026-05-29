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
    # Engagement : séries de victoires et record du plus gros gain en une main.
    current_win_streak: int = 0
    longest_win_streak: int = 0
    biggest_win: float = 0.0

    def record(self, outcome: Outcome, net: float, bet: float) -> None:
        self.hands_played += 1
        self.total_bet += bet
        self.total_won += net
        if net > self.biggest_win:
            self.biggest_win = net
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

    def record_round(self, net: float) -> None:
        """Met à jour la série de victoires d'après le gain net d'une manche.

        Gain positif → la série s'allonge ; perte → elle repart à zéro ;
        égalité (net nul) → série inchangée.
        """
        if net > 0:
            self.current_win_streak += 1
            self.longest_win_streak = max(self.longest_win_streak,
                                          self.current_win_streak)
        elif net < 0:
            self.current_win_streak = 0

    def record_side_bet(self, wager: float, net: float) -> None:
        """Comptabilise une mise annexe (assurance) dans le total misé et le bilan.

        N'affecte pas le compte de mains gagnées/perdues : seule l'espérance et
        le bilan net intègrent ce pari pour rester cohérents avec le solde réel.
        """
        self.total_bet += wager
        self.total_won += net

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
        round_net = 0.0
        # Mise annexe : l'assurance entre dans le bilan et l'EV (cohérence solde).
        if rnd._insurance_bet > 0:
            self.stats.record_side_bet(rnd._insurance_bet, rnd._insurance_net)
            round_net += rnd._insurance_net
        for hand, outcome, net in results:
            self.stats.record(outcome, net, hand.bet)
            round_net += net
            logger.info("Manche %d : %s — main %s, net=%.2f",
                        self.stats.rounds_played, outcome.value, hand, net)
        # Série de victoires (sur le résultat global de la manche).
        self.stats.record_round(round_net)
        return results

    # ------------------------------------------------------------------ #
    def suggested_bet(self) -> float:
        """Mise conseillée par la stratégie courante."""
        return self.strategy.betting_units(
            self.shoe.decks_remaining,
            self.rules.min_bet,
            self.rules.max_bet,
        )
