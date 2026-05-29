"""
Module ``audio`` — musique d'ambiance optionnelle.

Sans dépendance externe : on s'appuie sur un lecteur audio en ligne de commande
déjà présent sur le système (``afplay`` sur macOS, ``aplay``/``paplay`` sous
Linux, ``ffplay``…) lancé en arrière-plan. À défaut de fichier fourni par
l'utilisateur, une nappe d'ambiance discrète est *générée* à la volée avec le
module standard :mod:`wave`. Si aucun lecteur n'est disponible, la
fonctionnalité se désactive silencieusement (``available()`` renvoie ``False``).
"""

from __future__ import annotations

import logging
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import wave
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# Lecteurs CLI testés, dans l'ordre de préférence. Chaque entrée donne le nom
# de l'exécutable et les arguments à placer avant le chemin du fichier.
_PLAYERS = [
    ("afplay", ["afplay"]),
    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ("paplay", ["paplay"]),
    ("aplay", ["aplay", "-q"]),
    ("cvlc", ["cvlc", "--play-and-exit", "--quiet"]),
    ("mpg123", ["mpg123", "-q"]),
]

# Lecteurs capables de lire un flux réseau (afplay/aplay/paplay ne savent pas).
_STREAM_PLAYERS = [
    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ("mpg123", ["mpg123", "-q"]),
    ("cvlc", ["cvlc", "--play-and-exit", "--quiet"]),
]

# Webradios lounge gratuites et légales (SomaFM) prêtes à l'emploi. Flux MP3
# directs (compatibles ffplay/mpg123/cvlc).
WEBRADIOS: Tuple[Tuple[str, str], ...] = (
    ("Groove Salad — downtempo / ambient (SomaFM)",
     "https://ice1.somafm.com/groovesalad-128-mp3"),
    ("Secret Agent — lounge & exotica feutrés (SomaFM)",
     "https://ice1.somafm.com/secretagent-128-mp3"),
    ("Lush — chill vocal (SomaFM)",
     "https://ice1.somafm.com/lush-128-mp3"),
)


def _find_player() -> Optional[List[str]]:
    """Renvoie la commande du premier lecteur audio disponible, ou ``None``."""
    for name, cmd in _PLAYERS:
        if shutil.which(name):
            return cmd
    return None


def _find_stream_player() -> Optional[List[str]]:
    """Renvoie la commande d'un lecteur capable de lire un flux réseau."""
    for name, cmd in _STREAM_PLAYERS:
        if shutil.which(name):
            return cmd
    return None


# Progression de lounge jazz (Cmaj7 – Am7 – Dm7 – G7), calme et feutrée.
# Chaque accord : fréquence de basse (octave grave) + notes de la nappe.
_PROGRESSION = (
    (65.41,  (164.81, 196.00, 246.94)),  # Cmaj7 : basse C2 ; nappe E3 G3 B3
    (110.00, (164.81, 196.00, 261.63)),  # Am7   : basse A2 ; nappe E3 G3 C4
    (73.42,  (174.61, 220.00, 261.63)),  # Dm7   : basse D2 ; nappe F3 A3 C4
    (98.00,  (174.61, 246.94, 293.66)),  # G7    : basse G2 ; nappe F3 B3 D4
)
_TWO_PI = 2 * math.pi

# Extensions reconnues quand BLACKJACK_MUSIC pointe vers un dossier (playlist).
_AUDIO_EXT = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus")


def _voice(bass: float, pad, t: float) -> float:
    """Somme basse + nappe d'un accord à l'instant ``t`` (sonorité douce)."""
    v = 0.13 * (math.sin(_TWO_PI * bass * t)
                + 0.20 * math.sin(_TWO_PI * 2 * bass * t))
    for f in pad:
        v += 0.10 * math.sin(_TWO_PI * f * t)
    return v


def _build_sequence(rng):
    """Construit une suite d'accords qui module de tonalité puis revient en C.

    L'ordre des modulations est tiré au hasard : le morceau diffère à chaque
    session et sa période de répétition est longue (≈ 50 s)."""
    choices = [2, 5, -3, 7, -5]            # demi-tons de modulation possibles
    sections = [0] + [rng.choice(choices) for _ in range(3)] + [0]
    sequence = []
    for semis in sections:
        ratio = 2 ** (semis / 12)
        for bass, pad in _PROGRESSION:
            sequence.append((bass * ratio, tuple(f * ratio for f in pad)))
    return sequence


def generate_ambient_wav(path: str, *, seconds: float = 50.0,
                         rate: int = 16000, seed: Optional[int] = None) -> str:
    """Écrit un morceau d'ambiance « salon de casino » : progression de lounge
    jazz feutrée qui module de tonalité, basse douce, fondus enchaînés et léger
    arpège. Randomisé (``seed=None`` → aléatoire) pour varier d'une fois à
    l'autre ; fondu d'entrée/sortie pour une boucle sans clic.
    """
    rng = random.Random(seed)
    sequence = _build_sequence(rng)
    num = len(sequence)
    n = int(seconds * rate)
    slot = seconds / num                    # durée d'un accord
    xfade = min(1.0, slot * 0.5)            # fondu enchaîné entre accords
    fade = max(1, int(0.6 * rate))          # fondu de boucle (entrée/sortie)
    arp_step = 0.8                           # un grain d'arpège toutes les 0.8 s
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            t = i / rate
            idx = min(int(t / slot), num - 1)
            local = t - idx * slot
            bass, pad = sequence[idx]
            sample = _voice(bass, pad, t)
            # Fondu enchaîné vers l'accord suivant (sauf le dernier).
            if idx < num - 1 and local > slot - xfade:
                a = (local - (slot - xfade)) / xfade
                nb, npad = sequence[idx + 1]
                sample = (math.cos(a * math.pi / 2) * sample
                          + math.sin(a * math.pi / 2) * _voice(nb, npad, t))
            # Arpège doux (notes de l'accord une octave plus haut, pincé).
            step = int(t / arp_step)
            arp_freq = pad[step % len(pad)] * 2
            env = math.exp(-3.2 * (t - step * arp_step))
            sample += 0.045 * env * math.sin(_TWO_PI * arp_freq * t)
            # Fondu de boucle.
            if i < fade:
                sample *= i / fade
            elif i > n - fade:
                sample *= (n - i) / fade
            sample = max(-1.0, min(1.0, sample))
            frames += struct.pack("<h", int(sample * 32767))
        w.writeframes(bytes(frames))
    return path


class AmbientMusic:
    """Joue une musique d'ambiance en arrière-plan.

    Source (par ordre de priorité) : chemin/URL passé au constructeur, variable
    d'environnement ``BLACKJACK_MUSIC``, sinon un morceau généré. ``BLACKJACK_MUSIC``
    peut désigner :

    * un **fichier** audio,
    * un **dossier** → tous les morceaux sont lus en ordre aléatoire (playlist),
    * une **URL** de flux (webradio) → musique continue.

    Conçu pour ne jamais bloquer ni planter l'interface : lecture dans un thread
    démon, sortie du lecteur mise en sourdine.
    """

    def __init__(self, source: Optional[str] = None) -> None:
        self._source: Optional[str] = source or os.environ.get("BLACKJACK_MUSIC")
        # Source imposée (argument ou variable d'env) → pas de choix au menu.
        self._fixed_source = self._source is not None
        self._player = _find_player()
        self._generated_path: Optional[str] = None
        self._proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------ #
    @property
    def enabled(self) -> bool:
        """True si la musique tourne actuellement."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def using_generated(self) -> bool:
        """True si aucune source n'est définie (morceau généré hors-ligne)."""
        return self._source is None

    @property
    def is_webradio(self) -> bool:
        """True si la source courante est une URL de flux."""
        return bool(self._source) and self._is_url(self._source)

    @property
    def has_fixed_source(self) -> bool:
        """True si la source vient d'un argument/variable d'env (pas de menu)."""
        return self._fixed_source

    def set_source(self, source: Optional[str]) -> None:
        """Change la source (fichier/dossier/URL, ou None pour le morceau généré).

        Sans effet si la musique tourne déjà.
        """
        if not self.enabled:
            self._source = source

    def available(self) -> bool:
        """True si un lecteur adapté à la source courante est présent."""
        if self.is_webradio:
            return _find_stream_player() is not None
        return self._player is not None

    @staticmethod
    def _is_url(value: str) -> bool:
        return value.startswith(("http://", "https://"))

    def _player_for(self, item: str) -> Optional[List[str]]:
        """Lecteur adapté à un élément : flux réseau ou fichier local."""
        return _find_stream_player() if self._is_url(item) else self._player

    def _list_folder(self, folder: str) -> List[str]:
        try:
            names = sorted(os.listdir(folder))
        except OSError:
            return []
        return [os.path.join(folder, f) for f in names
                if f.lower().endswith(_AUDIO_EXT)]

    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Démarre la lecture. Renvoie False si indisponible ou source vide."""
        if not self.available() or self.enabled:
            return False
        # Vérifie tout de suite qu'une source explicite est exploitable.
        src = self._source
        if src and not self._is_url(src):
            if os.path.isdir(src):
                if not self._list_folder(src):
                    return False
            elif not os.path.exists(src):
                return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Coupe la musique (arrêt propre du lecteur et du thread)."""
        self._stop.set()
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:  # noqa: BLE001 — terminaison best-effort
                pass
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)
        self._thread = None
        self._proc = None

    def toggle(self) -> bool:
        """Bascule l'état. Renvoie le nouvel état (True = active)."""
        if self.enabled:
            self.stop()
            return False
        return self.start()

    # ------------------------------------------------------------------ #
    def _resolve_playlist(self) -> List[str]:
        """Liste des morceaux/flux à enchaîner (re-mélangée pour un dossier)."""
        src = self._source
        if src:
            if self._is_url(src):
                return [src]
            if os.path.isdir(src):
                files = self._list_folder(src)
                random.shuffle(files)
                return files
            if os.path.exists(src):
                return [src]
            return []
        generated = self._ensure_generated()
        return [generated] if generated else []

    def _run(self) -> None:
        devnull = subprocess.DEVNULL
        failures = 0  # échecs consécutifs de flux (webradio injoignable)
        try:
            while not self._stop.is_set():
                playlist = self._resolve_playlist()
                if not playlist:
                    return
                for item in playlist:
                    if self._stop.is_set():
                        break
                    cmd = self._player_for(item)
                    if cmd is None:
                        return
                    started = time.monotonic()
                    self._proc = subprocess.Popen(
                        cmd + [item], stdout=devnull, stderr=devnull,
                    )
                    while self._proc.poll() is None:
                        if self._stop.wait(0.2):
                            self._proc.terminate()
                            break
                    # Flux qui sort trop vite = connexion échouée : on temporise
                    # pour ne pas marteler le serveur, et on abandonne après 3 essais.
                    if self._is_url(item) and not self._stop.is_set():
                        if time.monotonic() - started < 2.0:
                            failures += 1
                            if failures >= 3:
                                logger.warning("Webradio injoignable — musique arrêtée.")
                                return
                            self._stop.wait(3.0)
                        else:
                            failures = 0
                # Playlist terminée : on recommence (un dossier sera re-mélangé).
        except Exception as exc:  # noqa: BLE001
            logger.warning("Musique d'ambiance interrompue : %s", exc)

    def _ensure_generated(self) -> Optional[str]:
        """Génère (une fois par session) un morceau et renvoie son chemin."""
        if self._generated_path and os.path.exists(self._generated_path):
            return self._generated_path
        try:
            fd, tmp = tempfile.mkstemp(prefix="blackjack_ambiance_", suffix=".wav")
            os.close(fd)
            generate_ambient_wav(tmp)  # randomisé → différent à chaque session
            self._generated_path = tmp
            return tmp
        except Exception as exc:  # noqa: BLE001
            logger.warning("Génération de la musique impossible : %s", exc)
            return None
