"""Tests des stratégies d'aide à la décision.

Vérifie :
  * que la stratégie de base recommande la bonne action sur des cas
    canoniques (paires, mains soft, mains hard) ;
  * que chaque comptage attribue la bonne valeur à chaque rang de carte
    (référence : sources mentionnées dans le module ``counting``).
"""

import unittest

from blackjack.core import Action, Card, Hand, Rank, Suit
from blackjack.strategies import (
    BasicStrategy,
    HiLoStrategy,
    HiOptIStrategy,
    HiOptIIStrategy,
    KOStrategy,
    OmegaIIStrategy,
    Red7Strategy,
    ReinforcementStrategy,
    SolverStrategy,
    ZenStrategy,
)


def _hand(*ranks: Rank, from_split: bool = False) -> Hand:
    h = Hand()
    h.from_split = from_split
    for r in ranks:
        h.add_card(Card(r, Suit.SPADES))
    return h


class TestBasicStrategyDecisions(unittest.TestCase):
    """Cas canoniques de la stratégie de base (multi-deck S17 DAS)."""

    def setUp(self):
        self.s = BasicStrategy()

    # ---- Paires ---- #
    def test_paire_d_as_split(self):
        # A,A => toujours split
        h = _hand(Rank.ACE, Rank.ACE)
        for up in (Rank.TWO, Rank.SIX, Rank.TEN, Rank.ACE):
            self.assertEqual(self.s.recommend(h, Card(up, Suit.SPADES)),
                              Action.SPLIT, msg=f"upcard={up}")

    def test_paire_de_8_split(self):
        h = _hand(Rank.EIGHT, Rank.EIGHT)
        for up in (Rank.TWO, Rank.SEVEN, Rank.TEN, Rank.ACE):
            self.assertEqual(self.s.recommend(h, Card(up, Suit.SPADES)),
                              Action.SPLIT)

    def test_paire_de_10_jamais_split(self):
        h = _hand(Rank.TEN, Rank.TEN)
        # Ne doit jamais splitter — il rendra STAND (le code H/S des paires
        # 10 dit S partout, et 10-10 ne peut de toute façon pas être splittée
        # sans casser la table).
        self.assertEqual(self.s.recommend(h, Card(Rank.SIX, Suit.SPADES)),
                          Action.STAND)

    # ---- Mains hard ---- #
    def test_hard_16_contre_10_surrender(self):
        h = _hand(Rank.TEN, Rank.SIX)
        self.assertEqual(self.s.recommend(h, Card(Rank.TEN, Suit.SPADES)),
                          Action.SURRENDER)

    def test_hard_17_toujours_stand(self):
        h = _hand(Rank.TEN, Rank.SEVEN)
        for up in (Rank.TWO, Rank.SIX, Rank.SEVEN, Rank.TEN, Rank.ACE):
            self.assertEqual(self.s.recommend(h, Card(up, Suit.SPADES)),
                              Action.STAND)

    def test_hard_11_double_sauf_contre_as(self):
        h = _hand(Rank.SIX, Rank.FIVE)
        self.assertEqual(self.s.recommend(h, Card(Rank.TEN, Suit.SPADES)),
                          Action.DOUBLE)
        self.assertEqual(self.s.recommend(h, Card(Rank.ACE, Suit.SPADES)),
                          Action.HIT)

    # ---- Mains soft ---- #
    def test_soft_18_contre_6_double(self):
        h = _hand(Rank.ACE, Rank.SEVEN)
        self.assertEqual(self.s.recommend(h, Card(Rank.SIX, Suit.SPADES)),
                          Action.DOUBLE)

    def test_soft_18_contre_9_hit(self):
        h = _hand(Rank.ACE, Rank.SEVEN)
        self.assertEqual(self.s.recommend(h, Card(Rank.NINE, Suit.SPADES)),
                          Action.HIT)

    def test_soft_20_stand(self):
        h = _hand(Rank.ACE, Rank.NINE)
        self.assertEqual(self.s.recommend(h, Card(Rank.SIX, Suit.SPADES)),
                          Action.STAND)


class TestCountingValues(unittest.TestCase):
    """Vérifie les valeurs attribuées par chaque comptage à chaque rang."""

    def _check(self, strategy, expected: dict):
        """``expected`` : { Rank: valeur_attendue }."""
        for rank, expected_val in expected.items():
            c = Card(rank, Suit.SPADES)
            self.assertEqual(strategy.card_value(c), expected_val,
                              msg=f"{strategy.name} sur {rank.label}")

    def test_hi_lo(self):
        # 2-6 = +1 ; 7-9 = 0 ; 10-A = -1
        self._check(HiLoStrategy(), {
            Rank.TWO: +1, Rank.THREE: +1, Rank.FOUR: +1, Rank.FIVE: +1, Rank.SIX: +1,
            Rank.SEVEN: 0, Rank.EIGHT: 0, Rank.NINE: 0,
            Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1,
            Rank.ACE: -1,
        })

    def test_ko(self):
        # 2-7 = +1 ; 8-9 = 0 ; 10-A = -1
        self._check(KOStrategy(num_decks=6), {
            Rank.TWO: +1, Rank.THREE: +1, Rank.FOUR: +1, Rank.FIVE: +1,
            Rank.SIX: +1, Rank.SEVEN: +1,
            Rank.EIGHT: 0, Rank.NINE: 0,
            Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1,
            Rank.ACE: -1,
        })

    def test_hi_opt_i(self):
        # 3-6 = +1 ; A,2,7,8,9 = 0 ; 10-R = -1
        self._check(HiOptIStrategy(), {
            Rank.TWO: 0, Rank.THREE: +1, Rank.FOUR: +1, Rank.FIVE: +1, Rank.SIX: +1,
            Rank.SEVEN: 0, Rank.EIGHT: 0, Rank.NINE: 0,
            Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1,
            Rank.ACE: 0,
        })

    def test_hi_opt_ii(self):
        # 2,3,6,7 = +1 ; 4,5 = +2 ; 8,9,A = 0 ; 10-R = -2
        self._check(HiOptIIStrategy(), {
            Rank.TWO: +1, Rank.THREE: +1, Rank.FOUR: +2, Rank.FIVE: +2,
            Rank.SIX: +1, Rank.SEVEN: +1,
            Rank.EIGHT: 0, Rank.NINE: 0,
            Rank.TEN: -2, Rank.JACK: -2, Rank.QUEEN: -2, Rank.KING: -2,
            Rank.ACE: 0,
        })

    def test_omega_ii(self):
        # 2,3,7 = +1 ; 4,5,6 = +2 ; 8,A = 0 ; 9 = -1 ; 10-R = -2
        self._check(OmegaIIStrategy(), {
            Rank.TWO: +1, Rank.THREE: +1,
            Rank.FOUR: +2, Rank.FIVE: +2, Rank.SIX: +2,
            Rank.SEVEN: +1,
            Rank.EIGHT: 0, Rank.NINE: -1,
            Rank.TEN: -2, Rank.JACK: -2, Rank.QUEEN: -2, Rank.KING: -2,
            Rank.ACE: 0,
        })

    def test_zen(self):
        # 2,3,7 = +1 ; 4,5,6 = +2 ; 8,9 = 0 ; 10-R = -2 ; A = -1
        self._check(ZenStrategy(), {
            Rank.TWO: +1, Rank.THREE: +1,
            Rank.FOUR: +2, Rank.FIVE: +2, Rank.SIX: +2,
            Rank.SEVEN: +1,
            Rank.EIGHT: 0, Rank.NINE: 0,
            Rank.TEN: -2, Rank.JACK: -2, Rank.QUEEN: -2, Rank.KING: -2,
            Rank.ACE: -1,
        })

    def test_red_7_distingue_rouge_noir(self):
        s = Red7Strategy(num_decks=6)
        # 7 de cœur = +1
        self.assertEqual(s.card_value(Card(Rank.SEVEN, Suit.HEARTS)), +1)
        # 7 de pique = 0
        self.assertEqual(s.card_value(Card(Rank.SEVEN, Suit.SPADES)), 0)
        # Le reste suit la même grille que Hi-Lo.
        self.assertEqual(s.card_value(Card(Rank.FIVE, Suit.SPADES)), +1)
        self.assertEqual(s.card_value(Card(Rank.ACE, Suit.HEARTS)), -1)


class TestBalancedSystems(unittest.TestCase):
    """Vérifie que la somme des valeurs sur un jeu complet est 0 (=> balanced)."""

    def _sum_full_deck(self, strategy) -> int:
        total = 0
        for suit in Suit:
            for rank in Rank:
                total += strategy.card_value(Card(rank, suit))
        return total

    def test_hi_lo_est_equilibre(self):
        self.assertEqual(self._sum_full_deck(HiLoStrategy()), 0)

    def test_hi_opt_i_est_equilibre(self):
        self.assertEqual(self._sum_full_deck(HiOptIStrategy()), 0)

    def test_hi_opt_ii_est_equilibre(self):
        self.assertEqual(self._sum_full_deck(HiOptIIStrategy()), 0)

    def test_omega_ii_est_equilibre(self):
        self.assertEqual(self._sum_full_deck(OmegaIIStrategy()), 0)

    def test_zen_est_equilibre(self):
        self.assertEqual(self._sum_full_deck(ZenStrategy()), 0)


class TestAIAgents(unittest.TestCase):
    """Fumée pour les deux agents IA portés depuis le projet NFP106
    « blackjack-ia » (voir ``ai/solver.py`` et ``ai/rl_agent.py``) : on ne
    revalide pas leur algorithmie ici (déjà couverte côté NFP106), juste
    qu'ils sont correctement branchés à l'interface ``Strategy`` de ce
    projet et rendent le verdict évident sur des mains sans ambiguïté."""

    def test_solveur_construction_sans_argument(self):
        # Doit s'instancier sans argument comme toute entrée de STRATEGIES
        # (charge les règles par défaut via ``utils.load_rules``).
        strat = SolverStrategy()
        self.assertIsInstance(strat, SolverStrategy)

    def test_solveur_hard_20_stand(self):
        s = SolverStrategy()
        h = _hand(Rank.TEN, Rank.TEN)
        self.assertEqual(s.recommend(h, Card(Rank.SIX, Suit.SPADES)), Action.STAND)

    def test_solveur_hard_8_hit(self):
        s = SolverStrategy()
        h = _hand(Rank.FIVE, Rank.THREE)
        self.assertEqual(s.recommend(h, Card(Rank.TEN, Suit.SPADES)), Action.HIT)

    def test_q_learning_construction_sans_argument(self):
        # Charge la Q-table pré-entraînée livrée avec le projet (data/q_table.json).
        strat = ReinforcementStrategy()
        self.assertIsInstance(strat, ReinforcementStrategy)
        self.assertGreater(strat.trained_episodes, 0)

    def test_q_learning_hard_20_stand(self):
        s = ReinforcementStrategy()
        h = _hand(Rank.TEN, Rank.TEN)
        self.assertEqual(s.recommend(h, Card(Rank.SIX, Suit.SPADES)), Action.STAND)

    def test_q_learning_hard_8_hit(self):
        s = ReinforcementStrategy()
        h = _hand(Rank.FIVE, Rank.THREE)
        self.assertEqual(s.recommend(h, Card(Rank.TEN, Suit.SPADES)), Action.HIT)

    # ---- Assurance ---- #
    def test_solveur_refuse_assurance(self):
        # EV négative sous hypothèse de sabot infini (4/13 < 1/3) : jamais.
        self.assertFalse(SolverStrategy().take_insurance())

    def test_q_learning_refuse_assurance(self):
        # Jamais appris (hors du champ d'entraînement) : délègue au solveur.
        self.assertFalse(ReinforcementStrategy().take_insurance())

    # ---- Détail de la décision (explain) ---- #
    def test_solveur_explain_coherent_avec_recommend(self):
        s = SolverStrategy()
        h = _hand(Rank.FIVE, Rank.THREE)
        up = Card(Rank.TEN, Suit.SPADES)
        self.assertEqual(s.explain(h, up).action, s.recommend(h, up))

    def test_q_learning_explain_coherent_avec_recommend(self):
        s = ReinforcementStrategy()
        h = _hand(Rank.FIVE, Rank.THREE)
        up = Card(Rank.TEN, Suit.SPADES)
        self.assertEqual(s.explain(h, up).action, s.recommend(h, up))


if __name__ == "__main__":
    unittest.main()
