# Snake - Guide du jeu

## Auteurs

Lilian STRUB & Merouan MENEU

## Installation
```bash
pip install pygame
py snake.py dans /TP04
```

## Commandes
- **↑** : Haut
- **↓** : Bas
- **←** : Gauche
- **→** : Droite
- **ESCAPE** : Pause
- **SPACE** : Lancer/rejouer

## Règles
- Manger la nourriture (rouge) pour grandir
- Éviter les murs et votre propre corps
- Chaque nourriture = +1 point
- Demi-tour interdit (impossible de revenir sur soi-même)
- Déplacement sur grille (160*160 pixels)

# Analyse du jeu Snake - Réponses

## 1. Rôles respectifs
- **Snake** : entité joueur, gère son corps, direction et collisions
- **Food** : cible à manger, gère sa position et son respawn
- **Game** : coordinateur central (boucle de jeu, événements, score, création des entités)

## 2. Exemple avec Food qui intervient sur `_body`
```python
# Si Food accédait directement à _body du serpent
self.snake._body.append(self.food.pos())  # Segment incohérent, collision faussée
```

## 3. Interface implicite (polymorphisme)
`Snake` et `Food` héritent tous deux de `MovingEntity`, qui définit l'interface commune : `draw(screen)`, `set_direction()`, et les attributs de position/taille.

## 4. Pourquoi `Food.update()` existe
Dans notre cas, seul le serpent s'update (il bouge et mange). La food ne s'update pas — c'est `Game` qui gère son respawn. La méthode existe par héritage pour maintenir une interface cohérente.

## 5. Logique factorisée dans MovingEntity
Position (`x`, `y`), taille (`width`, `height`), direction (`_dx`, `_dy`) et vitesse (`_speed`) de l'entité.

## 6. Attributs de classe vs instance
Si c'étaient des paramètres d'instance, des valeurs mal définies (ex: `snake.CELL_SIZE = 20` et `food.CELL_SIZE = 15`) créeraient des incohérences et causeraient des bugs de collision/alignement.

## 7. Protection par `set_cell_size()`
Dans le cas où un développeur tente de modifier la taille avec une valeur invalide (négative, nulle), le setter peut valider et rejeter la modification.

## 8. Éviter l'héritage ?
Oui, via **composition** (ex: `self.movement = Movement()`). Mais ici l'héritage reste pertinent car la hiérarchie est simple et naturelle.