from classes.Entity import Entity

# Définition de la classe MovingEntity qui hérite de Entity
class MovingEntity(Entity):
    CELL_SIZE = 20
    DEFAULT_SPEED = 10
    
    def __init__(self):
        """
        Constructeur de la classe MovingEntity.
        Initialise la position, la taille, la direction et la vitesse de l'entité mobile.
        """
        self._dx = self.CELL_SIZE
        self._dy = 0
        self._speed = self.DEFAULT_SPEED
        super().__init__(0,0,self.CELL_SIZE,self.CELL_SIZE)

    @classmethod
    def set_cell_size(cls, value):
        """
        Définit la taille de la cellule.
        :param value: nouvelle taille de cellule
        """
        cls.CELL_SIZE = value
        
    @classmethod
    def set_default_speed(cls, value):
        """
        Définit la vitesse par défaut du serpent.
        :param value: nouvelle vitesse par défaut
        """
        cls.DEFAULT_SPEED = value
        
    def set_direction(self,dx,dy):
        """
        Met à jour la direction.
        :param dx: direction en x
        :param dy: direction en y
        """
        self._dx = dx * self.CELL_SIZE
        self._dy = dy * self.CELL_SIZE