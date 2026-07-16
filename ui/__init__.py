# -*- coding: utf-8 -*-
"""
Paquete ui - Interfaz de usuario para painter-tk

Este paquete contiene la interfaz gráfica de la aplicación,
construida sobre Tkinter. Separa la lógica de presentación
de la lógica de dominio (geometry) y de persistencia (storage).
"""

from ui.app import App
from ui.toolbar import Toolbar
from ui.statusbar import StatusBar
from .canvasview import CanvasView

__all__ = [
    'App',
    'Toolbar',
    'StatusBar',
    'CanvasView',
]

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'