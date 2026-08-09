from .shape import Shape
from .point import Punto
import tkinter as tk

class Linea(Shape):
    def __init__(self, p1: Punto, p2: Punto, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2
    
    def dibujar_en(self, canvas:tk.Canvas) -> int:
        p1_sx, p1_sy = canvas.world_to_screen(self.p1.x, self.p1.y)
        p2_sx, p2_sy = canvas.world_to_screen(self.p2.x, self.p2.y)
        self._canvas_id = canvas.create_line(
            #self.p1.sx, self.p1.y, self.p2.x, self.p2.y,
            p1_sx, p1_sy, p2_sx, p2_sy,
            fill=self.color, width=self.grosor
        )
        return self._canvas_id
    
    def actualizar_en_canvas(self, canvas:tk.Canvas):
        """Actualiza las coordenadas de la línea en el canvas"""
        if self._canvas_id is not None:
            # Convertir coordenadas del mundo a pantalla
            p1_sx, p1_sy = canvas.world_to_screen(self.p1.x, self.p1.y)
            p2_sx, p2_sy = canvas.world_to_screen(self.p2.x, self.p2.y)
            #canvas.coords(self._canvas_id, self.p1.x, self.p1.y, self.p2.x, self.p2.y)
            # Actualizar las coordenadas del item en el canvas
            canvas.coords(self._canvas_id, p1_sx, p1_sy, p2_sx, p2_sy)

            
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


    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=self.color, width=self.grosor)

    def to_dict(self):
        return {
            "type": "Linea",
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "color": self.color,
            "grosor": self.grosor
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Linea':
        """Deserializa una línea desde un diccionario JSON"""
        p1 = Punto.from_dict(data["p1"])
        p2 = Punto.from_dict(data["p2"])
        return cls(
            p1=p1,
            p2=p2,
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0)
        )

    def dibujar_en_pil(self, draw, transform=None, scale=1.0):
        """Dibuja la línea en una imagen PIL"""
        if transform is None:
            transform = lambda x, y: (x, y)
        p1 = transform(self.p1.x, self.p1.y)
        p2 = transform(self.p2.x, self.p2.y)
        stroke = max(1, int(self.grosor * scale))
        draw.line([p1, p2], fill=self.color, width=stroke)

    def __repr__(self):
        return f"Linea({self.p1}, {self.p2}, color={self.color})"