"""Tests du profil persistant et des séries de victoires.

Couvre :
    - la sauvegarde / le rechargement JSON d'un :class:`Profile` (round-trip) ;
    - l'absence de fichier (``load_profile`` renvoie ``None``) ;
    - le repli d'une session dans le profil (``folded_with`` : cumul + records) ;
    - les séries de victoires de :class:`Statistics` (``record_round``).
"""

import os
import tempfile
import unittest

from blackjack.game import Profile, Statistics, load_profile, save_profile


class TestProfilePersistence(unittest.TestCase):

    def test_aucun_fichier_renvoie_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(load_profile(os.path.join(d, "absent.json")))

    def test_sauvegarde_et_rechargement(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            prof = Profile(bankroll=250.0, rounds_played=12, blackjacks=3,
                           best_bankroll=400.0, longest_win_streak=5,
                           biggest_win=75.0)
            self.assertTrue(save_profile(prof, path))
            loaded = load_profile(path)
            self.assertEqual(loaded, prof)  # dataclass __eq__ : tous les champs

    def test_json_corrompu_renvoie_none(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "bad.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{ pas du json")
            self.assertIsNone(load_profile(path))


class TestProfileFold(unittest.TestCase):

    def test_cumul_et_records(self):
        base = Profile(bankroll=100.0, rounds_played=10, hands_played=10,
                       wins=4, blackjacks=1, total_bet=100.0, total_won=20.0,
                       best_bankroll=150.0, longest_win_streak=3, biggest_win=30.0,
                       rebuys=1)
        stats = Statistics(rounds_played=5, hands_played=6, wins=3,
                           blackjacks=2, total_bet=50.0, total_won=40.0,
                           longest_win_streak=4, biggest_win=60.0)
        merged = base.folded_with(stats, bankroll=210.0, session_peak=260.0,
                                  rebuys=2)
        # Cumul additif.
        self.assertEqual(merged.rounds_played, 15)
        self.assertEqual(merged.hands_played, 16)
        self.assertEqual(merged.wins, 7)
        self.assertEqual(merged.blackjacks, 3)
        self.assertAlmostEqual(merged.total_won, 60.0)
        self.assertEqual(merged.rebuys, 3)
        # Solde courant repris tel quel.
        self.assertAlmostEqual(merged.bankroll, 210.0)
        # Records = maximum entre base et session.
        self.assertAlmostEqual(merged.best_bankroll, 260.0)
        self.assertEqual(merged.longest_win_streak, 4)
        self.assertAlmostEqual(merged.biggest_win, 60.0)

    def test_fold_idempotent_sur_la_base(self):
        # Replier deux fois la même session donne le même résultat (base figée).
        base = Profile(rounds_played=2, total_won=10.0)
        stats = Statistics(rounds_played=3, total_won=15.0)
        a = base.folded_with(stats, 100.0, 100.0, 0)
        b = base.folded_with(stats, 100.0, 100.0, 0)
        self.assertEqual(a, b)
        self.assertEqual(a.rounds_played, 5)  # pas 8 → base inchangée


class TestWinStreak(unittest.TestCase):

    def test_serie_de_victoires(self):
        s = Statistics()
        s.record_round(+10)   # 1
        s.record_round(+5)    # 2
        self.assertEqual(s.current_win_streak, 2)
        s.record_round(0)     # push : inchangé
        self.assertEqual(s.current_win_streak, 2)
        s.record_round(+1)    # 3
        self.assertEqual(s.current_win_streak, 3)
        self.assertEqual(s.longest_win_streak, 3)
        s.record_round(-10)   # défaite : remise à zéro
        self.assertEqual(s.current_win_streak, 0)
        self.assertEqual(s.longest_win_streak, 3)  # record conservé

    def test_plus_gros_gain(self):
        from blackjack.core import Outcome
        s = Statistics()
        s.record(Outcome.WIN, net=10.0, bet=10.0)
        s.record(Outcome.BLACKJACK, net=30.0, bet=20.0)
        s.record(Outcome.LOSS, net=-10.0, bet=10.0)
        self.assertAlmostEqual(s.biggest_win, 30.0)


if __name__ == "__main__":
    unittest.main()
