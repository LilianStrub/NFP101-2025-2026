class Snake(MovingEntity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self._body = [(x, y)]
        self._grow_pending = 0
    
    # Insère une nouvelle tête et renvoie la position de la tête
    @classmethod
    def update(self):
        # Calculate new head position
        new_head = (self.x + self._dx, self.y + self._dy)
        self._body.insert(0, new_head)  # Ajoute une nouvelle tête au début de la liste
        
        if self._grow_pending > 0:
            self._grow_pending -= 1  # Diminue le compteur
        else:
            self._body.pop()  # Retire le dernier segment si pas en croissance
        
        self.x, self.y = new_head  # Met à jour la position actuelle

        return new_head

    # Dessine chaque segment du serpent
    @classmethod
    def draw(self, screen):
        for segment in self._body:
            rect = (segment[0], segment[1], self.width, self.height)
            screen.draw_rect(rect, color=(0, 255, 0))  # Draw each segment in green

    @classmethod
    def move(self):
        # Update the position of the snake based on its direction
        new_head = (self.position[0] + self.direction[0], self.position[1] + self.direction[1])
        self.segments.insert(0, new_head)  # Add new head position
        self.segments.pop()  # Remove the last segment to maintain length
        self.position = new_head

    # Augmente la taille du serpent via la variable _grow_pending
    @classmethod
    def grow(self, n):
        self._grow_pending += n

    @classmethod
    def change_direction(self, new_direction):
        # Change the direction of the snake
        self.direction = new_direction
    
from TP04.classes.MovingEntity import MovingEntity