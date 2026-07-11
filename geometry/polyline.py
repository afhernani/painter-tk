# -*- coding: utf-8 -*-
"""
Clase Polyline para representar polilíneas (trazos libres)
"""
from .punto import Punto
from .shape import Shape
import tkinter as tk
from typing import List, Tuple


class Polyline(Shape):
    """Representa una polilínea (trazo libre) definida por múltiples puntos"""
    
    def __init__(self, puntos: List[Punto], color: str = 'black',
                 grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa una polilínea
        
        Args:
            puntos: Lista de puntos que definen la polilínea
            color: Color de la línea
            grosor: Grosor de la línea
            relleno: No aplicable para polilíneas
        """
        super().__init__(color, grosor, relleno)
        self.puntos = [p.copiar() for p in puntos]
    
    def agregar_punto(self, punto: Punto):
        """
        Agrega un punto a la polilínea
        
        Args:
            punto: Punto a agregar
        """
        self.puntos.append(punto.copiar())
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja la polilínea en el canvas"""
        if len(self.puntos) < 2:
            return None
        
        coords = []
        for punto in self.puntos:
            coords.extend([punto.x, punto.y])
        
        self._canvas_id = canvas.create_line(
            *coords,
            fill=self.color,
            width=self.grosor,
            capstyle=tk.ROUND,
            smooth=False
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box de la polilínea"""
        if not self.puntos:
            return (0, 0, 0, 0)
        
        xs = [p.x for p in self.puntos]
        ys = [p.y for p in self.puntos]
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def mover(self, dx: float, dy: float):
        """Mueve la polilínea una distancia dx, dy"""
        for punto in self.puntos:
            punto.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza la polilínea en el canvas"""
        if self._canvas_id is not None and len(self.puntos) >= 2:
            coords = []
            for punto in self.puntos:
                coords.extend([punto.x, punto.y])
            canvas.coords(self._canvas_id, *coords)
    
    def __repr__(self) -> str:
        return f"Polyline({len(self.puntos)} puntos, color={self.color})"