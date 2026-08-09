# -*- coding: utf-8 -*-
import math
import tkinter as tk
from .shape import Shape, _screen_coords
from .point import Punto

class Poligono(Shape):
    def __init__(self, centro: Punto, radio: float, lados: int = 5, rotacion: float = -math.pi / 2, **kwargs):
        super().__init__(**kwargs)
        self.centro = centro
        self.radio = float(radio)
        self.lados = max(3, int(lados))
        self.rotacion = rotacion  # Rotación inicial (empezar desde arriba)

    def _generar_coords(self) -> list:
        """Genera las coordenadas de los vértices usando rotación"""
        coords = []
        angulo_paso = 2 * math.pi / self.lados
        
        for i in range(self.lados):
            theta = i * angulo_paso + self.rotacion  # ✅ Usar self.rotacion
            x = self.centro.x + self.radio * math.cos(theta)
            y = self.centro.y + self.radio * math.sin(theta)
            coords.extend([x, y])
        return coords

    def obtener_vertices(self) -> list:
        """Devuelve la lista de puntos de los vértices actuales"""
        vertices = []
        angulo_paso = 2 * math.pi / self.lados
        
        for i in range(self.lados):
            theta = i * angulo_paso + self.rotacion  # Usar self.rotacion
            x = self.centro.x + self.radio * math.cos(theta)
            y = self.centro.y + self.radio * math.sin(theta)
            vertices.append(Punto(x, y))
        return vertices

    def actualizar_desde_vertice(self, indice_vertice: int, nuevo_punto: Punto):
        """
        Recalcula radio y rotación para que el vértice especificado 
        esté exactamente en la posición del nuevo punto
        """
        # Calcular nueva distancia al centro (radio)
        dx = nuevo_punto.x - self.centro.x
        dy = nuevo_punto.y - self.centro.y
        self.radio = math.hypot(dx, dy)
        
        # Calcular nuevo ángulo para este vértice
        angulo_paso = 2 * math.pi / self.lados
        angulo_objetivo = math.atan2(dy, dx)
        
        # La rotación del polígono es el ángulo del vértice menos su posición angular relativa
        self.rotacion = angulo_objetivo - indice_vertice * angulo_paso

    def dibujar_en(self, canvas: tk.Canvas) -> int:
        coords = self._generar_coords()
        coords = _screen_coords(canvas, coords)
        self._canvas_id = canvas.create_polygon(
            *coords, outline=self.color, width=self.grosor, fill=self.relleno
        )

    def bbox(self):
        return (
            self.centro.x - self.radio, self.centro.y - self.radio,
            self.centro.x + self.radio, self.centro.y + self.radio
        )

    def mover(self, dx: float, dy: float):
        self.centro.mover(dx, dy)

    def actualizar_en_canvas(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            coords = self._generar_coords()
            coords = _screen_coords(canvas, coords)
            canvas.coords(self._canvas_id, *coords)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=self.color, width=self.grosor)

    def to_dict(self) -> dict:
        return {
            "type": "Poligono",
            "centro": self.centro.to_dict(),
            "radio": self.radio,
            "lados": self.lados,
            "color": self.color,
            "grosor": self.grosor,
            "relleno": getattr(self, 'relleno', '')
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Poligono':
        """Deserializa un polígono desde un diccionario JSON"""
        centro_data = data.get("centro", {"x": 0, "y": 0})
        if isinstance(centro_data, dict):
            centro = Punto.from_dict(centro_data)
        else:
            centro = centro_data
        
        return cls(
            centro=centro,
            radio=data.get("radio", 10.0),
            lados=data.get("lados", 6),
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0),
            relleno=data.get("relleno", "")
        )

    def dibujar_en_pil(self, draw):
        """Dibuja el polígono en una imagen PIL"""
        puntos = []
        for i in range(self.lados):
            angulo = self.rotacion + (2 * math.pi * i / self.lados)
            x = self.centro.x + self.radio * math.cos(angulo)
            y = self.centro.y + self.radio * math.sin(angulo)
            puntos.append((x, y))
        
        draw.polygon(puntos, outline=self.color, width=int(self.grosor))

    def __repr__(self):
        return f"Poligono(centro={self.centro}, radio={self.radio}, lados={self.lados})"