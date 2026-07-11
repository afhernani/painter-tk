# -*- coding: utf-8 -*-
"""
Paquete storage - Persistencia para painter-tk

Este paquete maneja la importación y exportación de archivos SVG.
Actúa como capa de persistencia entre los modelos geométricos
y el formato de archivo SVG.
"""

from .svg_exporter import saveall, convert, SVGdocument
from .svg_importer import loadSvg

__all__ = [
    'saveall',
    'convert',
    'SVGdocument',
    'loadSvg',
]

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'