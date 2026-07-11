# -*- coding: utf-8 -*-
"""
Paquete ui - Interfaz de usuario para painter-tk

Este paquete contiene la interfaz gráfica de la aplicación,
construida sobre Tkinter. Separa la lógica de presentación
de la lógica de dominio (geometry) y de persistencia (storage).
"""

from .app import App
from .toolbar import Toolbar
from .statusbar import StatusBar
from .canvas_view import CanvasView

__all__ = [
    'App',
    'Toolbar',
    'StatusBar',
    'CanvasView',
]

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'