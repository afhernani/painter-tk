# -*- coding: utf-8 -*-
"""
Clase Linea para representar líneas rectas
"""
from .punto import Punto
from .shape import Shape
import tkinter as tk
from typing import Tuple


class Linea(Shape):
    """Representa una línea recta entre dos puntos"""
    
    def __init__(self, p1: Punto, p2: Punto, color: str = 'black', 
                 grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa una línea entre dos puntos
        
        Args:
            p1: Punto inicial
            p2: Punto final
            color: Color de la línea
            grosor: Grosor de la línea
            relleno: No aplicable para líneas
        """
        super().__init__(color, grosor, relleno)
        self.p1 = p1
        self.p2 = p2
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja la línea en el canvas"""
        self._canvas_id = canvas.create_line(
            self.p1.x, self.p1.y,
            self.p2.x, self.p2.y,
            fill=self.color,
            width=self.grosor,
            capstyle=tk.ROUND,
            smooth=False
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box de la línea"""
        x1 = min(self.p1.x, self.p2.x)
        y1 = min(self.p1.y, self.p2.y)
        x2 = max(self.p1.x, self.p2.x)
        y2 = max(self.p1.y, self.p2.y)
        return (x1, y1, x2, y2)
    
    def mover(self, dx: float, dy: float):
        """Mueve la línea una distancia dx, dy"""
        self.p1.mover(dx, dy)
        self.p2.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza la línea en el canvas"""
        if self._canvas_id is not None:
            canvas.coords(
                self._canvas_id,
                self.p1.x, self.p1.y,
                self.p2.x, self.p2.y
            )
    
    def __repr__(self) -> str:
        return f"Linea({self.p1}, {self.p2}, color={self.color})"