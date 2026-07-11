from .shape import Shape
from .point import Punto

class Circulo(Shape):
    def __init__(self, centro: Punto, radio: float, **kwargs):
        super().__init__(**kwargs)
        self.centro = centro
        self.radio = radio
    
    def dibujar_en(self, canvas):
        x1 = self.centro.x - self.radio
        y1 = self.centro.y - self.radio
        x2 = self.centro.x + self.radio
        y2 = self.centro.y + self.radio
        self._canvas_id = canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color, width=self.grosor
        )
        return self._canvas_id
    
    def bbox(self):
        return (
            self.centro.x - self.radio, self.centro.y - self.radio,
            self.centro.x + self.radio, self.centro.y + self.radio
        )
    
    def mover(self, dx, dy):
        self.centro.x += dx
        self.centro.y += dy