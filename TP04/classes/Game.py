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
        self.state = "menu" 
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Snake")

        self.clock = pygame.time.Clock()
        self.score = 0

        self.snake = Snake(width/2, height/2)
        
        x = random.randrange(0, self.width, 20)
        y = random.randrange(0, self.height, 20)
        self.food = Food(x, y)
        self.entities = [self.snake, self.food]

    def draw_menu(self):
        """
        Affiche le menu principal du jeu.
        """

        self.screen.fill((0, 0, 0))
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        # Titre
        title = font_title.render("Le super SNAKE", True, (0, 255, 0))
        title_rect = title.get_rect(center=(self.width/2, self.height/3))
        self.screen.blit(title, title_rect)
        
        # Instructions
        text = font_text.render("Appuyez sur ESPACE pour jouer", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def draw_game_over(self):
        """
        Affiche l'écran de fin de jeu.
        """

        self.screen.fill((0, 0, 0))
        font_title = pygame.font.Font(None, 74)
        font_text = pygame.font.Font(None, 36)
        
        # Game Over
        title = font_title.render("LOOSER", True, (255, 0, 0))
        title_rect = title.get_rect(center=(self.width/2, self.height/3))
        self.screen.blit(title, title_rect)
        
        # Score
        score_text = font_text.render(f"Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.width/2, self.height/2))
        self.screen.blit(score_text, score_rect)
        
        # Rejouer
        restart = font_text.render("Appuyez sur ESPACE pour rejouer", True, (255, 255, 255))
        restart_rect = restart.get_rect(center=(self.width/2, self.height*2/3))
        self.screen.blit(restart, restart_rect)
        
        pygame.display.flip()

    def reset_game(self):
        """
        Réinitialise l'état du jeu pour une nouvelle partie.
        """

        self.snake = Snake(self.width/2, self.height/2)
        x = random.randrange(0, self.width, 20)
        y = random.randrange(0, self.height, 20)
        self.food = Food(x, y)
        self.entities = [self.snake, self.food]
        self.score = 0
        self.state = "playing"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                # Menu ou Game Over : ESPACE pour (re)démarrer
                if self.state in ["menu", "game_over"]:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                
                # En jeu : contrôles du serpent
                elif self.state == "playing":
                    if event.key == pygame.K_UP:
                        self.snake.set_direction(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.snake.set_direction(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.snake.set_direction(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.set_direction(1, 0)
    def update(self):
        if self.state != "playing":
            return
            
        game_over = self.snake.update()
        if game_over:
            self.state = "game_over"  # Au lieu de quit_game()
            return
            
        # Collision serpent / nourriture
        if self.snake._body[0] == (self.food.x, self.food.y):
            self.snake.grow(1)  # augmente _grow_pending de 1
            self.score += 1
            # repositionner la nourriture
            self.food.x = random.randrange(0, self.width, self.food.width)
            self.food.y = random.randrange(0, self.height, self.food.height)

    def draw(self):
        """
        Met à jour les éléments graphiques du jeu.
        """
        self.screen.fill((0, 0, 0))
        for entity in self.entities:
            entity.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.update()
                self.draw()
            elif self.state == "game_over":
                self.draw_game_over()
                
            self.clock.tick(10)

    def quit_game(self):
        """
        Affiche "Game Over" et quitte le jeu proprement.
        """
        print(f"Game Over ! Ton score : {self.score}")
        pygame.quit()
        exit()
