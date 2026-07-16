# -*- coding: utf-8 -*-
"""
Clase Arco para representar arcos
"""
from .point import Punto
from .shape import Shape
import tkinter as tk
from typing import Tuple


class Arco(Shape):
    """Representa un arco definido por bounding box y ángulos"""
    
    def __init__(self, p1: Punto, p2: Punto, inicio: float = 0.0,
                 extension: float = 90.0, color: str = 'black',
                 grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa un arco
        
        Args:
            p1: Esquina superior izquierda del bounding box
            p2: Esquina inferior derecha del bounding box
            inicio: Ángulo de inicio en grados
            extension: Ángulo de extensión en grados
            color: Color del contorno
            grosor: Grosor del contorno
            relleno: Color de relleno
        """
        super().__init__(color, grosor, relleno)
        self.p1 = p1
        self.p2 = p2
        self.inicio = float(inicio)
        self.extension = float(extension)
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el arco en el canvas"""
        self._canvas_id = canvas.create_arc(
            self.p1.x, self.p1.y,
            self.p2.x, self.p2.y,
            start=self.inicio,
            extent=self.extension,
            outline=self.color,
            width=self.grosor,
            fill=self.relleno,
            style=tk.ARC
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box del arco"""
        x1 = min(self.p1.x, self.p2.x)
        y1 = min(self.p1.y, self.p2.y)
        x2 = max(self.p1.x, self.p2.x)
        y2 = max(self.p1.y, self.p2.y)
        return (x1, y1, x2, y2)
    
    def mover(self, dx: float, dy: float):
        """Mueve el arco una distancia dx, dy"""
        self.p1.mover(dx, dy)
        self.p2.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza el arco en el canvas"""
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
            "type": "Arco",
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "inicio": getattr(self, 'inicio', 0),
            "extension": getattr(self, 'extension', 90),
            "color": self.color,
            "grosor": self.grosor
        }

    def dibujar_en_pil(self, draw):
        """Dibuja el arco en una imagen PIL"""
        # PIL usa start y extent en grados
        bbox = [
            min(self.p1.x, self.p2.x), min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x), max(self.p1.y, self.p2.y)
        ]
        draw.arc(
            bbox,
            start=self.inicio,
            end=self.inicio + self.extension,
            fill=self.color,
            width=int(self.grosor)
        )

    def __repr__(self) -> str:
        return f"Arco({self.p1}, {self.p2}, inicio={self.inicio}, extension={self.extension})"