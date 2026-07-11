# -*- coding: utf-8 -*-
"""
Clase Circulo para representar círculos
"""
from .punto import Punto
from .shape import Shape
import tkinter as tk
from typing import Tuple


class Circulo(Shape):
    """Representa un círculo definido por centro y radio"""
    
    def __init__(self, centro: Punto, radio: float, color: str = 'black',
                 grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa un círculo
        
        Args:
            centro: Punto central del círculo
            radio: Radio del círculo
            color: Color del contorno
            grosor: Grosor del contorno
            relleno: Color de relleno
        """
        super().__init__(color, grosor, relleno)
        self.centro = centro
        self.radio = float(radio)
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el círculo en el canvas"""
        x1 = self.centro.x - self.radio
        y1 = self.centro.y - self.radio
        x2 = self.centro.x + self.radio
        y2 = self.centro.y + self.radio
        
        self._canvas_id = canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color,
            width=self.grosor,
            fill=self.relleno
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box del círculo"""
        x1 = self.centro.x - self.radio
        y1 = self.centro.y - self.radio
        x2 = self.centro.x + self.radio
        y2 = self.centro.y + self.radio
        return (x1, y1, x2, y2)
    
    def mover(self, dx: float, dy: float):
        """Mueve el círculo una distancia dx, dy"""
        self.centro.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza el círculo en el canvas"""
        if self._canvas_id is not None:
            bbox = self.bbox()
            canvas.coords(self._canvas_id, *bbox)
    
    def __repr__(self) -> str:
        return f"Circulo(centro={self.centro}, radio={self.radio}, color={self.color})"