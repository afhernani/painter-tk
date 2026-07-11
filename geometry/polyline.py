from .shape import Shape
from .point import Punto
from .line import Linea

class Polyline(Shape):
    """Bloque de rectas conectadas (trazo de lápiz)"""
    
    def __init__(self, puntos: list[Punto], **kwargs):
        super().__init__(**kwargs)
        self.puntos = puntos
        self._lineas = [
            Linea(puntos[i], puntos[i+1], **kwargs)
            for i in range(len(puntos) - 1)
        ]
        self._canvas_ids = []
    
    def dibujar_en(self, canvas):
        self._canvas_ids = []
        for linea in self._lineas:
            cid = linea.dibujar_en(canvas)
            self._canvas_ids.append(cid)
        return self._canvas_ids
    
    def bbox(self):
        xs = [p.x for p in self.puntos]
        ys = [p.y for p in self.puntos]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def mover(self, dx, dy):
        for p in self.puntos:
            p.x += dx
            p.y += dy