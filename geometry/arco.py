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
        x1, y1 = canvas.world_to_screen(self.centro.x - self.radio, self.centro.y - self.radio)
        x2, y2 = canvas.world_to_screen(self.centro.x + self.radio, self.centro.y + self.radio)
        self._canvas_id = canvas.create_arc(
            x1, y1, x2, y2,
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
    
    def dibujar_en_pil(self, draw, transform=None, scale=1.0):
        """Dibuja el arco en una imagen PIL"""
        if transform is None:
            transform = lambda x, y: (x, y)

        # Construir puntos muestreados desde angulo_inicio hasta angulo_inicio+extension
        if self.extension == 0:
            return

        start_deg = float(self.angulo_inicio)
        end_deg = float(self.angulo_inicio + self.extension)

        # Normalizar número de pasos para suavidad (aprox 1° por segmento, mínimo 4)
        total_deg = abs(end_deg - start_deg)
        steps = max(4, int(total_deg / 1.0))

        # Generar ángulos en radianes y calcular puntos en coordenadas del mundo
        puntos = []
        for i in range(steps + 1):
            t = i / steps
            ang_deg = start_deg + t * (end_deg - start_deg)
            ang = math.radians(ang_deg)
            xw = self.centro.x + self.radio * math.cos(ang)
            # Usar convención de Y coherente con create_arc (invertida)
            yw = self.centro.y - self.radio * math.sin(ang)
            puntos.append(transform(xw, yw))

        stroke = max(1, int(self.grosor * scale))
        # Dibujar como polilínea para evitar dependencias de convención de ángulos
        try:
            draw.line(puntos, fill=self.color, width=stroke)
        except Exception:
            # Fallback: si draw.line falla, intentar usar arc sobre bbox aproximado
            x1w, y1w = self.centro.x - self.radio, self.centro.y - self.radio
            x2w, y2w = self.centro.x + self.radio, self.centro.y + self.radio
            x1, y1 = transform(x1w, y1w)
            x2, y2 = transform(x2w, y2w)
            draw.arc([x1, y1, x2, y2], start=start_deg, end=end_deg, fill=self.color, width=stroke)
    
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

    def actualizar_punto_inicio(self, nuevo_punto: Punto):
        """Recalcula radio y ángulo de inicio, manteniendo el ángulo final absoluto"""
        # Calcular ángulo final absoluto ANTES de cambiar nada
        angulo_final_abs = self.angulo_inicio + self.extension
        
        # Nuevo radio (distancia al centro)
        self.radio = self.centro.distancia(nuevo_punto)
        
        # Nuevo ángulo de inicio
        dx = nuevo_punto.x - self.centro.x
        dy = -(nuevo_punto.y - self.centro.y)
        self.angulo_inicio = math.degrees(math.atan2(dy, dx))
        
        # Recalcular extensión basándose en el ángulo final absoluto
        self.extension = angulo_final_abs - self.angulo_inicio
        
        # La extensión se mantiene (el punto final no cambia)

    def actualizar_punto_final(self, nuevo_punto: Punto):
        """Recalcula radio y ángulo final, manteniendo el ángulo inicial absoluto"""
        # El ángulo inicial se mantiene (no lo tocamos)
        
        # Nuevo radio (distancia al centro)
        self.radio = self.centro.distancia(nuevo_punto)
        
        # Nuevo ángulo final
        dx = nuevo_punto.x - self.centro.x
        dy = -(nuevo_punto.y - self.centro.y)
        angulo_final = math.degrees(math.atan2(dy, dx))
        
        # Recalcular extensión
        self.extension = angulo_final - self.angulo_inicio


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

    def actualizar_en_canvas(self, canvas):
        """Actualiza el arco existente en el canvas (no crea uno nuevo)"""
        if self._canvas_id is None:
            return
        
        # Calcular nuevo bbox en coordenadas de pantalla
        x1, y1 = canvas.world_to_screen(self.centro.x - self.radio, self.centro.y - self.radio)
        x2, y2 = canvas.world_to_screen(self.centro.x + self.radio, self.centro.y + self.radio)
        
        # Actualizar coordenadas del arco
        canvas.coords(self._canvas_id, x1, y1, x2, y2)
        
        # Actualizar parámetros del arco (ángulos, color, grosor)
        canvas.itemconfig(self._canvas_id,
                        start=self.angulo_inicio,
                        extent=self.extension,
                        outline=self.color,
                        width=self.grosor)

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