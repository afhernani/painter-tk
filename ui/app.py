# -*- coding: utf-8 -*-
"""
App - Clase principal de la aplicación
"""
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import logging
import os

from photos import Photos
from configmanager import config
from .canvasview import CanvasView
from .toolbar import Toolbar
from .statusbar import StatusBar
from configmanager import config
from storage.image_exporter import export_to_png

log = logging.getLogger('Paint.App')


class App(tk.Frame):
    """Aplicación principal de dibujo"""
    
    def __init__(self, master):
        #super().__init__(master)
        self.master = master
        self.master.title("Painter TK")
        # Si config es None, usa el config global
        # if config is None:
        #     from configmanager import config as config_global
        #     self.config = config_global
        # else:
        #     self.config = config
        
        #self.pack(fill=tk.BOTH, expand=True)
        
        # Configuración
        pen_defaults  = config.get_pen_defaults()
        canvas_width, canvas_height = config.get_canvas_size()
        default_mode = config.get('General', 'default_mode', 'L')
        
        self.color_fg = pen_defaults['color_fg']
        self.color_bg = pen_defaults['color_bg']
        self.penwidth = pen_defaults['width']
        self.color_fill = pen_defaults['color_fill']
        
        self.photos = Photos()
        
        # StatusBar
        self.statusbar = StatusBar(self.master)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Toolbar
        self.toolbar = Toolbar(
            self.master,
            self.photos,
            default_mode=default_mode,
            default_width=self.penwidth
        )
        #self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # CanvasView
        self.canvasview = CanvasView(
            self.master,
            color_bg=self.color_bg,
            width=canvas_width,
            height=canvas_height
        )
        self.canvasview.pack(fill=tk.BOTH, expand=True)

        #self.canvasview.configure(bg=self.new_color)
        #self.canvasview.clear_all()
        
        # Conectar CanvasView con Toolbar
        self.canvasview._get_mode = self.toolbar.get_mode
        self.canvasview._get_width = self.toolbar.get_penwidth
        self.canvasview._get_color_fg = lambda: self.color_fg
        self.canvasview._get_polygon_sides = self.toolbar.get_polygon_sides
        self.canvasview.set_status_callback(self.statusbar.set_text)
        
        # Callbacks de Toolbar
        self.toolbar._on_mode_change = self._on_mode_change
        self.toolbar._on_width_change = self._on_width_change
        self.toolbar.on_polygon_sides_change = self._on_polygon_sides_change
        # Conectar botones de color
        self.toolbar.on_bg_color_change = self.change_bg
        self.toolbar.on_brush_color_change = self.change_fg
        # conectar botones de Undo/Redo de la toolbar
        self.toolbar.on_undo = self.canvasview.undo
        self.toolbar.on_redo = self.canvasview.redo
        self.toolbar.on_fill_color_change = self.change_fill
        # Menú
        self._build_menu()
             
        log.info("Aplicación inicializada")
    
    def _build_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # Menú Colors
        colormenu = tk.Menu(menubar)
        menubar.add_cascade(label='Colors', menu=colormenu)
        colormenu.add_command(label='Brush Color', command=self.change_fg)
        colormenu.add_command(label='Background Color', command=self.change_bg)
        
        # Menú Options
        optionmenu = tk.Menu(menubar, tearoff=0) # evita el separador puntero tearoff=0
        menubar.add_cascade(label='Options', menu=optionmenu)
        optionmenu.add_command(label='Undo (Ctrl+Z)', command=self.canvasview.undo, accelerator='Ctrl+Z')
        optionmenu.add_command(label='Redo (Ctrl+Y)', command=self.canvasview.redo, accelerator='Ctrl+Y')
        optionmenu.add_separator()
        optionmenu.add_command(label='Clear Canvas', command=self.clear)
        optionmenu.add_separator()
        optionmenu.add_command(label='Save', command=self.save)
        optionmenu.add_command(label='Load', command=self.load)
        optionmenu.add_separator()
        optionmenu.add_command(label='Exportar a PNG...', command=self.export_png)
        optionmenu.add_separator()
        optionmenu.add_command(label='Exit', command=self.master.destroy)
    
    def _on_polygon_sides_change(self, sides):
        """Modificar los lados del poligon a crar"""
        log.info(f"Lados del polígono cambiados a: {sides}")
        # Opcional: guardar en config
        # self.canvasview.lados_poligono = sides
        config.set('General', 'polygon_sides', str(sides))
        config.save()


    def _on_mode_change(self, mode):
        """Callback cuando cambia el modo de dibujo desde la toolbar"""
        log.info(f"Modo cambiado a: {mode}")
        # desseleccionar cualquier objeto al cambiar de herramienta
        self.canvasview._desseleccionar_todo()
        config.set('General', 'default_mode', mode)
        config.save()
        self.canvasview._set_mode(mode)
        self.statusbar.set_text(f"Mode: {mode}")
    
    def _on_width_change(self, width):
        """callback cuando cambia el grosor del pincel"""
        self.penwidth = width
        config.set('Pen', 'default_width', str(width))
        config.save()
        self.statusbar.set_text(f"Grosor: {width}")
    
        # Si hay una figura seleccionada, actualizar su grosor
        if self.canvasview.shape_seleccionada:
            self.canvasview.actualizar_grosor_seleccionado(width)
    
    def change_fg(self):
        new_color = colorchooser.askcolor(color=self.color_fg)[1]
        if new_color is not None:
            self.color_fg = new_color
            config.set('Pen', 'default_color_fg', new_color)
            config.save()
            self.statusbar.set_text(f"Color del pincel: {new_color}")
            # si hay una figura seleccionada, actualizar su color
            if self.canvasview.shape_seleccionada:
                self.canvasview.actualizar_color_seleccionado(new_color)
        else:
            self.statusbar.set_text(f"Cambio de color cancelado")
    
    def change_bg(self):
        new_color = colorchooser.askcolor(color=self.color_bg)[1]
        if new_color:
            self.color_bg = new_color
            self.canvasview.configure(bg=new_color)
            config.set('Pen', 'default_color_bg', new_color)
            config.save()
    
    def clear(self):
        # limpia el canvas y el modelo
        self.canvasview.clear_all()
        # CRÍTICO: Olvidar el último archivo cargado para que no se abra solo la próxima vez
        config.set('General', 'last_file', '')
        config.save()
        
        # 3. Avisar al usuario
        self.statusbar.set_text("Canvas limpiado y memoria de archivo reiniciada")
        log.info("Canvas limpiado y last_file borrado de la configuración")
    
    # def save(self):
    #     filepath = filedialog.asksaveasfilename(
    #         defaultextension='.svg',
    #         filetypes=[('SVG files', '*.svg')]
    #     )
    #     if filepath:
    #         self.canvas_view.save_to_svg(filepath)
    #         config.save_last_file(filepath)
    
    # def load(self):
        # filepath = filedialog.askopenfilename(
        #     filetypes=[('SVG files', '*.svg')]
        # )
        # if filepath:
        #     self.canvas_view.load_from_svg(filepath)
    
    def save(self):
        """Salvar a fichero """
        log.info(f"Save json:")
        filepath = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
        )
        if filepath:
            self.canvasview.save_to_json(filepath)
            config.save_last_file(filepath)

    def load(self):
        """Cargar fichero json"""
        log.info(f"load json:")
        filepath = filedialog.askopenfilename(
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
        )
        if filepath:
            self.canvasview.load_from_json(filepath)
            config.save_last_file(filepath)
    
    def export_png(self):
        """Exporta el canvas actual a una imagen PNG"""
        filepath = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG images', '*.png'), ('All files', '*.*')]
        )
        if filepath:
            width, height = config.get_canvas_size()
            bg_color = config.get('Pen', 'default_color_bg', 'white')
            
            export_to_png(
                self.canvasview.shapes,
                filepath,
                width=width,
                height=height,
                bg_color=bg_color
            )
            self.statusbar.set_text(f"Imagen exportada: {filepath}")
    
    # Y crea el método (similar a change_fg y change_bg):
    def change_fill(self):
        """cambiar el color de relleno"""
        color = tk.colorchooser.askcolor(title="Color de Relleno")[1]
        if color is not None:
            config.set('Pen', 'default_color_fill', color)
            self.statusbar.set_text(f"Color de relleno: {color}")
            # si hay una figura seleccionada, actualiza su relleno
            if self.canvasview.shape_seleccionada:
                self.canvasview.actualizar_relleno_seleccionado(color)
        else:
            config.set('Pen', 'default_color_fill', '')
            self.statusbar.set_text("Relleno: Transparente (sin relleno)")
            # si hay una figura seleccionada, quitar relleno
            if self.canvasview.shape_seleccionada:
                self.canvasview.actualizar_relleno_seleccionado('')
            
        config.save()
        