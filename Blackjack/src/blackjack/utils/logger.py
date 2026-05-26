"""
Module ``logger`` — configuration centralisée des journaux.

Écrit les évènements détaillés dans ``logs/blackjack.log`` (créé au besoin)
sans polluer la sortie standard. Utile pour le debug et l'analyse des
parties après coup.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


def configure_logging(level: int = logging.INFO,
                       log_dir: str = "logs",
                       filename: str = "blackjack.log") -> None:
    """Initialise le logging racine.

    :param level: Niveau de log (DEBUG/INFO/WARNING/ERROR).
    :param log_dir: Dossier où écrire les fichiers de log.
    :param filename: Nom du fichier de log.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, filename)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )
    logging.getLogger(__name__).debug("Journalisation initialisée -> %s", log_path)
