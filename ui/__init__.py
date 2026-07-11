# -*- coding: utf-8 -*-
"""
Paquete ui - Interfaz de usuario para painter-tk

Este paquete contiene los componentes visuales de la aplicación:
- App: clase principal que orquesta todo
- Toolbar: barra de herramientas (modos y grosor)
- StatusBar: barra de estado inferior
- CanvasView: lienzo con lógica de dibujo y selección
"""

from .app import App
from .toolbar import Toolbar
from .statusbar import StatusBar
from .canvas_view import CanvasView

__all__ = ['App', 'Toolbar', 'StatusBar', 'CanvasView']

__version__ = '1.0.0'
__author__ = 'hernani <afhernani@gmail.com>'