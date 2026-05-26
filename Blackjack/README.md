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

- **Jeu de Blackjack complet** : Hit, Stand, Double, Split, Surrender.
- **Sabot multi-deck** avec carte de coupe et remélange automatique.
- **Règles paramétrables** (S17/H17, DAS, paiement blackjack, etc.).
- **Aide à la décision en temps réel** selon la stratégie sélectionnée.
- **8 stratégies** au choix (1 manuelle, 1 de base, 6 comptages).
- **Mise conseillée** par true count pour les stratégies de comptage.
- **Mode simulation** : compare les stratégies sur des milliers de mains.
- **Statistiques de session** : EV, win rate, blackjacks naturels…
- **Journaux** dans `logs/blackjack.log`.
- **Configuration JSON** dans `config/default.json`.
- **Tests unitaires et d'intégration** (`unittest`, sans dépendance externe).

---

## 🛠 Installation

Le projet n'a **aucune dépendance externe** ; seul Python 3.10 ou plus est requis.

```bash
# 1) Récupérer le code
git clone <url-du-depot>
cd blackjack

# 2) (Optionnel) Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows

# 3) Installer en mode développement
pip install -e .
```

---

## 🚀 Lancement

```bash
# Option A : via le module
python -m blackjack

# Option B : via le script installé
blackjack
```

Le menu principal s'affiche :

```
╔═══════════════════════════════════╗
║  BLACKJACK — Menu Principal       ║
╚═══════════════════════════════════╝
  1. Démarrer une nouvelle partie
  2. Comparer les stratégies (simulation)
  3. À propos / aide
  0. Quitter
```

### Démarrer une partie

1. Saisissez votre nom et votre solde de départ.
2. Choisissez si vous voulez l'aide d'une stratégie.
3. Si oui : sélectionnez la stratégie dans la liste affichée.
4. Misez puis jouez votre main : `h` (Hit), `s` (Stand), `d` (Double),
   `p` (Split), `r` (Surrender).

À chaque coup, le conseil de la stratégie choisie s'affiche en magenta :

```
    💡 Conseil       : Doubler (D)
```

### Comparer les stratégies

Le mode 2 simule N manches (par défaut 2 000) pour chaque stratégie et
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
│       ├── ui/              ← interface CLI (ANSI couleurs)
│       └── utils/           ← logger, chargeur de config
└── tests/                   ← tests unitaires & intégration
```

---

## 🧪 Tests

Les tests ne nécessitent que la bibliothèque standard. Lancement :

```bash
# Depuis la racine du projet
python -m unittest discover -s tests -v

# Ou avec pytest si installé
pytest -v
```

Les tests couvrent :

- la création et l'immuabilité des cartes,
- le calcul soft/hard d'une main, les paires, les bust, les blackjacks,
- la reproductibilité du sabot (seed),
- les valeurs des 7 systèmes de comptage,
- l'équilibre des comptages équilibrés (somme = 0 sur un jeu),
- des décisions canoniques de la stratégie de base,
- une simulation de 200 manches bout en bout.

---

## 🔍 Choix techniques

- **Aucune dépendance externe** — n'utilise que la stdlib Python 3.10+.
- **Couleurs ANSI** plutôt qu'une bibliothèque (Colorama / Rich) :
  fonctionne sur tous les terminaux modernes y compris Windows 10+.
- **Patron Stratégie** : une `Strategy` abstraite + 8 implémentations,
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
- Pas d'**insurance** ni d'**even money** (peu d'impact sur l'EV avec la
  stratégie de base, mais utile pour les comptages).
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
