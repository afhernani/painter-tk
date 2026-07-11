# -*- coding: utf-8 -*-
"""
Clase base abstracta para todas las formas geométricas
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import tkinter as tk


class Shape(ABC):
    """Clase base abstracta para formas geométricas"""
    
    def __init__(self, color: str = 'black', grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa una forma con propiedades visuales
        
        Args:
            color: Color del contorno
            grosor: Grosor del contorno
            relleno: Color de relleno (vacío por defecto)
        """
        self.color = color
        self.grosor = grosor
        self.relleno = relleno
        self._canvas_id: Optional[int] = None
    
    @property
    def canvas_id(self) -> Optional[int]:
        """ID del objeto en el canvas de Tkinter"""
        return self._canvas_id
    
    @canvas_id.setter
    def canvas_id(self, value: int):
        self._canvas_id = value
    
    @abstractmethod
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """
        Dibuja la forma en un canvas de Tkinter
        
        Args:
            canvas: Canvas de Tkinter donde dibujar
            
        Returns:
            ID del objeto creado en el canvas
        """
        pass
    
    @abstractmethod
    def bbox(self) -> Tuple[float, float, float, float]:
        """
        Calcula el bounding box de la forma
        
        Returns:
            Tupla (x1, y1, x2, y2) del bounding box
        """
        pass
    
    @abstractmethod
    def mover(self, dx: float, dy: float):
        """
        Mueve la forma una distancia dx, dy
        
        Args:
            dx: Desplazamiento en x
            dy: Desplazamiento en y
        """
        pass
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """
        Actualiza la posición de la forma en el canvas
        
        Args:
            canvas: Canvas de Tkinter
        """
        if self._canvas_id is not None:
            bbox = self.bbox()
            canvas.coords(self._canvas_id, *bbox)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(color={self.color}, grosor={self.grosor})"