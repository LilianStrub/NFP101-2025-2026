"""
Point d'entrée du jeu.

Lancement :  ``python -m blackjack``
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from .core import Action
from .game import Game, Profile, load_profile, save_profile
from .players import HumanPlayer
from .strategies import (
    STRATEGIES,
    BasicStrategy,
    ManualStrategy,
    ReinforcementStrategy,
    SolverStrategy,
    Strategy,
)
from .strategies.reinforcement_strategy import Q_TABLE_PATH
from .ui import UI
from .ui.audio import WEBRADIOS, AmbientMusic
from .utils import configure_logging, load_rules

logger = logging.getLogger(__name__)


def _play_session(ui: UI) -> None:
    """Partie normale : reprise du profil sauvegardé, aide et animations au choix."""
    rules = load_rules()

    ui.header("Configuration du joueur")

    # Sauvegarde & reprise : on repart du solde sauvegardé si le joueur le souhaite.
    base = load_profile()
    if base is not None:
        if ui.ask_yes_no(f"Reprendre votre partie (solde {base.bankroll:.2f}) ?",
                         default=True):
            bankroll = base.bankroll
        else:
            bankroll = ui.ask_float("Nouveau solde de départ (votre argent de jeu, en €)",
                                    default=rules.starting_bankroll,
                                    minimum=rules.min_bet)
    else:
        base = Profile()
        bankroll = ui.ask_float("Solde de départ (votre argent de jeu, en €)", default=rules.starting_bankroll,
                                minimum=rules.min_bet)

    use_advice = ui.ask_yes_no(
        "Voulez-vous afficher l'aide d'une stratégie pendant le jeu ?",
        default=False,
    )
    strategy: Strategy = ManualStrategy()
    if use_advice:
        _, strategy = ui.choose_strategy()
    ui.learning_mode = False

    ui.write()
    ui.info("Animations : distribution carte par carte et suspense sur les "
            "tirages du croupier. Désactivez-les pour un jeu plus rapide.")
    ui.set_animations(ui.ask_yes_no("Activer les animations ?", default=True))

    player = HumanPlayer(name="Joueur", bankroll=bankroll, strategy=strategy)
    player.show_advice = use_advice and not isinstance(strategy, ManualStrategy)

    game = Game(rules=rules, player=player, strategy=strategy, ui=ui)

    # Re-cave proposée quand le solde est épuisé (montant = cave de départ).
    rebuy = max(rules.min_bet, round(rules.starting_bankroll, 2))

    def persist(peak: float, rebuys: int) -> None:
        save_profile(base.folded_with(game.stats, player.bankroll, peak, rebuys))

    _game_loop(ui, game, player, strategy, rules, bankroll,
               rebuy_amount=rebuy, persist=persist)

    # Bilan persistant : records et solde sauvegardé.
    saved = load_profile()
    if saved is not None:
        ui.show_records(saved)


def _tutorial_session(ui: UI) -> None:
    """Didacticiel : tout est commenté (narration + conseil + explications),
    animations activées, pour apprendre le jeu en débutant."""
    rules = load_rules()

    ui.header("Didacticiel — apprendre en jouant")
    ui.info("Chaque action à l'écran est commentée par le croupier, le conseil "
            "de la stratégie de base s'affiche à chaque tour, et chaque choix "
            "possible est expliqué. Idéal pour découvrir le Blackjack.")
    ui.write()
    bankroll = ui.ask_float("Solde de départ (votre argent de jeu, en €)", default=rules.starting_bankroll,
                            minimum=rules.min_bet)

    strategy: Strategy = BasicStrategy()
    ui.learning_mode = True
    ui.set_animations(True)  # animations + narration : indispensables au didacticiel

    player = HumanPlayer(name="Joueur", bankroll=bankroll, strategy=strategy)
    player.show_advice = True

    game = Game(rules=rules, player=player, strategy=strategy, ui=ui)
    rebuy = max(rules.min_bet, round(rules.starting_bankroll, 2))
    _game_loop(ui, game, player, strategy, rules, bankroll, rebuy_amount=rebuy)


def _game_loop(ui: UI, game: "Game", player: HumanPlayer,
               strategy: Strategy, rules, bankroll: float, *,
               rebuy_amount: Optional[float] = None,
               persist=None) -> None:  # noqa: ANN001
    """Boucle de manches partagée entre la partie normale et le didacticiel.

    ``rebuy_amount`` : si défini, propose de remettre une cave quand le solde
    est épuisé (au lieu de terminer). ``persist`` : callback ``(peak, rebuys)``
    appelé après chaque manche pour sauvegarder la progression.
    """
    peak = player.bankroll
    rebuys = 0
    last_bet: Optional[float] = None  # dernière mise du joueur (manches ≥ 2)

    while True:
        if player.bankroll < rules.min_bet:
            if rebuy_amount and ui.ask_yes_no(
                    f"Solde épuisé. Remettre une cave de {rebuy_amount:.2f} "
                    "pour continuer ?", default=True):
                player.credit(rebuy_amount)
                rebuys += 1
                peak = max(peak, player.bankroll)
                ui.success(f"Nouvelle cave de {rebuy_amount:.2f}. Bonne chance !")
                if persist is not None:
                    persist(peak, rebuys)
                continue
            ui.error("Plus assez d'argent pour miser. Fin de la partie.")
            break

        # En-tête de manche affiché dès que le joueur s'engage, avant la mise.
        manche = game.stats.rounds_played + 1
        ui.show_round_header(manche)
        ui.show_bankroll(player)
        if strategy.counts_cards:
            ui.show_count_status(strategy, game.shoe.decks_remaining)

        # Mise proposée par défaut :
        #  • comptage → palier 1× à 8× selon le true count (mise variable,
        #    recalculée à chaque manche car c'est tout l'intérêt du comptage) ;
        #  • sinon → 1 % du solde à la 1re manche, puis on conserve la dernière
        #    mise du joueur (elle ne « bouge » plus à chaque gain/perte).
        if strategy.counts_cards:
            unit = max(rules.min_bet, round(player.bankroll * 0.01, 2))
            unit = min(unit, rules.max_bet)
            suggested = game.suggested_bet(unit)
            ui.info("Mise conseillée selon le comptage (plus le sabot est "
                    "favorable, plus elle augmente).")
        elif last_bet is None:
            suggested = min(max(rules.min_bet, round(player.bankroll * 0.01, 2)),
                            rules.max_bet)
        else:
            suggested = last_bet
        bet = ui.ask_bet(
            default=min(suggested, player.bankroll),
            minimum=rules.min_bet,
            maximum=min(rules.max_bet, player.bankroll),
        )
        last_bet = bet  # mémorisée pour servir de défaut à la manche suivante

        try:
            results = game.play_round(bet)
        except ValueError as exc:
            ui.error(str(exc))
            continue

        ui.show_round_results(results)
        peak = max(peak, player.bankroll)
        ui.show_streak(game.stats.current_win_streak)
        if persist is not None:
            persist(peak, rebuys)

        if not ui.ask_yes_no("Jouer une autre manche ?", default=True):
            break

    ui.show_stats(game.stats)


def _sim_bet(strategy: Strategy, game: "Game", rules, base_unit: float) -> float:
    """Mise d'une manche en simulation.

    Pour un compteur, on mise davantage quand le sabot est favorable (palier
    1× → 8× selon le true count, plafonné par la mise max). Pour les autres,
    la mise reste fixe (l'unité de base).
    """
    if strategy.counts_cards:
        return strategy.betting_units(game.shoe.decks_remaining, base_unit,
                                      rules.max_bet)
    return base_unit


def _compare_strategies(ui: UI) -> None:
    """Mode simulation : compare les stratégies sur plusieurs milliers de mains."""
    ui.header("Mode simulation comparative")

    # Explication : pourquoi ce mode existe et comment lire le tableau.
    ui.info("Un robot joue automatiquement des milliers de mains avec chaque "
            "stratégie, puis on compare leurs résultats.")
    ui.write()
    ui.write(f"  • {'EV par main':<11} : gain net moyen par unité misée. Négatif "
             "= avantage du casino ; proche de 0 ou positif = favorable au joueur.")
    ui.write(f"  • {'Win %':<11} : part de mains gagnées.")
    ui.write(f"  • {'BJ %':<11} : part de blackjacks naturels.")
    ui.write()
    ui.info("La stratégie de base ramène l'EV tout près de l'avantage de la "
            "maison. Les stratégies de comptage MISENT PLUS quand le sabot est "
            "favorable (mise variable selon le « true count ») : leur EV peut "
            "alors devenir meilleure, voire positive.")
    ui.info("Plus le nombre de manches est grand, plus le résultat est fiable.")

    rules = load_rules()

    # Boucle : on peut enchaîner plusieurs simulations sans revenir au menu.
    while True:
        ui.write()
        n_rounds = ui.ask_int("Combien de manches simuler par stratégie ?",
                               default=5000, minimum=100, maximum=50000)
        bet_size = ui.ask_float("Mise de base (unité ; les compteurs misent 1× à 8×)",
                                default=10.0, minimum=0.5, maximum=1000.0)

        ui.write()
        ui.info("Simulation en cours… une ligne s'affiche au fur et à mesure que "
                "chaque stratégie termine (augmentez le nombre de manches pour plus "
                "de fiabilité, au prix d'un calcul plus long).")
        ui.write()
        ui.write(f"{'Stratégie':<38}{'EV par main':>16}{'Win %':>10}{'BJ %':>10}")
        ui.write("─" * 74)
        for key, cls in STRATEGIES.items():
            if cls is ManualStrategy:
                continue
            # Le joueur de simu utilise la *même* stratégie pour décider.
            strategy = cls()
            sim_player = HumanPlayer(name="SimBot", bankroll=1e9, strategy=strategy)
            sim_player.ui = _SilentUI(strategy)
            game = Game(rules=rules, player=sim_player, strategy=strategy, ui=None)
            for _ in range(n_rounds):
                try:
                    game.play_round(_sim_bet(strategy, game, rules, bet_size))
                except ValueError:
                    break
            ev = game.stats.expected_value * 100
            wr = game.stats.win_rate * 100
            bj = (game.stats.blackjacks / game.stats.hands_played * 100
                  if game.stats.hands_played else 0.0)
            ui.write(f"{cls.name:<38}{ev:>+15.3f}%{wr:>9.2f}%{bj:>9.2f}%")
        ui.write()
        ui.info("Lecture : la stratégie de base mise à plat et tend vers l'avantage "
                "de la maison (≈ -0,5 %). Les comptages varient leur mise sur les "
                "sabots favorables et peuvent dégager une EV positive — c'est "
                "l'essence du comptage.")
        ui.info("Attention : avec une mise variable, la variance est forte. Sur peu "
                "de manches, le hasard domine (un compteur peut sembler moins bon). "
                "Augmentez fortement le nombre de manches (p. ex. 50000) pour voir "
                "l'avantage se confirmer.")

        ui.write()
        if not ui.ask_yes_no("Lancer une autre simulation ?", default=False):
            break


def _watch_ai_session(ui: UI) -> None:
    """Regarder un agent IA (solveur exact ou Q-learning) jouer seul.

    Reprend telles quelles les animations, la narration et l'audio de la
    partie normale : seule la décision de jeu change de main (l'IA choisit
    l'action au lieu du joueur), via :class:`_AutoPlayUI`.
    """
    ui.header("Regarder l'IA jouer")
    ui.info("Un agent IA joue à votre place, avec les mêmes animations et le "
            "même suspense qu'en partie normale. Deux façons radicalement "
            "différentes d'arriver à jouer : le solveur calcule "
            "l'espérance de gain (EV) de chaque action par recherche exacte "
            "(expectiminimax) ; l'agent Q-learning l'a apprise en jouant "
            "3 millions de mains contre lui-même, sans qu'on lui fournisse "
            "aucune règle de décision au départ.")
    ui.info("À chaque tour, un panneau détaille l'EV (ou la Q-value apprise) "
            "de chaque action envisagée, triée de la meilleure à la pire : "
            "c'est ce qui explique *pourquoi* l'action retenue (flèche) l'a "
            "été, et de combien elle vaut mieux que les autres. Repérez les "
            "coups qui vous surprennent (tirer sur 16, par exemple) : ce "
            "n'est presque jamais une erreur, mais un signe que l'intuition "
            "et le calcul divergent — le détail affiché vous dit pourquoi.")
    ui.write()

    rules = load_rules()
    agents = [("Solveur (recherche exacte)", lambda: SolverStrategy(rules))]
    if Q_TABLE_PATH.exists():
        agents.append(("Agent Q-learning", lambda: ReinforcementStrategy(rules)))
    else:
        ui.info("(Agent Q-learning indisponible : data/q_table.json est absent.)")
    for i, (label, _) in enumerate(agents, start=1):
        ui.write(f"  {i}. {label}")
    choice = ui.ask_int("Quel agent regarder ?", default=1, minimum=1, maximum=len(agents))
    strategy: Strategy = agents[choice - 1][1]()

    ui.set_animations(ui.ask_yes_no("Activer les animations ?", default=True))
    n = ui.ask_int("Combien de manches ?", default=5, minimum=1, maximum=1000)

    player = HumanPlayer(name=strategy.name, bankroll=rules.starting_bankroll, strategy=strategy)
    game = Game(rules=rules, player=player, strategy=strategy, ui=_AutoPlayUI(ui, strategy))

    for _ in range(n):
        if player.bankroll < rules.min_bet:
            ui.error("Solde épuisé.")
            break
        ui.show_round_header(game.stats.rounds_played + 1)
        ui.show_bankroll(player)
        results = game.play_round(bet=rules.min_bet)
        ui.show_round_results(results)

    ui.show_stats(game.stats)
    ui.info("Sur si peu de manches, le résultat (gain/perte) est surtout du "
            "hasard — ce n'est pas là-dessus qu'il faut juger un agent. Pour "
            "un jugement chiffré et fiable, comparez les stratégies au "
            "menu 4 sur plusieurs milliers de manches simulées.")


def _about(ui: UI) -> bool:
    """Affiche l'aide / à-propos. Renvoie True pour revenir au menu, False pour
    quitter le jeu."""
    ui.header("À propos / Aide")
    ui.write("""
  Projet pédagogique — NFP01 (CNAM) : Blackjack en Python orienté objet.

  Comment jouer :
    • Au menu, choisissez un mode (1 à 6).
    • Pendant une main, tapez la lettre de l'action — h (tirer), s (rester),
      d (doubler), p (séparer) — ou le mot entier (« tirer », « rester »…).

  Les modes :
    • 1  Nouvelle partie — reprend votre solde sauvegardé si vous le souhaitez.
    • 2  Didacticiel — tout est commenté pas à pas, idéal pour débuter.
    • 3  Règles du jeu — récapitulatif complet et illustré.
    • 4  Comparer les stratégies — simulation chiffrée sur des milliers de mains.
    • 6  Musique d'ambiance — morceau de lounge généré ou webradio (SomaFM…).

  Aide à la décision : stratégie de base + 7 comptages (Hi-Lo, KO, Hi-Opt I/II,
  Omega II, Zen, Red 7), avec mise conseillée selon le « true count ».

  Confort & progression :
    • Animations et narration activables (le croupier « parle » en didacticiel).
    • Solde, statistiques et records sauvegardés entre les sessions ; re-cave
      possible en cas de faillite ; séries de victoires affichées.
    • Assurance proposée quand le croupier montre un As.

  Règles de la table (modifiables dans config/default.json) :
    6 jeux, croupier reste sur 17, double sur durs 9-11, blackjack payé 3:2,
    carte cachée + vérification (peek). Journaux dans logs/blackjack.log,
    profil dans ~/.blackjack_profile.json.

  Sources de référence pour les stratégies :
    • E. O. Thorp,    Beat the Dealer
    • S. Wong,        Professional Blackjack
    • D. Schlesinger, Blackjack Attack
    • A. Snyder,      Blackbelt in Blackjack
    • B. Carlson,     Blackjack for Blood
""")
    ui.write()
    return ui.ask_yes_no("Revenir à l'écran d'accueil ?", default=True)


class _SilentUI:
    """Faux UI utilisé en mode simulation : auto-décide selon la stratégie."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy

    def prompt_action(self, player, hand, dealer_up, advice=None, rules=None, hand_index=0):  # noqa: ANN001, ARG002
        action = self.strategy.recommend(hand, dealer_up)
        # Filet de sécurité : si l'action n'est pas faisable, basculer en sécurité.
        if action.name == "DOUBLE" and not hand.can_double:
            return _safe_fallback(action)
        if action.name == "SPLIT" and not hand.can_split:
            return _safe_fallback(action)
        if action.name == "SURRENDER" and not hand.can_surrender:
            return _safe_fallback(action)
        return action

    # Les autres callbacks ne font rien.
    def narrate(self, *a, **k): pass                   # noqa: E704
    def show_pre_deal(self, *a, **k): pass             # noqa: E704
    def show_deal_step(self, *a, **k): pass            # noqa: E704
    def show_split_step(self, *a, **k): pass           # noqa: E704
    def show_initial_deal(self, *a, **k): pass        # noqa: D401, E704
    def show_dealer_reveal(self, *a, **k): pass       # noqa: E704
    def show_showdown(self, *a, **k): pass            # noqa: E704
    def show_dealer_draw(self, *a, **k): pass         # noqa: E704
    def show_action(self, *a, **k): pass              # noqa: E704
    def show_player_hand(self, *a, **k): pass         # noqa: E704
    def show_shuffle(self, *a, **k): pass             # noqa: E704
    def show_round_results(self, *a, **k): pass       # noqa: E704


class _AutoPlayUI:
    """UI pour le mode « Regarder l'IA jouer » : délègue tout (animations,
    narration, audio…) à la vraie UI, sauf la décision de jeu, prise
    automatiquement par la stratégie IA au lieu d'être demandée au clavier."""

    def __init__(self, ui: UI, strategy: Strategy) -> None:
        self._ui = ui
        self._strategy = strategy

    def prompt_action(self, player, hand, dealer_up, advice=None, rules=None,  # noqa: ANN001, ARG002
                       hand_index: int = 0) -> Action:
        explain = getattr(self._strategy, "explain", None)
        if explain is not None:
            decision = explain(hand, dealer_up)
            self._ui.show_ai_decision(hand, dealer_up, decision, self._strategy.name)
            action = decision.action
        else:
            action = self._strategy.recommend(hand, dealer_up)
        if action is Action.DOUBLE and not hand.can_double:
            return _safe_fallback(action)
        if action is Action.SPLIT and not hand.can_split:
            return _safe_fallback(action)
        if action is Action.SURRENDER and not hand.can_surrender:
            return _safe_fallback(action)
        return action

    def prompt_insurance(self, player, dealer, max_insurance: float) -> float:  # noqa: ANN001, ARG002
        """Décide l'assurance via la stratégie au lieu de la demander au
        clavier (sinon le mode auto-play resterait bloqué sur un
        ``input()`` dès que le croupier montre un As)."""
        return max_insurance if self._strategy.take_insurance() else 0.0

    def __getattr__(self, name):  # noqa: ANN001
        return getattr(self._ui, name)


def _safe_fallback(action):  # noqa: ANN001
    from .core import Action
    if action is Action.DOUBLE:
        return Action.HIT
    if action is Action.SPLIT:
        return Action.HIT
    if action is Action.SURRENDER:
        return Action.HIT
    return Action.STAND


def _choose_music_source(ui: UI) -> Optional[str]:
    """Laisse choisir la source : morceau généré (None) ou une webradio lounge."""
    ui.write()
    ui.info("Source de la musique d'ambiance :")
    ui.write("  1   Morceau d'ambiance généré (hors-ligne)")
    for i, (label, _) in enumerate(WEBRADIOS, start=2):
        ui.write(f"  {i}   Webradio — {label}")
    choice = ui.ask_int("Votre choix", default=1, minimum=1,
                        maximum=1 + len(WEBRADIOS))
    if choice == 1:
        return None
    return WEBRADIOS[choice - 2][1]


def _toggle_music(ui: UI, music: AmbientMusic) -> None:
    """Active/coupe la musique d'ambiance et informe le joueur."""
    if music.enabled:
        music.stop()
        ui.info("Musique d'ambiance coupée.")
        return

    # Choix de la source (sauf si imposée par BLACKJACK_MUSIC).
    if not music.has_fixed_source:
        music.set_source(_choose_music_source(ui))

    if not music.available():
        if music.is_webradio:
            ui.warn("Webradio indisponible : il faut ffplay, mpg123 ou cvlc "
                    "(afplay ne lit pas les flux réseau).")
        else:
            ui.warn("Aucun lecteur audio trouvé (afplay, aplay, paplay, ffplay…).")
        return

    if music.start():
        ui.success("Musique d'ambiance activée.")
        if music.is_webradio:
            ui.info("Connexion à la webradio en cours (nécessite une connexion "
                    "internet).")
        elif music.using_generated:
            ui.info("Astuce : BLACKJACK_MUSIC=<dossier|fichier|URL> pour brancher "
                    "votre propre playlist de casino.")
    else:
        ui.warn("Source musicale introuvable ou vide "
                "(vérifiez la variable BLACKJACK_MUSIC).")


def main(argv: Optional[list] = None) -> int:
    """Point d'entrée CLI."""
    configure_logging()
    ui = UI()
    music = AmbientMusic()
    try:
        while True:
            choice = ui.main_menu(music_on=music.enabled,
                                  music_available=music.available())
            if choice == "1":
                _play_session(ui)
            elif choice == "2":
                _tutorial_session(ui)
            elif choice == "3":
                ui.show_rules()
            elif choice == "4":
                _compare_strategies(ui)
            elif choice == "5":
                if not _about(ui):
                    ui.success("Au revoir !")
                    return 0
            elif choice == "6":
                _toggle_music(ui, music)
            elif choice == "7":
                _watch_ai_session(ui)
            elif choice == "0":
                ui.success("Au revoir !")
                return 0
            else:
                ui.error("Choix invalide.")
    except (KeyboardInterrupt, EOFError):
        ui.write()
        ui.success("Au revoir !")
        return 0
    finally:
        music.stop()


if __name__ == "__main__":
    sys.exit(main())
