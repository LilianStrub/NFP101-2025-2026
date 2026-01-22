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
        if (new_head[0] < 0 or new_head[0] >= 800 or
            new_head[1] < 0 or new_head[1] >= 600):
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
        Dessine chaque segment du serpent.
        :param screen: surface de dessin
        """
        for x, y in self._body:
            rect = (x, y, self.width, self.height)
            screen.draw_rect(rect, color=(0, 255, 0))

    def grow(self, n):
        """
        Augmente la taille du serpent.
        :param n: nombre de segments à ajouter
        """
        self._grow_pending += n
