# -*- coding: utf-8 -*-
"""
Paquete geometry - Clases para formas geométricas en painter-tk

Este paquete contiene todas las clases necesarias para representar
formas geométricas en el sistema de dibujo.
"""

from .punto import Punto
from .shape import Shape
from .linea import Linea
from .circulo import Circulo
from .rectangulo import Rectangulo
from .elipse import Elipse
from .arco import Arco
from .polyline import Polyline

__all__ = [
    'Punto',
    'Shape',
    'Linea',
    'Circulo',
    'Rectangulo',
    'Elipse',
    'Arco',
    'Polyline',
]

__version__ = '1.0.0'