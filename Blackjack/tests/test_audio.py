"""Tests de la musique d'ambiance (:mod:`blackjack.ui.audio`).

On ne joue aucun son : on vérifie la génération du fichier WAV et le
comportement dégradé quand aucun lecteur audio n'est disponible.
"""

import os
import tempfile
import unittest
import wave

from blackjack.ui.audio import WEBRADIOS, AmbientMusic, generate_ambient_wav


class TestGenerateWav(unittest.TestCase):

    def test_genere_un_wav_valide(self):
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            generate_ambient_wav(path, seconds=0.5, rate=8000)
            with wave.open(path, "r") as w:
                self.assertEqual(w.getnchannels(), 1)
                self.assertEqual(w.getsampwidth(), 2)
                self.assertEqual(w.getframerate(), 8000)
                self.assertEqual(w.getnframes(), int(0.5 * 8000))
        finally:
            os.remove(path)


class TestAmbientMusic(unittest.TestCase):

    def test_indisponible_sans_lecteur(self):
        m = AmbientMusic()
        m._player = None  # simule l'absence de lecteur audio
        self.assertFalse(m.available())
        self.assertFalse(m.enabled)
        self.assertFalse(m.start())   # ne démarre pas
        self.assertFalse(m.toggle())  # reste inactif
        m.stop()                      # ne lève rien

    def test_etat_initial_inactif(self):
        m = AmbientMusic()
        self.assertFalse(m.enabled)
        self.assertTrue(m.using_generated)

    def test_source_personnalisee_non_generee(self):
        m = AmbientMusic(source="https://example.com/stream")
        self.assertFalse(m.using_generated)

    def test_playlist_dossier_melangee(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.mp3", "b.wav", "notes.txt", "c.ogg"):
                open(os.path.join(d, name), "w").close()
            m = AmbientMusic(source=d)
            playlist = m._resolve_playlist()
            self.assertEqual(
                sorted(os.path.basename(p) for p in playlist),
                ["a.mp3", "b.wav", "c.ogg"],  # le .txt est ignoré
            )

    def test_url_jouee_directement(self):
        url = "http://example.com/lounge"
        m = AmbientMusic(source=url)
        self.assertEqual(m._resolve_playlist(), [url])

    def test_dossier_vide_ne_demarre_pas(self):
        with tempfile.TemporaryDirectory() as d:
            m = AmbientMusic(source=d)
            m._player = ["true"]  # simule un lecteur présent
            self.assertFalse(m.start())  # dossier sans audio -> pas de lecture


class TestWebradio(unittest.TestCase):

    def test_presets_sont_des_urls(self):
        self.assertTrue(WEBRADIOS)
        for label, url in WEBRADIOS:
            self.assertIsInstance(label, str)
            self.assertTrue(url.startswith(("http://", "https://")))

    def test_source_webradio_detectee(self):
        _, url = WEBRADIOS[0]
        m = AmbientMusic(source=url)
        self.assertTrue(m.is_webradio)
        self.assertFalse(m.using_generated)
        self.assertTrue(m.has_fixed_source)
        self.assertEqual(m._resolve_playlist(), [url])

    def test_set_source_bascule_vers_webradio(self):
        m = AmbientMusic()
        self.assertTrue(m.using_generated)
        self.assertFalse(m.has_fixed_source)
        m.set_source("http://exemple.fm/lounge")
        self.assertTrue(m.is_webradio)
        self.assertFalse(m.using_generated)

    def test_lecteur_streaming_pour_les_urls(self):
        # Un flux doit utiliser un lecteur capable de streamer (pas afplay seul).
        m = AmbientMusic()
        m._player = ["afplay"]  # lecteur local only
        cmd = m._player_for("https://exemple.fm/lounge")
        if cmd is not None:               # si un lecteur de flux est installé
            self.assertNotEqual(cmd, ["afplay"])
        self.assertEqual(m._player_for("/tmp/x.wav"), ["afplay"])


if __name__ == "__main__":
    unittest.main()
