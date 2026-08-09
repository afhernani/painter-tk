# -*- coding: utf-8 -*-
"""
Exporta las figuras del modelo a una imagen PNG usando Pillow.
"""
import logging
from PIL import Image, ImageDraw

log = logging.getLogger('Storage.ImageExporter')


def export_to_png(shapes, filepath, width=800, height=600, bg_color='white', transform=None, scale=1.0):
    """
    Exporta una lista de figuras Shape a un archivo PNG.
    
    Args:
        shapes: lista de objetos Shape (deben implementar dibujar_en_pil)
        filepath: ruta del archivo .png de salida
        width: ancho de la imagen en píxeles
        height: alto de la imagen en píxeles
        bg_color: color de fondo (nombre CSS, hex, o tupla RGB)
    """
    # Crear imagen en memoria
    imagen = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(imagen)
    
    # Dibujar cada figura, aplicando transform/scale si la forma lo soporta
    for shape in shapes:
        try:
            # intentamos llamar con la nueva firma (transform, scale)
            try:
                shape.dibujar_en_pil(draw, transform=transform, scale=scale)
            except TypeError:
                # si la forma aún espera la firma antigua, usar la llamada antigua
                shape.dibujar_en_pil(draw)
        except Exception as e:
            log.warning(f"No se pudo dibujar {shape} en PIL: {e}")
    
    # Guardar como PNG
    imagen.save(filepath, 'PNG')
    log.info(f"Imagen exportada a PNG: {filepath} ({width}x{height}, {len(shapes)} figuras)")