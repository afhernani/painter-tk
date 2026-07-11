# -*- coding: utf-8 -*-
"""
App - Clase principal de la aplicación painter-tk.

Orquesta los componentes de la interfaz (Toolbar, StatusBar, CanvasView)
y gestiona el menú, la configuración y la comunicación entre componentes.
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, colorchooser

from photos import Photos
from configmanager import config
from .toolbar import Toolbar
from .statusbar import StatusBar
from .canvas_view import CanvasView

log = logging.getLogger('Paint.App')


class App:
    """Aplicación principal de dibujo."""
    
    def __init__(app_self, master):
        """
        Inicializa la aplicación.
        
        Args:
            master: Ventana raíz de Tkinter
        """
        self.master = master
        master.title('Paint App')
        
        # Cargar configuración
        pen_defaults = config.get_pen_defaults()
        canvas_width, canvas_height = config.get_canvas_size()
        default_mode = config.get('General', 'default_mode', 'L')
        
        # Estado global de la aplicación
        self.color_fg = pen_defaults['color_fg']
        self.color_bg = pen_defaults['color_bg']
        self.penwidth = pen_defaults['width']
        
        # Cargar iconos
        self.photos = Photos()
        
        # Crear componentes de la UI
        self.statusbar = StatusBar(master)
        self.toolbar = Toolbar(
            master,
            self.photos,
            default_mode=default_mode,
            default_width=self.penwidth
        )
        self.canvas_view = CanvasView(
            master,
            self.toolbar,
            self.statusbar
        )
        
        # Conectar callbacks de la toolbar
        self.toolbar.on_mode_change = self._on_mode_changed
        self.toolbar.on_width_change = self._on_width_changed
        
        # Sincronizar colores de la toolbar con la app
        self.toolbar.color_fg = self.color_fg
        self.toolbar.color_bg = self.color_bg
        
        # Crear el menú
        self._build_menu()
        
        # Cargar último archivo si existe
        last_file = config.get_last_file()
        if last_file and os.path.exists(last_file):
            self._load_file(last_file)
        
        log.info("Aplicación inicializada")
    
    # ================================================================
    # Callbacks de la toolbar
    # ================================================================
    def _on_mode_changed(self, mode):
        """Se llama cuando cambia el modo de dibujo."""
        log.info(f"Modo cambiado a: {mode}")
        config.set('General', 'default_mode', mode)
        config.save()
    
    def _on_width_changed(self, width):
        """Se llama cuando cambia el grosor del pincel."""
        self.penwidth = width
        config.set('Pen', 'default_width', str(width))
        config.save()
    
    # ================================================================
    # Menú
    # ================================================================
    def _build_menu(self):
        """Construye la barra de menú de la aplicación."""
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        
        # Menú Colors
        colormenu = tk.Menu(menu)
        menu.add_cascade(label='Colors', menu=colormenu)
        colormenu.add_command(label='Brush Color', command=self.change_fg)
        colormenu.add_command(label='Background Color', command=self.change_bg)
        
        # Menú Options
        optionmenu = tk.Menu(menu)
        menu.add_cascade(label='Options', menu=optionmenu)
        optionmenu.add_command(label='Clear Canvas', command=self.clear)
        optionmenu.add_separator()
        optionmenu.add_command(label='Save', command=self.save)
        optionmenu.add_command(label='Load', command=self.load)
        optionmenu.add_command(label='Config', command=self.canvasconfig)
        optionmenu.add_separator()
        optionmenu.add_command(label='Exit', command=self.master.destroy)
    
    # ================================================================
    # Acciones del menú
    # ================================================================
    def change_fg(self):
        """Cambia el color del pincel."""
        new_color = colorchooser.askcolor(color=self.color_fg)[1]
        if new_color:
            self.color_fg = new_color
            self.toolbar.color_fg = new_color
            config.set('Pen', 'default_color_fg', new_color)
            config.save()
    
    def change_bg(self):
        """Cambia el color de fondo del canvas."""
        new_color = colorchooser.askcolor(color=self.color_bg)[1]
        if new_color:
            self.color_bg = new_color
            self.toolbar.color_bg = new_color
            self.canvas_view.canvas.config(bg=new_color)
            config.set('Pen', 'default_color_bg', new_color)
            config.save()
    
    def clear(self):
        """Limpia el canvas."""
        self.canvas_view.clear()
        self.statusbar.set_text("Canvas limpiado")
    
    def save(self):
        """Guarda el canvas en un archivo SVG."""
        filepath = 'downloads/canvas.svg'
        os.makedirs('downloads', exist_ok=True)
        self.canvas_view.save_to_svg(filepath)
        config.save_last_file(filepath)
        self.statusbar.set_text(f"Guardado en {filepath}")
    
    def load(self):
        """Carga un archivo SVG."""
        filepath = 'downloads/canvas.svg'
        self._load_file(filepath)
    
    def _load_file(self, filepath):
        """Carga un archivo SVG específico."""
        if os.path.exists(filepath):
            count = self.canvas_view.load_from_svg(filepath)
            self.statusbar.set_text(
                f"{filepath} cargado ({count} objetos)"
            )
        else:
            self.statusbar.set_text(f"Archivo no encontrado: {filepath}")
    
    def canvasconfig(self):
        """Muestra información de configuración del canvas (debug)."""
        c = self.canvas_view.canvas
        log.info(f"Config canvas: {c}")
        log.info(f"Estado: {c['state']}")