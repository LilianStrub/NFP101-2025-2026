# Documentation détaillée — Blackjack POO

## 1. Contexte et besoin

Projet personnel rendu dans le cadre du module **NFP01 – Programmation
Orientée Objet en Python, Java et autres** (CNAM, 2025-2026,
M. Adrien Escourrou).

Le sujet est libre, sous trois contraintes : logique significative,
projet entièrement fini, et exigences minimales (modules, I/O, tests,
documentation). Le sujet retenu — un **jeu de Blackjack** — coche
toutes ces cases tout en offrant un terrain idéal pour démontrer
l'héritage, le polymorphisme et l'encapsulation.

Au-delà du jeu lui-même, l'objectif pédagogique est de **rendre
visibles toutes les méthodes de prise de décision existantes** :
stratégie de base et systèmes de comptage de cartes.

---

## 2. Fonctionnalités

### Centrale
Jeu de Blackjack en CLI, actions standard (Hit, Stand, Double, Split,
Surrender), règles paramétrables.

### Plus-value pédagogique
Aide à la décision activable au lancement. Le joueur sélectionne, dans
un menu, l'une des **huit stratégies** disponibles. Pendant chaque tour,
le conseil de la stratégie est affiché — sans forcer le joueur à le
suivre, le but étant l'apprentissage.

### Bonus
- Mode **simulation comparative** (commande 2 du menu) qui calcule l'EV
  empirique de chaque stratégie sur N manches.
- **Journalisation** dans `logs/blackjack.log`.
- **Configuration** des règles dans `config/default.json`.

---

## 3. Choix techniques

### Langage et environnement
Python 3.10+ (utilise les *match-case* du cours quand pertinent, les
annotations de type, et `from __future__ import annotations`).

**Aucune dépendance externe** pour faciliter la prise en main et la
correction. Le rendu visuel est obtenu via les codes ANSI standard,
compatibles avec tous les terminaux modernes.

### Architecture en couches

```
┌────────────────────────────────────────────┐
│ ui/  (CLI, prompts, affichage)             │
├────────────────────────────────────────────┤
│ game/ (Rules, Round, Game, Statistics)     │
├────────────────────────────────────────────┤
│ players/ (BasePlayer → Dealer / Human)     │
│ strategies/ (Strategy → 8 stratégies)      │
├────────────────────────────────────────────┤
│ core/ (Card, Hand, Shoe, énumérations)     │
└────────────────────────────────────────────┘
```

Chaque couche ne dépend que des couches inférieures. La couche `ui` est
injectée dans `HumanPlayer` au moment de la création de `Game`, ce qui
permettrait par la suite de remplacer la CLI par une GUI sans toucher au
moteur.

### Patrons de conception utilisés
- **Strategy pattern** : classe `Strategy` abstraite et 8 implémentations
  interchangeables. C'est le polymorphisme de l'enseignement traduit en
  code.
- **Template method** : `BasePlayer.decide()` reste abstrait, chaque
  sous-classe l'implémente différemment.
- **Registry** : `strategies.STRATEGIES` (dict) sert de registre central
  des stratégies disponibles — ajouter une stratégie revient à ajouter
  une ligne.
- **Dataclass** : `Rules` et `Statistics` (réduction du boilerplate).

### Encapsulation
Toutes les classes utilisent des attributs privés (`__name`,
`__rank`, `__bankroll`, etc.) exposés en lecture via `@property`, et en
écriture uniquement par des méthodes publiques validantes (`credit`,
`debit`, `add_card`, etc.). Cf. cours « 3 - Héritage Polymorphisme &
Encapsulation en Python ».

### Sources des valeurs de stratégie
Les valeurs de chaque comptage et le contenu des tables de stratégie de
base proviennent d'ouvrages de référence :

- E. O. Thorp, *Beat the Dealer*, 1962 (édition révisée).
- S. Wong, *Professional Blackjack*.
- D. Schlesinger, *Blackjack Attack*.
- A. Snyder, *Blackbelt in Blackjack* (Zen Count, Red 7).
- B. Carlson, *Blackjack for Blood* (Omega II).
- O. Vancura & K. Fuchs, *Knock-Out Blackjack* (KO).

Ces valeurs ont été croisées avec plusieurs sources web spécialisées
(blackjackhero.com, casinoguardian.co.uk, lolblackjack.com,
blackjackstrategist.com, etc.).

---

## 4. Détails d'implémentation notables

### Calcul du total d'une main (`Hand.total`)
On somme toutes les cartes avec l'As compté 11, puis on ramène chaque As
à 1 (`total -= 10`) tant que le total dépasse 21. Cette boucle gère
proprement le cas des **deux As** dans la même main.

### Distinction soft / hard
Une main est **soft** quand elle contient un As compté 11 dans le total
courant. C'est crucial pour la stratégie de base (tableau dédié aux
mains soft).

### Sabot avec carte de coupe
Le `Shoe` n'est jamais remélangé en plein milieu d'une main. Quand la
pénétration est atteinte, un drapeau `needs_shuffle` est levé ; le
moteur (`Game.play_round`) le consulte **avant** chaque manche et
remélange seulement à ce moment-là.

### Comptage et carte cachée du croupier
Subtilité importante : la carte cachée (hole card) du croupier n'a pas
été *visible* du joueur, donc le compteur ne doit pas la comptabiliser
tant qu'elle reste cachée. Le code annule explicitement l'observation
faite au moment de la distribution, puis l'observe à nouveau au moment
du retournement. Sans cette précaution, les comptages seraient
systématiquement biaisés.

### Split et règles spécifiques
- Une seule carte est tirée après split d'As (règle classique).
- Le ré-split d'As est interdit par défaut (paramétrable).
- Le nombre maximum de mains après splits est paramétrable
  (`max_splits`).
- Une main issue d'un split ne peut **pas** être un blackjack naturel
  (drapeau `from_split` posé).

---

## 5. Tests

8 fichiers, ~50 cas de test au total. Couverture :
- Cartes : création, immutabilité, égalité, hash.
- Sabot : reproductibilité, taille, signal de remélange.
- Mains : soft/hard, As multiples, paires, bust, double.
- Stratégies : décisions canoniques, valeurs de tous les comptages,
  équilibre (somme = 0) des comptages balanced.
- End-to-end : 200 manches simulées sans exception.

```bash
python -m unittest discover -s tests -v
```

---

## 6. Utilisation de l'IA

### Pourquoi
- **Génération de squelettes** (boilerplate de classes, docstrings).
- **Vérification des tables** de stratégie de base et des valeurs de
  chaque système de comptage en croisant plusieurs sources.
- **Suggestions de structure** de projet et de patrons de conception.

### Ce qu'a apporté l'IA
- Accélération sur les parties répétitives (énumérations, accesseurs,
  tests unitaires).
- Aide à la rédaction des docstrings et de la documentation.
- Vérification croisée des valeurs (ex : Omega II → 2,3,7=+1 ; 4,5,6=+2 ;
  8,A=0 ; 9=-1 ; 10..R=-2) via plusieurs sources spécialisées.

### Ce qui reste de l'étudiant
- Choix du sujet et du périmètre.
- Architecture en couches.
- Conception du registre des stratégies.
- Toutes les décisions de design (composition vs héritage, encapsulation,
  séparation moteur/UI).

### Exemples de prompts utilisés
- « Génère le squelette d'une classe `Card` immuable avec encapsulation
  forte (attributs privés, propriétés en lecture seule). »
- « Liste les valeurs de chaque carte pour les comptages Hi-Lo, KO, Hi-Opt
  I/II, Omega II, Zen, Red 7 en t'appuyant sur les sources de référence
  (Thorp, Snyder, Carlson). »
- « Écris la table complète de stratégie de base multi-deck, S17, DAS,
  surrender tardif autorisé. »

---

## 7. Données nécessaires

Aucune donnée externe n'est nécessaire pour faire fonctionner le projet.
Le fichier `config/default.json` est fourni avec des valeurs raisonnables
et peut être édité.

---

## 8. Lancement et utilisation

Voir le `README.md` à la racine.

---

## 9. Limites connues

- Pas de gestion de **l'assurance** (impact mineur, négligeable hors
  comptage).
- Pas d'**index plays** (déviations selon le true count).
- Pas de mode **multi-joueurs**.
- Pas d'interface graphique (CLI uniquement).

---

## 10. Bibliographie

- E. O. Thorp, *Beat the Dealer*, 1962 (révisions ultérieures).
- S. Wong, *Professional Blackjack*.
- D. Schlesinger, *Blackjack Attack*.
- A. Snyder, *Blackbelt in Blackjack*.
- B. Carlson, *Blackjack for Blood*.
- O. Vancura, K. Fuchs, *Knock-Out Blackjack*.
- Documentation Python officielle (https://docs.python.org/3/).
- Cours NFP01 (A. Escourrou), supports 1 à 3.
