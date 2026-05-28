"""
Outil de prévisualisation du rendu (développement).

Permet de forcer une situation précise (ex. : croupier avec un 10) afin de
vérifier visuellement le rendu dans le terminal, sans dépendre du hasard du
sabot.

Lancement :
    python scripts/preview.py

Deux approches sont fournies :
  - ``preview_full_round`` : truque le sabot et joue une VRAIE manche complète
    (animations, narration, prompts) — le plus fidèle.
  - ``preview_table`` : affiche directement la table d'un coup, sans logique de
    jeu (le plus rapide pour ajuster un détail d'affichage).

Modifie ``main()`` pour choisir la situation à observer.
"""

from __future__ import annotations

import builtins
import pathlib
import sys

# Permet de lancer le script même sans `pip install -e .` (layout src/).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from blackjack.core import Action, Card, Hand, Shoe  # noqa: E402
from blackjack.core.enums import Rank, Suit  # noqa: E402
from blackjack.game import Game  # noqa: E402
from blackjack.players import HumanPlayer  # noqa: E402
from blackjack.strategies import BasicStrategy  # noqa: E402
from blackjack.ui import UI  # noqa: E402
from blackjack.utils import load_rules  # noqa: E402


def force_next_cards(shoe: Shoe, draw_order: list[Card]) -> None:
    """Place des cartes précises au sommet du sabot.

    ``draw_order`` = cartes dans l'ordre où elles seront TIRÉES. En mode peek
    (règle par défaut), l'ordre de distribution d'une manche est :
        1) carte cachée du croupier
        2) 1re carte du joueur
        3) carte visible du croupier  ← « 1re carte visible » du croupier
        4) 2e carte du joueur
    Les cartes suivantes (tirages du croupier, hits) restent aléatoires.
    """
    internal = shoe._Shoe__cards  # liste interne ; draw() retire la dernière
    internal.extend(reversed(draw_order))


def preview_full_round() -> None:
    """Joue une manche complète avec une situation imposée (interactif)."""
    ui = UI()
    ui.learning_mode = True
    ui.set_animations(False)  # ni animations ni narration

    rules = load_rules()
    strat = BasicStrategy()
    player = HumanPlayer(name="Joueur", bankroll=100.0, strategy=strat)
    game = Game(rules=rules, player=player, strategy=strat, ui=ui, seed=1)

    # ↓↓↓ Situation à observer : croupier 10 (carte visible), joueur 8 + 8 ↓↓↓
    force_next_cards(game.shoe, [
        Card(Rank.ACE, Suit.SPADES),    # croupier — carte cachée
        Card(Rank.EIGHT, Suit.HEARTS),   # joueur   — 1re carte
        Card(Rank.TEN, Suit.DIAMONDS),   # croupier — carte visible
        Card(Rank.EIGHT, Suit.CLUBS),    # joueur   — 2e carte
    ])

    ui.show_round_header(game.stats.rounds_played + 1)
    ui.show_bankroll(player)
    results = game.play_round(bet=10.0)
    ui.show_round_results(results)


def preview_table(dealer_up: Card, player_cards: list[Card], bet: float = 10.0) -> None:
    """Affiche la table (croupier + main + actions) sans jouer ni bloquer."""
    ui = UI()
    ui.learning_mode = True
    ui.set_animations(False)  # ni animations ni narration
    rules = load_rules()

    hand = Hand(bet=bet)
    for c in player_cards:
        hand.add_card(c)
    player = HumanPlayer(name="Joueur", bankroll=100.0, strategy=BasicStrategy())
    player.add_hand(hand)

    # Auto-répond "s" pour rendre la table puis sortir sans interaction.
    original_input = builtins.input
    builtins.input = lambda *a, **k: "s"
    try:
        ui.prompt_action(player, hand, dealer_up, advice=Action.STAND, rules=rules)
    finally:
        builtins.input = original_input


def main() -> None:
    preview_full_round()

    # Variante rapide, sans jouer (décommente pour l'utiliser) :
    preview_table(
        dealer_up=Card(Rank.TEN, Suit.SPADES),
        player_cards=[Card(Rank.EIGHT, Suit.HEARTS), Card(Rank.EIGHT, Suit.CLUBS)],
    )


if __name__ == "__main__":
    main()
