import pygame
from classes.MovingEntity import MovingEntity

# Définition de la classe Food qui hérite de MovingEntity
class Food(MovingEntity):
    def __init__(self, x, y):
        """
        Constructeur de la classe Food.
        Initialise la position initiale de la nourriture.
        @param x: position initiale en x
        @param y: position initiale en y
        """
        super().__init__(x,y)

    def draw(self, screen):
        """
        Dessine la nourriture avec une pomme ronde rouge et une tige penchée verte.
        :param screen: surface de dessin
        """
        # Dessiner le corps de la pomme (rouge)
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        radius = self.width // 2
        pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), radius)

        # Dessiner la tige de la pomme (verte)
        stem_width = self.width // 6
        stem_height = self.height // 3
        stem_x = center_x - stem_width // 2 + 4  # Décalage pour pencher la tige
        stem_y = self.y - stem_height // 2
        pygame.draw.rect(screen, (0, 255, 0), (stem_x, stem_y, stem_width, stem_height))
        
    def pos(self):
        """
        Retourne la position actuelle de la nourriture.
        :return: tuple (x, y)
        """
        return (self.x, self.y)    
        
    def respawn(self, x, y):
        """
        Réinitialise la position de la nourriture.
        Utilise MovingEntity.CELL_SIZE pour réaparaître sur la grille.
        :param x: nouvelle position en x
        :param y: nouvelle position en y
        """
        self.x = x * self.CELL_SIZE
        self.y = y * self.CELL_SIZE
        
   