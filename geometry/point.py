class Punto:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def distancia(self, otro: 'Punto') -> float:
        return ((self.x - otro.x)**2 + (self.y - otro.y)**2) ** 0.5
    
    def __repr__(self):
        return f"Punto({self.x}, {self.y})"