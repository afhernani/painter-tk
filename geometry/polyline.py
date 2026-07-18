from .shape import Shape
from .point import Punto
from .line import Linea
import tkinter as tk

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
        self._tag_unico = f"polyline_{id(self)}" # tag propio
    
    def dibujar_en(self, canvas: tk.Canvas):
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
            p.mover(dx, dy)

    def actualizar_en_canvas(self, canvas: tk.Canvas):
        for i, linea in enumerate(self._lineas):
            if i < len(self._canvas_ids):
                canvas.coords(
                    self._canvas_ids[i],
                    linea.p1.x, linea.p1.y, linea.p2.x, linea.p2.y
                )

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        for cid in self._canvas_ids:
            canvas.itemconfig(cid, fill=color)

    def restaurar(self, canvas: tk.Canvas):
        for cid in self._canvas_ids:
            canvas.itemconfig(cid, fill=self.color, width=self.grosor)

    def to_dict(self):
        return {
            "type": "Polyline",
            "puntos": [p.to_dict() for p in self.puntos],
            "color": self.color,
            "grosor": self.grosor
        }

    def dibujar_en_pil(self, draw):
        """Dibuja la polilínea en una imagen PIL"""
        if len(self.puntos) < 2:
            return
        puntos = [(p.x, p.y) for p in self.puntos]
        draw.line(puntos, fill=self.color, width=int(self.grosor))

    def __repr__(self):
        return f"Polyline({len(self.puntos)} puntos)"