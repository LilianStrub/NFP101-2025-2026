"""Tests du sabot (:class:`Shoe`)."""

import unittest

from blackjack.core import Shoe


class TestShoe(unittest.TestCase):

    def test_taille_initiale(self):
        s = Shoe(num_decks=6, seed=42)
        s.shuffle()
        self.assertEqual(s.cards_remaining, 6 * 52)

    def test_tirage_decremente(self):
        s = Shoe(num_decks=1, seed=42)
        s.shuffle()
        initial = s.cards_remaining
        s.draw()
        self.assertEqual(s.cards_remaining, initial - 1)

    def test_seed_reproductible(self):
        s1 = Shoe(num_decks=2, seed=12345)
        s2 = Shoe(num_decks=2, seed=12345)
        s1.shuffle()
        s2.shuffle()
        cards1 = [s1.draw() for _ in range(10)]
        cards2 = [s2.draw() for _ in range(10)]
        self.assertEqual(cards1, cards2)

    def test_penetration_signale_remelange(self):
        s = Shoe(num_decks=1, penetration=0.5, seed=42)
        s.shuffle()
        # On tire 26 cartes => on doit avoir besoin d'un remélange.
        for _ in range(26):
            s.draw()
        self.assertTrue(s.needs_shuffle)

    def test_parametres_invalides(self):
        with self.assertRaises(ValueError):
            Shoe(num_decks=0)
        with self.assertRaises(ValueError):
            Shoe(penetration=0)
        with self.assertRaises(ValueError):
            Shoe(penetration=1.5)


if __name__ == "__main__":
    unittest.main()
