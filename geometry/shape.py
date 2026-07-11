from abc import ABC, abstractmethod

class Shape(ABC):
    """Clase base abstracta para todas las formas geométricas"""
    
    def __init__(self, color: str = 'black', grosor: float = 1.0):
        self.color = color
        self.grosor = grosor
        self._canvas_id = None  # ID en el canvas de Tkinter (se asigna al dibujar)
    
    @abstractmethod
    def dibujar_en(self, canvas):
        """Dibuja la forma en un canvas de Tkinter"""
        pass
    
    @abstractmethod
    def bbox(self):
        """Retorna el bounding box (x1, y1, x2, y2)"""
        pass
    
    def mover(self, dx: float, dy: float):
        """Mueve la forma una distancia dx, dy"""
        pass