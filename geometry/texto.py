# -*- coding: utf-8 -*-
"""
Clase Texto para representar elementos de texto en el canvas.
"""
import tkinter as tk
from geometry.shape import Shape, _screen_point
from geometry.point import Punto
import logging

log = logging.getLogger('Geometry.Texto')


class Texto(Shape):
    """
    Representa un elemento de texto en el canvas.
    """
    
    def __init__(self, posicion: Punto, texto: str = "Texto",
                 fuente: str = "Arial", tamaño: int = 12,
                 color: str = "black", negrita: bool = False,
                 cursiva: bool = False, alineacion: str="center", **kwargs):
        super().__init__(color=color, **kwargs)
        self.posicion = posicion
        self.texto = texto
        self.fuente = fuente
        self.tamaño = tamaño
        self.negrita = negrita
        self.cursiva = cursiva
        self.alineacion = alineacion
    
    def _construir_fuente(self) -> str:
        """Construye la cadena de fuente para Tkinter"""
        estilo = ""
        if self.negrita and self.cursiva:
            estilo = "bold italic"
        elif self.negrita:
            estilo = "bold"
        elif self.cursiva:
            estilo = "italic"
        
        if estilo:
            return f"{self.fuente} {self.tamaño} {estilo}"
        return f"{self.fuente} {self.tamaño}"
    
    def dibujar_en(self, canvas: tk.Canvas) -> int:
        """Dibuja el texto en el canvas"""
        fuente_str = self._construir_fuente()
        # Mapear alineación a anchor de Tkinter
        anchor_map = {
            "left": tk.W,
            "center": tk.CENTER,
            "right": tk.E
        }
        anchor = anchor_map.get(self.alineacion, tk.CENTER)
        x, y = _screen_point(canvas, self.posicion.x, self.posicion.y)
        self._canvas_id = canvas.create_text(
            x,
            y,
            text=self.texto,
            font=fuente_str,
            fill=self.color,
            anchor=anchor
        )
        return self._canvas_id
    
    def bbox(self) -> tuple:
        """Devuelve el bounding box del texto"""
        # Estimación básica (Tkinter puede calcularlo exactamente con canvas.bbox())
        ancho_estimado = len(self.texto) * self.tamaño * 0.6
        alto_estimado = self.tamaño * 1.2
        
        x1 = self.posicion.x - ancho_estimado / 2
        y1 = self.posicion.y - alto_estimado / 2
        x2 = self.posicion.x + ancho_estimado / 2
        y2 = self.posicion.y + alto_estimado / 2
        
        return (x1, y1, x2, y2)
    
    def resaltar(self, canvas, color='red'):
        """Resalta el texto cambiando su color"""
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=color)
    
    def restaurar(self, canvas):
        """Restaura el color original del texto"""
        if self._canvas_id is not None:
            canvas.itemconfig(self._canvas_id, fill=self.color)
    
    def mover(self, dx: float, dy: float):
        """Mueve el texto"""
        self.posicion = Punto(self.posicion.x + dx, self.posicion.y + dy)
    
    def actualizar_en_canvas(self, canvas):
        """Actualiza la posición del texto en el canvas"""
        if self._canvas_id is not None:
            x, y = _screen_point(canvas, self.posicion.x, self.posicion.y)
            canvas.coords(self._canvas_id, x, y)
    
    def dibujar_en_pil(self, draw, transform=None, scale=1.0):
        """Dibuja el texto en una imagen PIL"""
        try:
            from PIL import ImageFont

            if transform is None:
                transform = lambda x, y: (x, y)

            # Escalar tamaño de fuente según scale
            font_size = max(1, int(self.tamaño * scale))
            font_name = self.fuente

            # Intentar cargar la fuente TrueType
            try:
                if self.negrita and self.cursiva:
                    font_path = f"{font_name} Bold Italic.ttf"
                elif self.negrita:
                    font_path = f"{font_name} Bold.ttf"
                elif self.cursiva:
                    font_path = f"{font_name} Italic.ttf"
                else:
                    font_path = f"{font_name}.ttf"
                font = ImageFont.truetype(font_path, font_size)
            except (IOError, OSError):
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except (IOError, OSError):
                    font = ImageFont.load_default()

            px, py = transform(self.posicion.x, self.posicion.y)
            draw.text((px, py), self.texto, fill=self.color, font=font)

        except Exception as e:
            import logging
            log = logging.getLogger('Geometry.Texto')
            log.warning(f"Error al dibujar texto en PIL: {e}")

    def to_dict(self) -> dict:
        """Serializa el texto a diccionario para JSON"""
        return {
            "type": "Texto",
            "posicion": self.posicion.to_dict(),
            "texto": self.texto,
            "fuente": self.fuente,
            "tamaño": self.tamaño,
            "color": self.color,
            "negrita": self.negrita,
            "cursiva": self.cursiva,
            "alineacion": self.alineacion
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Texto':
        """Deserializa desde diccionario JSON"""
        # Convertir el diccionario de posicion a objeto Punto
        posicion_data = data.get("posicion", {"x": 0, "y": 0})
        if isinstance(posicion_data, dict):
            posicion = Punto.from_dict(posicion_data)
        else:
            posicion = posicion_data  # Ya es un Punto
        
        return cls(
            posicion=posicion,
            texto=data.get("texto", "Texto"),
            fuente=data.get("fuente", "Arial"),
            tamaño=data.get("tamaño", 12),
            color=data.get("color", "black"),
            negrita=data.get("negrita", False),
            cursiva=data.get("cursiva", False),
            alineacion=data.get("alineacion", "center")
        )
    
    def __repr__(self):
        return f"Texto(posicion={self.posicion}, texto='{self.texto}', fuente={self.fuente}, tamaño={self.tamaño})"