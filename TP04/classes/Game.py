import pygame
import random
from classes.Snake import Snake
from classes.Food import Food

class Game:
    def __init__(self, width, height):
        """
        Constructeur de la classe Game.
        Initialise la largeur et la hauteur du jeu.
        :param width: largeur du jeu
        :param height: hauteur du jeu
        """
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Snake")

        self.clock = pygame.time.Clock()
        self.score = 0

        self.snake = Snake(400, 300)
        
        x = random.randrange(0, self.width, 20)
        y = random.randrange(0, self.height, 20)
        self.food = Food(x, y)
        self.entities = [self.snake, self.food]

    def handle_events(self):
        """
        Gère les événements du jeu au clavier.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.set_direction(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.snake.set_direction(0, 1)
                elif event.key == pygame.K_LEFT:
                    self.snake.set_direction(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.snake.set_direction(1, 0)

    def update(self):
        """
        Met à jour les déplacements du serpent via les entities
        """
        game_over = self.snake.update()
        if game_over:
            self.quit_game()

    def draw(self):
        """
        Met à jour les éléments graphiques du jeu.
        """
        self.screen.fill((0, 0, 0))
        for entity in self.entities:
            entity.draw(self.screen)
        pygame.display.flip()

    def run(self):
        """
        Démarre la boucle principale du jeu.
        """
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(10)

    def quit_game(self):
        """
        Quitte le jeu proprement.
        """
        pygame.quit()
        exit()
