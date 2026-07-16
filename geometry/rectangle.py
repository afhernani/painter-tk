# -*- coding: utf-8 -*-
"""
Clase Rectangulo para representar rectángulos
"""
from .point import Punto
from .shape import Shape
import tkinter as tk
from typing import Tuple


class Rectangulo(Shape):
    """Representa un rectángulo definido por dos esquinas"""
    
    def __init__(self, p1: Punto, p2: Punto, color: str = 'black',
                 grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa un rectángulo
        
        Args:
            p1: Esquina superior izquierda
            p2: Esquina inferior derecha
            color: Color del contorno
            grosor: Grosor del contorno
            relleno: Color de relleno
        """
        super().__init__(color, grosor, relleno)
        self.p1 = p1
        self.p2 = p2
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el rectángulo en el canvas"""
        self._canvas_id = canvas.create_rectangle(
            self.p1.x, self.p1.y,
            self.p2.x, self.p2.y,
            outline=self.color,
            width=self.grosor,
            fill=self.relleno
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box del rectángulo"""
        x1 = min(self.p1.x, self.p2.x)
        y1 = min(self.p1.y, self.p2.y)
        x2 = max(self.p1.x, self.p2.x)
        y2 = max(self.p1.y, self.p2.y)
        return (x1, y1, x2, y2)
    
    def mover(self, dx: float, dy: float):
        """Mueve el rectángulo una distancia dx, dy"""
        self.p1.mover(dx, dy)
        self.p2.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza el rectángulo en el canvas"""
        if self._canvas_id is not None:
            bbox = self.bbox()
            canvas.coords(self._canvas_id, *bbox)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=self._original_color)

    def to_dict(self):
        return {
            "type": "Rectangulo",
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "color": self.color,
            "grosor": self.grosor,
            "relleno": getattr(self, 'relleno', '')
        }

    def dibujar_en_pil(self, draw):
        """Dibuja el rectángulo en una imagen PIL"""
        bbox = [
            min(self.p1.x, self.p2.x), min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x), max(self.p1.y, self.p2.y)
        ]
        draw.rectangle(bbox, outline=self.color, width=int(self.grosor))

    def __repr__(self) -> str:
        return f"Rectangulo({self.p1}, {self.p2}, color={self.color})"