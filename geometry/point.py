# -*- coding: utf-8 -*-

class Punto:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
    
    def distancia(self, otro: 'Punto') -> float:
        return ((self.x - otro.x)**2 + (self.y - otro.y)**2) ** 0.5
    
    # def distancia(self, dx:float, dy:float):
    #     return( (self.x - dx)**2 + (self.y - dy)**2 )**0.5
    
    def mover(self, dx: float, dy:float):
        """Desplazar el punto una distancia (dx, dy)"""
        self.x += dx
        self.y += dy
    
    # def mover(self, otro: 'Punto'):
    #     self.x = otro.x
    #     self.y = otro.y
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"])
    
    def __repr__(self):
        return f"Punto({self.x}, {self.y})"