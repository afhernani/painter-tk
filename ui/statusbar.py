# -*- coding: utf-8 -*-
"""
StatusBar - Barra de estado inferior de la aplicación.

Muestra información contextual como coordenadas del ratón,
mensajes de estado y notificaciones al usuario.
"""

import tkinter as tk
from tkinter import ttk


class StatusBar:
    """Barra de estado inferior con un label de texto."""
    
    def __init__(self, parent):
        """
        Crea la barra de estado.
        
        Args:
            parent: Widget padre (normalmente la ventana raíz)
        """
        self.label = ttk.Label(
            parent,
            text="Listo",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.label.pack(side=tk.BOTTOM, fill=tk.BOTH)
    
    def set_text(self, text):
        """
        Actualiza el texto de la barra de estado.
        
        Args:
            text: Nuevo texto a mostrar
        """
        self.label.config(text=text)
    
    def get_text(self):
        """Devuelve el texto actual de la barra de estado."""
        return self.label.cget('text')