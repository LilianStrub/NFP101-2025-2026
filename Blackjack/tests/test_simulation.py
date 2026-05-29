"""Tests du mode simulation : mise variable selon le true count.

Vérifie que la simulation fait miser davantage un compteur quand le sabot est
favorable (``_sim_bet``), alors que la stratégie de base mise à plat.
"""

import unittest

from blackjack.__main__ import _sim_bet
from blackjack.game import Game, Rules
from blackjack.players import HumanPlayer
from blackjack.strategies import BasicStrategy, HiLoStrategy


class TestBettingUnits(unittest.TestCase):
    """Le palier de mise du Hi-Lo suit le true count (1× → 8×)."""

    def test_palier_selon_true_count(self):
        strat = HiLoStrategy()
        # true count = running_count / decks_remaining
        strat._running_count = 0
        self.assertEqual(strat.betting_units(6.0, 10.0, 500.0), 10.0)   # TC 0 → 1×
        strat._running_count = 12                                       # TC 2 → 2×
        self.assertEqual(strat.betting_units(6.0, 10.0, 500.0), 20.0)
        strat._running_count = 60                                       # TC 10 → 8×
        self.assertEqual(strat.betting_units(6.0, 10.0, 500.0), 80.0)

    def test_plafond_mise_max(self):
        strat = HiLoStrategy()
        strat._running_count = 60  # TC élevé → 8× = 200, mais plafonné à 50
        self.assertEqual(strat.betting_units(6.0, 25.0, 50.0), 50.0)


class TestSimBet(unittest.TestCase):

    def _game(self, strategy):
        rules = Rules()
        player = HumanPlayer(name="SimBot", bankroll=1e9, strategy=strategy)
        return Game(rules=rules, player=player, strategy=strategy, ui=None), rules

    def test_base_mise_a_plat(self):
        strat = BasicStrategy()
        game, rules = self._game(strat)
        self.assertEqual(_sim_bet(strat, game, rules, 10.0), 10.0)
        # Même avec des cartes vues, la stratégie de base ne varie pas.
        strat._running_count = 99
        self.assertEqual(_sim_bet(strat, game, rules, 10.0), 10.0)

    def test_compteur_mise_plus_si_favorable(self):
        strat = HiLoStrategy()
        game, rules = self._game(strat)
        base = _sim_bet(strat, game, rules, 10.0)        # count ~0 → 1×
        strat._running_count = 60                        # sabot très favorable
        boosted = _sim_bet(strat, game, rules, 10.0)
        self.assertEqual(base, 10.0)
        self.assertGreater(boosted, base)                # mise augmentée


if __name__ == "__main__":
    unittest.main()
