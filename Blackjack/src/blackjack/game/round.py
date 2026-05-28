"""
Module ``round`` — orchestration d'une manche complète.

Sépare proprement la *logique d'une donne* (distribution, tour du joueur,
tour du croupier, paiement) du *contrôleur de partie* (boucle principale,
gestion du sabot, statistiques).
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from ..core import Action, Card, Hand, Outcome, Shoe
from ..players import Dealer, HumanPlayer
from ..strategies import Strategy
from .rules import Rules

logger = logging.getLogger(__name__)


class Round:
    """Une manche : du « faites vos jeux » au paiement."""

    def __init__(self, rules: Rules, shoe: Shoe, dealer: Dealer,
                 player: HumanPlayer, strategy: Strategy,
                 ui: "Optional[object]" = None) -> None:  # noqa: ANN001
        self.rules = rules
        self.shoe = shoe
        self.dealer = dealer
        self.player = player
        self.strategy = strategy
        self.ui = ui  # peut être None (mode silencieux pour les tests).

    # ------------------------------------------------------------------ #
    # Utilitaire : notification UI + observation par la stratégie
    # ------------------------------------------------------------------ #
    def _deal_card(self, hand: Hand) -> Card:
        card = self.shoe.draw()
        hand.add_card(card)
        # Observation pour le comptage (polymorphisme : observe peut être no-op).
        self.strategy.observe(card)
        return card

    # ------------------------------------------------------------------ #
    # Étapes d'une manche
    # ------------------------------------------------------------------ #
    def play(self, bet: float) -> List[Tuple[Hand, Outcome, float]]:
        """Joue une manche complète et renvoie la liste (main, issue, gain net)."""
        bet = max(self.rules.min_bet, min(bet, self.rules.max_bet))
        if bet > self.player.bankroll:
            raise ValueError("Mise supérieure au solde du joueur")
        self.player.debit(bet)

        # Préparation
        self.player.reset_hands()
        self.dealer.reset_hands()
        initial_hand = Hand(bet=bet)
        self.player.add_hand(initial_hand)
        self.dealer.add_hand(Hand())

        self._insurance_bet: float = 0.0

        if self.rules.no_hole_card:
            return self._play_enhc(initial_hand)
        else:
            return self._play_peek(initial_hand)

    # ------------------------------------------------------------------ #
    # Flux ENHC (European No Hole Card) — casinos français
    # ------------------------------------------------------------------ #
    def _play_enhc(self, initial_hand: Hand) -> List[Tuple[Hand, Outcome, float]]:
        """Distribution et résolution sans carte cachée (règle européenne)."""
        if self.ui is not None:
            self.ui.narrate("Nouvelle donne. Ici le croupier ne prend pas de carte "
                            "cachée : il ne tirera sa 2e carte qu'après votre tour.")
            self.ui.show_pre_deal(self.player, self.dealer, hide_hole=False)
        if self.ui is not None:
            self.ui.narrate("Votre première carte.", pause=False)
        self._deal_card(initial_hand)
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=False)

        if self.ui is not None:
            self.ui.narrate("La carte visible du croupier.", pause=False)
        self._deal_card(self.dealer.hand)
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=False)

        if self.ui is not None:
            self.ui.narrate("Votre deuxième carte.", pause=False)
        self._deal_card(initial_hand)
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=False)
            self.ui.show_initial_deal(self.player, self.dealer)

        # Blackjack joueur détecté dès le départ (le croupier n'a qu'une carte,
        # donc pas encore de blackjack possible côté croupier).
        player_bj = initial_hand.is_blackjack

        # Assurance proposée si le croupier montre un As.
        if self.rules.insurance_allowed and self.dealer.hand.cards[0].is_ace:
            self._offer_insurance(initial_hand)

        # Tour du joueur — si blackjack naturel, afficher les mains sans actions.
        if not player_bj:
            if self.ui is not None:
                self.ui.narrate("À vous de jouer.")
            self._play_player_hands()
        elif self.ui is not None:
            self.ui.narrate("Vous avez un Blackjack naturel !")
            self.ui.show_deal_state(self.player, self.dealer)

        # Le croupier tire maintenant sa 2e carte (et les suivantes si besoin).
        if self.ui is not None:
            self.ui.narrate("Le croupier tire enfin sa deuxième carte.", pause=False)
        self._deal_card(self.dealer.hand)
        dealer_bj = self.dealer.hand.is_blackjack

        if self.ui is not None:
            self.ui.show_dealer_reveal(self.dealer)

        # Paiement de l'assurance.
        if self._insurance_bet > 0:
            if dealer_bj:
                # Assurance gagnée : 2:1 (on rend la mise + le double).
                self.player.credit(self._insurance_bet * 3)
            if self.ui is not None:
                self.ui.show_insurance_result(dealer_bj, self._insurance_bet)

        # Si blackjack joueur ET blackjack croupier → égalité.
        if player_bj or dealer_bj:
            return self._settle(player_blackjack=player_bj,
                                dealer_blackjack=dealer_bj)

        # Tour normal du croupier (tire si nécessaire).
        self._play_dealer()
        return self._settle()

    # ------------------------------------------------------------------ #
    # Flux avec hole card + peek (règle française)
    # ------------------------------------------------------------------ #
    def _play_peek(self, initial_hand: Hand) -> List[Tuple[Hand, Outcome, float]]:
        """Distribution avec hole card et peek silencieux (casinos français)."""
        if self.ui is not None:
            self.ui.narrate("Nouvelle donne. Le croupier distribue les cartes une à une.")
            self.ui.show_pre_deal(self.player, self.dealer, hide_hole=True)
        # Hole card d'abord, cachée et non observée par le compteur.
        if self.ui is not None:
            self.ui.narrate("Le croupier se donne d'abord une carte face cachée, "
                            "la « carte du trou ».", pause=False)
        self._deal_card(self.dealer.hand)
        hole = self.dealer.hand.cards[0]
        self.strategy._running_count -= self.strategy.card_value(hole)
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=True)

        if self.ui is not None:
            self.ui.narrate("Votre première carte, face visible.", pause=False)
        self._deal_card(initial_hand)             # joueur 1re carte
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=True)

        if self.ui is not None:
            self.ui.narrate("Le croupier retourne sa carte visible.", pause=False)
        self._deal_card(self.dealer.hand)         # up card visible
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=True)

        if self.ui is not None:
            self.ui.narrate("Votre deuxième carte, face visible.", pause=False)
        self._deal_card(initial_hand)             # joueur 2e carte
        if self.ui is not None:
            self.ui.show_deal_step(self.player, self.dealer, hide_hole=True)
            self.ui.show_initial_deal(self.player, self.dealer)

        player_bj = initial_hand.is_blackjack
        up = self.dealer.up_card  # cards[1]

        # Assurance proposée uniquement quand le croupier montre un As.
        if up.is_ace and self.rules.insurance_allowed:
            self._offer_insurance(initial_hand)

        # Le croupier ne vérifie sa carte cachée que si sa carte visible peut
        # compléter un Blackjack (un As ou une carte à 10).
        peek_possible = up.is_ace or up.value == 10
        if peek_possible and self.ui is not None:
            self.ui.narrate("Le croupier jette un œil discret à sa carte cachée "
                            "pour vérifier s'il a un Blackjack.")
        dealer_bj = self.dealer.hand.is_blackjack

        if dealer_bj:
            # Révélation immédiate de la hole card.
            self.strategy.observe(hole)
            if self._insurance_bet > 0:
                self.player.credit(self._insurance_bet * 3)
            if self.ui is not None:
                self.ui.narrate("Le croupier a un Blackjack ! Il dévoile sa carte cachée.",
                                pause=False)
                self.ui.show_showdown(self.player, self.dealer)
                if self._insurance_bet > 0:
                    self.ui.show_insurance_result(True, self._insurance_bet)
            return self._settle(player_blackjack=player_bj, dealer_blackjack=True)

        # Pas de blackjack : assurance perdue si elle a été prise.
        if self._insurance_bet > 0 and self.ui is not None:
            self.ui.show_insurance_result(False, self._insurance_bet)

        # Tour du joueur — si blackjack naturel, afficher les mains sans actions.
        if not player_bj:
            if self.ui is not None:
                if peek_possible:
                    self.ui.narrate("Pas de Blackjack pour le croupier. À vous de jouer.")
                else:
                    self.ui.narrate("À vous de jouer.")
            self._play_player_hands()
        elif self.ui is not None:
            self.ui.narrate("Vous avez un Blackjack naturel ! Vous êtes payé immédiatement.")
            self.ui.show_deal_state(self.player, self.dealer)

        # Révélation de la hole card.
        self.strategy.observe(hole)
        if self.ui is not None:
            self.ui.narrate("Le croupier dévoile sa carte cachée.", pause=False)
            self.ui.show_dealer_reveal(self.dealer, revealed=hole)
        # Blackjack joueur : le croupier ne joue pas, le joueur gagne immédiatement.
        if not player_bj:
            self._play_dealer()
        return self._settle(player_blackjack=player_bj, dealer_blackjack=False)

    # ------------------------------------------------------------------ #
    # Assurance
    # ------------------------------------------------------------------ #
    def _offer_insurance(self, initial_hand: Hand) -> None:
        """Propose l'assurance ; débite la mise si le joueur accepte."""
        max_ins = initial_hand.bet / 2
        if self.ui is None:
            return
        amount = self.ui.prompt_insurance(self.player, self.dealer, max_ins)
        if amount > 0:
            amount = min(amount, max_ins)
            self.player.debit(amount)
            self._insurance_bet = amount

    # ------------------------------------------------------------------ #
    # Restriction de double (règle française)
    # ------------------------------------------------------------------ #
    def _can_double(self, hand: Hand) -> bool:
        """Vérifie si le double est autorisé selon les règles courantes."""
        if not hand.can_double:
            return False
        if self.rules.double_hard_9_to_11_only:
            return not hand.is_soft and hand.total in (9, 10, 11)
        return True

    # ------------------------------------------------------------------ #
    def _play_player_hands(self) -> None:
        """Joue toutes les mains du joueur (gère les splits dynamiquement)."""
        i = 0
        # On itère par index car ``add_hand`` peut allonger la liste.
        while i < len(self.player.hands):
            hand = self.player.hands[i]
            self._play_one_hand(hand, hand_index=i)
            i += 1

    def _play_one_hand(self, hand: Hand, hand_index: int = 0) -> None:
        """Joue une main jusqu'à STAND, BUST ou 21."""
        last_action: Optional[Action] = None
        while not hand.is_done:
            action = self.player.decide(hand, self.dealer.up_card,
                                        rules=self.rules,
                                        hand_index=hand_index)
            self._apply_action(hand, action)
            last_action = action
            if self.ui is not None:
                self.ui.show_action(self.player, hand, action)
                # Tirage : on annonce la distribution puis on laisse un léger
                # suspense avant la révélation de la carte (au tour suivant).
                if action is Action.HIT:
                    self.ui.narrate("Le croupier vous distribue une carte.",
                                    pause=False)
                    if not hand.is_done:
                        self.ui.pause_suspense()
        if self.ui is None:
            return
        # La main s'est terminée sur un tirage qui dépasse 21 : suspense, puis
        # on la montre (avec la carte de trop) et on annonce qu'elle est brûlée.
        if hand.is_bust:
            self.ui.pause_suspense()
            self.ui.show_player_hand(self.player, hand)
            self.ui.narrate("Vous avez dépassé 21 : votre main est brûlée.",
                            pause=False)
        # Double : une seule carte est tirée puis on s'arrête — on montre la main.
        elif last_action is Action.DOUBLE:
            self.ui.narrate("Vous avez doublé : une seule carte est tirée, "
                            "puis la main s'arrête.", pause=False)
            self.ui.pause_suspense()
            self.ui.show_player_hand(self.player, hand)
        # Tirage atteignant exactement 21 : la main s'arrête, on la révèle.
        elif last_action is Action.HIT:
            self.ui.pause_suspense()
            self.ui.show_player_hand(self.player, hand)

    def _apply_action(self, hand: Hand, action: Action) -> None:
        if action is Action.HIT:
            self._deal_card(hand)
            return
        if action is Action.STAND:
            hand.stand()
            return
        if action is Action.DOUBLE:
            if not self._can_double(hand):
                # Sécurité : si une UI propose Double à tort, on transforme en hit.
                self._deal_card(hand)
                hand.stand()
                return
            self.player.debit(hand.bet)  # on double la mise
            hand.double()
            self._deal_card(hand)
            return
        if action is Action.SURRENDER:
            if not hand.can_surrender or not self.rules.surrender_allowed:
                # Convertit en HIT par défaut (cas dégénéré).
                self._deal_card(hand)
                return
            hand.surrender()
            return
        if action is Action.SPLIT:
            self._split(hand)
            return

    def _split(self, hand: Hand) -> None:
        if not hand.can_split:
            return
        # Compte les mains déjà ouvertes pour respecter max_splits.
        if len(self.player.hands) > self.rules.max_splits:
            return
        # Restriction : ré-split d'As souvent interdit.
        if hand.cards[0].is_ace and not self.rules.resplit_aces and any(
            (h is not hand) and h.cards and h.cards[0].is_ace
            for h in self.player.hands
        ):
            return

        second_card = hand.remove_last_card()
        new_hand = Hand(bet=hand.bet)
        new_hand.from_split = True
        hand.from_split = True
        new_hand.add_card(second_card)
        # Le joueur paie une seconde mise égale à la première.
        self.player.debit(hand.bet)
        self.player.add_hand(new_hand)

        # Animation : la paire se sépare en deux mains, puis chacune reçoit une carte.
        if self.ui is not None:
            self.ui.narrate("Vous séparez votre paire en deux mains distinctes.")
            self.ui.show_split_step(self.player)

        self._deal_card(hand)
        if self.ui is not None:
            self.ui.narrate("Une nouvelle carte pour la première main.", pause=False)
            self.ui.show_split_step(self.player)

        self._deal_card(new_hand)
        if self.ui is not None:
            self.ui.narrate("Une nouvelle carte pour la seconde main.", pause=False)
            self.ui.show_split_step(self.player)

        # Règle classique : une seule carte par As splittée.
        if hand.cards[0].is_ace:
            hand.stand()
            new_hand.stand()

    def _play_dealer(self) -> None:
        """Tour du croupier : tire selon la règle S17/H17."""
        # Inutile de jouer si toutes les mains du joueur sont busts/surrendered.
        live_hands = [
            h for h in self.player.hands
            if not h.is_bust and not h.surrendered
        ]
        if not live_hands:
            return
        if self.ui is not None:
            regle = ("Le croupier tire tant qu'il n'a pas 17, puis s'arrête "
                     "(il reste même sur un 17 « soft »)."
                     if not self.rules.dealer_hits_soft_17 else
                     "Le croupier tire tant qu'il n'a pas 17 (et sur un 17 « soft »).")
            self.ui.narrate(regle)
        while True:
            action = self.dealer.decide(self.dealer.hand, self.dealer.up_card)
            if action is Action.STAND:
                break
            self._deal_card(self.dealer.hand)
            if self.ui is not None:
                self.ui.show_dealer_draw(self.dealer)
            if self.dealer.hand.is_bust:
                if self.ui is not None:
                    self.ui.show_dealer_bust(self.dealer)
                break

    # ------------------------------------------------------------------ #
    # Liquidation
    # ------------------------------------------------------------------ #
    def _settle(self, player_blackjack: bool = False,
                 dealer_blackjack: bool = False
                 ) -> List[Tuple[Hand, Outcome, float]]:
        """Calcule les gains/pertes pour chaque main."""
        results: List[Tuple[Hand, Outcome, float]] = []
        dealer_total = self.dealer.hand.total
        dealer_bust = self.dealer.hand.is_bust

        for hand in self.player.hands:
            outcome, payout = self._resolve_hand(
                hand, dealer_total, dealer_bust,
                player_blackjack=player_blackjack,
                dealer_blackjack=dealer_blackjack,
            )
            if payout > 0:
                self.player.credit(payout)
            results.append((hand, outcome, payout - hand.bet))
        return results

    def _resolve_hand(self, hand: Hand, dealer_total: int, dealer_bust: bool,
                       *, player_blackjack: bool, dealer_blackjack: bool
                       ) -> Tuple[Outcome, float]:
        """Détermine l'issue et la somme à reverser pour une main."""
        bet = hand.bet  # /!\ : bet déjà doublé si double.

        # Cas spécifiques aux blackjacks naturels (au coup initial).
        if player_blackjack and dealer_blackjack:
            return Outcome.PUSH, bet
        if player_blackjack:
            return Outcome.BLACKJACK, bet + bet * self.rules.blackjack_payout
        if dealer_blackjack:
            # En ENHC le joueur perd sa mise totale (y compris doublée/splittée).
            return Outcome.LOSS, 0.0

        if hand.surrendered:
            return Outcome.SURRENDER, bet / 2

        if hand.is_bust:
            return Outcome.BUST, 0.0

        if dealer_bust:
            return Outcome.WIN, bet * 2

        total = hand.total
        if total > dealer_total:
            return Outcome.WIN, bet * 2
        if total == dealer_total:
            return Outcome.PUSH, bet
        return Outcome.LOSS, 0.0
