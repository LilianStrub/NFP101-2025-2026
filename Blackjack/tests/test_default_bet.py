"""Test de la mise par défaut dans la boucle de jeu (``_game_loop``).

Pour une stratégie sans comptage : la mise par défaut vaut 1 % du solde à la
1re manche, puis conserve la dernière mise du joueur (elle ne se recalcule plus
à chaque gain/perte).
"""

import builtins
import io
import unittest

from blackjack.__main__ import _game_loop
from blackjack.core import Action
from blackjack.game import Game, Rules
from blackjack.players import HumanPlayer
from blackjack.strategies import BasicStrategy
from blackjack.ui import UI


class _RecordingUI:
    """Faux UI : enregistre la mise proposée par défaut à chaque manche.

    Le joueur mise 25 à la 1re manche, puis accepte le défaut proposé ensuite.
    On arrête après deux manches.
    """

    def __init__(self):
        self.defaults = []
        self.chosen = [25.0]  # mise forcée de la 1re manche

    def ask_bet(self, default, minimum, maximum):
        self.defaults.append(default)
        if self.chosen:
            return self.chosen.pop(0)
        return default  # manches suivantes : le joueur garde le défaut

    def ask_yes_no(self, question, default=True):
        # « Jouer une autre manche ? » : oui après la 1re, non après la 2e.
        return len(self.defaults) < 2

    def prompt_action(self, *a, **k):
        return Action.STAND

    def prompt_insurance(self, *a, **k):
        return 0.0

    def __getattr__(self, name):
        return lambda *a, **k: None


class TestDefaultBet(unittest.TestCase):

    def test_premiere_manche_1pct_puis_derniere_mise(self):
        rules = Rules(no_hole_card=False, min_bet=1.0, max_bet=500.0)
        strat = BasicStrategy()
        player = HumanPlayer(name="J", bankroll=1000.0, strategy=strat)
        ui = _RecordingUI()
        player.ui = ui
        game = Game(rules=rules, player=player, strategy=strat, ui=ui, seed=4)

        _game_loop(ui, game, player, strat, rules, 1000.0)

        self.assertEqual(len(ui.defaults), 2)
        # 1re manche : 1 % de 1000 = 10.
        self.assertAlmostEqual(ui.defaults[0], 10.0)
        # 2e manche : on garde la mise placée (25), pas un nouveau 1 % du solde.
        self.assertAlmostEqual(ui.defaults[1], 25.0)


class TestBetInput(unittest.TestCase):
    """On tape le montant ; Entrée valide ; pas de centime."""

    def _ask_bet(self, commands, default, minimum, maximum):
        it = iter(commands)
        original = builtins.input
        builtins.input = lambda *a, **k: next(it)
        try:
            ui = UI(stream=io.StringIO())
            return ui.ask_bet(default=default, minimum=minimum, maximum=maximum)
        finally:
            builtins.input = original

    def test_montant_tape(self):
        self.assertEqual(self._ask_bet(["30"], 10, 1, 500), 30.0)

    def test_entree_garde_le_conseil(self):
        self.assertEqual(self._ask_bet([""], 10, 1, 500), 10.0)

    def test_tapis_mise_le_solde(self):
        self.assertEqual(self._ask_bet(["tapis"], 10, 1, 100), 100.0)

    def test_arrondi_sans_centime(self):
        # 7,34 € → arrondi à 7 € (jetons, pas de centime).
        self.assertEqual(self._ask_bet(["7,34"], 10, 1, 500), 7.0)

    def test_hors_bornes_puis_valide(self):
        # 600 > max 100 → redemande, puis 50 accepté.
        self.assertEqual(self._ask_bet(["600", "50"], 10, 1, 100), 50.0)

    def test_saisie_invalide_puis_valide(self):
        self.assertEqual(self._ask_bet(["abc", "25"], 10, 1, 500), 25.0)


if __name__ == "__main__":
    unittest.main()
