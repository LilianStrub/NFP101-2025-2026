class MovingEntity(Entity):
    CELL_SIZE = 20
    DEFAULT_SPEED = 10
    def __init__(self):
        self._dx = self.CELL_SIZE
        self._dy = 0
        self._speed = self.DEFAULT_SPEED
        super().__init__(0,0,self.CELL_SIZE,self.CELL_SIZE)
    def set_cell_size(cls, value):
        cls.CELL_SIZE = value
    def set_default_speed(cls, value):
        cls.DEFAULT_SPEED = value
    def set_direction(self,dx,dy):
        self._dx = dx * self.CELL_SIZE
        self._dy = dy * self.CELL_SIZE

from TP04.classes.Entity import Entity