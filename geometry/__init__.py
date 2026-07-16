# -*- coding: utf-8 -*-
"""
Paquete geometry - Modelos geométricos para painter-tk

Este paquete contiene las clases que representan las formas geométricas
que se pueden dibujar en el canvas. Cada clase encapsula sus propios
datos geométricos y sabe cómo dibujarse a sí misma.
"""

from .point import Punto
from .shape import Shape
from .line import Linea
from .circle import Circulo
from .rectangle import Rectangulo
from .ellipse import Elipse
from .arc import Arco
from .polyline import Polyline
from .pointshape import PointShape
from .polygon import Poligono

__all__ = [
    'Punto',
    'Shape',
    'Linea',
    'Circulo',
    'Rectangulo',
    'Elipse',
    'Arco',
    'Polyline',
    'PointShape',
    'Poligono'
]

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'