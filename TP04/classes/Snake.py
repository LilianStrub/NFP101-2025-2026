import pygame
from classes.MovingEntity import MovingEntity

# Définition de la classe Snake qui hérite de MovingEntity
class Snake(MovingEntity):

    def __init__(self, x, y):
        """
        Constructeur de la classe Snake.
        Initialise la position initiale et le corps du serpent.
        @param x: position initiale en x
        @param y: position initiale en y
        """
        super().__init__(x, y)
        self._body = [(x, y)]
        self._grow_pending = 0

    def update(self):
        """
        Met à jour la position du serpent.
        Retourne True si game over, False sinon.
        """
        new_head = (self.x + self._dx, self.y + self._dy)

        # Collision avec les murs
        if (new_head[0] < 0 or new_head[0] >= 400 or
            new_head[1] < 0 or new_head[1] >= 400):
            return True

        # Collision avec lui-même
        if new_head in self._body:
            return True

        # Déplacement
        self._body.insert(0, new_head)

        if self._grow_pending > 0:
            self._grow_pending -= 1
        else:
            self._body.pop()

        self.x, self.y = new_head
        return False

    def draw(self, screen):
        """
        Dessine chaque segment du serpent de plus en plus petit (1% en moins).
        La tête comporte 2 yeux et une langue rouge avec la queue du serpent plus fine.
        :param screen: surface de dessin
        """
        segment_size = self.CELL_SIZE
        for index, (seg_x, seg_y) in enumerate(self._body):
            # Calcul de la taille du segment
            size = int(segment_size * (0.99 ** index))
            offset = (self.CELL_SIZE - size) // 2
            pygame.draw.rect(screen, (0, 255, 0), (seg_x + offset, seg_y + offset, size, size))

            # Dessiner les yeux et la langue pour la tête
            if index == 0:
                eye_radius = size // 10
                eye_offset_x = size // 4
                eye_offset_y = size // 4
                # Yeux
                pygame.draw.circle(screen, (0, 0, 0), (seg_x + offset + eye_offset_x, seg_y + offset + eye_offset_y), eye_radius)
                pygame.draw.circle(screen, (0, 0, 0), (seg_x + offset + size - eye_offset_x, seg_y + offset + eye_offset_y), eye_radius)
                # Langue
                tongue_width = size // 6
                tongue_height = size // 4
                tongue_x = seg_x + offset + (size - tongue_width) // 2
                tongue_y = seg_y + offset + size
                pygame.draw.rect(screen, (255, 0, 0), (tongue_x, tongue_y, tongue_width, tongue_height))

    def grow(self, n):
        """
        Augmente la taille du serpent via la variable _grow_pending.
        :param n: nombre de segments à ajouter
        """
        self._grow_pending += n
    
    def head_pos(self):
        """
        Retourne la position actuelle de la tête du serpent.
        :return: tuple (x, y)
        """
        return (self.x, self.y)
    
    def length(self):
        """
        Retourne la longueur actuelle du serpent.
        :return: longueur du serpent
        """
        return len(self._body)
    
