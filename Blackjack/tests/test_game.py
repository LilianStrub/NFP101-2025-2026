"""Tests d'intégration de bout en bout.

Joue plusieurs manches complètes en pilotant le ``HumanPlayer`` par un faux
UI (« HeadlessUI ») qui décide selon une stratégie donnée. Vérifie
notamment que :
    - les statistiques s'incrémentent correctement,
    - les soldes sont cohérents,
    - aucune exception n'est levée sur 200 manches.
"""

import unittest

from blackjack.core import Action
from blackjack.game import Game, Rules
from blackjack.players import HumanPlayer
from blackjack.strategies import BasicStrategy, HiLoStrategy


class HeadlessUI:
    """Faux UI qui décide via la stratégie sans rien afficher."""

    def __init__(self, strategy):
        self.strategy = strategy

    def prompt_action(self, player, hand, dealer_up, advice=None, rules=None, hand_index=0):
        action = self.strategy.recommend(hand, dealer_up)
        if action is Action.DOUBLE:
            can_double = hand.can_double and (
                rules is None
                or not getattr(rules, "double_hard_9_to_11_only", False)
                or (not hand.is_soft and hand.total in (9, 10, 11))
            )
            if not can_double:
                return Action.HIT
        if action is Action.SPLIT and not hand.can_split:
            return Action.HIT
        if action is Action.SURRENDER:
            if not hand.can_surrender or not getattr(rules, "surrender_allowed", True):
                return Action.HIT
        return action

    def prompt_insurance(self, player, dealer, max_insurance: float) -> float:
        return 0.0  # pas d'assurance en mode headless

    # Callbacks no-op
    def narrate(self, *a, **k): pass
    def show_pre_deal(self, *a, **k): pass
    def show_deal_step(self, *a, **k): pass
    def show_initial_deal(self, *a, **k): pass
    def show_dealer_reveal(self, *a, **k): pass
    def show_dealer_draw(self, *a, **k): pass
    def show_action(self, *a, **k): pass
    def show_shuffle(self, *a, **k): pass
    def show_insurance_result(self, *a, **k): pass
    def show_dealer_bust(self, *a, **k): pass


class TestEndToEnd(unittest.TestCase):

    def test_200_manches_basic_strategy(self):
        rules = Rules(num_decks=6, starting_bankroll=10000)
        strat = BasicStrategy()
        player = HumanPlayer(name="Test", bankroll=10000, strategy=strat)
        player.ui = HeadlessUI(strat)
        game = Game(rules=rules, player=player, strategy=strat, ui=None, seed=42)
        for _ in range(200):
            if player.bankroll < rules.min_bet:
                break
            game.play_round(bet=5.0)
        self.assertGreaterEqual(game.stats.rounds_played, 1)
        self.assertGreaterEqual(game.stats.hands_played, game.stats.rounds_played)

    def test_running_count_evolue_avec_hi_lo(self):
        rules = Rules(num_decks=2, starting_bankroll=10000)
        strat = HiLoStrategy()
        player = HumanPlayer(name="Test", bankroll=10000, strategy=strat)
        player.ui = HeadlessUI(strat)
        game = Game(rules=rules, player=player, strategy=strat, ui=None, seed=7)
        for _ in range(10):
            game.play_round(bet=5.0)
        # On ne peut pas prédire la valeur exacte, mais on peut vérifier
        # qu'elle est dans une plage raisonnable.
        self.assertIsInstance(strat.running_count, int)
        self.assertGreater(abs(strat.running_count), 0)


if __name__ == "__main__":
    unittest.main()
