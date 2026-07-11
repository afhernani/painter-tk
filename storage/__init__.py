# -*- coding: utf-8 -*-
"""
Paquete storage - Persistencia para painter-tk

Este paquete maneja la importación y exportación de archivos SVG.
Actúa como capa de persistencia entre los modelos geométricos
y el formato de archivo SVG.
"""

from .svg_exporter import exportar_svg
from .svg_importer import importar_svg

__all__ = [
    'exportar_svg',
    'importar_svg',
]

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'