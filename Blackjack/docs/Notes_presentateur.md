# Notes de présentateur — Soutenance « Blackjack POO »

> Fiche d'accompagnement du diaporama `Presentation_Blackjack_NFP01.pptx`.
> **Une section par diapo, numérotée.** Les mêmes notes figurent aussi dans le
> volet « Notes » de chaque diapo du PowerPoint (mode Présentateur). Ce fichier
> reste pratique pour réviser ou le garder sous les yeux (téléphone, feuille, 2e écran).

**Objectif global :** ~20 à 25 minutes, dont **5 min maximum de démo**, puis 5-10 min de questions.

**Conseils généraux :**

- Parle avec **tes mots** : ce sont des repères, pas un texte à réciter.
- Regarde le **jury**, pas l'écran. Ralentis sur la démo et sur la partie objet.
- Chaque terme technique a déjà une explication « En clair » sur la diapo : appuie-toi dessus.
- Surveille le temps : environ **1 minute par diapo** en moyenne (la démo est le gros morceau).
- Tu n'es pas obligé de tout dire : si tu es en retard, garde l'essentiel.

---
## Diapo 1 — Page de titre

*Durée indicative : ~20 s*

**But de la diapo :** Te présenter, annoncer le sujet en une phrase, et donner le plan + la durée.

**Ce que tu peux dire :**

- « Bonjour, je m'appelle Lilian Strub, je présente mon projet du module NFP01, Programmation Orientée Objet. »
- Pitch en UNE phrase simple : « J'ai créé un jeu de Blackjack en Python qui, en plus de faire jouer, affiche le meilleur coup à jouer et mesure quelle stratégie rapporte le plus. »
- Annoncer le plan : « Je vais d'abord expliquer pourquoi ce sujet, puis vous montrer le jeu en direct, ensuite comment c'est construit, et enfin les tests et le bilan. »
- Donner la durée : « Comptez une vingtaine de minutes, dont 5 minutes de démonstration. »

**Astuce orale :** Reste debout, regarde le jury (pas l'écran), souris : c'est un jeu, l'ambiance peut être détendue.

---

## Diapo 2 — Au programme

*Durée indicative : ~30 s*

**But de la diapo :** Donner le fil rouge pour que le jury sache toujours où on en est (critère « clarté & narration »).

**Ce que tu peux dire :**

- Lire rapidement les grandes étapes, sans détailler.
- Préciser le moment fort : « Le cœur, c'est la démonstration en direct, au milieu de la présentation. »
- Rassurer les non-initiés : « Pas besoin de connaître le blackjack, je fais un rappel des règles juste après. »

**Astuce orale :** Ne reste pas plus de 30 s sur cette diapo : c'est juste une boussole.

---

## Diapo 3 — Pourquoi le blackjack ?

*Durée indicative : ~1 min 30*

**But de la diapo :** Poser le PROBLÈME avant de montrer la solution. C'est ce qui rend le projet « utile ».

**Ce que tu peux dire :**

- Raconter une image simple : « À une vraie table, le débutant joue à l'instinct… et perd. »
- Expliquer l'idée centrale : « Mon outil affiche le bon coup à jouer ET l'explique : on apprend en jouant. »
- Faire le lien avec le cours : « Le sujet était libre ; j'ai choisi un domaine assez riche pour illustrer la programmation objet. »

**Astuce orale :** C'est le moment « accroche » : prends ton temps, c'est l'histoire que tu racontes.

**Si le jury demande :**

- *« Compter les cartes, c'est interdit ? »* → Non, c'est légal ; c'est juste mal vu et les casinos peuvent refuser un joueur. Ici c'est un outil pédagogique.

---

## Diapo 4 — Ce que le projet vise

*Durée indicative : ~1 min*

**But de la diapo :** Annoncer la valeur du projet et distinguer l'essentiel des bonus.

**Ce que tu peux dire :**

- Distinguer le CŒUR (jouer + conseil) des BONUS (simulation, sauvegarde, musique).
- Phrase à retenir : « C'est un outil d'apprentissage, pas seulement un jeu. »
- Annoncer la suite : « Avant la démo, 30 secondes de règles pour tout le monde. »

---

## Diapo 5 — Le blackjack en 30 secondes

*Durée indicative : ~45 s*

**But de la diapo :** Mettre TOUT le jury au même niveau avant la démo. Indispensable pour les non-joueurs.

**Ce que tu peux dire :**

- Aller vite et concret : montrer avec les mains « plus proche de 21 que le croupier, sans dépasser ».
- Insister sur la carte cachée du croupier : elle servira dans la partie technique (le comptage).
- Donner l'exemple du blackjack : « As + Roi = 21 d'entrée, c'est le jackpot. »

**Astuce orale :** Tu peux mimer un tirage de carte : ça détend et ça aide les non-initiés à suivre la démo qui arrive.

---

## Diapo 6 — Comment le projet a été construit

*Durée indicative : ~1 min 30*

**But de la diapo :** Montrer une progression claire (critère « présentation complète, toutes les étapes »).

**Ce que tu peux dire :**

- Raconter le sens de construction : « Je suis parti du cœur (les cartes) vers l'extérieur (l'écran), brique par brique. »
- Mentionner les itérations : « D'abord une version jouable simple, puis j'ai enrichi : didacticiel, comptages, simulation. »
- Souligner les commits réguliers : « Le sujet l'exige, et ça prouve l'avancement. »

**Astuce orale :** Tu peux pointer l'écran de gauche à droite pour suivre les étapes 1 → 7.

**Si le jury demande :**

- *« Combien de temps ça t'a pris ? »* → Donne une fourchette honnête en jours/semaines de travail, par itérations.

---

## Diapo 7 — Démonstration en direct  (≈ 5 min)

*Durée indicative : ~15 s d'intro, puis 4-5 min de démo en direct*

**But de la diapo :** Annoncer ce qu'on va voir, puis basculer sur le terminal.

**Ce que tu peux dire :**

- « Place à la démonstration. » Lancer la commande : python -m blackjack
- Annoncer le fil : menu → didacticiel → simulation → tests.

**À montrer / préparer :** Terminal large, police monospace, son activé. Lancer une partie AVANT la soutenance pour « chauffer » (sabot mélangé).

**Astuce orale :** On MONTRE, on ne lit pas le code. Garde un œil sur le temps : la démo ne doit pas dépasser 5 min. Si ça casse → passe aux maquettes des diapos suivantes.

---

## Diapo 8 — Le menu principal

*Durée indicative : ~30 s (ou en direct)*

**But de la diapo :** Montrer que l'outil est accueillant et clair dès l'ouverture.

**Ce que tu peux dire :**

- « Voici le menu : 6 options, tout en français. »
- « On va choisir l'option 2, le Didacticiel : le mode qui explique tout. »

---

## Diapo 9 — Le Didacticiel : le cœur du projet

*Durée indicative : ~2 min (le moment fort de la démo)*

**But de la diapo :** Prouver la promesse « apprendre en jouant ».

**Ce que tu peux dire :**

- Pointer trois choses : (1) le jeu RACONTE ce qui se passe (« le croupier distribue… »), (2) les cartes s'affichent une par une, (3) le CONSEIL apparaît à chaque tour.
- Lire l'exemple : « Ici j'ai 17, le croupier montre un 9, le jeu me conseille de Doubler — et m'explique pourquoi. »
- Jouer le coup conseillé, laisser le croupier finir, montrer le résultat (gagné/perdu, série de victoires).

**Astuce orale :** C'est LA diapo à soigner : ralentis, c'est ce qui impressionne le jury.

**Si le jury demande :**

- *« Le conseil vient d'où ? »* → De tables de stratégie reconnues (Thorp, Wong…), recopiées dans le code et vérifiées par des tests.

---

## Diapo 10 — Comparer les stratégies : un résultat chiffré

*Durée indicative : ~1 min 30*

**But de la diapo :** Donner un RÉSULTAT OBSERVABLE et chiffré (très valorisé par la grille).

**Ce que tu peux dire :**

- Lancer la simulation en direct (menu 4). Pendant le calcul : « Un robot joue des milliers de mains pour chaque stratégie, on mesure le gain moyen. »
- À l'arrivée du tableau, expliquer simplement : « Sans comptage, on perd un peu en moyenne. Avec comptage, on mise plus au bon moment, et ça peut repasser positif. »
- Être honnête : « Les chiffres de la diapo sont un exemple ; les vrais viennent de la simulation que je lance là, en direct. »

**Astuce orale :** « Gain/main » négatif = on perd en moyenne ; positif = on gagne. Dis-le avec ces mots simples.

**Si le jury demande :**

- *« Pourquoi des chiffres si proches de zéro ? »* → Le blackjack est un jeu très serré : l'avantage se joue à moins de 1 % par main, d'où l'intérêt de jouer beaucoup de mains.

---

## Diapo 11 — Ce que le projet sait faire

*Durée indicative : ~1 min*

**But de la diapo :** Balayer l'étendue du projet sans tout re-détailler (la démo a déjà parlé).

**Ce que tu peux dire :**

- Distinguer encore l'essentiel (jeu + conseil) des bonus (sauvegarde, musique).
- Mentionner que les règles se changent dans un simple fichier de configuration, sans toucher au code.

---

## Diapo 12 — Le code, rangé en étages

*Durée indicative : ~1 min 30*

**But de la diapo :** Montrer que le code est organisé, pas un seul gros fichier.

**Ce que tu peux dire :**

- Lire de bas en haut : « Les briques de base (les cartes) ne connaissent rien du reste ; chaque étage s'appuie seulement sur ceux du dessous. »
- Donner l'intérêt concret : « Je pourrais remplacer l'écran texte par une interface graphique sans toucher au moteur du jeu. »

**Astuce orale :** Analogie : « comme une maison — les fondations ne dépendent pas de la décoration, l'inverse oui. »

**Si le jury demande :**

- *« Pourquoi séparer en autant de dossiers ? »* → Chaque dossier a une responsabilité unique : c'est plus facile à lire, à tester et à faire évoluer.

---

## Diapo 13 — Les 3 principes de la programmation objet

*Durée indicative : ~1 min 30*

**But de la diapo :** LE bloc attendu par un jury de POO. À maîtriser pour les questions.

**Ce que tu peux dire :**

- Prendre chaque principe et donner l'exemple « en clair » de la diapo.
- Pour le polymorphisme, insister : « C'est ça qui rend les 9 stratégies interchangeables sans modifier le jeu. »

**Astuce orale :** Si tu ne dois retenir qu'un exemple : le polymorphisme avec les stratégies. C'est le plus parlant.

**Si le jury demande :**

- *« Donne un exemple d'héritage dans ton code. »* → BasePlayer → Dealer et HumanPlayer ; ou Strategy → BasicStrategy, HiLoStrategy…
- *« À quoi sert l'encapsulation ici ? »* → Empêcher de modifier le solde ou une carte par erreur ; on passe par des méthodes qui valident.

---

## Diapo 14 — Des choix réfléchis (pas par hasard)

*Durée indicative : ~1 min 30*

**But de la diapo :** Montrer que chaque choix a une RAISON (critère « choix justifiés »).

**Ce que tu peux dire :**

- Pour chaque point, dire le POURQUOI en une phrase.
- Le plus intéressant : « Faire hériter un comptage de la stratégie de base aurait mélangé deux rôles — compter, et décider. La composition garde les rôles séparés. »

**Si le jury demande :**

- *« Composition ou héritage : comment choisir ? »* → Héritage si « est un » (un Dealer EST un joueur) ; composition si « utilise un » (un comptage UTILISE une stratégie).

---

## Diapo 15 — Le piège du comptage : la carte cachée

*Durée indicative : ~1 min*

**But de la diapo :** Montrer la profondeur du travail — souvent source de questions.

**Ce que tu peux dire :**

- Expliquer le bug évité : « Si on comptait la carte cachée tout de suite, le joueur « tricherait » avec une info qu'il n'a pas. »
- Préciser : « C'est le seul endroit du code où je touche au compteur autrement que par la fonction normale — et c'est testé. »

**Astuce orale :** Bonne diapo pour montrer que tu comprends VRAIMENT ton code, pas seulement que ça marche.

---

## Diapo 16 — Tests : 94 vérifications automatiques

*Durée indicative : ~1 min 30*

**But de la diapo :** Prouver la fiabilité (critère « tests / validation »).

**Ce que tu peux dire :**

- Si possible, lancer les tests en direct dans un 2e terminal : « tout vert en moins d'une seconde ».
- Donner un exemple de test malin : « Sur un jeu complet, mon comptage doit retomber exactement à zéro — sinon mes tables sont fausses. »
- Mentionner que les tests ont attrapé de vrais bugs (ex. une boucle sans fin sur la séparation de cartes).

**Si le jury demande :**

- *« Tes tests couvrent tout ? »* → Pas 100 % des lignes, mais tous les cas critiques : règles, gains, comptages, sauvegarde, et une partie complète de bout en bout.

---

## Diapo 17 — Limites assumées

*Durée indicative : ~45 s*

**But de la diapo :** Être lucide rapporte des points et désamorce les questions.

**Ce que tu peux dire :**

- Présenter ces limites comme des CHOIX, pas des oublis : « J'ai préféré un projet fini et testé sur un périmètre maîtrisé. »
- Enchaîner naturellement : « Voici justement comment j'irais plus loin. »

---

## Diapo 18 — Pistes pour aller plus loin

*Durée indicative : ~45 s*

**But de la diapo :** Montrer que tu sais où aller ensuite.

**Ce que tu peux dire :**

- Relier à l'architecture : « Ajouter une interface graphique ou une stratégie coûte peu, grâce au rangement en étages et au registre. »

---

## Diapo 19 — Ce que j'en retire — et l'entreprise

*Durée indicative : ~1 min*

**But de la diapo :** Répondre à la question du sujet : qu'as-tu appris, est-ce utile en entreprise ?

**Ce que tu peux dire :**

- Être sincère : « La vraie compétence, c'est découper un problème et sécuriser par des tests — exactement le travail en équipe. »
- Ajouter : « Savoir diriger une IA, la relire et la valider, est devenu une compétence à part entière. »

---

## Diapo 20 — Usage de l'IA — déclaré ouvertement

*Durée indicative : ~1 min 30*

**But de la diapo :** Section sensible ET notée (3 pts). Être totalement transparent.

**Ce que tu peux dire :**

- Message clé : « Tout est déclaré, prompts inclus dans la documentation — et je peux expliquer chaque partie du code. »
- Donner un exemple de pilotage : « C'est moi qui ai demandé les touches en français, le mode didacticiel, la musique. »
- Donner un exemple de refus : « J'ai refusé d'arrondir les gains, pour rester fidèle aux vraies règles. »

**Astuce orale :** Le sujet met un 0 à toute IA non déclarée. Ici on assume franchement : c'est la bonne stratégie.

**Si le jury demande :**

- *« Qu'as-tu fait toi, exactement ? »* → La conception, les décisions, la validation par le jeu et les 94 tests, et l'acceptation ou le refus des propositions de l'IA.
- *« Peux-tu expliquer ce bout de code ? »* → Oui — reprends l'exemple du comptage avec la carte cachée ou du polymorphisme.

---

## Diapo 21 — Sources

*Durée indicative : ~30 s*

**But de la diapo :** Crédibiliser : les tables et valeurs ne sont pas inventées.

**Ce que tu peux dire :**

- Citer rapidement : « Les conseils du jeu viennent de livres de référence, recoupés avec des sources spécialisées. »
- Rappeler l'IA dans les sources, comme demandé par le sujet.

---

## Diapo 22 — Ce que j'aurais changé dans le sujet

*Durée indicative : ~45 s*

**But de la diapo :** Répondre au point du sujet « ce que vous auriez changé… ou pas ».

**Ce que tu peux dire :**

- Rester constructif et poli, pas de critique gratuite.
- Valoriser ce qui marche (la liberté), proposer 1-2 améliorations concrètes.

**Astuce orale :** Montre du recul : c'est apprécié. Termine sur du positif.

---

## Diapo 23 — En résumé

*Durée indicative : ~30 s*

**But de la diapo :** Boucler sur la promesse de départ et finir avec assurance.

**Ce que tu peux dire :**

- Reprendre le fil : « apprendre en jouant », fini, testé, propre, IA déclarée.
- Phrase de clôture nette, puis enchaîner sur la diapo Questions.

**Astuce orale :** Ne t'excuse pas, ne marmonne pas la fin : termine droit, en regardant le jury.

---

## Diapo 24 — Questions

*Durée indicative : 5 à 10 min*

**But de la diapo :** Échange avec le jury.

**Ce que tu peux dire :**

- Prendre le temps de bien écouter la question, reformuler si besoin.
- Si tu ne sais pas : être honnête, proposer une piste plutôt que d'inventer.

**Astuce orale :** Garde la diapo Annexe (suivante) sous le coude pour les questions techniques pointues.

**Si le jury demande :**

- *« Pourquoi la composition pour les comptages ? »* → Voir la diapo « Choix techniques » : compter ≠ décider, on sépare les rôles.
- *« Comment gères-tu la carte cachée du croupier ? »* → Voir la diapo « Point délicat » : on l'« oublie » tant qu'elle est cachée.
- *« Qu'as-tu fait toi vs l'IA ? »* → Voir la diapo « Usage de l'IA » : conception, décisions, validation par le jeu et les tests.
- *« Pourquoi pas d'interface graphique ? »* → Choix de périmètre ; l'architecture en étages permet de l'ajouter facilement.

---

## Diapo 25 — Les 9 stratégies & règles de table

*Durée indicative : à n'afficher que si on te le demande*

**But de la diapo :** Diapo de SECOURS pour les questions techniques. Ne pas la présenter d'office.

**Ce que tu peux dire :**

- L'afficher seulement si le jury demande le détail des stratégies, des comptages ou des règles exactes.

---
