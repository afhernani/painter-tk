#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de imágenes e iconos para painter-tk
Carga y gestiona todos los recursos gráficos de la aplicación
"""
import tkinter as tk
import os
import sys

__author__ = 'Hernani Aleman Ferraz'
__email__ = 'afhernani@gmail.com'
__version__ = '1.0'
__all__ = ('Photos',)


def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso.
    Funciona tanto en desarrollo como en PyInstaller.
    
    Args:
        relative_path: Ruta relativa al recurso
        
    Returns:
        Ruta absoluta al recurso
    """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En desarrollo, usar la carpeta actual
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class Photos:
    """Gestiona todos los iconos e imágenes de la aplicación"""
    
    def __init__(self):
        """Carga todos los iconos necesarios"""
        # Iconos de herramientas de dibujo
        self._line = tk.PhotoImage(file=resource_path('Assets/line.png'))
        self._pen = tk.PhotoImage(file=resource_path('Assets/pen.png'))
        self._polyline = tk.PhotoImage(file=resource_path('Assets/polyline.png'))
        self._polygon = tk.PhotoImage(file=resource_path('Assets/polygon.png'))
        self._circle = tk.PhotoImage(file=resource_path('Assets/circle.png'))
        self._arco = tk.PhotoImage(file=resource_path('Assets/arco.png'))
        self._elipse = tk.PhotoImage(file=resource_path('Assets/elipse.png'))
        self._square = tk.PhotoImage(file=resource_path('Assets/square.png'))
        self._rectangle = tk.PhotoImage(file=resource_path('Assets/rectangle.png'))
        self._select = tk.PhotoImage(file=resource_path('Assets/select.png'))
        self._punto = tk.PhotoImage(file=resource_path('Assets/punto.png'))
        self._undo = tk.PhotoImage(file=resource_path('Assets/undo.png'))
        self._redo = tk.PhotoImage(file=resource_path('Assets/redo.png'))
        
        # Iconos de acciones
        self._fillcolor = tk.PhotoImage(file=resource_path('Assets/fillcolor.png'))
        self._BackgroundColor = tk.PhotoImage(file=resource_path('Assets/Background-color.png'))
        self._BrushColor = tk.PhotoImage(file=resource_path('Assets/Brush-color.png'))
        self._penwidth = tk.PhotoImage(file=resource_path('Assets/pens_width.png'))
        self._apply = tk.PhotoImage(file=resource_path('Assets/pirate.png'))
        self._copy = tk.PhotoImage(file=resource_path('Assets/copy.png'))
        self._delete = tk.PhotoImage(file=resource_path('Assets/delete.png'))
        self._move = tk.PhotoImage(file=resource_path('Assets/move.png'))
        self._property = tk.PhotoImage(file=resource_path('Assets/property.png'))
        self._rename = tk.PhotoImage(file=resource_path('Assets/rename.png'))
        self._spider = tk.PhotoImage(file=resource_path('Assets/spider.png'))
        self._sprite = tk.PhotoImage(file=resource_path('Assets/th.png'))
        
        # Logo
        self._logo = tk.PhotoImage(file=resource_path('Assets/th.png'))
        
        # Animación de carga (frames de loading.gif)
        try:
            from PIL import Image
            loading_path = resource_path('Assets/loading.gif')
            img = Image.open(loading_path)
            self._frames = [
                tk.PhotoImage(
                    file=loading_path, 
                    format=f'gif -index {i}'
                ) 
                for i in range(img.n_frames)
            ]
        except Exception as e:
            print(f"Error cargando animación: {e}")
            self._frames = []


if __name__ == '__main__':
    # Prueba de carga de iconos
    root = tk.Tk()
    p = Photos()
    print("Iconos cargados correctamente:")
    print(f"  - Line: {p._line}")
    print(f"  - Pen: {p._pen}")
    print(f"  - Circle: {p._circle}")
    print(f"  - Arco: {p._arco}")
    root.mainloop()