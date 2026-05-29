"""Tests de la manche (:class:`Round`).

Couvre trois aspects clés et déterministes :
    - le **règlement des gains** (``_resolve_hand``) pour chaque issue ;
    - la **restriction de double** (``_can_double``) selon les règles ;
    - le **flux avec carte cachée + peek** sur les cas de Blackjack (joueur,
      croupier, double Blackjack), pilotés par un sabot truqué pour être
      reproductibles sans dépendre du hasard.
"""

import unittest

from blackjack.core import Action, Card, Hand, Outcome, Rank, Shoe, Suit
from blackjack.game import Round, Rules, Statistics
from blackjack.players import Dealer, HumanPlayer
from blackjack.strategies import BasicStrategy


def _card(rank: Rank, suit: Suit = Suit.SPADES) -> Card:
    return Card(rank, suit)


def _make_round(rules: Rules) -> Round:
    """Construit une manche prête à l'emploi (sabot mélangé, sans UI)."""
    shoe = Shoe(num_decks=1, seed=1)
    shoe.shuffle()
    strat = BasicStrategy()
    dealer = Dealer(hit_soft_17=rules.dealer_hits_soft_17)
    player = HumanPlayer(name="Test", bankroll=1000.0, strategy=strat)
    return Round(rules, shoe, dealer, player, strat, ui=None)


class _ScriptedShoe(Shoe):
    """Sabot qui distribue d'abord une séquence imposée, puis du hasard."""

    def __init__(self, scripted):
        super().__init__(num_decks=1, seed=1)
        self.shuffle()
        self._scripted = list(scripted)

    def draw(self) -> Card:
        if self._scripted:
            return self._scripted.pop(0)
        return super().draw()


class _FakeUI:
    """UI factice : prend (ou non) l'assurance et joue une file d'actions.

    Tous les autres callbacks (narration, affichages…) sont des no-op grâce à
    ``__getattr__``.
    """

    def __init__(self, insurance=0.0, actions=None):
        self._insurance = insurance
        self._actions = list(actions or [])

    def prompt_insurance(self, player, dealer, max_ins):
        return min(self._insurance, max_ins) if self._insurance else 0.0

    def prompt_action(self, *a, **k):
        return self._actions.pop(0) if self._actions else Action.STAND

    def __getattr__(self, name):
        return lambda *a, **k: None


class TestSettlement(unittest.TestCase):
    """Vérifie ``_resolve_hand`` : issue + somme reversée (mise incluse)."""

    def setUp(self):
        self.rules = Rules(blackjack_payout=1.5)
        self.rnd = _make_round(self.rules)

    def _hand(self, *ranks, bet=10.0):
        h = Hand(bet=bet)
        for r in ranks:
            h.add_card(_card(r))
        return h

    def test_blackjack_joueur_paye_3_2(self):
        h = self._hand(Rank.ACE, Rank.KING)
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=18, dealer_bust=False,
            player_blackjack=True, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.BLACKJACK)
        self.assertAlmostEqual(payout, 25.0)  # 10 + 10 * 1.5

    def test_double_blackjack_push(self):
        h = self._hand(Rank.ACE, Rank.KING)
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=21, dealer_bust=False,
            player_blackjack=True, dealer_blackjack=True,
        )
        self.assertIs(outcome, Outcome.PUSH)
        self.assertAlmostEqual(payout, 10.0)

    def test_blackjack_croupier_seul_perd(self):
        h = self._hand(Rank.NINE, Rank.EIGHT)
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=21, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=True,
        )
        self.assertIs(outcome, Outcome.LOSS)
        self.assertAlmostEqual(payout, 0.0)

    def test_abandon_rend_la_moitie(self):
        h = self._hand(Rank.TEN, Rank.SIX)
        h.surrender()
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=20, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.SURRENDER)
        self.assertAlmostEqual(payout, 5.0)

    def test_joueur_brule_perd(self):
        h = self._hand(Rank.TEN, Rank.TEN, Rank.FIVE)  # 25
        self.assertTrue(h.is_bust)
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=18, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.BUST)
        self.assertAlmostEqual(payout, 0.0)

    def test_croupier_brule_gagne(self):
        h = self._hand(Rank.TEN, Rank.EIGHT)  # 18
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=24, dealer_bust=True,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.WIN)
        self.assertAlmostEqual(payout, 20.0)

    def test_total_superieur_gagne(self):
        h = self._hand(Rank.TEN, Rank.TEN)  # 20
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=18, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.WIN)
        self.assertAlmostEqual(payout, 20.0)

    def test_egalite_push(self):
        h = self._hand(Rank.TEN, Rank.EIGHT)  # 18
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=18, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.PUSH)
        self.assertAlmostEqual(payout, 10.0)

    def test_total_inferieur_perd(self):
        h = self._hand(Rank.TEN, Rank.SEVEN)  # 17
        outcome, payout = self.rnd._resolve_hand(
            h, dealer_total=20, dealer_bust=False,
            player_blackjack=False, dealer_blackjack=False,
        )
        self.assertIs(outcome, Outcome.LOSS)
        self.assertAlmostEqual(payout, 0.0)


class TestDoubleRestriction(unittest.TestCase):
    """Vérifie ``_can_double`` selon ``double_hard_9_to_11_only``."""

    def _hand(self, *ranks):
        h = Hand(bet=10.0)
        for r in ranks:
            h.add_card(_card(r))
        return h

    def test_restreint_aux_durs_9_10_11(self):
        rnd = _make_round(Rules(double_hard_9_to_11_only=True))
        self.assertTrue(rnd._can_double(self._hand(Rank.SIX, Rank.FIVE)))   # hard 11
        self.assertTrue(rnd._can_double(self._hand(Rank.FOUR, Rank.FIVE)))  # hard 9
        self.assertFalse(rnd._can_double(self._hand(Rank.TEN, Rank.TWO)))   # hard 12
        self.assertFalse(rnd._can_double(self._hand(Rank.ACE, Rank.FOUR)))  # soft 15

    def test_double_libre_si_non_restreint(self):
        rnd = _make_round(Rules(double_hard_9_to_11_only=False))
        self.assertTrue(rnd._can_double(self._hand(Rank.ACE, Rank.FOUR)))   # soft 15
        self.assertTrue(rnd._can_double(self._hand(Rank.TEN, Rank.TWO)))    # hard 12

    def test_pas_de_double_a_trois_cartes(self):
        rnd = _make_round(Rules(double_hard_9_to_11_only=False))
        h = self._hand(Rank.FOUR, Rank.THREE, Rank.FOUR)  # 11 mais 3 cartes
        self.assertFalse(rnd._can_double(h))


class TestPeekBlackjack(unittest.TestCase):
    """Flux carte cachée + peek : issues de Blackjack, sabot truqué.

    Ordre de distribution en peek : hole croupier, 1re joueur, up croupier,
    2e joueur. Aucune décision joueur n'est requise sur ces cas.
    """

    def _play(self, scripted, rules=None):
        # no_hole_card=False -> flux avec carte cachée + peek (comme la config).
        rules = rules or Rules(no_hole_card=False, blackjack_payout=1.5,
                               insurance_allowed=True)
        shoe = _ScriptedShoe(scripted)
        strat = BasicStrategy()
        dealer = Dealer(hit_soft_17=rules.dealer_hits_soft_17)
        player = HumanPlayer(name="Test", bankroll=1000.0, strategy=strat)
        rnd = Round(rules, shoe, dealer, player, strat, ui=None)
        return rnd.play(bet=10.0)

    def test_blackjack_joueur(self):
        # hole=2, joueur=As, up=7, joueur=10 -> joueur BJ, croupier 9 (pas BJ)
        results = self._play([
            _card(Rank.TWO), _card(Rank.ACE), _card(Rank.SEVEN), _card(Rank.TEN),
        ])
        self.assertEqual(len(results), 1)
        _, outcome, net = results[0]
        self.assertIs(outcome, Outcome.BLACKJACK)
        self.assertAlmostEqual(net, 15.0)  # 25 reversés - 10 misés

    def test_blackjack_croupier(self):
        # hole=R(10), joueur=9, up=As, joueur=8 -> croupier As+R = BJ, joueur 17
        results = self._play([
            _card(Rank.KING), _card(Rank.NINE), _card(Rank.ACE), _card(Rank.EIGHT),
        ])
        self.assertEqual(len(results), 1)
        _, outcome, net = results[0]
        self.assertIs(outcome, Outcome.LOSS)
        self.assertAlmostEqual(net, -10.0)

    def test_double_blackjack_push(self):
        # hole=R(10), joueur=As, up=As, joueur=10 -> les deux BJ -> égalité
        results = self._play([
            _card(Rank.KING), _card(Rank.ACE), _card(Rank.ACE), _card(Rank.TEN),
        ])
        self.assertEqual(len(results), 1)
        _, outcome, net = results[0]
        self.assertIs(outcome, Outcome.PUSH)
        self.assertAlmostEqual(net, 0.0)


class TestInsurance(unittest.TestCase):
    """L'assurance est résolue et son bilan (``_insurance_net``) est correct."""

    def _round(self, scripted, ui):
        rules = Rules(no_hole_card=False, blackjack_payout=1.5,
                      insurance_allowed=True)
        shoe = _ScriptedShoe(scripted)
        strat = BasicStrategy()
        dealer = Dealer(hit_soft_17=rules.dealer_hits_soft_17)
        player = HumanPlayer(name="Test", bankroll=1000.0, strategy=strat)
        player.ui = ui
        return Round(rules, shoe, dealer, player, strat, ui=ui)

    def test_assurance_gagnee_paye_2_1(self):
        # up=As, hole=R(10) -> croupier BJ ; joueur 9+7 ; assurance prise (5).
        ui = _FakeUI(insurance=5.0)
        rnd = self._round([
            _card(Rank.KING), _card(Rank.NINE), _card(Rank.ACE), _card(Rank.SEVEN),
        ], ui)
        rnd.play(bet=10.0)
        self.assertEqual(rnd._insurance_bet, 5.0)
        self.assertAlmostEqual(rnd._insurance_net, 10.0)  # 2:1 sur 5

    def test_assurance_perdue(self):
        # up=As, hole=5 -> pas de BJ ; joueur reste ; assurance prise (5) perdue.
        ui = _FakeUI(insurance=5.0, actions=[Action.STAND])
        rnd = self._round([
            _card(Rank.FIVE), _card(Rank.NINE), _card(Rank.ACE), _card(Rank.SEVEN),
        ], ui)
        rnd.play(bet=10.0)
        self.assertEqual(rnd._insurance_bet, 5.0)
        self.assertAlmostEqual(rnd._insurance_net, -5.0)


class TestStatistics(unittest.TestCase):
    """La mise annexe (assurance) entre dans le total misé et le bilan."""

    def test_record_side_bet(self):
        stats = Statistics()
        stats.record(Outcome.LOSS, net=-10.0, bet=10.0)
        stats.record_side_bet(wager=5.0, net=10.0)  # assurance gagnée
        self.assertAlmostEqual(stats.total_bet, 15.0)
        self.assertAlmostEqual(stats.total_won, 0.0)  # -10 (main) + 10 (assurance)
        # Les mains gagnées/perdues ne sont pas affectées par le pari annexe.
        self.assertEqual(stats.losses, 1)
        self.assertEqual(stats.wins, 0)


class TestOriginalBetsOnly(unittest.TestCase):
    """OBO : en ENHC, un double face à un Blackjack croupier ne perd que
    la mise d'origine (la portion doublée est rendue)."""

    def _play_enhc_double_vs_dealer_bj(self, obo: bool):
        rules = Rules(no_hole_card=True, insurance_allowed=False,
                      double_hard_9_to_11_only=True, original_bets_only=obo,
                      blackjack_payout=1.5)
        # Ordre ENHC : joueur1, up croupier, joueur2, carte du double, 2e croupier.
        scripted = [
            _card(Rank.SIX), _card(Rank.ACE), _card(Rank.FIVE),   # joueur 11, up=As
            _card(Rank.NINE),                                      # carte du double
            _card(Rank.TEN),                                       # 2e croupier -> A+10 = BJ
        ]
        shoe = _ScriptedShoe(scripted)
        strat = BasicStrategy()
        dealer = Dealer(hit_soft_17=rules.dealer_hits_soft_17)
        player = HumanPlayer(name="Test", bankroll=1000.0, strategy=strat)
        ui = _FakeUI(actions=[Action.DOUBLE])
        player.ui = ui
        rnd = Round(rules, shoe, dealer, player, strat, ui=ui)
        return rnd.play(bet=10.0)

    def test_obo_rend_la_portion_doublee(self):
        results = self._play_enhc_double_vs_dealer_bj(obo=True)
        _, outcome, net = results[0]
        self.assertIs(outcome, Outcome.LOSS)
        self.assertAlmostEqual(net, -10.0)  # ne perd que la mise d'origine

    def test_sans_obo_perd_la_mise_doublee(self):
        results = self._play_enhc_double_vs_dealer_bj(obo=False)
        _, outcome, net = results[0]
        self.assertIs(outcome, Outcome.LOSS)
        self.assertAlmostEqual(net, -20.0)  # perd toute la mise doublée


if __name__ == "__main__":
    unittest.main()
