# -*- coding: utf-8 -*-
"""
Clase Elipse para representar elipses
"""
from .point import Punto
from .shape import Shape
import tkinter as tk
from typing import Tuple
import logging

log = logging.getLogger('Geometry.elipse')

class Elipse(Shape):
    """Representa una elipse definida por centro y radios"""
    
    def __init__(self, centro: Punto, radio_x: float, radio_y: float,
                 color: str = 'black', grosor: float = 1.0, relleno: str = ''):
        """
        Inicializa una elipse
        
        Args:
            centro: Punto central de la elipse
            radio_x: Radio en el eje x
            radio_y: Radio en el eje y
            color: Color del contorno
            grosor: Grosor del contorno
            relleno: Color de relleno
        """
        super().__init__(color, grosor, relleno)
        self.centro = centro
        self.radio_x = float(radio_x)
        self.radio_y = float(radio_y)
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja la elipse en el canvas"""
        x1 = self.centro.x - self.radio_x
        y1 = self.centro.y - self.radio_y
        x2 = self.centro.x + self.radio_x
        y2 = self.centro.y + self.radio_y
        
        self._canvas_id = canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color,
            width=self.grosor,
            fill=self.relleno
        )
        return self._canvas_id
    
    def bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box de la elipse"""
        x1 = self.centro.x - self.radio_x
        y1 = self.centro.y - self.radio_y
        x2 = self.centro.x + self.radio_x
        y2 = self.centro.y + self.radio_y
        return (x1, y1, x2, y2)
    
    def mover(self, dx: float, dy: float):
        """Mueve la elipse una distancia dx, dy"""
        self.centro.mover(dx, dy)
    
    def actualizar_en_canvas(self, canvas: tk.Canvas):
        """Actualiza la elipse en el canvas"""
        if self._canvas_id is not None:
            bbox = self.bbox()
            canvas.coords(self._canvas_id, *bbox)

    def resaltar(self, canvas: tk.Canvas, color: str = 'red'):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=color)

    def restaurar(self, canvas: tk.Canvas):
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, outline=self.color, width=self.grosor)

    def _finalizar_elipse(self, x, y):
        """Borra la preview y crea la Elipse definitiva"""
        if self.elipse_preview_id is not None:
            self.delete(self.elipse_preview_id)
            self.elipse_preview_id = None
        
        radio_x = abs(x - self.elipse_centro.x)
        radio_y = abs(y - self.elipse_centro.y)
        
        if radio_x < 2 or radio_y < 2:
            self.elipse_centro = None
            return
        
        width = self.grosor 
        color = self.color
        relleno = self.grosor
        
        # ✅ CORREGIDO: usar radio_x y radio_y como argumentos nombrados
        shape = Elipse(
            centro=self.elipse_centro,
            radio_x=radio_x,
            radio_y=radio_y,
            color=color,
            grosor=width,
            relleno=relleno
        )
        shape._tag = 'Elipse'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        log.info(f"Elipse creada: {shape}")
        self.elipse_centro = None
        self._set_status("Elipse creada")
        self._save_state()

    def to_dict(self) -> dict:
        return {
            "type": "Elipse",
            "centro": self.centro.to_dict(),
            "radio_x": self.radio_x,
            "radio_y": self.radio_y,
            "color": self.color,
            "grosor": self.grosor,
            "relleno": getattr(self, 'relleno', '')
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Elipse':
        """Deserializa una elipse desde un diccionario JSON"""
        centro_data = data.get("centro", {"x": 0, "y": 0})
        if isinstance(centro_data, dict):
            centro = Punto.from_dict(centro_data)
        else:
            centro = centro_data
        
        return cls(
            centro=centro,
            radio_x=data.get("radio_x", 10.0),
            radio_y=data.get("radio_y", 10.0),
            color=data.get("color", "black"),
            grosor=data.get("grosor", 1.0),
            relleno=data.get("relleno", "")
        )

    def obtener_punto_eje_x(self) -> Punto:
        """Devuelve el punto en el borde derecho (eje X máximo)"""
        return Punto(self.centro.x + self.radio_x, self.centro.y)

    def obtener_punto_eje_y(self) -> Punto:
        """Devuelve el punto en el borde inferior (eje Y máximo)"""
        return Punto(self.centro.x, self.centro.y + self.radio_y)

    def actualizar_radio_x_desde_punto(self, nuevo_punto: Punto):
        """Actualiza el radio horizontal basado en la distancia al centro"""
        self.radio_x = abs(nuevo_punto.x - self.centro.x)

    def actualizar_radio_y_desde_punto(self, nuevo_punto: Punto):
        """Actualiza el radio vertical basado en la distancia al centro"""
        self.radio_y = abs(nuevo_punto.y - self.centro.y)

    def dibujar_en_pil(self, draw):
        """Dibuja la elipse en una imagen PIL"""
        bbox = [
            self.centro.x - self.radio_x, self.centro.y - self.radio_y,
            self.centro.x + self.radio_x, self.centro.y + self.radio_y
        ]
        draw.ellipse(bbox, outline=self.color, width=int(self.grosor))

    def __repr__(self) -> str:
        return f"Elipse(centro={self.centro}, rx={self.radio_x}, ry={self.radio_y}, color={self.color})"