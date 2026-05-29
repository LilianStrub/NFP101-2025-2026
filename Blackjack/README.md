# Blackjack — Projet NFP01 (CNAM)

> Implémentation orientée objet d'un jeu de **Blackjack** en Python avec une
> option sélectionnable affichant **toutes les méthodes de prise de décision**
> existantes (stratégie de base et systèmes de comptage : Hi-Lo, KO,
> Hi-Opt I, Hi-Opt II, Omega II, Zen Count, Red 7).

---

## 📌 Sommaire

1. [Présentation](#-présentation)
2. [Fonctionnalités](#-fonctionnalités)
3. [Installation](#-installation)
4. [Lancement](#-lancement)
5. [Stratégies disponibles](#-stratégies-disponibles)
6. [Architecture du projet](#-architecture-du-projet)
7. [Tests](#-tests)
8. [Choix techniques](#-choix-techniques)
9. [Limites et pistes d'amélioration](#-limites-et-pistes-damélioration)
10. [Usage IA](#-usage-ia)

---

## 🎯 Présentation

**Public cible** : étudiants en POO et passionnés de blackjack qui veulent
comprendre l'impact concret des différentes stratégies sur l'espérance de
gain.

**Problème adressé** : un débutant face à une table de blackjack ne sait
généralement pas quoi faire d'un « hard 16 contre 10 » ou d'un « soft 18
contre 9 ». Et personne ne sait à quoi ressemble vraiment un comptage de
cartes en action. Ce projet permet de **jouer** au blackjack tout en
**affichant le conseil** d'une stratégie au choix : on apprend en jouant.

Le projet illustre directement les trois piliers de la POO enseignés dans
le cours **NFP01 / CNAM** (Adrien Escourrou) :

| Pilier         | Mise en pratique dans le projet                           |
|----------------|-----------------------------------------------------------|
| Héritage       | `Strategy` → `BasicStrategy`, `HiLoStrategy`, … `BasePlayer` → `Dealer`, `HumanPlayer` |
| Polymorphisme  | `Strategy.recommend()`, `Strategy.card_value()` redéfinis dans chaque sous-classe |
| Encapsulation  | Attributs `__rank`, `__suit`, `__bankroll`, etc. exposés via `@property` |

---

## ⭐ Fonctionnalités

- **Jeu de Blackjack complet** : Hit, Stand, Double, Split, Surrender,
  assurance (carte cachée + peek du croupier).
- **Sabot multi-deck** avec carte de coupe, remélange automatique et brûlage
  de la première carte après chaque mélange (comme au casino).
- **Mode didacticiel** : tout est commenté en temps réel (le croupier
  « parle »), avec conseil + explications des actions + animations — pensé
  pour les débutants.
- **Narration pas à pas** : chaque action de la table est commentée —
  distribution carte par carte, peek du croupier, mélange et brûlage.
- **Règles paramétrables** (S17/H17, DAS, paiement blackjack, etc.).
- **Aide à la décision en temps réel** selon la stratégie sélectionnée.
- **9 stratégies** au choix (1 manuelle, 1 de base, 7 comptages).
- **Mise conseillée** par true count pour les stratégies de comptage.
- **Mode simulation** : compare les stratégies sur des milliers de mains.
- **Sauvegarde & reprise** : le solde, les statistiques cumulées « à vie » et
  les records sont conservés entre les sessions (profil JSON dans
  `~/.blackjack_profile.json`) — on quitte et on reprend sa partie plus tard.
- **Records à battre** : meilleur solde atteint, plus longue série de victoires,
  plus gros gain en une main, blackjacks et manches cumulés.
- **Re-cave après faillite** : quand le solde est épuisé, on peut remettre une
  cave pour continuer à jouer au lieu de terminer.
- **Séries de victoires** affichées en cours de jeu (« 🔥 3 victoires d'affilée ! »).
- **Statistiques de session** : EV, win rate, blackjacks naturels…
- **Musique d'ambiance** activable depuis le menu (sans dépendance : lecteur
  système type `afplay`/`aplay`/`ffplay`). À l'activation, on choisit la source :
  - un **morceau de lounge jazz généré** à la volée (≈ 50 s, modulant et
    randomisé à chaque session) — fonctionne **hors-ligne** ;
  - une **webradio lounge** intégrée (flux gratuits SomaFM : *Groove Salad*,
    *Secret Agent*, *Lush*) — musique continue, **jamais en boucle** (nécessite
    internet + un lecteur de flux : `ffplay`, `mpg123` ou `cvlc`).

  Pour votre **propre playlist de casino**, définissez la variable
  d'environnement `BLACKJACK_MUSIC` :
  - un **fichier** audio,
  - un **dossier** → tous les morceaux sont lus en ordre aléatoire,
  - une **URL** de flux (webradio lounge/downtempo — p. ex. les flux gratuits
    de SomaFM type *Groove Salad* / *Secret Agent*) → musique continue.

  ```bash
  BLACKJACK_MUSIC="$HOME/Music/casino_lounge" python -m blackjack   # dossier
  BLACKJACK_MUSIC="https://exemple.fm/lounge" python -m blackjack    # webradio
  ```

  Se désactive d'elle-même si aucun lecteur audio n'est présent.
- **Journaux** dans `logs/blackjack.log`.
- **Configuration JSON** dans `config/default.json`.
- **Tests unitaires et d'intégration** (`unittest`, sans dépendance externe).

---

## 🛠 Installation

Python 3.10 ou plus est requis. L'installation tire automatiquement deux
dépendances pour l'interface : **rich** (panneaux, tables, couleurs RGB)
et **pyfiglet** (gros titres ASCII).

```bash
# 1) Récupérer le code
git clone <url-du-depot>
cd blackjack

# 2) (Optionnel) Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows

# 3) Installer en mode développement (tire rich + pyfiglet)
pip install -e .
```

> 💡 **Rendu optimal** : pour profiter pleinement des cartes Unicode et
> des emojis, utilisez un terminal moderne avec une police monospace
> supportant les caractères étendus, par exemple
> *Cascadia Code*, *Fira Code*, *JetBrains Mono* ou *MesloLGS NF*.

---

## 🚀 Lancement

```bash
# Option A : via le module
python -m blackjack

# Option B : via le script installé
blackjack
```

Le menu principal s'affiche en grosses lettres ASCII dorées et propose :

```
  1   Démarrer une nouvelle partie
  2   Didacticiel — apprendre en jouant
  3   Règles du jeu
  4   Comparer les stratégies (simulation)
  5   À propos / aide
  6   Musique d'ambiance : activée / désactivée
  0   Quitter
```

### Démarrer une partie

1. Saisissez votre solde de départ.
2. Choisissez d'afficher ou non l'aide d'une **stratégie** (et laquelle).
3. Activez ou non les **animations** (distribution carte par carte, suspense).
4. Misez puis jouez votre main avec les initiales françaises `t` / `r` / `d` /
   `s` / `a` (Tirer, Rester, Doubler, Séparer, Abandonner) ou en tapant le mot
   entier : `tirer`, `rester`, `doubler`, `séparer`, `abandonner`.

### Didacticiel

Pensé pour les débutants : tout est commenté en temps réel (le croupier
« parle » à chaque action), le conseil de la stratégie de base s'affiche à
chaque tour, chaque action possible est expliquée, et les animations sont
activées. Idéal pour comprendre le déroulement d'une manche.

À chaque coup, le conseil de la stratégie s'affiche dans un panneau magenta :

```
╭──────────────────────────────────────╮
│  💡 Conseil : Doubler  (D)           │
╰──────────────────────────────────────╯
```

### Règles du jeu

Le mode « Règles du jeu » affiche un récapitulatif complet (objectif, valeur
des cartes, déroulement, actions, paiements, règles de la table) dans des
panneaux encadrés.

### Comparer les stratégies

Le mode 3 simule N manches (par défaut 2 000) pour chaque stratégie et
affiche un tableau récapitulatif (EV, win %, blackjacks).

---

## 🎲 Stratégies disponibles

| Clé           | Stratégie                | Comptage |  Niveau |
|---------------|--------------------------|:--------:|:-------:|
| `manuelle`    | Manuelle (aucune aide)   | non      | —       |
| `basique`     | Stratégie de Base        | non      | —       |
| `hi-lo`       | Hi-Lo                    | oui      | 1       |
| `ko`          | KO (Knock-Out)           | oui      | 1       |
| `hi-opt-i`    | Hi-Opt I                 | oui      | 1       |
| `hi-opt-ii`   | Hi-Opt II                | oui      | 2       |
| `omega-ii`    | Omega II                 | oui      | 2       |
| `zen`         | Zen Count                | oui      | 2       |
| `red-7`       | Red 7                    | oui      | 1       |

**Valeurs détaillées** de chaque comptage : voir le module
[`strategies/counting.py`](src/blackjack/strategies/counting.py).

**Stratégie de base** : tables complètes (hard / soft / paires) dans
[`strategies/basic_strategy.py`](src/blackjack/strategies/basic_strategy.py),
référencées d'après Thorp, Wong et Schlesinger.

---

## 🧱 Architecture du projet

```
blackjack/
├── README.md
├── pyproject.toml
├── requirements.txt
├── config/
│   └── default.json         ← règles modifiables
├── docs/
│   └── documentation.md     ← documentation détaillée
├── src/
│   └── blackjack/
│       ├── __main__.py      ← point d'entrée CLI
│       ├── core/            ← Card, Hand, Shoe, énumérations
│       ├── players/         ← BasePlayer, Dealer, HumanPlayer
│       ├── strategies/      ← toutes les stratégies (registre central)
│       ├── game/            ← Rules, Round, Game, Statistics
│       ├── ui/              ← interface CLI (Rich + pyfiglet)
│       └── utils/           ← logger, chargeur de config
└── tests/                   ← tests unitaires & intégration
```

---

## 🧪 Tests

Les tests utilisent uniquement `unittest` (stdlib) — aucun rendu Rich n'est
sollicité car les UI sont remplacées par des stubs en mode test. Lancement :

```bash
# Depuis la racine du projet
python -m unittest discover -s tests -v

# Ou avec pytest si installé
pytest -v
```

Les tests couvrent :

- la création et l'immuabilité des cartes,
- le calcul soft/hard d'une main, les paires, les bust, les blackjacks,
- la reproductibilité du sabot (seed) et le brûlage de carte,
- les valeurs des 7 systèmes de comptage,
- l'équilibre des comptages équilibrés (somme = 0 sur un jeu),
- des décisions canoniques de la stratégie de base,
- le règlement des gains d'une manche (blackjack 3:2, push, abandon, bust,
  égalité…) et la restriction de double aux durs 9-10-11,
- le flux carte cachée + peek (Blackjack joueur / croupier / double),
- le profil persistant (sauvegarde/reprise, cumul, records) et les séries de
  victoires,
- une simulation de 200 manches bout en bout.

---

## 🔍 Choix techniques

- **Dépendances minimales** : seules `rich` et `pyfiglet` sont requises,
  toutes deux pour l'affichage CLI (panneaux, tables, gros titres ASCII).
  Le moteur de jeu lui-même reste 100 % stdlib.
- **Rich** plutôt qu'ANSI brut : composants prêts à l'emploi (`Panel`,
  `Table`, `Columns`) et couleurs RGB pour un rendu cohérent sur tous
  les terminaux modernes (macOS, Linux, Windows 10+).
- **Patron Stratégie** : une `Strategy` abstraite + 9 implémentations,
  toutes interchangeables sans modifier le moteur (`Game`/`Round`). C'est
  l'illustration directe du **polymorphisme**.
- **Composition** plutôt qu'héritage entre `_CountingStrategy` et
  `BasicStrategy` : un comptage *contient* une stratégie de base au lieu
  d'en hériter. Cela évite la duplication et garde les responsabilités
  claires.
- **`@dataclass`** pour `Rules` et `Statistics` (boilerplate minimal).
- **`Enum` / `IntEnum`** pour `Action`, `Rank`, `Suit`, `Outcome` :
  constantes typées, jamais confondues avec des chaînes.
- **Encapsulation forte** : double-underscore (`__rank`, `__bankroll`) +
  `@property` pour exposer en lecture seule, avec validation côté setter
  quand pertinent.

---

## ⚠️ Limites et pistes d'amélioration

- **Pas de GUI** : l'interface reste en ligne de commande.
- Pas d'**even money** sur blackjack joueur face à un As (l'assurance, elle,
  est bien gérée).
- Pas d'**index plays** ni d'« Illustrious 18 » : la stratégie est la
  même que la stratégie de base pour les compteurs, on ne dévie pas
  selon le true count.
- Pas de **mise à jour de mise par paliers customisables**.
- Pourrait être enrichi par un mode **multi-joueurs** sur la même table.

---

## 🤖 Usage IA

Conformément à la section 3 du sujet, l'utilisation de l'IA générative
(Claude) est déclarée. Détail dans
[`docs/documentation.md`](docs/documentation.md) — section « Utilisation
de l'IA ».

---

*Projet réalisé dans le cadre du module NFP01 – Programmation Orientée
Objet en Python, Java et autres — CNAM, 2025-2026.*
