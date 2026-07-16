from .shape import Shape
from .point import Punto
import tkinter as tk

class Linea(Shape):
    def __init__(self, p1: Punto, p2: Punto, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2
    
    def dibujar_en(self, canvas:tk.Canvas) -> int:
        self._canvas_id = canvas.create_line(
            self.p1.x, self.p1.y, self.p2.x, self.p2.y,
            fill=self.color, width=self.grosor
        )
        return self._canvas_id
    
    def actualizar_en_canvas(self, canvas:tk.Canvas):
        """Actualiza las coordenadas de la línea en el canvas"""
        if self._canvas_id is not None:
            canvas.coords(
                self._canvas_id, 
                self.p1.x, self.p1.y, 
                self.p2.x, self.p2.y
            )

    def bbox(self):
        return (
            min(self.p1.x, self.p2.x), min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x), max(self.p1.y, self.p2.y)
        )
    
    # def mover(self, dx, dy):
    #     self.p1.x += dx
    #     self.p1.y += dy
    #     self.p2.x += dx
    #     self.p2.y += dy
    
    def mover(self, dx:float, dy:float):
        self.p1.mover(dx, dy)
        self.p2.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Las líneas necesitan 4 coordenadas, no un bbox."""
        if self._canvas_id is not None:
            canvas.coords(
                self._canvas_id,
                self.p1.x, self.p1.y, self.p2.x, self.p2.y
            )

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=self._original_color)

    def to_dict(self):
        return {
            "type": "Linea",
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "color": self.color,
            "grosor": self.grosor
        }

    def dibujar_en_pil(self, draw):
        """Dibuja la línea en una imagen PIL"""
        draw.line(
            [(self.p1.x, self.p1.y), (self.p2.x, self.p2.y)],
            fill=self.color, width=int(self.grosor)
        )

    def __repr__(self):
        return f"Linea({self.p1}, {self.p2}, color={self.color})"