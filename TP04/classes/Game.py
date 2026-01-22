from TP04.classes.Food import Food
import pygame

# Définition de la classe Game
class Game:
    def __init__(self, width, height):
        """
        Constructeur de la classe Game.
        Initialise la largeur et la hauteur du jeu.
        :param width: largeur du jeu
        :param height: hauteur du jeu
        """
        pygame.init()
        self.score = 0
        self.food = Food()
        self.entities = [self.food, self.snake]
        self.width = width
        self.height = height
    
    def handle_events(self, events):
        """
        Gère les événements du jeu.
        :param events: liste des événements
        """
        for event in events:
            if event.type == 'QUIT':
                self.quit_game()
    
    def update(self):
        """
        Met à jour les déplacements du serpent via les entities
        """
        for entity in self.entities:
            entity.update()

    def draw(self, screen):
        """
        Met à jour les éléments graphiques du jeu.
        :param screen: surface de dessin
        """
        for entity in self.entities:
            entity.draw(screen)
    
    def run(self):
        """
        Démarre la boucle principale du jeu.
        """
        running = True
        while running:
            events = self.get_events()
            self.handle_events(events)
            self.update()
            self.draw(None)  # Remplacer None par l'objet écran réel