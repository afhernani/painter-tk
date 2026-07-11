# -*- coding: utf-8 -*-
"""
Clase Punto para representar coordenadas 2D
"""
import math


class Punto:
    """Representa un punto en el plano 2D"""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """
        Inicializa un punto con coordenadas x, y
        
        Args:
            x: Coordenada x (default: 0.0)
            y: Coordenada y (default: 0.0)
        """
        self.x = float(x)
        self.y = float(y)
    
    def distancia_a(self, otro: 'Punto') -> float:
        """
        Calcula la distancia euclidiana a otro punto
        
        Args:
            otro: Otro punto
            
        Returns:
            Distancia entre los dos puntos
        """
        return math.sqrt((self.x - otro.x)**2 + (self.y - otro.y)**2)
    
    def mover(self, dx: float, dy: float):
        """
        Mueve el punto una distancia dx, dy
        
        Args:
            dx: Desplazamiento en x
            dy: Desplazamiento en y
        """
        self.x += dx
        self.y += dy
    
    def copiar(self) -> 'Punto':
        """Crea una copia de este punto"""
        return Punto(self.x, self.y)
    
    def __repr__(self) -> str:
        return f"Punto({self.x:.2f}, {self.y:.2f})"
    
    def __eq__(self, otro) -> bool:
        if not isinstance(otro, Punto):
            return False
        return abs(self.x - otro.x) < 1e-10 and abs(self.y - otro.y) < 1e-10
    
    def __hash__(self) -> int:
        return hash((round(self.x, 10), round(self.y, 10)))