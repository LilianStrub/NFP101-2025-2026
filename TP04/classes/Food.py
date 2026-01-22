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
        super().__init__()
        self.x = x
        self.y = y

    def draw(self, screen):
        """
        Dessine la nourriture.
        :param screen: surface de dessin
        """
        rect = (self.x, self.y, self.width, self.height)
        screen.draw_rect(rect, color=(255, 0, 0))
        
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
        
   