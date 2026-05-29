# Script de démonstration — Blackjack POO (≤ 5 min)

> Objectif : montrer une **fonctionnalité centrale claire**, des **entrées/sorties**,
> un **résultat observable**, et glisser les points qui rapportent des points
> (architecture, tests, IA déclarée). Garder un rythme vif : on *montre*, on ne
> lit pas le code.

## Avant de commencer (à préparer)
- Terminal large, police monospace (Menlo / Fira Code) pour les cartes Unicode.
- Son activé (pour la musique d'ambiance), connexion internet (pour la webradio).
- Lancer une fois avant pour « chauffer » (sabot mélangé, pas de surprise).
- Avoir un 2e terminal prêt pour `python -m unittest`.

---

## Déroulé minuté

### 0:00 — Accroche (15 s)
« Le Blackjack contre la maison : mon projet permet d'**apprendre à bien jouer**.
Il affiche en temps réel le **meilleur coup** selon des stratégies réelles, de la
stratégie de base aux comptages de cartes, et il simule leur rentabilité. »

### 0:15 — Lancement & menu (20 s)
```bash
python -m blackjack
```
Montrer le **menu** (titre ASCII, 6 options). Dire : « interface CLI soignée avec
la librairie *rich*, entièrement en français pour un débutant ».

### 0:35 — Le Didacticiel : la fonctionnalité centrale (≈ 1 min 30)
Choisir **2 (Didacticiel)**. Jouer **une manche** :
- Souligner la **narration** (« le croupier distribue… », peek, etc.) et
  l'**animation** carte par carte.
- Montrer le **conseil de la stratégie de base** affiché à chaque tour, et la
  table des actions avec touches **françaises** (T/R/D/S).
- Jouer le coup conseillé, laisser le croupier finir, montrer le **résultat**
  (gain/perte, série de victoires).

### 2:05 — Mise façon casino & sauvegarde (30 s)
- Au moment de miser : montrer la saisie **en jetons** (pas de centime) et la
  **mise conseillée** par défaut.
- Mentionner : « le solde, les **records** et les statistiques sont **sauvegardés**
  entre les sessions ; on peut reprendre sa partie ». (Montrer le panneau records
  en quittant, si le temps le permet.)

### 2:35 — Le cœur technique : comparer les stratégies (≈ 1 min)
Revenir au menu → **4 (Comparer les stratégies)**.
- Lancer avec les valeurs par défaut. Pendant le calcul, expliquer : « un robot
  joue des milliers de mains par stratégie ; on mesure l'**espérance de gain** ».
- Sur le tableau : « la stratégie de base tend vers l'avantage de la maison ; les
  comptages, eux, **misent plus quand le sabot est favorable** et peuvent passer
  gagnants ». ← **résultat chiffré observable**, c'est le point fort.

### 3:35 — Tests (30 s) — 2e terminal
```bash
python -m unittest discover -s tests -v
```
« 94 tests automatisés : règlement des gains, comptages, sauvegarde, mise…
tout est vérifié, et la suite tourne en moins d'une seconde. »

### 4:05 — Architecture en 20 s (parler, ne pas scroller)
« Code en 5 sous-paquets — *core, players, strategies, game, ui* — illustrant les
3 piliers POO : **héritage** (Strategy → comptages), **polymorphisme**
(`recommend()`), **encapsulation** (attributs privés + properties). Le patron
**Stratégie** rend les 9 méthodes interchangeables sans toucher au moteur. »

### 4:25 — IA & clôture (35 s)
« L'IA (Claude) a été utilisée pour le boilerplate, la vérification des tables de
comptage et la rédaction ; c'est **déclaré** dans le README et la doc, avec les
prompts. J'ai conçu l'architecture, le registre de stratégies et toutes les
décisions de design. » Conclure sur une amélioration possible (index plays, GUI).

---

## Phrases-clés à ne pas oublier
- « fonctionnalité centrale : apprendre en jouant, avec conseil temps réel ».
- « résultat observable : EV chiffrée par stratégie ».
- « tests automatisés », « architecture POO », « IA déclarée ».

## Plan B si quelque chose casse
- Si le terminal est petit/cartes mal alignées : agrandir la fenêtre AVANT.
- Si pas de réseau : ne pas lancer la webradio, garder la musique générée.
- Si une manche tourne mal en live : enchaîner, ce n'est pas grave — le propos
  est la démonstration des fonctionnalités, pas de gagner.
