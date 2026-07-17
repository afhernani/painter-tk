# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk

class Toolbar:
    def __init__(self, parent, photos, default_mode='L', default_width=2.):
        self.photos = photos
        
        # Variables de estado
        self.modo_var = tk.StringVar(value=default_mode)
        self.penwidth_var = tk.DoubleVar(value=default_width)
        self.polygon_sides_var = tk.IntVar(value=6)
        
        self.on_fill_color_change = None
        self.on_undo = None
        self.on_redo = None

        # Callbacks
        self.on_mode_change = None
        self.on_width_change = None
        self.on_polygon_sides_change = None
        self.on_bg_color_change = None       # NUEVO
        self.on_brush_color_change = None    # NUEVO
        
        # Construir UI
        self.frame = tk.Frame(parent, padx=5, pady=5)
        
        self._build_undo_redo_controls()     # undo / redo
        self._build_color_controls()         # 1. Colores
        self._build_penwidth_control()       # 2. Grosor (Icono + Spinbox)
        self._build_polygon_control()        # 3. Lados polígono
        self._build_mode_buttons()           # 4. Modos de dibujo
        
        self.frame.pack(side=tk.TOP, fill=tk.X)
        
        # Ocultar control de polígono por defecto
        self.polygon_frame.pack_forget()

    def _build_color_controls(self):
        """Botones de color de fondo y color de pincel"""
        # Botón Color de Fondo
        self.btn_bg_color = tk.Button(
            self.frame,
            image=self.photos._BackgroundColor,
            command=self._on_bg_color_click,
            relief=tk.FLAT,
            borderwidth=0,
            activebackground=self.frame.cget('bg') # Para que no parpadee al pasar el ratón
        )
        self.btn_bg_color.pack(side=tk.LEFT, padx=5)

        # Botón Color de Pincel
        self.btn_brush_color = tk.Button(
            self.frame,
            image=self.photos._BrushColor,
            command=self._on_brush_color_click,
            relief=tk.FLAT,
            borderwidth=0,
            activebackground=self.frame.cget('bg')
        )
        self.btn_brush_color.pack(side=tk.LEFT, padx=5)

        self.btn_fill_color = tk.Button(
            self.frame,
            image=self.photos._fillcolor,  # Asegúrate de añadir este icono en photos.py
            command=self._on_fill_color_click,
            relief=tk.FLAT, borderwidth=0, activebackground=self.frame.cget('bg')
        )
        self.btn_fill_color.pack(side=tk.LEFT, padx=5)


    def _build_penwidth_control(self):
        """Icono de grosor + Spinbox decimal (0.0 a 20.0)"""
        # Icono
        lbl_penwidth = tk.Label(
            self.frame, 
            image=self.photos._penwidth,
            bg=self.frame.cget('bg')
        )
        lbl_penwidth.pack(side=tk.LEFT, padx=(10, 2))
        
        # Spinbox decimal
        self.penwidth_spinbox = ttk.Spinbox(
            self.frame,
            from_=0.0,
            to=20.0,
            increment=0.1,
            format="%.1f",       # Fuerza a mostrar 1 decimal (ej: 1.5, 2.0)
            width=4,
            textvariable=self.penwidth_var,
            command=self._on_width_changed
        )
        self.penwidth_spinbox.pack(side=tk.LEFT, padx=5)

    def _build_polygon_control(self):
        """Control para el número de lados del polígono"""
        self.polygon_frame = tk.Frame(self.frame)
        
        self.polygon_label = tk.Label(
            self.polygon_frame, text='Lados:', font=('arial', 9)
        )
        self.polygon_label.pack(side=tk.LEFT, padx=(10, 2))
        
        self.polygon_spinbox = tk.Spinbox(
            self.polygon_frame, from_=3, to=20, width=4,
            textvariable=self.polygon_sides_var,
            command=self._on_polygon_sides_changed
        )
        self.polygon_spinbox.pack(side=tk.LEFT)
        self.polygon_frame.pack(side=tk.LEFT, padx=10)

    def _build_mode_buttons(self):
        """Construye los RadioButtons de modos de dibujo"""
        draw_frame = tk.Frame(self.frame, padx=5, pady=5)
        style = ttk.Style(draw_frame)
        style.theme_use('default')
        style.configure(
            'IndicatorOff.TRadiobutton',
            indicatorrelief=tk.FLAT, indicatormargin=-10,
            indicatordiameter=-1, relief=tk.RAISED, padding=5
        )
        style.map(
            'IndicatorOff.TRadiobutton',
            background=[('selected', 'white'), ('active', '#ececec')]
        )
        # Definición de modos: (texto, valor, icono)
        modes = [
            ("Punto",     "Pt", self.photos._punto),
            ("Line",      "L",  self.photos._line),
            ("Polyline",  "Pl", self.photos._polyline),
            ("Polygon",   "G",  self.photos._polygon),
            ("Pen",       "P",  self.photos._pen),
            ("Circle",    "C",  self.photos._circle),
            ("Rectangle", "R",  self.photos._rectangle),
            ("Elipse",      "E",  self.photos._elipse),
            ("Arco",      "A", self.photos._arco),
            ("Texto",     "T", self.photos._texto),
            ("Select",    "S", self.photos._move),
        ]
        # Trazar cambios de modo
        self.modo_var.trace_add('write', self._on_mode_changed)
        
        for text, mode, img in modes:
            rb = ttk.Radiobutton(
                draw_frame, image=img, variable=self.modo_var,
                value=mode, width=15, style='IndicatorOff.TRadiobutton'
            )
            rb.pack(side=tk.LEFT)
        draw_frame.pack(side=tk.LEFT, padx=10)

    # --- Callbacks Internos ---

    def _on_bg_color_click(self):
        if self.on_bg_color_change:
            self.on_bg_color_change()

    def _on_brush_color_click(self):
        if self.on_brush_color_change:
            self.on_brush_color_change()

    def _on_mode_changed(self, *args):
        mode = self.modo_var.get()
        if mode == 'G':
            self.polygon_frame.pack(side=tk.LEFT, padx=10)
        else:
            self.polygon_frame.pack_forget()
        
        if self.on_mode_change:
            self.on_mode_change(mode)

    def _on_width_changed(self):
        """Callback interno cuando cambia el grosor del pincel desde el Spinbox"""
        # Leemos el valor directamente de la variable asociada al Spinbox
        # value = self.penwidth_var.get()
        # log.info(f"_on_width_changed: {value}")
        if self.on_width_change:
            self.on_width_change(self.penwidth_var.get())
            # config.set('Pen', 'default_width', str(value))
            #config.save()

    def _on_polygon_sides_changed(self):
        if self.on_polygon_sides_change:
            self.on_polygon_sides_change(self.polygon_sides_var.get())

    # --- Getters ---
    def get_mode(self): return self.modo_var.get()
    def get_penwidth(self): return self.penwidth_var.get()
    def get_polygon_sides(self): return self.polygon_sides_var.get()

    # Botones undo redo.
    def _build_undo_redo_controls(self):
        """Botones de Deshacer y Rehacer"""
        # Botón Deshacer (Undo)
        self.btn_undo = tk.Button(
            self.frame,
            image=self.photos._undo,  # Asegúrate de tener este icono en photos.py
            command=self._on_undo_click,
            relief=tk.FLAT,
            borderwidth=0,
            activebackground=self.frame.cget('bg')
        )
        self.btn_undo.pack(side=tk.LEFT, padx=5)

        # Botón Rehacer (Redo)
        self.btn_redo = tk.Button(
            self.frame,
            image=self.photos._redo,  # Asegúrate de tener este icono en photos.py
            command=self._on_redo_click,
            relief=tk.FLAT,
            borderwidth=0,
            activebackground=self.frame.cget('bg')
        )
        self.btn_redo.pack(side=tk.LEFT, padx=5)

    def _on_undo_click(self):
        if self.on_undo:
            self.on_undo()

    def _on_redo_click(self):
        if self.on_redo:
            self.on_redo()

    def _on_fill_color_click(self):
        if self.on_fill_color_change:
            self.on_fill_color_change()