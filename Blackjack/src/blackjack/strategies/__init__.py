"""
Sous-package ``strategies`` — toutes les méthodes de décision.

Exporte un dictionnaire :data:`STRATEGIES` qui sert de **registre** au menu :
ajouter une stratégie revient à ajouter une entrée ici.
"""

from typing import Dict, Type

from .base_strategy import Strategy
from .basic_strategy import BasicStrategy
from .counting import (
    HiLoStrategy,
    HiOptIStrategy,
    HiOptIIStrategy,
    KOStrategy,
    OmegaIIStrategy,
    Red7Strategy,
    ZenStrategy,
)
from .manual import ManualStrategy

#: Registre central des stratégies disponibles.
STRATEGIES: Dict[str, Type[Strategy]] = {
    "manuelle":      ManualStrategy,
    "basique":       BasicStrategy,
    "hi-lo":         HiLoStrategy,
    "ko":            KOStrategy,
    "hi-opt-i":      HiOptIStrategy,
    "hi-opt-ii":     HiOptIIStrategy,
    "omega-ii":      OmegaIIStrategy,
    "zen":           ZenStrategy,
    "red-7":         Red7Strategy,
}


def get_strategy(key: str) -> Strategy:
    """Fabrique : instancie la stratégie correspondant à la clé.

    Lève :class:`KeyError` si la clé est inconnue.
    """
    key = key.lower().strip()
    if key not in STRATEGIES:
        raise KeyError(f"Stratégie inconnue : {key!r}. "
                       f"Disponibles : {sorted(STRATEGIES)}")
    return STRATEGIES[key]()


__all__ = [
    "Strategy",
    "ManualStrategy",
    "BasicStrategy",
    "HiLoStrategy",
    "KOStrategy",
    "HiOptIStrategy",
    "HiOptIIStrategy",
    "OmegaIIStrategy",
    "ZenStrategy",
    "Red7Strategy",
    "STRATEGIES",
    "get_strategy",
]
