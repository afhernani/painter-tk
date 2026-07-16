# -*- coding: utf-8 -*-
import math
import tkinter as tk
from typing import Optional
from geometry.shape import Shape
from geometry.point import Punto
import logging

log = logging.getLogger('Geometry.Arc')

class Arco(Shape):
    """Arco definido por centro, radio, ángulo inicial y extensión"""
    
    def __init__(self, centro: Punto, radio: float, 
                 angulo_inicio: float, extension: float,
                 color: str = 'black', grosor: float = 1.0, 
                 relleno: str = '', **kwargs):
        super().__init__(color=color, grosor=grosor, relleno=relleno, **kwargs)
        self.centro = centro
        self.radio = float(radio)
        self.angulo_inicio = float(angulo_inicio)  # en grados
        self.extension = float(extension)          # en grados
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el arco en el canvas"""
        bbox = [
            self.centro.x - self.radio, self.centro.y - self.radio,
            self.centro.x + self.radio, self.centro.y + self.radio
        ]
        self._canvas_id = canvas.create_arc(
            *bbox,
            start=self.angulo_inicio,
            extent=self.extension,
            style=tk.ARC,
            outline=self.color,
            width=self.grosor
        )
        return self._canvas_id
    
    def bbox(self):
        """Devuelve el bounding box del arco (x1, y1, x2, y2)"""
        return (
            self.centro.x - self.radio, 
            self.centro.y - self.radio,
            self.centro.x + self.radio, 
            self.centro.y + self.radio
        )
    
    def resaltar(self, canvas, color='red'):
        """Resalta el arco cambiando el color del contorno"""
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=color, width=self.grosor + 1)
    
    def restaurar(self, canvas):
        """Restaura el color original del arco"""
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=self.color, width=self.grosor)
    
    def dibujar_en_pil(self, draw):
        """Dibuja el arco en una imagen PIL"""
        bbox = [
            self.centro.x - self.radio, self.centro.y - self.radio,
            self.centro.x + self.radio, self.centro.y + self.radio
        ]
        draw.arc(
            bbox,
            start=self.angulo_inicio,
            end=self.angulo_inicio + self.extension,
            fill=self.color,
            width=int(self.grosor)
        )
    
    def mover(self, dx: float, dy: float):
        """Mueve el arco"""
        self.centro = Punto(self.centro.x + dx, self.centro.y + dy)
    
    def to_dict(self) -> dict:
        return {
            "type": "Arco",
            "centro": self.centro.to_dict(),
            "radio": self.radio,
            "angulo_inicio": self.angulo_inicio,
            "extension": self.extension,
            "color": self.color,
            "grosor": self.grosor,
            "relleno": self.relleno
        }
    
    def obtener_punto_centro(self) -> Punto:
        """Devuelve el centro del arco"""
        return self.centro

    def obtener_punto_inicio(self) -> Punto:
        """Devuelve el punto en el borde donde empieza el arco"""
        # Convertir grados a radianes
        rad = math.radians(self.angulo_inicio)
        # Tkinter usa eje Y invertido, así que usamos -sin para compensar
        x = self.centro.x + self.radio * math.cos(rad)
        y = self.centro.y - self.radio * math.sin(rad)
        return Punto(x, y)

    def obtener_punto_final(self) -> Punto:
        """Devuelve el punto en el borde donde termina el arco"""
        angulo_fin = self.angulo_inicio + self.extension
        rad = math.radians(angulo_fin)
        x = self.centro.x + self.radio * math.cos(rad)
        y = self.centro.y - self.radio * math.sin(rad)
        return Punto(x, y)

    def actualizar_angulo_inicio_desde_punto(self, nuevo_punto: Punto):
        """Recalcula el ángulo de inicio basado en la posición del punto"""
        dx = nuevo_punto.x - self.centro.x
        dy = -(nuevo_punto.y - self.centro.y)  # Negar Y por eje invertido
        self.angulo_inicio = math.degrees(math.atan2(dy, dx))

    def actualizar_extension_desde_punto(self, nuevo_punto: Punto):
        """Recalcula la extensión basada en la posición del punto final"""
        dx = nuevo_punto.x - self.centro.x
        dy = -(nuevo_punto.y - self.centro.y)
        angulo_final = math.degrees(math.atan2(dy, dx))
        self.extension = angulo_final - self.angulo_inicio


    @classmethod
    def from_dict(cls, data: dict) -> 'Arco':
        centro = Punto.from_dict(data["centro"])
        return cls(
            centro=centro,
            radio=data["radio"],
            angulo_inicio=data["angulo_inicio"],
            extension=data["extension"],
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0),
            relleno=data.get("relleno", "")
        )
    
    def __repr__(self):
        return f"Arco(centro={self.centro}, radio={self.radio}, inicio={self.angulo_inicio}°, ext={self.extension}°)"