"""
Module ``mdp`` — modèle de transition partagé par les agents IA.

Le Blackjack est modélisé ici comme un problème de décision séquentielle
sous incertitude : à chaque tour, l'état est (total de la main, main
« soft » ou non), l'action est tirée de :class:`~blackjack.core.Action`,
et la transition vers l'état suivant dépend d'un tirage aléatoire de carte.
C'est un **MDP** (Markov Decision Process) au sens classique : la probabilité
du prochain état ne dépend que de l'état courant et de l'action, pas de
l'historique — propriété de Markov vérifiée ici car ``(total, soft)`` résume
toute l'information utile de la main.

Hypothèse « sabot infini » : comme pour établir une table de stratégie de
base, on suppose que chaque tirage suit une distribution fixe indépendante
des cartes déjà sorties (P(carte de rang 2..9) = 1/13, P(dix-valeur) = 4/13,
P(As) = 1/13). C'est l'hypothèse standard utilisée pour dériver les tables
de stratégie de base publiées (elle ignore le tirage sans remise d'un sabot
fini) ; le solveur (voir ``solver.py``) est donc *composition-independent*.
"""

from __future__ import annotations

from typing import List, Tuple

#: Distribution de probabilité d'une carte tirée d'un sabot infini,
#: exprimée par sa valeur de jeu (2..9, 10 pour 10/V/D/R, 11 pour l'As).
CARD_PROBS: List[Tuple[int, float]] = [
    (2, 1 / 13), (3, 1 / 13), (4, 1 / 13), (5, 1 / 13),
    (6, 1 / 13), (7, 1 / 13), (8, 1 / 13), (9, 1 / 13),
    (10, 4 / 13),  # 10, Valet, Dame, Roi
    (11, 1 / 13),  # As
]


def add_card_value(total: int, soft: bool, card_value: int) -> Tuple[int, bool, bool]:
    """Ajoute une carte à une main représentée par ``(total, soft)``.

    Astuce classique : à tout instant, au plus un As « compte » pour 11 dans
    le meilleur total (deux As à 11 dépasseraient toujours 21). L'état
    ``(total, soft)`` — où ``soft`` signifie « un As y est compté pour 11 » —
    suffit donc à représenter n'importe quelle main, sans avoir à mémoriser
    le nombre exact d'As. Cette fonction gère les trois cas possibles quand
    le nouveau total dépasse 21 :

    1. la carte ajoutée est elle-même un As : on le rabat à 1 (softness
       préexistante inchangée) ;
    2. la main était déjà « soft » : on rabat l'As déjà présent à 1
       (la main devient « hard ») ;
    3. sinon : buste réel, aucun As à rabattre.

    :return: ``(nouveau_total, nouveau_soft, buste)``.
    """
    new_total = total + card_value
    new_card_is_ace = card_value == 11
    new_soft = soft or new_card_is_ace

    if new_total <= 21:
        return new_total, new_soft, False

    if new_card_is_ace:
        # On rabat la carte qu'on vient d'ajouter (11 -> 1). La « softness »
        # préexistante de la main, elle, ne change pas.
        demoted = new_total - 10
        return (demoted, soft, False) if demoted <= 21 else (demoted, False, True)
    if soft:
        # On rabat l'As déjà présent dans la main : elle redevient « hard ».
        demoted = new_total - 10
        return (demoted, False, False) if demoted <= 21 else (demoted, False, True)

    # Aucun As disponible pour absorber le dépassement : buste réel.
    return new_total, False, True
