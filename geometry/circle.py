# -*- coding: utf-8 -*-
import math
import tkinter as tk
from .shape import Shape, _screen_coords
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
        # Dibujar usando un óvalo (mejor soporte de relleno y rendimiento)
        x1w = self.centro.x - self.radio
        y1w = self.centro.y - self.radio
        x2w = self.centro.x + self.radio
        y2w = self.centro.y + self.radio
        x1, y1 = canvas.world_to_screen(x1w, y1w)
        x2, y2 = canvas.world_to_screen(x2w, y2w)
        fill_color = self.relleno if getattr(self, 'relleno', '') else ''
        self._canvas_id = canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color,
            fill=fill_color,
            width=self.grosor,
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
            x1w = self.centro.x - self.radio
            y1w = self.centro.y - self.radio
            x2w = self.centro.x + self.radio
            y2w = self.centro.y + self.radio
            x1, y1 = canvas.world_to_screen(x1w, y1w)
            x2, y2 = canvas.world_to_screen(x2w, y2w)
            canvas.coords(self._canvas_id, x1, y1, x2, y2)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            # Resaltar cambiando el contorno (outline) para mantener el relleno
            canvas.itemconfig(self._canvas_id, outline=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            fill_color = self.relleno if getattr(self, 'relleno', '') else ''
            canvas.itemconfig(self._canvas_id, outline=self.color, fill=fill_color, width=self.grosor)

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

    @classmethod
    def from_dict(cls, data: dict) -> 'Circulo':
        """Deserializa un círculo desde un diccionario JSON"""
        centro = Punto.from_dict(data["centro"])
        return cls(
            centro=centro,
            radio=data["radio"],
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0),
            relleno=data.get("relleno", "")
        )

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