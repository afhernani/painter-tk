# -*- coding: utf-8 -*-
"""
Toolbar - Barra de herramientas superior de la aplicación.

Contiene:
- Slider para ajustar el grosor del pincel
- RadioButtons para seleccionar el modo de dibujo
  (Select, Line, Pen, Circle, Rectangle, Oval, Arco)

Mantiene el estado actual (modo, grosor, colores) y notifica
los cambios mediante callbacks opcionales.
"""

import tkinter as tk
from tkinter import ttk


class Toolbar:
    """Barra de herramientas con controles de dibujo."""
    
    def __init__(self, parent, photos, default_mode='L', default_width=5.0):
        """
        Crea la barra de herramientas.
        
        Args:
            parent: Widget padre
            photos: Instancia de Photos con los iconos
            default_mode: Modo inicial ('L', 'P', 'C', etc.)
            default_width: Grosor inicial del pincel
        """
        self.photos = photos
        
        # Variables de estado
        self.modo_var = tk.StringVar(value=default_mode)
        self.penwidth_var = tk.DoubleVar(value=default_width)
        
        # Colores (se actualizan desde App)
        self.color_fg = 'black'
        self.color_bg = 'white'
        
        # Callbacks opcionales
        self.on_mode_change = None
        self.on_width_change = None
        
        # Construir la UI
        self.frame = tk.Frame(parent, padx=5, pady=5)
        self._build_width_control()
        self._build_mode_buttons()
        self.frame.pack(side=tk.TOP, fill=tk.X)
    
    def _build_width_control(self):
        """Construye el control de grosor del pincel (label + slider)."""
        label = tk.Label(
            self.frame,
            text='Pen Width:',
            font=('arial', 9)
        )
        label.grid(row=0, column=0)
        
        self.slider = ttk.Scale(
            self.frame,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.penwidth_var,
            command=self._on_width_changed
        )
        self.slider.grid(row=0, column=1, ipadx=30)
    
    def _build_mode_buttons(self):
        """Construye los RadioButtons de modos de dibujo."""
        draw_frame = tk.Frame(self.frame, padx=5, pady=5)
        
        # Configurar estilo para RadioButtons sin indicador
        style = ttk.Style(draw_frame)
        style.theme_use('default')
        style.configure(
            'IndicatorOff.TRadiobutton',
            indicatorrelief=tk.FLAT,
            indicatormargin=-10,
            indicatordiameter=-1,
            relief=tk.RAISED,
            focusthickness=0,
            highlightthickness=0,
            padding=5
        )
        style.map(
            'IndicatorOff.TRadiobutton',
            background=[('selected', 'white'), ('active', '#ececec')]
        )
        
        # Definición de modos: (texto, valor, icono)
        modes = [
            ("Select",    "S", self.photos._move),
            ("Line",      "L", self.photos._line),
            ("Pen",       "P", self.photos._pen),
            ("Circle",    "C", self.photos._circle),
            ("Rectangle", "R", self.photos._rectangle),
            ("Oval",      "O", self.photos._oval),
            ("Arco",      "A", self.photos._arco),
        ]
        
        # Trazar cambios de modo
        self.modo_var.trace_add('write', self._on_mode_changed)
        
        for text, mode, img in modes:
            rb = ttk.Radiobutton(
                draw_frame,
                image=img,
                variable=self.modo_var,
                value=mode,
                width=15,
                style='IndicatorOff.TRadiobutton'
            )
            rb.pack(side=tk.LEFT)
        
        draw_frame.grid(row=0, column=2, ipadx=30)
    
    def _on_mode_changed(self, *args):
        """Callback interno cuando cambia el modo de dibujo."""
        if self.on_mode_change:
            self.on_mode_change(self.modo_var.get())
    
    def _on_width_changed(self, value):
        """Callback interno cuando cambia el grosor del pincel."""
        if self.on_width_change:
            self.on_width_change(float(value))
    
    def get_mode(self):
        """Devuelve el modo de dibujo actual."""
        return self.modo_var.get()
    
    def get_penwidth(self):
        """Devuelve el grosor actual del pincel."""
        return self.penwidth_var.get()
    
    def set_penwidth(self, value):
        """Establece el grosor del pincel."""
        self.penwidth_var.set(value)