# -*- coding: utf-8 -*-
import math
import tkinter as tk
from .shape import Shape
from .point import Punto

class Circulo(Shape):
    def __init__(self, centro: Punto, radio: float, **kwargs):
        super().__init__(**kwargs)
        self.centro = centro
        self.radio = float(radio)
        self._canvas_ids = []
        self._tag_unico = f'circle_{id(self)}'

    def _generar_coords(self) -> list:
        coords = []
        paso = 0.05
        num_puntos = int(2 * math.pi / paso)
        for i in range(num_puntos):
            theta = i * paso
            x = self.centro.x + self.radio * math.cos(theta)
            y = self.centro.y + self.radio * math.sin(theta)
            coords.extend([x, y])
        if coords:
            coords.extend([coords[0], coords[1]])
        return coords

    def dibujar_en(self, canvas: tk.Canvas) -> int:
        coords = self._generar_coords()
        self._canvas_id = canvas.create_line(
            *coords,
            fill=self.color,
            width=self.grosor,
            smooth=False,
            tags=(self._tag_unico,)
        )
        self._canvas_ids = [self._canvas_id]
        return self._canvas_id

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
            canvas.coords(self._canvas_id, *coords)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=self.color, width=self.grosor)

    def obtener_punto_perimetro(self) -> Punto:
        """Devuelve un punto en el perímetro (a la derecha del centro)"""
        return Punto(self.centro.x + self.radio, self.centro.y)

    def actualizar_radio_desde_punto(self, nuevo_punto: Punto):
        """Recalcula el radio basado en la distancia del nuevo punto al centro"""
        self.radio = self.centro.distancia(nuevo_punto)
    
    def to_dict(self):
        return {
            "type": "Circulo",
            "centro": self.centro.to_dict(),
            "radio": self.radio,
            "color": self.color,
            "grosor": self.grosor,
            "relleno": getattr(self, 'relleno', '')
        }

    def dibujar_en_pil(self, draw):
        """Dibuja el círculo en una imagen PIL"""
        # PIL dibuja óvalos dentro de un bounding box
        bbox = [
            self.centro.x - self.radio, self.centro.y - self.radio,
            self.centro.x + self.radio, self.centro.y + self.radio
        ]
        # Si hay relleno, lo dibujamos. Si no, solo el borde.
        fill_color = self.relleno if self.relleno else None
        draw.ellipse(bbox, outline=self.color, fill=fill_color, width=int(self.grosor))

    def __repr__(self):
        return f"Circulo(centro={self.centro}, radio={self.radio})"