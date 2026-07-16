# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import colorchooser
import logging

log = logging.getLogger('UI.PropertiesWindow')

class PropertiesWindow(tk.Toplevel):
    def __init__(self, parent, canvasview, shape):
        super().__init__(parent)
        self.title("Propiedades de la Figura")
        # Hacemos la ventana un poco más grande para que quepa todo
        self.geometry("320x300") 
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set() 
        
        self.canvasview = canvasview  # Guardamos la referencia al CanvasView
        self.shape = shape
        
        # Variables temporales
        self.temp_color = shape.color
        self.temp_width = shape.grosor
        self.temp_fill = getattr(shape, 'relleno', '')
        
        self._build_ui()
        
    def _build_ui(self):
        # Contenedor principal con buen padding
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. Color de Contorno
        tk.Label(main_frame, text="Color de Contorno:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.btn_color = tk.Button(main_frame, bg=self.temp_color, height=2, 
                                   command=self._choose_color, relief=tk.GROOVE)
        self.btn_color.pack(fill=tk.X, pady=(5, 15))
        
        # 2. Color de Relleno (Solo si aplica)
        if hasattr(self.shape, 'relleno'):
            tk.Label(main_frame, text="Color de Relleno:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            
            fill_frame = tk.Frame(main_frame)
            fill_frame.pack(fill=tk.X, pady=(5, 15))
            
            fill_display = self.temp_fill if self.temp_fill else 'white'
            self.btn_fill = tk.Button(fill_frame, bg=fill_display, height=2, 
                                      command=self._choose_fill, relief=tk.GROOVE)
            self.btn_fill.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
            
            btn_no_fill = tk.Button(fill_frame, text="Sin relleno", 
                                    command=self._clear_fill, bg='#f0f0f0')
            btn_no_fill.pack(side=tk.RIGHT, padx=(5, 0))
        else:
            self.btn_fill = None
            
        # 3. Grosor
        tk.Label(main_frame, text="Grosor de línea:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.width_var = tk.DoubleVar(value=self.temp_width)
        self.sp_width = tk.Spinbox(main_frame, from_=0.1, to=50.0, increment=0.1, 
                                   textvariable=self.width_var, width=10, font=('Arial', 10))
        self.sp_width.pack(fill=tk.X, pady=(5, 20))
        
        # 4. Botones de Acción (Bien separados y grandes)
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Botón Aplicar
        self.btn_apply = tk.Button(btn_frame, text="✅ ACEPTAR", command=self._apply_changes, 
                                   bg='#2E7D32', fg='white', font=('Arial', 11, 'bold'),
                                   activebackground='#1B5E20')
        self.btn_apply.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5), pady=5)
        
        # Botón Cancelar
        self.btn_cancel = tk.Button(btn_frame, text="❌ CANCELAR", command=self.destroy, 
                                    bg='#C62828', fg='white', font=('Arial', 11, 'bold'),
                                    activebackground='#B71C1C')
        self.btn_cancel.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0), pady=5)

    def _choose_color(self):
        color = colorchooser.askcolor(title="Color de Contorno", initialcolor=self.temp_color)[1]
        if color:
            self.temp_color = color
            self.btn_color.config(bg=color)
            
    def _choose_fill(self):
        initial = self.temp_fill if self.temp_fill else 'white'
        color = colorchooser.askcolor(title="Color de Relleno", initialcolor=initial)[1]
        if color:
            self.temp_fill = color
            self.btn_fill.config(bg=color)

    def _clear_fill(self):
        self.temp_fill = ''
        self.btn_fill.config(bg='white')

    def _apply_changes(self):
        """Aplica los cambios y llama al CanvasView"""
        new_width = self.width_var.get()
        
        # 1. Actualizar el modelo de datos
        self.shape.color = self.temp_color
        self.shape.grosor = float(new_width)
        if hasattr(self.shape, 'relleno'):
            self.shape.relleno = self.temp_fill
            
        # 2. LLAMAR AL CANVASVIEW para que redibuje (Aquí ocurre la magia)
        if hasattr(self.canvasview, 'redraw_shape'):
            self.canvasview.redraw_shape(self.shape)
            
        self.destroy()