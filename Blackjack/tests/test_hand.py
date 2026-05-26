"""Tests de la classe :class:`Hand`."""

import unittest

from blackjack.core import Card, Hand, Rank, Suit


def _card(rank: Rank, suit: Suit = Suit.SPADES) -> Card:
    return Card(rank, suit)


class TestHand(unittest.TestCase):

    def test_total_simple(self):
        h = Hand()
        h.add_card(_card(Rank.SEVEN))
        h.add_card(_card(Rank.NINE))
        self.assertEqual(h.total, 16)
        self.assertFalse(h.is_soft)

    def test_total_avec_as_soft(self):
        h = Hand()
        h.add_card(_card(Rank.ACE))
        h.add_card(_card(Rank.SIX))
        self.assertEqual(h.total, 17)  # soft 17
        self.assertTrue(h.is_soft)

    def test_as_devient_dur_pour_eviter_le_bust(self):
        h = Hand()
        h.add_card(_card(Rank.ACE))    # 11
        h.add_card(_card(Rank.SIX))    # 17
        h.add_card(_card(Rank.TEN))    # 27 -> 17 (As compté 1)
        self.assertEqual(h.total, 17)
        self.assertFalse(h.is_soft)
        self.assertFalse(h.is_bust)

    def test_blackjack(self):
        h = Hand()
        h.add_card(_card(Rank.ACE))
        h.add_card(_card(Rank.KING))
        self.assertTrue(h.is_blackjack)
        self.assertEqual(h.total, 21)

    def test_blackjack_apres_split_nest_pas_un_blackjack(self):
        h = Hand()
        h.from_split = True
        h.add_card(_card(Rank.ACE))
        h.add_card(_card(Rank.KING))
        self.assertFalse(h.is_blackjack)

    def test_bust(self):
        h = Hand()
        h.add_card(_card(Rank.KING))
        h.add_card(_card(Rank.QUEEN))
        h.add_card(_card(Rank.FIVE))
        self.assertTrue(h.is_bust)
        self.assertTrue(h.is_done)

    def test_paire(self):
        h = Hand()
        h.add_card(_card(Rank.EIGHT, Suit.HEARTS))
        h.add_card(_card(Rank.EIGHT, Suit.CLUBS))
        self.assertTrue(h.is_pair)
        self.assertTrue(h.can_split)

    def test_double_modifie_la_mise(self):
        h = Hand(bet=10.0)
        h.add_card(_card(Rank.FIVE))
        h.add_card(_card(Rank.SIX))
        h.double()
        self.assertEqual(h.bet, 20.0)
        self.assertTrue(h.doubled)
        self.assertTrue(h.stood)


if __name__ == "__main__":
    unittest.main()
