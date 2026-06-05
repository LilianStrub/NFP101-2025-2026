# ###############  CODE IA (Claude / Claude Code)  ###############
"""Génère le diaporama de soutenance (.pptx) + les notes de présentateur (.md).

Conforme aux sections 5 (structure du support oral) et 6 (grille de l'oral)
du sujet. Le diaporama est pensé pour être compris par des DÉBUTANTS, en
informatique comme au blackjack : chaque terme technique est expliqué « en
clair » sur la diapo, et un rappel des règles du blackjack est inclus.

Style : sobre et professionnel — fond foncé, accent or discret, sur-titre
(« eyebrow ») en petites capitales espacées, séparateurs fins, numéros de page.

Deux sorties :
  - docs/Presentation_Blackjack_NFP01.pptx   (les diapos, SANS notes intégrées)
  - docs/Notes_presentateur.md               (le discours, une section par diapo)

Usage :
    pip install python-pptx          # ou : pip install -e ".[dev]"
    python docs/generate_slides.py

Tout le code de ce fichier a été généré avec l'IA Claude (Claude Code), sous la
direction de l'étudiant — cf. README §Usage IA et docs/documentation.md §6.
"""
# ################################################################
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# --- Palette sobre & professionnelle -------------------------------------
BG = RGBColor(0x0C, 0x1F, 0x19)        # vert très foncé (presque charbon)
PANEL = RGBColor(0x08, 0x16, 0x11)     # panneau (maquettes, archi)
GOLD = RGBColor(0xC8, 0xA2, 0x4B)      # or laiton, discret
TEXT = RGBColor(0xED, 0xEF, 0xEA)      # blanc cassé
MUTED = RGBColor(0x93, 0xA3, 0x9A)     # texte secondaire
LINE = RGBColor(0x2C, 0x47, 0x3C)      # filets / séparateurs

TITLE_FONT = "Georgia"
BODY_FONT = "Calibri"
MONO_FONT = "Consolas"

# Marges et repères de mise en page
LM = 0.9                                # marge gauche (pouces)
CONTENT_W = 11.55

HERE = Path(__file__).resolve().parent
OUT_PPTX = HERE / "Presentation_Blackjack_NFP01.pptx"
OUT_NOTES = HERE / "Notes_presentateur.md"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Notes de présentateur collectées dans l'ordre de création des diapos —
# écrites dans un fichier .md séparé, volontairement PAS dans le .pptx.
SPEAKER_NOTES: list[tuple[str, dict]] = []


# --- Briques de bas niveau ----------------------------------------------
def _blank(prs: Presentation):
    """Diapo vierge (layout 6) au fond foncé."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG
    return slide


def _box(slide, left, top, width, height, wrap=True):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = wrap
    return tf


def _run(paragraph, text, size, color=TEXT, *, bold=False, italic=False, font=BODY_FONT, track=0.0):
    run = paragraph.add_run()
    run.text = text
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = font
    f.color.rgb = color
    if track:  # espacement des lettres (effet « eyebrow » professionnel)
        f._rPr.set("spc", str(int(track * 100)))
    return run


def _rect(slide, left, top, width, height, color, line_color=None, line_w=0.0):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_w)
    shape.shadow.inherit = False
    return shape


def _header(slide, kicker, title):
    """Accent or + sur-titre discret + titre + filet séparateur."""
    _rect(slide, LM + 0.02, 0.52, 0.42, 0.045, GOLD)          # petit trait d'accent
    if kicker:
        ktf = _box(slide, LM, 0.60, CONTENT_W, 0.35)
        _run(ktf.paragraphs[0], kicker.upper(), 12, GOLD, bold=True, track=2.2)
    ttf = _box(slide, LM - 0.02, 0.93, CONTENT_W, 0.78)
    _run(ttf.paragraphs[0], title, 29, TEXT, bold=True, font=TITLE_FONT)
    _rect(slide, LM, 1.74, CONTENT_W, 0.018, LINE)            # filet sous l'en-tête


def _register(title, note):
    SPEAKER_NOTES.append((title, note or {}))


# --- Constructeurs de diapositives ---------------------------------------
def add_title_slide(prs, note=None):
    slide = _blank(prs)
    # sur-titre centré
    eb = _box(slide, 0.5, 1.85, 12.333, 0.5)
    pe = eb.paragraphs[0]
    pe.alignment = PP_ALIGN.CENTER
    _run(pe, "PROJET NFP01 · PROGRAMMATION ORIENTÉE OBJET", 14, GOLD, bold=True, track=3.0)
    # titre
    tb = _box(slide, 0.5, 2.45, 12.333, 1.5)
    pt = tb.paragraphs[0]
    pt.alignment = PP_ALIGN.CENTER
    _run(pt, "Blackjack", 60, TEXT, bold=True, font=TITLE_FONT)
    pt2 = tb.add_paragraph()
    pt2.alignment = PP_ALIGN.CENTER
    _run(pt2, "Un jeu en Python pour apprendre à bien jouer", 21, GOLD)
    # filet décoratif centré
    _rect(slide, (13.333 - 3.0) / 2, 4.35, 3.0, 0.02, LINE)
    # bloc auteur
    meta = _box(slide, 0.5, 4.7, 12.333, 1.7)
    for i, (txt, sz, col) in enumerate([
        ("Lilian Strub", 21, TEXT),
        ("CNAM · 2025-2026 — Encadrant : Adrien Escourrou", 15, MUTED),
    ]):
        p = meta.paragraphs[0] if i == 0 else meta.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_after = Pt(6)
        _run(p, txt, sz, col)
    # discret rappel « cartes » en bas
    sb = _box(slide, 0.5, 6.55, 12.333, 0.5)
    ps = sb.paragraphs[0]
    ps.alignment = PP_ALIGN.CENTER
    _run(ps, "♠   ♥   ♦   ♣", 16, LINE)
    _register("Page de titre", note)
    return slide


def add_bullets_slide(prs, kicker, title, bullets, note=None):
    """bullets : "texte" | ("texte", 1) sous-puce | ("texte", "tip") « En clair »."""
    slide = _blank(prs)
    _header(slide, kicker, title)
    tf = _box(slide, LM, 1.98, CONTENT_W, 4.85)
    for i, item in enumerate(bullets):
        text, kind = item if isinstance(item, tuple) else (item, 0)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.05
        if kind == "tip":
            p.space_after = Pt(7)
            _run(p, "       En clair — ", 15, GOLD, italic=True, bold=True)
            _run(p, text, 15, TEXT, italic=True)
        elif kind == 1:
            p.space_after = Pt(7)
            _run(p, "       ·  ", 17, MUTED)
            _run(p, text, 17, MUTED)
        else:
            p.space_after = Pt(11)
            _run(p, "—  ", 20, GOLD, bold=True)
            _run(p, text, 20, TEXT)
    _register(title, note)
    return slide


def add_mono_slide(prs, kicker, title, mono_text, note=None, caption=""):
    """Diapo « maquette » : panneau sombre encadré, texte monospace."""
    slide = _blank(prs)
    _header(slide, kicker, title)
    panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(LM), Inches(1.98), Inches(CONTENT_W), Inches(4.35))
    panel.fill.solid()
    panel.fill.fore_color.rgb = PANEL
    panel.line.color.rgb = LINE
    panel.line.width = Pt(1.0)
    panel.shadow.inherit = False
    tf = panel.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.35)
    tf.margin_top = Inches(0.2)
    for i, line in enumerate(mono_text.splitlines()):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        _run(p, line if line else " ", 13.5, TEXT, font=MONO_FONT)
    if caption:
        ctf = _box(slide, LM, 6.42, CONTENT_W, 0.5)
        _run(ctf.paragraphs[0], caption, 13, MUTED, italic=True)
    _register(title, note)
    return slide


def add_layers_slide(prs, kicker, title, layers, note=None, footnote=""):
    """Diagramme d'architecture en couches (rectangles empilés)."""
    slide = _blank(prs)
    _header(slide, kicker, title)
    top, height, gap, left, width = 2.05, 0.86, 0.16, 2.2, 8.9
    for i, (name, desc) in enumerate(layers):
        y = top + i * (height + gap)
        rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                      Inches(left), Inches(y), Inches(width), Inches(height))
        rect.fill.solid()
        rect.fill.fore_color.rgb = PANEL
        rect.line.color.rgb = GOLD
        rect.line.width = Pt(1.0)
        rect.shadow.inherit = False
        tf = rect.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        _run(p, name + "   ", 18, GOLD, bold=True, font=MONO_FONT)
        _run(p, "— " + desc, 13.5, TEXT)
    arrow = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(1.15), Inches(top),
                                   Inches(0.55), Inches(len(layers) * (height + gap) - gap))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = LINE
    arrow.line.fill.background()
    arrow.shadow.inherit = False
    _run(arrow.text_frame.paragraphs[0], "dépend de", 9, TEXT, bold=True)
    if footnote:
        ftf = _box(slide, LM, 6.5, CONTENT_W, 0.5)
        _run(ftf.paragraphs[0], footnote, 13, MUTED, italic=True)
    _register(title, note)
    return slide


def add_questions_slide(prs, note=None):
    slide = _blank(prs)
    tb = _box(slide, 0.5, 2.7, 12.333, 1.4)
    p = tb.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, "Questions", 54, TEXT, bold=True, font=TITLE_FONT)
    _rect(slide, (13.333 - 3.0) / 2, 4.05, 3.0, 0.02, LINE)
    sub = _box(slide, 0.5, 4.25, 12.333, 1.2)
    ps = sub.paragraphs[0]
    ps.alignment = PP_ALIGN.CENTER
    _run(ps, "Merci de votre attention", 20, GOLD)
    ps2 = sub.add_paragraph()
    ps2.alignment = PP_ALIGN.CENTER
    _run(ps2, "Lilian Strub · Blackjack POO · NFP01 — CNAM", 14, MUTED, italic=True)
    _register("Questions", note)
    return slide


def _add_footers(prs):
    """Filet + pied de page (nom à gauche, numéro à droite) sur toutes les
    diapos sauf la page de titre."""
    total = len(prs.slides)
    for idx, slide in enumerate(prs.slides, start=1):
        if idx == 1:
            continue
        _rect(slide, LM, 7.02, CONTENT_W, 0.014, LINE)
        ltf = _box(slide, LM, 7.08, 8.0, 0.35)
        _run(ltf.paragraphs[0], "Blackjack POO · Lilian Strub", 9, MUTED)
        rtf = _box(slide, 10.4, 7.08, 2.03, 0.35)
        pr = rtf.paragraphs[0]
        pr.alignment = PP_ALIGN.RIGHT
        _run(pr, f"{idx} / {total}", 9, MUTED)


# --- Maquettes ASCII (écrans du jeu) -------------------------------------
MENU_MOCKUP = r"""
       ____  __           __        __         __
      / __ )/ /___ ______/ /__     / /___ ____/ /__
     / __  / / __ `/ ___/ //_/    / / __ `/ __  / //_
    / /_/ / / /_/ / /__/  '<  /  / / /_/ / /_/ /  '</
   /_____/_/\__,_/\___/_/|_|  \_/  \__,_/\__,_/_/|_|

   ╔════════════════════════════════════════════════╗
   ║   1   Démarrer une nouvelle partie               ║
   ║   2   Didacticiel — apprendre en jouant          ║
   ║   3   Règles du jeu                              ║
   ║   4   Comparer les stratégies (simulation)       ║
   ║   5   À propos / aide                            ║
   ║   6   Musique d'ambiance : activée               ║
   ║   0   Quitter                                    ║
   ╚════════════════════════════════════════════════╝
              Votre choix  ▸ _
"""

DIDACTICIEL_MOCKUP = r"""
  « Le croupier distribue les cartes… »

       VOUS                    CROUPIER
   ┌────┐ ┌────┐            ┌────┐ ┌────┐
   │ A♠ │ │ 6♦ │            │ 9♣ │ │ ?? │   ← carte cachée
   └────┘ └────┘            └────┘ └────┘
     Total : 17               Montre : 9

   ╭──────────────────────────────────────────╮
   │      Conseil : Doubler   (D)               │
   ╰──────────────────────────────────────────╯

   Actions :  [T] Tirer   [R] Rester   [D] Doubler
              [S] Séparer  [A] Abandonner
   Votre action  ▸ _
"""

SIMULATION_MOCKUP = r"""
   Comparaison — 2 000 manches jouées par un robot, par stratégie

   ┌────────────────┬───────────┬─────────┬────────────┐
   │ Stratégie      │  Gain/main│   Win % │ Blackjacks │
   ├────────────────┼───────────┼─────────┼────────────┤
   │ Stratégie base │   -0.0050 │  43.2 % │    4.7 %   │
   │ Hi-Lo          │   +0.0041 │  43.5 % │    4.8 %   │
   │ KO             │   +0.0034 │  43.4 % │    4.7 %   │
   │ Omega II       │   +0.0057 │  43.6 % │    4.8 %   │
   │ Zen Count      │   +0.0050 │  43.5 % │    4.8 %   │
   └────────────────┴───────────┴─────────┴────────────┘

   ▸ Sans comptage : on perd un peu en moyenne (avantage casino).
   ▸ Avec comptage : on mise plus quand il reste des grosses cartes
     → le gain moyen peut repasser positif.
"""


# --- Assemblage du diaporama ---------------------------------------------
def build():
    SPEAKER_NOTES.clear()
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # 1 — Titre
    add_title_slide(prs, {
        "duree": "~20 s",
        "but": "Te présenter, annoncer le sujet en une phrase, et donner le plan + la durée.",
        "dire": [
            "« Bonjour, je m'appelle Lilian Strub, je présente mon projet du module NFP01, Programmation Orientée Objet. »",
            "Pitch en UNE phrase simple : « J'ai créé un jeu de Blackjack en Python qui, en plus de faire jouer, affiche le meilleur coup à jouer et mesure quelle stratégie rapporte le plus. »",
            "Annoncer le plan : « Je vais d'abord expliquer pourquoi ce sujet, puis vous montrer le jeu en direct, ensuite comment c'est construit, et enfin les tests et le bilan. »",
            "Donner la durée : « Comptez une vingtaine de minutes, dont 5 minutes de démonstration. »",
        ],
        "astuce": "Reste debout, regarde le jury (pas l'écran), souris : c'est un jeu, l'ambiance peut être détendue.",
    })

    # 2 — Plan
    add_bullets_slide(
        prs, "Plan", "Au programme",
        [
            "Pourquoi ce projet : contexte et objectif",
            "Le blackjack en 30 secondes (pour ceux qui ne connaissent pas)",
            "Démonstration en direct du jeu (≈ 5 min)",
            "Comment c'est construit : architecture et programmation objet",
            "Tests, limites, et ce que le projet m'a apporté",
            "Usage de l'IA, sources, puis vos questions",
        ],
        {
            "duree": "~30 s",
            "but": "Donner le fil rouge pour que le jury sache toujours où on en est (critère « clarté & narration »).",
            "dire": [
                "Lire rapidement les grandes étapes, sans détailler.",
                "Préciser le moment fort : « Le cœur, c'est la démonstration en direct, au milieu de la présentation. »",
                "Rassurer les non-initiés : « Pas besoin de connaître le blackjack, je fais un rappel des règles juste après. »",
            ],
            "astuce": "Ne reste pas plus de 30 s sur cette diapo : c'est juste une boussole.",
        })

    # 3 — Contexte
    add_bullets_slide(
        prs, "Contexte", "Pourquoi le blackjack ?",
        [
            "Le blackjack est le seul jeu de casino où bien réfléchir peut donner l'avantage au joueur — pas seulement la chance.",
            "Problème : un débutant ne sait pas quoi faire face à une main difficile.",
            ("Faut-il demander une carte de plus au risque de dépasser 21, ou s'arrêter ? Personne ne le sait au début.", "tip"),
            "Et personne ne « voit » concrètement ce qu'est le comptage de cartes.",
            "Public visé : à la fois les étudiants en programmation et les curieux du blackjack.",
        ],
        {
            "duree": "~1 min 30",
            "but": "Poser le PROBLÈME avant de montrer la solution. C'est ce qui rend le projet « utile ».",
            "dire": [
                "Raconter une image simple : « À une vraie table, le débutant joue à l'instinct… et perd. »",
                "Expliquer l'idée centrale : « Mon outil affiche le bon coup à jouer ET l'explique : on apprend en jouant. »",
                "Faire le lien avec le cours : « Le sujet était libre ; j'ai choisi un domaine assez riche pour illustrer la programmation objet. »",
            ],
            "astuce": "C'est le moment « accroche » : prends ton temps, c'est l'histoire que tu racontes.",
            "questions": [
                ("Compter les cartes, c'est interdit ?", "Non, c'est légal ; c'est juste mal vu et les casinos peuvent refuser un joueur. Ici c'est un outil pédagogique."),
            ],
        })

    # 4 — Objectif
    add_bullets_slide(
        prs, "Objectif", "Ce que le projet vise",
        [
            "Rendre visibles toutes les façons de décider : la stratégie de base + 7 méthodes de comptage de cartes.",
            ("Compter les cartes = repérer s'il reste beaucoup de grosses cartes à venir, pour miser plus au bon moment.", "tip"),
            "« Apprendre en jouant » : le conseil s'affiche, mais on reste libre de le suivre ou non.",
            "Comparer : un mode « simulation » calcule quelle stratégie gagne le plus sur des milliers de mains.",
            "Côté école : montrer en vrai les 3 grands principes de la programmation objet.",
        ],
        {
            "duree": "~1 min",
            "but": "Annoncer la valeur du projet et distinguer l'essentiel des bonus.",
            "dire": [
                "Distinguer le CŒUR (jouer + conseil) des BONUS (simulation, sauvegarde, musique).",
                "Phrase à retenir : « C'est un outil d'apprentissage, pas seulement un jeu. »",
                "Annoncer la suite : « Avant la démo, 30 secondes de règles pour tout le monde. »",
            ],
        })

    # 5 — Le blackjack en 30 secondes (pour débutants)
    add_bullets_slide(
        prs, "Rappel des règles", "Le blackjack en 30 secondes",
        [
            "But : avoir une main plus proche de 21 que le croupier, sans dépasser 21.",
            "Valeur des cartes : 2 à 10 = leur chiffre ; Valet / Dame / Roi = 10 ; As = 1 ou 11 (au choix).",
            "Le croupier a une carte cachée et doit continuer à tirer jusqu'à atteindre au moins 17.",
            "Tes choix : Tirer (1 carte de plus), Rester, Doubler (×2 la mise + 1 seule carte), Séparer une paire, Abandonner.",
            "« Blackjack » = un As + une carte de valeur 10 dès le départ → la meilleure main, payée 3 contre 2.",
            ("Dépasser 21 = « bust » = perdu tout de suite.", "tip"),
        ],
        {
            "duree": "~45 s",
            "but": "Mettre TOUT le jury au même niveau avant la démo. Indispensable pour les non-joueurs.",
            "dire": [
                "Aller vite et concret : montrer avec les mains « plus proche de 21 que le croupier, sans dépasser ».",
                "Insister sur la carte cachée du croupier : elle servira dans la partie technique (le comptage).",
                "Donner l'exemple du blackjack : « As + Roi = 21 d'entrée, c'est le jackpot. »",
            ],
            "astuce": "Tu peux mimer un tirage de carte : ça détend et ça aide les non-initiés à suivre la démo qui arrive.",
        })

    # 6 — Étapes
    add_bullets_slide(
        prs, "Démarche", "Comment le projet a été construit",
        [
            "1. Cadrage : choix du sujet, des règles et du périmètre.",
            "2. Le moteur de base : les cartes, une main (calcul du total), le sabot de plusieurs jeux.",
            "3. Les joueurs et les 9 stratégies de décision.",
            "4. Le déroulé d'une partie : une manche, puis la session complète.",
            "5. L'interface en couleur (terminal), le mode didacticiel et les explications pas à pas.",
            "6. Les bonus : comptages, simulation, sauvegarde, musique, journaux.",
            "7. Les tests (94) et la documentation. Des commits réguliers du début à la fin.",
        ],
        {
            "duree": "~1 min 30",
            "but": "Montrer une progression claire (critère « présentation complète, toutes les étapes »).",
            "dire": [
                "Raconter le sens de construction : « Je suis parti du cœur (les cartes) vers l'extérieur (l'écran), brique par brique. »",
                "Mentionner les itérations : « D'abord une version jouable simple, puis j'ai enrichi : didacticiel, comptages, simulation. »",
                "Souligner les commits réguliers : « Le sujet l'exige, et ça prouve l'avancement. »",
            ],
            "astuce": "Tu peux pointer l'écran de gauche à droite pour suivre les étapes 1 → 7.",
            "questions": [
                ("Combien de temps ça t'a pris ?", "Donne une fourchette honnête en jours/semaines de travail, par itérations."),
            ],
        })

    # 7 — Démo (intro)
    add_bullets_slide(
        prs, "Démonstration", "Démonstration en direct  (≈ 5 min)",
        [
            "1. Le menu, puis le Didacticiel : jouer une manche avec le conseil affiché.",
            "2. La mise « façon casino » (en jetons) et les records sauvegardés.",
            "3. Comparer les stratégies : un résultat chiffré, visible à l'écran.",
            "4. Les tests qui passent, dans un second terminal.",
            ("Les 3 diapos suivantes reproduisent ces écrans — utile comme secours si la démo plante.", "tip"),
        ],
        {
            "duree": "~15 s d'intro, puis 4-5 min de démo en direct",
            "but": "Annoncer ce qu'on va voir, puis basculer sur le terminal.",
            "dire": [
                "« Place à la démonstration. » Lancer la commande : python -m blackjack",
                "Annoncer le fil : menu → didacticiel → simulation → tests.",
            ],
            "montrer": "Terminal large, police monospace, son activé. Lancer une partie AVANT la soutenance pour « chauffer » (sabot mélangé).",
            "astuce": "On MONTRE, on ne lit pas le code. Garde un œil sur le temps : la démo ne doit pas dépasser 5 min. Si ça casse → passe aux maquettes des diapos suivantes.",
        })

    # 8 — Maquette menu
    add_mono_slide(
        prs, "Démonstration", "Le menu principal",
        MENU_MOCKUP,
        caption="Interface en français, dans le terminal — pensée pour un débutant.",
        note={
            "duree": "~30 s (ou en direct)",
            "but": "Montrer que l'outil est accueillant et clair dès l'ouverture.",
            "dire": [
                "« Voici le menu : 6 options, tout en français. »",
                "« On va choisir l'option 2, le Didacticiel : le mode qui explique tout. »",
            ],
        })

    # 9 — Maquette didacticiel
    add_mono_slide(
        prs, "Démonstration", "Le Didacticiel : le cœur du projet",
        DIDACTICIEL_MOCKUP,
        caption="Le conseil s'affiche à chaque tour ; les touches sont en français (T/R/D/S/A).",
        note={
            "duree": "~2 min (le moment fort de la démo)",
            "but": "Prouver la promesse « apprendre en jouant ».",
            "dire": [
                "Pointer trois choses : (1) le jeu RACONTE ce qui se passe (« le croupier distribue… »), (2) les cartes s'affichent une par une, (3) le CONSEIL apparaît à chaque tour.",
                "Lire l'exemple : « Ici j'ai 17, le croupier montre un 9, le jeu me conseille de Doubler — et m'explique pourquoi. »",
                "Jouer le coup conseillé, laisser le croupier finir, montrer le résultat (gagné/perdu, série de victoires).",
            ],
            "astuce": "C'est LA diapo à soigner : ralentis, c'est ce qui impressionne le jury.",
            "questions": [
                ("Le conseil vient d'où ?", "De tables de stratégie reconnues (Thorp, Wong…), recopiées dans le code et vérifiées par des tests."),
            ],
        })

    # 10 — Maquette simulation
    add_mono_slide(
        prs, "Démonstration", "Comparer les stratégies : un résultat chiffré",
        SIMULATION_MOCKUP,
        caption="« Gain/main » = ce qu'on gagne ou perd en moyenne par main. Valeurs d'exemple : les vraies s'affichent en lançant la simulation (menu → 4).",
        note={
            "duree": "~1 min 30",
            "but": "Donner un RÉSULTAT OBSERVABLE et chiffré (très valorisé par la grille).",
            "dire": [
                "Lancer la simulation en direct (menu 4). Pendant le calcul : « Un robot joue des milliers de mains pour chaque stratégie, on mesure le gain moyen. »",
                "À l'arrivée du tableau, expliquer simplement : « Sans comptage, on perd un peu en moyenne. Avec comptage, on mise plus au bon moment, et ça peut repasser positif. »",
                "Être honnête : « Les chiffres de la diapo sont un exemple ; les vrais viennent de la simulation que je lance là, en direct. »",
            ],
            "astuce": "« Gain/main » négatif = on perd en moyenne ; positif = on gagne. Dis-le avec ces mots simples.",
            "questions": [
                ("Pourquoi des chiffres si proches de zéro ?", "Le blackjack est un jeu très serré : l'avantage se joue à moins de 1 % par main, d'où l'intérêt de jouer beaucoup de mains."),
            ],
        })

    # 11 — Fonctionnalités
    add_bullets_slide(
        prs, "Fonctionnalités", "Ce que le projet sait faire",
        [
            "Blackjack complet : tirer, rester, doubler, séparer, abandonner, assurance.",
            "9 stratégies au choix : 1 manuelle, 1 de base, 7 comptages (Hi-Lo, KO, Hi-Opt I/II, Omega II, Zen, Red 7).",
            "Mise conseillée plus élevée quand le sabot devient favorable.",
            "Sauvegarde & reprise : ton solde, tes statistiques et tes records sont gardés d'une partie à l'autre.",
            "Bonus : musique d'ambiance, réglages dans un fichier, journaux d'activité.",
        ],
        {
            "duree": "~1 min",
            "but": "Balayer l'étendue du projet sans tout re-détailler (la démo a déjà parlé).",
            "dire": [
                "Distinguer encore l'essentiel (jeu + conseil) des bonus (sauvegarde, musique).",
                "Mentionner que les règles se changent dans un simple fichier de configuration, sans toucher au code.",
            ],
        })

    # 12 — Architecture
    add_layers_slide(
        prs, "Architecture", "Le code, rangé en étages",
        [
            ("ui/", "ce que l'on voit : affichage, menus, couleurs, musique"),
            ("game/", "le déroulé : règles, une manche, la partie, les stats"),
            ("players/ + strategies/", "les joueurs et les 9 façons de décider"),
            ("core/", "les briques de base : cartes, main, sabot"),
        ],
        footnote="utils/ (journaux, configuration) sert partout · chaque étage ne dépend que des étages du dessous.",
        note={
            "duree": "~1 min 30",
            "but": "Montrer que le code est organisé, pas un seul gros fichier.",
            "dire": [
                "Lire de bas en haut : « Les briques de base (les cartes) ne connaissent rien du reste ; chaque étage s'appuie seulement sur ceux du dessous. »",
                "Donner l'intérêt concret : « Je pourrais remplacer l'écran texte par une interface graphique sans toucher au moteur du jeu. »",
            ],
            "astuce": "Analogie : « comme une maison — les fondations ne dépendent pas de la décoration, l'inverse oui. »",
            "questions": [
                ("Pourquoi séparer en autant de dossiers ?", "Chaque dossier a une responsabilité unique : c'est plus facile à lire, à tester et à faire évoluer."),
            ],
        })

    # 13 — Piliers POO
    add_bullets_slide(
        prs, "Programmation objet", "Les 3 principes de la programmation objet",
        [
            "Héritage : des classes « filles » réutilisent le code d'une classe « mère ».",
            ("Dealer et HumanPlayer héritent tous deux de BasePlayer : ils partagent la base et ajoutent leurs différences.", "tip"),
            "Polymorphisme : un même appel donne un comportement différent selon l'objet.",
            ("Le jeu dit toujours « donne-moi ton conseil » ; selon la stratégie choisie, la réponse change toute seule.", "tip"),
            "Encapsulation : les données sensibles sont protégées derrière des fonctions.",
            ("On ne peut pas trafiquer le solde directement : on passe par des fonctions qui vérifient (credit / debit).", "tip"),
        ],
        {
            "duree": "~1 min 30",
            "but": "LE bloc attendu par un jury de POO. À maîtriser pour les questions.",
            "dire": [
                "Prendre chaque principe et donner l'exemple « en clair » de la diapo.",
                "Pour le polymorphisme, insister : « C'est ça qui rend les 9 stratégies interchangeables sans modifier le jeu. »",
            ],
            "astuce": "Si tu ne dois retenir qu'un exemple : le polymorphisme avec les stratégies. C'est le plus parlant.",
            "questions": [
                ("Donne un exemple d'héritage dans ton code.", "BasePlayer → Dealer et HumanPlayer ; ou Strategy → BasicStrategy, HiLoStrategy…"),
                ("À quoi sert l'encapsulation ici ?", "Empêcher de modifier le solde ou une carte par erreur ; on passe par des méthodes qui valident."),
            ],
        })

    # 14 — Décisions techniques
    add_bullets_slide(
        prs, "Choix techniques", "Des choix réfléchis (pas par hasard)",
        [
            "Un « registre » central des stratégies : ajouter une nouvelle stratégie = ajouter une seule ligne.",
            "Pour les comptages, j'utilise la composition plutôt que l'héritage.",
            ("Un comptage CONTIENT une stratégie de base (il s'en sert) au lieu d'en hériter → code plus simple à comprendre.", "tip"),
            "Des outils Python qui évitent le code répétitif (dataclass, énumérations).",
            "Très peu de librairies externes : 2 pour l'affichage, le reste en Python « pur ».",
            "Les règles du jeu sont dans un fichier à part (configuration), pas mélangées au code.",
        ],
        {
            "duree": "~1 min 30",
            "but": "Montrer que chaque choix a une RAISON (critère « choix justifiés »).",
            "dire": [
                "Pour chaque point, dire le POURQUOI en une phrase.",
                "Le plus intéressant : « Faire hériter un comptage de la stratégie de base aurait mélangé deux rôles — compter, et décider. La composition garde les rôles séparés. »",
            ],
            "questions": [
                ("Composition ou héritage : comment choisir ?", "Héritage si « est un » (un Dealer EST un joueur) ; composition si « utilise un » (un comptage UTILISE une stratégie)."),
            ],
        })

    # 15 — Point subtil
    add_bullets_slide(
        prs, "Point délicat", "Le piège du comptage : la carte cachée",
        [
            "Pour compter juste, on ne doit compter QUE les cartes réellement vues.",
            "Or le croupier a une carte face cachée : elle est distribuée, mais invisible.",
            "Le programme « oublie » cette carte tant qu'elle est cachée, puis la « recompte » quand elle est retournée.",
            ("Sans cette correction, le comptage serait faussé à chaque main.", "tip"),
        ],
        {
            "duree": "~1 min",
            "but": "Montrer la profondeur du travail — souvent source de questions.",
            "dire": [
                "Expliquer le bug évité : « Si on comptait la carte cachée tout de suite, le joueur « tricherait » avec une info qu'il n'a pas. »",
                "Préciser : « C'est le seul endroit du code où je touche au compteur autrement que par la fonction normale — et c'est testé. »",
            ],
            "astuce": "Bonne diapo pour montrer que tu comprends VRAIMENT ton code, pas seulement que ça marche.",
        })

    # 16 — Tests
    add_bullets_slide(
        prs, "Validation & tests", "Tests : 94 vérifications automatiques",
        [
            "94 tests automatiques qui contrôlent le jeu en moins d'une seconde.",
            ("Un test = un petit programme qui vérifie tout seul qu'une partie du code fait bien ce qu'on attend.", "tip"),
            "Ils vérifient les règles : valeur des mains, gains (blackjack payé 3:2, égalité, abandon, dépassement).",
            "Ils contrôlent les valeurs des comptages et le cas délicat de la carte cachée.",
            "Ils testent la sauvegarde et jouent 200 mains d'affilée sans aucun plantage.",
            "Commande :  python -m unittest discover -s tests -v",
        ],
        {
            "duree": "~1 min 30",
            "but": "Prouver la fiabilité (critère « tests / validation »).",
            "dire": [
                "Si possible, lancer les tests en direct dans un 2e terminal : « tout vert en moins d'une seconde ».",
                "Donner un exemple de test malin : « Sur un jeu complet, mon comptage doit retomber exactement à zéro — sinon mes tables sont fausses. »",
                "Mentionner que les tests ont attrapé de vrais bugs (ex. une boucle sans fin sur la séparation de cartes).",
            ],
            "questions": [
                ("Tes tests couvrent tout ?", "Pas 100 % des lignes, mais tous les cas critiques : règles, gains, comptages, sauvegarde, et une partie complète de bout en bout."),
            ],
        })

    # 17 — Limites
    add_bullets_slide(
        prs, "Limites", "Limites assumées",
        [
            "Pas d'interface graphique : tout se joue dans le terminal (mode texte).",
            "Les comptages changent la mise, mais pas encore la décision de jeu selon le comptage.",
            "Quelques options avancées de casino ne sont pas gérées (ex. « even money »).",
            "Pas de mode à plusieurs joueurs sur la même table.",
        ],
        {
            "duree": "~45 s",
            "but": "Être lucide rapporte des points et désamorce les questions.",
            "dire": [
                "Présenter ces limites comme des CHOIX, pas des oublis : « J'ai préféré un projet fini et testé sur un périmètre maîtrisé. »",
                "Enchaîner naturellement : « Voici justement comment j'irais plus loin. »",
            ],
        })

    # 18 — Améliorations
    add_bullets_slide(
        prs, "Perspectives", "Pistes pour aller plus loin",
        [
            "Faire dévier la décision selon le comptage (le vrai jeu d'un compteur expert).",
            "Ajouter une interface graphique ou web (l'architecture en étages le permet facilement).",
            "Un mode à plusieurs joueurs.",
            "Exporter les statistiques (tableur, graphiques) pour analyser les simulations.",
        ],
        {
            "duree": "~45 s",
            "but": "Montrer que tu sais où aller ensuite.",
            "dire": [
                "Relier à l'architecture : « Ajouter une interface graphique ou une stratégie coûte peu, grâce au rangement en étages et au registre. »",
            ],
        })

    # 19 — Apports
    add_bullets_slide(
        prs, "Bilan", "Ce que j'en retire — et l'entreprise",
        [
            "La programmation objet est devenue concrète : héritage, polymorphisme, encapsulation.",
            "J'ai appris à découper un problème en responsabilités claires.",
            "Le réflexe des tests : vérifier automatiquement, et oser modifier sans tout casser.",
            "Des outils « pro » : packaging, Git régulier, configuration, journaux.",
            "Utile en entreprise : code organisé, testé, et savoir piloter une IA (cadrer, relire, valider).",
        ],
        {
            "duree": "~1 min",
            "but": "Répondre à la question du sujet : qu'as-tu appris, est-ce utile en entreprise ?",
            "dire": [
                "Être sincère : « La vraie compétence, c'est découper un problème et sécuriser par des tests — exactement le travail en équipe. »",
                "Ajouter : « Savoir diriger une IA, la relire et la valider, est devenu une compétence à part entière. »",
            ],
        })

    # 20 — Usage IA
    add_bullets_slide(
        prs, "Usage de l'IA", "Usage de l'IA — déclaré ouvertement",
        [
            "Outil : Claude (Anthropic), via Claude Code. Aucun autre.",
            "Ampleur : la quasi-totalité du code et de la doc a été générée avec l'IA — toujours sous ma direction.",
            "L'IA a fait : génération de code, corrections de bugs, tests, relecture, rédaction.",
            "J'ai dirigé : le sujet, le périmètre, l'architecture, les choix de règles.",
            "J'ai compris, testé et validé chaque partie — et j'ai parfois refusé des propositions.",
            "Déclaré dans le README, la doc PDF, et en-tête des fichiers (# CODE IA).",
        ],
        {
            "duree": "~1 min 30",
            "but": "Section sensible ET notée (3 pts). Être totalement transparent.",
            "dire": [
                "Message clé : « Tout est déclaré, prompts inclus dans la documentation — et je peux expliquer chaque partie du code. »",
                "Donner un exemple de pilotage : « C'est moi qui ai demandé les touches en français, le mode didacticiel, la musique. »",
                "Donner un exemple de refus : « J'ai refusé d'arrondir les gains, pour rester fidèle aux vraies règles. »",
            ],
            "astuce": "Le sujet met un 0 à toute IA non déclarée. Ici on assume franchement : c'est la bonne stratégie.",
            "questions": [
                ("Qu'as-tu fait toi, exactement ?", "La conception, les décisions, la validation par le jeu et les 94 tests, et l'acceptation ou le refus des propositions de l'IA."),
                ("Peux-tu expliquer ce bout de code ?", "Oui — reprends l'exemple du comptage avec la carte cachée ou du polymorphisme."),
            ],
        })

    # 21 — Bibliographie
    add_bullets_slide(
        prs, "Références", "Sources",
        [
            "E. O. Thorp — Beat the Dealer (1962) : fondements de la stratégie et du comptage.",
            "S. Wong — Professional Blackjack ; D. Schlesinger — Blackjack Attack.",
            "A. Snyder — Blackbelt in Blackjack (Zen, Red 7) ; B. Carlson — Blackjack for Blood (Omega II).",
            "Vancura & Fuchs — Knock-Out Blackjack (KO).",
            "Documentation Python officielle ; cours NFP01 (A. Escourrou).",
            "IA : Claude (Anthropic) — Claude Code.",
        ],
        {
            "duree": "~30 s",
            "but": "Crédibiliser : les tables et valeurs ne sont pas inventées.",
            "dire": [
                "Citer rapidement : « Les conseils du jeu viennent de livres de référence, recoupés avec des sources spécialisées. »",
                "Rappeler l'IA dans les sources, comme demandé par le sujet.",
            ],
        })

    # 22 — Ce que j'aurais changé dans l'énoncé
    add_bullets_slide(
        prs, "Retour sur l'énoncé", "Ce que j'aurais changé dans le sujet",
        [
            "La liberté totale du sujet est un vrai atout — à garder.",
            "J'aurais aimé un modèle imposé pour le support oral et un exemple de barème détaillé.",
            "Préciser le poids attendu de la démo par rapport à la partie technique aiderait à doser le temps.",
            "Sinon : un sujet clair, exigeant et formateur.",
        ],
        {
            "duree": "~45 s",
            "but": "Répondre au point du sujet « ce que vous auriez changé… ou pas ».",
            "dire": [
                "Rester constructif et poli, pas de critique gratuite.",
                "Valoriser ce qui marche (la liberté), proposer 1-2 améliorations concrètes.",
            ],
            "astuce": "Montre du recul : c'est apprécié. Termine sur du positif.",
        })

    # 23 — Conclusion
    add_bullets_slide(
        prs, "Conclusion", "En résumé",
        [
            "Un projet FINI : jouable, testé (94 tests), documenté.",
            "Une vraie utilité : apprendre le blackjack en jouant, et voir les stratégies à l'œuvre.",
            "Un code objet propre qui illustre héritage, polymorphisme et encapsulation.",
            "Une IA pilotée, relue et déclarée de bout en bout.",
            "Merci de votre attention — place à vos questions.",
        ],
        {
            "duree": "~30 s",
            "but": "Boucler sur la promesse de départ et finir avec assurance.",
            "dire": [
                "Reprendre le fil : « apprendre en jouant », fini, testé, propre, IA déclarée.",
                "Phrase de clôture nette, puis enchaîner sur la diapo Questions.",
            ],
            "astuce": "Ne t'excuse pas, ne marmonne pas la fin : termine droit, en regardant le jury.",
        })

    # 24 — Questions
    add_questions_slide(prs, {
        "duree": "5 à 10 min",
        "but": "Échange avec le jury.",
        "dire": [
            "Prendre le temps de bien écouter la question, reformuler si besoin.",
            "Si tu ne sais pas : être honnête, proposer une piste plutôt que d'inventer.",
        ],
        "questions": [
            ("Pourquoi la composition pour les comptages ?", "Voir la diapo « Choix techniques » : compter ≠ décider, on sépare les rôles."),
            ("Comment gères-tu la carte cachée du croupier ?", "Voir la diapo « Point délicat » : on l'« oublie » tant qu'elle est cachée."),
            ("Qu'as-tu fait toi vs l'IA ?", "Voir la diapo « Usage de l'IA » : conception, décisions, validation par le jeu et les tests."),
            ("Pourquoi pas d'interface graphique ?", "Choix de périmètre ; l'architecture en étages permet de l'ajouter facilement."),
        ],
        "astuce": "Garde la diapo Annexe (suivante) sous le coude pour les questions techniques pointues.",
    })

    # 25 — Annexe (référence pour les questions)
    add_bullets_slide(
        prs, "Annexe", "Les 9 stratégies & règles de table",
        [
            "Sans comptage : Manuelle (aucune aide) · Stratégie de Base.",
            "Comptages simples : Hi-Lo · KO · Hi-Opt I · Red 7.",
            "Comptages avancés : Hi-Opt II · Omega II · Zen Count.",
            "Exemple Hi-Lo : cartes 2-6 → +1 · 7-9 → 0 · 10-As → -1 (le total retombe à 0 sur un jeu complet).",
            "Règles par défaut : 6 jeux de cartes, le croupier reste à 17, blackjack payé 3:2.",
            ("On joue 75 % du sabot avant de remélanger (« pénétration »).", "tip"),
        ],
        {
            "duree": "à n'afficher que si on te le demande",
            "but": "Diapo de SECOURS pour les questions techniques. Ne pas la présenter d'office.",
            "dire": [
                "L'afficher seulement si le jury demande le détail des stratégies, des comptages ou des règles exactes.",
            ],
        })

    _add_footers(prs)
    _attach_notes(prs)
    return prs


def _note_plaintext(note):
    """Rend une note en texte simple (pour le volet Notes du PowerPoint)."""
    lines = []
    if note.get("duree"):
        lines += [f"Durée indicative : {note['duree']}", ""]
    if note.get("but"):
        lines += [f"But de la diapo : {note['but']}", ""]
    if note.get("dire"):
        lines += ["Ce que tu peux dire :", ""]
        lines += list(note["dire"])
        lines += [""]
    if note.get("montrer"):
        lines += [f"À montrer / préparer : {note['montrer']}", ""]
    if note.get("astuce"):
        lines += [f"Astuce orale : {note['astuce']}", ""]
    if note.get("questions"):
        lines += ["Si le jury demande :", ""]
        lines += [f"« {q} »  →  {a}" for q, a in note["questions"]]
        lines += [""]
    return "\n".join(lines).strip()


def _attach_notes(prs):
    """Écrit les notes de présentateur dans le volet Notes de chaque diapo
    (même ordre que la création des diapos)."""
    for slide, (_title, note) in zip(prs.slides, SPEAKER_NOTES):
        slide.notes_slide.notes_text_frame.text = _note_plaintext(note)


def _render_note(num, title, note):
    """Met en forme une diapo dans le fichier de notes (Markdown)."""
    out = [f"## Diapo {num} — {title}", ""]
    if note.get("duree"):
        out += [f"*Durée indicative : {note['duree']}*", ""]
    if note.get("but"):
        out += [f"**But de la diapo :** {note['but']}", ""]
    if note.get("dire"):
        out += ["**Ce que tu peux dire :**", ""]
        out += [f"- {d}" for d in note["dire"]]
        out += [""]
    if note.get("montrer"):
        out += [f"**À montrer / préparer :** {note['montrer']}", ""]
    if note.get("astuce"):
        out += [f"**Astuce orale :** {note['astuce']}", ""]
    if note.get("questions"):
        out += ["**Si le jury demande :**", ""]
        out += [f"- *« {q} »* → {a}" for q, a in note["questions"]]
        out += [""]
    out += ["---", ""]
    return "\n".join(out)


def write_speaker_notes(path: Path):
    """Écrit le fichier de notes de présentateur (une section par diapo)."""
    head = [
        "# Notes de présentateur — Soutenance « Blackjack POO »",
        "",
        "> Fiche d'accompagnement du diaporama `Presentation_Blackjack_NFP01.pptx`.",
        "> **Une section par diapo, numérotée.** Les mêmes notes figurent aussi dans le",
        "> volet « Notes » de chaque diapo du PowerPoint (mode Présentateur). Ce fichier",
        "> reste pratique pour réviser ou le garder sous les yeux (téléphone, feuille, 2e écran).",
        "",
        "**Objectif global :** ~20 à 25 minutes, dont **5 min maximum de démo**, puis 5-10 min de questions.",
        "",
        "**Conseils généraux :**",
        "",
        "- Parle avec **tes mots** : ce sont des repères, pas un texte à réciter.",
        "- Regarde le **jury**, pas l'écran. Ralentis sur la démo et sur la partie objet.",
        "- Chaque terme technique a déjà une explication « En clair » sur la diapo : appuie-toi dessus.",
        "- Surveille le temps : environ **1 minute par diapo** en moyenne (la démo est le gros morceau).",
        "- Tu n'es pas obligé de tout dire : si tu es en retard, garde l'essentiel.",
        "",
        "---",
        "",
    ]
    blocks = [_render_note(i, title, note) for i, (title, note) in enumerate(SPEAKER_NOTES, 1)]
    path.write_text("\n".join(head) + "\n".join(blocks), encoding="utf-8")


def main():
    prs = build()
    prs.save(str(OUT_PPTX))
    write_speaker_notes(OUT_NOTES)
    print(f"Diaporama généré : {OUT_PPTX}  ({len(prs.slides._sldIdLst)} diapositives)")
    print(f"Notes générées   : {OUT_NOTES}  ({len(SPEAKER_NOTES)} sections)")


if __name__ == "__main__":
    main()
