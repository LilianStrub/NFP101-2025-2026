class Entity:
    def __init__(self,x,y,width,height):
        """
        Constructeur de la classe Entity.
        Initialise la position et la taille de l'entité.
        :param x: position en x
        :param y: position en y
        :param width: largeur de l'entité
        :param height: hauteur de l'entité
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def update(self,game):
        """
        Met à jour l'état de l'entité.
        :param game: instance du jeu
        """
        pass
    
    def draw(self,screen):
        """
        Dessine l'entité sur l'écran.
        :param screen: surface de dessin"""
        pass
    