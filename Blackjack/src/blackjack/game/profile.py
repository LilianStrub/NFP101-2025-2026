"""
Module ``profile`` — profil de joueur persistant (sauvegarde & reprise).

Conserve, entre deux sessions, le solde du joueur, ses statistiques cumulées
« à vie » et ses records. Sérialisé en JSON dans le dossier personnel de
l'utilisateur. Aucune dépendance externe.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_PATH = str(Path.home() / ".blackjack_profile.json")


@dataclass
class Profile:
    """État persistant d'un joueur : solde, cumul à vie et records."""

    bankroll: float = 100.0

    # Statistiques cumulées (toutes sessions confondues).
    rounds_played: int = 0
    hands_played: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    blackjacks: int = 0
    busts: int = 0
    surrenders: int = 0
    total_bet: float = 0.0
    total_won: float = 0.0
    rebuys: int = 0

    # Records à battre.
    best_bankroll: float = 0.0
    longest_win_streak: int = 0
    biggest_win: float = 0.0

    def folded_with(self, stats, bankroll: float, session_peak: float,
                    rebuys: int) -> "Profile":
        """Renvoie une COPIE = ce profil de base + les stats d'une session.

        ``self`` reste l'instantané d'avant la session, ce qui rend l'appel
        idempotent : on peut sauvegarder après chaque manche sans double compte.
        """
        return Profile(
            bankroll=bankroll,
            rounds_played=self.rounds_played + stats.rounds_played,
            hands_played=self.hands_played + stats.hands_played,
            wins=self.wins + stats.wins,
            losses=self.losses + stats.losses,
            pushes=self.pushes + stats.pushes,
            blackjacks=self.blackjacks + stats.blackjacks,
            busts=self.busts + stats.busts,
            surrenders=self.surrenders + stats.surrenders,
            total_bet=self.total_bet + stats.total_bet,
            total_won=self.total_won + stats.total_won,
            rebuys=self.rebuys + rebuys,
            best_bankroll=max(self.best_bankroll, session_peak),
            longest_win_streak=max(self.longest_win_streak,
                                   getattr(stats, "longest_win_streak", 0)),
            biggest_win=max(self.biggest_win,
                            getattr(stats, "biggest_win", 0.0)),
        )


def load_profile(path: Optional[str] = None) -> Optional[Profile]:
    """Charge le profil sauvegardé, ou ``None`` s'il n'en existe pas (ou illisible)."""
    p = Path(path or _DEFAULT_PATH)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    fields = Profile.__dataclass_fields__.keys()  # type: ignore[attr-defined]
    return Profile(**{k: v for k, v in data.items() if k in fields})


def save_profile(profile: Profile, path: Optional[str] = None) -> bool:
    """Sauvegarde le profil en JSON. Renvoie False en cas d'échec d'écriture."""
    try:
        Path(path or _DEFAULT_PATH).write_text(
            json.dumps(asdict(profile), indent=2), encoding="utf-8")
        return True
    except OSError as exc:
        logger.warning("Sauvegarde du profil impossible : %s", exc)
        return False
