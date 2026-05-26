"""Tests de la classe :class:`Card`."""

import unittest

from blackjack.core import Card, Rank, Suit


class TestCard(unittest.TestCase):

    def test_creation_valide(self):
        c = Card(Rank.ACE, Suit.HEARTS)
        self.assertEqual(c.rank, Rank.ACE)
        self.assertEqual(c.suit, Suit.HEARTS)
        self.assertEqual(c.value, 11)
        self.assertTrue(c.is_ace)
        self.assertFalse(c.is_ten_value)

    def test_creation_type_invalide(self):
        with self.assertRaises(TypeError):
            Card("As", Suit.HEARTS)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            Card(Rank.ACE, "rouge")  # type: ignore[arg-type]

    def test_egalite_et_hash(self):
        c1 = Card(Rank.KING, Suit.SPADES)
        c2 = Card(Rank.KING, Suit.SPADES)
        c3 = Card(Rank.KING, Suit.HEARTS)
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertEqual(hash(c1), hash(c2))

    def test_immutabilite(self):
        c = Card(Rank.TEN, Suit.CLUBS)
        # __slots__ + name-mangling => impossible d'écrire ``c.rank = ...``.
        with self.assertRaises(AttributeError):
            c.rank = Rank.NINE  # type: ignore[misc]

    def test_valeur_des_figures(self):
        for r in (Rank.JACK, Rank.QUEEN, Rank.KING, Rank.TEN):
            c = Card(r, Suit.DIAMONDS)
            self.assertEqual(c.value, 10)
            self.assertTrue(c.is_ten_value)

    def test_couleur_rouge(self):
        self.assertTrue(Card(Rank.FIVE, Suit.HEARTS).suit.is_red)
        self.assertTrue(Card(Rank.FIVE, Suit.DIAMONDS).suit.is_red)
        self.assertFalse(Card(Rank.FIVE, Suit.CLUBS).suit.is_red)


if __name__ == "__main__":
    unittest.main()
