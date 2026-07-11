from .shape import Shape
from .point import Punto

class Linea(Shape):
    def __init__(self, p1: Punto, p2: Punto, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2
    
    def dibujar_en(self, canvas):
        self._canvas_id = canvas.create_line(
            self.p1.x, self.p1.y, self.p2.x, self.p2.y,
            fill=self.color, width=self.grosor
        )
        return self._canvas_id
    
    def bbox(self):
        return (
            min(self.p1.x, self.p2.x), min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x), max(self.p1.y, self.p2.y)
        )
    
    def mover(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy