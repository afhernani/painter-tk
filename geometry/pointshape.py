# -*- coding: utf-8 -*-
from .shape import Shape
from .point import Punto
import tkinter as tk


class PointShape(Shape):
    """Representa un punto dibujable en el canvas (compuesto por un Punto)"""
    
    def __init__(self, punto: Punto, radio: float = 3.0, **kwargs):
        super().__init__(**kwargs)
        self.punto = punto
        self.radio = radio  # Radio del círculo que representa el punto visualmente

    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el punto como un círculo pequeño"""
        x1 = self.punto.x - self.radio
        y1 = self.punto.y - self.radio
        x2 = self.punto.x + self.radio
        y2 = self.punto.y + self.radio
        self._canvas_id = canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color,
            width=self.grosor,
            fill=self.color  # Rellenado con el mismo color
        )
        return self._canvas_id

    def bbox(self):
        """Bounding box del punto"""
        return (
            self.punto.x - self.radio, self.punto.y - self.radio,
            self.punto.x + self.radio, self.punto.y + self.radio
        )

    def mover(self, dx: float, dy: float):
        """Mueve el punto"""
        self.punto.mover(dx, dy)

    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza la posición del punto en el canvas"""
        if self._canvas_id is not None:
            bbox = self.bbox()
            canvas.coords(self._canvas_id, *bbox)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=self._original_color)

    def to_dict(self):
        return {
            "type": "Point",
            "punto": self.punto.to_dict(),
            "radio": self.radio,
            "color": self.color,
            "grosor": self.grosor
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PointShape':
        """Deserializa un punto desde un diccionario JSON"""
        punto_data = data.get("punto", {"x": 0, "y": 0})
        if isinstance(punto_data, dict):
            punto = Punto.from_dict(punto_data)
        else:
            punto = punto_data
        
        return cls(
            punto=punto,
            radio=data.get("radio", 3.0),
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0)
        )

    def dibujar_en_pil(self, draw):
        """Dibuja el punto en una imagen PIL"""
        r = self.radio
        bbox = [
            self.punto.x - r, self.punto.y - r,
            self.punto.x + r, self.punto.y + r
        ]
        draw.ellipse(bbox, fill=self.color)

    def __repr__(self):
        return f"PointShape({self.punto}, radio={self.radio}, color={self.color})"