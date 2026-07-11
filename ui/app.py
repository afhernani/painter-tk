from tkinter import *
from ..geometry.punto import Punto
from ..geometry.linea import Linea
from ..geometry.circulo import Circulo
from ..geometry.polyline import Polyline

class App:
    def __init__(self, master):
        self.master = master
        self.canvas = Canvas(master, width=800, height=600, bg='white')
        self.canvas.pack()
        
        # Modelo: lista de formas
        self.formas = []
        self.forma_seleccionada = None
        
        # Estado de dibujo
        self.modo = 'line'  # 'line', 'circle', 'pen', 'select'
        self.punto_inicio = None
        self.puntos_trazo = []  # Para lápiz
        
        # Binds
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_motion)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_press(self, e):
        if self.modo == 'select':
            self._seleccionar(e.x, e.y)
        elif self.modo == 'line':
            self.punto_inicio = Punto(e.x, e.y)
        elif self.modo == 'circle':
            self.punto_inicio = Punto(e.x, e.y)
        elif self.modo == 'pen':
            self.puntos_trazo = [Punto(e.x, e.y)]
    
    def _on_release(self, e):
        if self.modo == 'line' and self.punto_inicio:
            linea = Linea(self.punto_inicio, Punto(e.x, e.y))
            linea.dibujar_en(self.canvas)
            self.formas.append(linea)
        
        elif self.modo == 'circle' and self.punto_inicio:
            radio = self.punto_inicio.distancia(Punto(e.x, e.y))
            circulo = Circulo(self.punto_inicio, radio)
            circulo.dibujar_en(self.canvas)
            self.formas.append(circulo)
        
        elif self.modo == 'pen' and len(self.puntos_trazo) > 1:
            poly = Polyline(self.puntos_trazo)
            poly.dibujar_en(self.canvas)
            self.formas.append(poly)