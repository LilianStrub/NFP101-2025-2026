import pygame
import random
from classes.Snake import Snake
from classes.Food import Food

class Game:

    def __init__(self, width, height):
        """
        Constructeur de la classe Game.
        Initialise la largeur et la hauteur du jeu (avec des bordures de couleurs blanches pour délimiter l'aire de jeu).
        Initialise Pygame, la fenêtre de jeu, l'horloge et les entités
        :param width: largeur du jeu
        :param height: hauteur du jeu
        """
        pygame.init()
        
        self.state = "menu" 
        
        self.game_width = width
        self.game_height = height
        
        self.window_width = width * 2
        self.window_height = height * 2
        
        self.TITLE_FONT_SIZE = 42
        self.TEXT_FONT_SIZE = 24


        self.screen = pygame.display.set_mode((self.window_width, self.window_height))

        pygame.display.set_caption("Snake")
        
        # Surface de jeu
        self.game_surface = pygame.Surface((self.game_width, self.game_height))
        
        self.game_x = (self.window_width - self.game_width) // 2
        self.game_y = (self.window_height - self.game_height) // 2

        self.clock = pygame.time.Clock()
        self.speed = 5
        
        self.score = 0

        self.snake = Snake(self.game_width // 2, self.game_height // 2)
        
        x = random.randrange(0, self.game_width, 20)
        y = random.randrange(0, self.game_height, 20)
        self.food = Food(x, y)
        
        self.entities = [self.snake, self.food]

    def draw_menu(self):
        """
        Affiche le menu principal du jeu.
        """

        self.screen.fill((0, 0, 0))
        font_title = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        font_text = pygame.font.Font(None, self.TEXT_FONT_SIZE)
        
        # Titre
        title = font_title.render("Le super SNAKE", True, (0, 255, 0))
        title_rect = title.get_rect(center=(self.window_width // 2, self.window_height // 3))
        self.screen.blit(title, title_rect)
        
        # Instructions
        text = font_text.render("Appuyez sur ESPACE pour jouer", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def draw_game_over(self):
        """
        Affiche l'écran de fin de jeu.
        """
        
        self.screen.fill((20, 20, 20))
        font_title = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        font_text = pygame.font.Font(None, self.TEXT_FONT_SIZE)
        
        # Game Over
        title = font_title.render("GAME OVER", True, (255, 0, 0))
        title_rect = title.get_rect(center=(self.window_width // 2, self.window_height // 3))
        self.screen.blit(title, title_rect)
        
        # Score
        score_text = font_text.render(f"Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.screen.blit(score_text, score_rect)
        
        # Rejouer
        restart = font_text.render("Appuyez sur ESPACE pour rejouer", True, (255, 255, 255))
        restart_rect = restart.get_rect(center=(self.window_width // 2, self.window_height * 2 // 3))
        self.screen.blit(restart, restart_rect)
        
        pygame.display.flip()

    def reset_game(self):
        """
        Réinitialise l'état du jeu pour une nouvelle partie.
        """

        self.snake = Snake(self.game_width // 2, self.game_height // 2)
        
        x = random.randrange(0, self.game_width, 20)
        y = random.randrange(0, self.game_height, 20)
        self.food = Food(x, y)
        
        self.entities = [self.snake, self.food]
        self.score = 0
        self.state = "playing"
    
    def pause_game(self):
        """
        Met le jeu en pause quand on appuie sur ECHAP et si on rappuie sur ECHAP, le jeu reprend la où il en était.
        """
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"
        

    def handle_events(self):
        """
        Gère les événements Pygame.
        Si le joueur ferme la fenêtre ou appuie sur la touche échap, quitte le jeu.
        """
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                # Menu ou Game Over : ESPACE pour (re)démarrer
                if self.state in ["menu", "game_over"]:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE: 
                        self.quit_game()
                
                # En jeu : contrôles du serpent (ne peut pas faire demi-tour)
                elif self.state in ["playing", "paused"]:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_game()

                    if self.state == "playing":
                        if event.key == pygame.K_UP and self.snake._dy == 0:
                            self.snake.set_direction(0, -1)
                        elif event.key == pygame.K_DOWN and self.snake._dy == 0:
                            self.snake.set_direction(0, 1)
                        elif event.key == pygame.K_LEFT and self.snake._dx == 0:
                            self.snake.set_direction(-1, 0)
                        elif event.key == pygame.K_RIGHT and self.snake._dx == 0:
                            self.snake.set_direction(1, 0)   
                
    def update(self):
        """
        Met à jour l'état du jeu.
        Gère les mises à jour du serpent et les collisions.
        """
        
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
            # repositionner la nourriture (sauf sur le serpent)
            while True:
                x = random.randrange(0, self.game_width, 20)
                y = random.randrange(0, self.game_height, 20)
                if (x, y) not in self.snake._body:
                    self.food.respawn(x // self.food.CELL_SIZE, y // self.food.CELL_SIZE)
                    break

    def draw(self):
        """
        Met à jour les éléments graphiques du jeu.
        """
        # Fond de la fenêtre
        self.screen.fill((30, 30, 30))

        # Fond d'écran de jeu
        self.game_surface.fill((0, 0, 0))

        # Dessin des entités sur la surface de jeu
        for entity in self.entities:
            entity.draw(self.game_surface)

        # Affichage centré
        self.screen.blit(self.game_surface, (self.game_x, self.game_y))

        # Bordure blanche
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (self.game_x, self.game_y, self.game_width, self.game_height),
            2  # épaisseur
        )

        pygame.display.flip()
        
    def draw_pause(self):
        # Dessiner le jeu figé
        self.draw()

##################### CODE IA #####################
        # Overlay semi-transparent
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
###################################################
        
        font_title = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        font_text = pygame.font.Font(None, self.TEXT_FONT_SIZE)

        pause_text = font_title.render("PAUSE", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(self.window_width // 2, self.window_height // 2 - 30))
        self.screen.blit(pause_text, pause_rect)

        info = font_text.render("Appuyez sur ECHAP pour reprendre", True, (200, 200, 200))
        info_rect = info.get_rect(center=(self.window_width // 2, self.window_height // 2 + 20))
        self.screen.blit(info, info_rect)

        pygame.display.flip()


    def run(self):
        while True:
            self.handle_events()
            
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.update()
                self.draw()
            elif self.state == "paused":
                self.draw_pause()
            elif self.state == "game_over":
                self.draw_game_over()
     
            self.clock.tick(self.speed)

    def quit_game(self):
        """
        Quitte le jeu proprement.
        """
        pygame.quit()
        exit()