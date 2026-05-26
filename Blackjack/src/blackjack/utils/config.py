"""
Module ``config`` — chargement d'une configuration depuis un fichier JSON.

Permet d'initialiser un objet :class:`Rules` à partir du fichier
``config/default.json`` (ou d'un autre fichier passé en argument).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..game import Rules


def load_rules(path: str = "config/default.json") -> Rules:
    """Charge un fichier JSON et le convertit en :class:`Rules`.

    En cas d'erreur (fichier introuvable, JSON invalide…) on retombe sur
    les valeurs par défaut de :class:`Rules`.
    """
    p = Path(path)
    if not p.is_file():
        return Rules()  # fallback : valeurs par défaut.
    try:
        data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Rules()

    # Ne garde que les clés qui correspondent à des champs de Rules.
    valid_keys = Rules.__dataclass_fields__.keys()  # type: ignore[attr-defined]
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return Rules(**filtered)
