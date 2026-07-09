# -*- coding: utf-8 -*-
# Tkinter canvas to SVG exporter
from tkinter import *
from tkinter import ttk, colorchooser
from canvasvg import saveall, convert
import logging
import tksvg
from enum import Enum
import os, sys
from photos import Photos
from utilitygraph import *
from svgcanvas import loadSvg
from configmanager import config

__author__  = "hernani <afhernani@gmail.com>"

__all__ = ["App"]

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('Paint')
log.setLevel(logging.DEBUG)


class App:
    def __init__(self, master):
        self.master = master
        self.modo = None
        self.photo = Photos()
        #  Cargar configuración
        pen_defaults = config.get_pen_defaults()
        canvas_width, canvas_height = config.get_canvas_size()
        
        # Usar valores de configuración o por defecto
        self.color_fg = pen_defaults['color_fg']
        self.color_bg = pen_defaults['color_bg']
        self.penwidth = pen_defaults['width']

        self.old_x = None
        self.old_y = None
        self.lin_x, self.lin_y = None, None
        self.penwidth = 5
        
        # === Estado de selección y edición ===
        self.objetos = []                  # IDs de todos los objetos dibujados
        self.objeto_seleccionado = None    # ID del objeto seleccionado
        self.tipo_seleccionado = None      # Tipo: 'line', 'oval', 'arc', etc.
        self.tag_trazo_seleccionado = None # Para lápiz
        self.trazos = {}                   # {tag_trazo: [lista de segmentos]}
        self.contador_trazos = 0           # Contador único para tags
        self.colores_originales = {}       # {item_id: color_original}
        
        # Handles (círculos de control)
        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        
        # Estado de arrastre
        self.dragging_handle = None
        self.dragging_line = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Selección múltiple con botón derecho
        self.selectBox = None
        self.linea = None
        self.originx, self.originy = 0, 0
        self._bbox_inicial = None
        
        self.inicialize(canvas_width, canvas_height)
        
        # Binds UNIFICADOS
        self.c.bind('<ButtonPress-1>', self.__on_press)
        self.c.bind('<B1-Motion>', self.__on_motion)
        self.c.bind('<ButtonRelease-1>', self.__on_release)
        
        self.c.bind('<ButtonPress-3>', self.__SelectStart__)
        self.c.bind('<B3-Motion>', self.__SelectMotion__)
        self.c.bind('<ButtonRelease-3>', self.__SelectRelease__)
        
        self.c.bind('<Enter>', self.__entercanvas)
        self.c.bind('<Leave>', self.__leavecanvas)

        # Cargar último archivo si existe
        last_file = config.get_last_file()
        if last_file and os.path.exists(last_file):
            self.muestra(last_file)


    def __entercanvas(self, *args):
        self.c.configure(cursor="tcross")

    def __leavecanvas(self, *args):
        self.c.configure(cursor="")

    # ================================================================
    # HANDLER PRINCIPAL DE PRESS
    # ================================================================
    def __on_press(self, e):
        if self.modo.get() == 'S':
            self.__press_select_mode(e)
            return
        
        # MODO DIBUJO
        self.lin_x, self.lin_y = e.x, e.y
        
        if self.modo.get() == 'L':
            self.linea = self.c.create_line(self.lin_x, self.lin_y,
                                            self.lin_x, self.lin_y)
        elif self.modo.get() == 'P':
            pass
        elif self.modo.get() == 'C':
            puntos = rectasCircunferencia(*[(self.lin_x, self.lin_y),
                                            (self.lin_x, self.lin_y)])
            self.linea = self.c.create_line(*puntos)
        elif self.modo.get() == 'R':
            puntos = rectasRectangulo(*[(self.lin_x, self.lin_y),
                                        (self.lin_x, self.lin_y)], n=4)
            self.linea = self.c.create_line(*puntos)
        elif self.modo.get() == 'O':
            self.linea = self.c.create_oval(self.lin_x, self.lin_y, e.x, e.y)
        elif self.modo.get() == 'A':
            self.linea = self.c.create_arc(self.lin_x, self.lin_y, e.x, e.y)

    # ================================================================
    # HANDLER PRINCIPAL DE MOTION
    # ================================================================
    def __on_motion(self, e):
        self.statusbar['text'] = f"{e.x} - {e.y}"
        
        if self.modo.get() == 'S':
            self.__motion_select_mode(e)
            return
        
        if self.modo.get() == 'P':
            if self.old_x is not None and self.old_y is not None:
                self.c.create_line(
                    self.old_x, self.old_y, e.x, e.y,
                    width=self.penwidth, fill=self.color_fg,
                    capstyle=ROUND, smooth=False,
                    tags=('lapiz', 'trazo_actual')
                )
        elif self.modo.get() == 'L':
            if self.linea is not None:
                self.c.coords(self.linea, self.lin_x, self.lin_y, e.x, e.y)
        elif self.modo.get() == 'C':
            if self.linea is not None:
                puntos = rectasCircunferencia(*[(self.lin_x, self.lin_y), (e.x, e.y)])
                self.c.coords(self.linea, *puntos)
        elif self.modo.get() == 'R':
            if self.linea is not None:
                puntos = rectasRectangulo(*[(self.lin_x, self.lin_y), (e.x, e.y)], n=4)
                self.c.coords(self.linea, *puntos)
        elif self.modo.get() == 'O':
            if self.linea is not None:
                self.c.coords(self.linea, self.lin_x, self.lin_y, e.x, e.y)
        elif self.modo.get() == 'A':
            if self.linea is not None:
                self.c.coords(self.linea, self.lin_x, self.lin_y, e.x, e.y)
        
        self.old_x = e.x
        self.old_y = e.y

    # ================================================================
    # HANDLER PRINCIPAL DE RELEASE
    # ================================================================
    def __on_release(self, e):
        """'<ButtonRelease-1>', self.__on_release : mouse button soltar."""
        self.old_x = None
        self.old_y = None
        
        if self.modo.get() == 'S':
            self.__release_select_mode(e)
            return
        
        
        if self.modo.get() == 'L' and self.linea is not None:
            x1, y1, x2, y2 = self.c.coords(self.linea)
            self.c.delete(self.linea)
            n_id = self.c.create_line(x1, y1, x2, y2,
                                      width=self.penwidth, fill=self.color_fg,
                                      capstyle=ROUND, smooth=False, tags='linea')
            self.objetos.append(n_id)
            self.colores_originales[n_id] = self.color_fg
        
        elif self.modo.get() == 'P':
            segmentos = self.c.find_withtag('trazo_actual')
            if segmentos:
                tag_trazo = f'trazo_{self.contador_trazos}'
                self.contador_trazos += 1
                lista_segmentos = []
                for seg in segmentos:
                    self.c.addtag_withtag(tag_trazo, seg)
                    self.c.dtag(seg, 'trazo_actual')
                    lista_segmentos.append(seg)
                    self.colores_originales[seg] = self.color_fg
                self.objetos.extend(lista_segmentos)
                self.trazos[tag_trazo] = lista_segmentos
        
        elif self.modo.get() == 'C' and self.linea is not None:
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            n_id = self.c.create_line(*puntos, width=self.penwidth, fill=self.color_fg,
                                      capstyle=ROUND, smooth=False, tags='circle')
            self.objetos.append(n_id)
            self.colores_originales[n_id] = self.color_fg
        
        elif self.modo.get() == 'R' and self.linea is not None:
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            n_id = self.c.create_line(*puntos, width=self.penwidth, fill=self.color_fg,
                                      capstyle=ROUND, smooth=False, tags='rectangle')
            self.objetos.append(n_id)
            self.colores_originales[n_id] = self.color_fg
        
        elif self.modo.get() == 'O' and self.linea is not None:
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            n_id = self.c.create_oval(*puntos, width=self.penwidth, outline=self.color_fg,
                                      fill='', tags='oval')
            self.objetos.append(n_id)
            self.colores_originales[n_id] = self.color_fg
        
        elif self.modo.get() == 'A' and self.linea is not None:
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            n_id = self.c.create_arc(*puntos, width=self.penwidth, outline=self.color_fg,
                                     fill='', tags='arc')
            self.objetos.append(n_id)
            self.colores_originales[n_id] = self.color_fg
        
        self.lin_x = self.lin_y = None
        self.linea = None

    # ================================================================
    # MODO SELECCIÓN
    # ================================================================
    def __press_select_mode(self, e):
        # 1. ¿Click sobre un handle?
        handle_items = self.c.find_overlapping(e.x-6, e.y-6, e.x+6, e.y+6)
        for item in handle_items:
            tags = self.c.gettags(item)
            if 'handle_start' in tags:
                self.dragging_handle = 'start'
                return
            if 'handle_end' in tags:
                self.dragging_handle = 'end'
                return
            if 'handle_nw' in tags:
                self.dragging_handle = 'nw'
                # Guardar bbox inicial al empezar a arrastrar
                self._bbox_inicial = self.c.bbox(self.objeto_seleccionado)
                return
            if 'handle_ne' in tags:
                self.dragging_handle = 'ne'
                self._bbox_inicial = self.c.bbox(self.objeto_seleccionado)
                return
            if 'handle_sw' in tags:
                self.dragging_handle = 'sw'
                self._bbox_inicial = self.c.bbox(self.objeto_seleccionado)
                return
            if 'handle_se' in tags:
                self.dragging_handle = 'se'
                self._bbox_inicial = self.c.bbox(self.objeto_seleccionado)
                return
        
        # 2. ¿Click sobre una figura existente?
        halo = 8
        encontrados = self.c.find_overlapping(e.x-halo, e.y-halo, e.x+halo, e.y+halo)
        candidatos = [i for i in encontrados if i in self.objetos]
        
        if candidatos:
            item_id = candidatos[-1]
            tags = self.c.gettags(item_id)
            tag_trazo = None
            for tag in tags:
                if tag.startswith('trazo_'):
                    tag_trazo = tag
                    break
            
            if tag_trazo:
                self.__seleccionar_trazo_lapiz(tag_trazo)
            else:
                self.__seleccionar_objeto(item_id)
            
            self.dragging_line = True
            self.drag_start_x = e.x
            self.drag_start_y = e.y
            return
        
        # 3. Click en vacío → deseleccionar
        self.__deseleccionar_todo()

    def __motion_select_mode(self, e):
        if self.dragging_handle:
            if self.dragging_handle in ('start', 'end'):
                self.__mover_handle_linea(e)
            elif self.dragging_handle in ('nw', 'ne', 'sw', 'se'):
                self.__redimensionar_bbox(e)
            return
        
        if self.dragging_line and self.objeto_seleccionado is not None:
            dx = e.x - self.drag_start_x
            dy = e.y - self.drag_start_y
            
            if self.tag_trazo_seleccionado:
                for seg_id in self.trazos[self.tag_trazo_seleccionado]:
                    self.c.move(seg_id, dx, dy)
            else:
                self.c.move(self.objeto_seleccionado, dx, dy)
            
            for h in [self.handle_start, self.handle_end,
                      self.handle_nw, self.handle_ne,
                      self.handle_sw, self.handle_se]:
                if h is not None:
                    self.c.move(h, dx, dy)
            
            self.drag_start_x = e.x
            self.drag_start_y = e.y

    def __release_select_mode(self, e):
        self.dragging_handle = None
        self.dragging_line = False
        self._bbox_inicial = None  #  Limpiar referencia

    # ================================================================
    # SELECCIÓN DE OBJETOS
    # ================================================================
    def __seleccionar_objeto(self, item_id):
        """seleccionar un objeto y muestra sus handles según el tipo"""
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        self.__deseleccionar_todo()
        
        self.objeto_seleccionado = item_id
        self.tipo_seleccionado = self.c.type(item_id)
        self.tag_trazo_seleccionado = None

        tags = self.c.gettags(item_id)
        log.info(f'Tags del objeto {item_id}: {tags}')

        # detectar si es un trazo de lápiz
        for tag in tags:
            if tag.startswith('trazo_'):
                self.tag_trazo_seleccionado = tag
                break
        
        # Resaltar visualmente
        color_original = self.colores_originales.get(item_id, self.color_fg)

        if self.tag_trazo_seleccionado:
            for seg_id in self.trazos.get(self.tag_trazo_seleccionado, []):
                self.c.itemconfig(seg_id, fill='red')
        else:
            # Manejar tanto tags de paint.py como svgcanvas.py
            if self.tipo_seleccionado == 'line' or 'linea' in tags or 'line' in tags:
                self.c.itemconfig(item_id, fill='red')
            else:
                self.c.itemconfig(item_id, outline='red')

        # if self.tipo_seleccionado == 'line':
        #     self.c.itemconfig(item_id, fill='red')
        # else:
        #     self.c.itemconfig(item_id, outline='red')
        
        # Mostrar handles según el tipo
        if self.tag_trazo_seleccionado:
            pass # el lapiz no tiene handles, sólo se mueve
        elif self.tipo_seleccionado == 'line' and ('linea' in tags or 'line' in tags):
            self.__mostrar_handles_linea(item_id) # linea simple: 2 handles en los extemos
        else:
            self.__mostrar_handles_bbox(item_id) #circulo, rectangulo, ovalo, arco: 4 hadles en bbox
        
        # tags = self.c.gettags(item_id)
        # if self.tipo_seleccionado == 'line' and 'linea' in tags:
        #     self.__mostrar_handles_linea(item_id)
        # else:
        #     self.__mostrar_handles_bbox(item_id)
        
        self.statusbar['text'] = f"Objeto {item_id} ({self.tipo_seleccionado}) seleccionado"

    def __seleccionar_trazo_lapiz(self, tag_trazo):
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        self.__deseleccionar_todo()
        
        self.tag_trazo_seleccionado = tag_trazo
        segmentos = self.trazos.get(tag_trazo, [])
        
        if segmentos:
            self.objeto_seleccionado = segmentos[0]
            for seg_id in segmentos:
                self.c.itemconfig(seg_id, fill='red')
        
        self.statusbar['text'] = f"Trazo {tag_trazo} seleccionado ({len(segmentos)} segmentos)"

    def __mostrar_handles_linea(self, item_id):
        coords = self.c.coords(item_id)
        if len(coords) < 4:
            return
        
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        
        self.handle_start = self.c.create_oval(
            x1-6, y1-6, x1+6, y1+6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_start')
        )
        self.handle_end = self.c.create_oval(
            x2-6, y2-6, x2+6, y2+6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_end')
        )

    def __mostrar_handles_bbox(self, item_id):
        bbox = self.c.bbox(item_id)
        if bbox is None:
            return
        
        x1, y1, x2, y2 = bbox
        
        self.handle_nw = self.c.create_oval(
            x1-6, y1-6, x1+6, y1+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_nw')
        )
        self.handle_ne = self.c.create_oval(
            x2-6, y1-6, x2+6, y1+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_ne')
        )
        self.handle_sw = self.c.create_oval(
            x1-6, y2-6, x1+6, y2+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_sw')
        )
        self.handle_se = self.c.create_oval(
            x2-6, y2-6, x2+6, y2+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_se')
        )

    # ================================================================
    # EDICIÓN
    # ================================================================
    def __mover_handle_linea(self, e):
        coords = self.c.coords(self.objeto_seleccionado)
        if len(coords) < 4:
            return
        
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        
        if self.dragging_handle == 'start':
            self.c.coords(self.objeto_seleccionado, e.x, e.y, x2, y2)
            self.c.coords(self.handle_start, e.x-6, e.y-6, e.x+6, e.y+6)
        elif self.dragging_handle == 'end':
            self.c.coords(self.objeto_seleccionado, x1, y1, e.x, e.y)
            self.c.coords(self.handle_end, e.x-6, e.y-6, e.x+6, e.y+6)

    def __redimensionar_bbox(self, e):
        """Redimensiona una figura manteniendo FIJA la esquina opuesta""" 
        # Usar el bbox inicial guardado, NO el actual (que Tkinter recalcula)
        if not hasattr(self, '_bbox_inicial') or self._bbox_inicial is None:
            return
        
        x1, y1, x2, y2 = self._bbox_inicial  # Coordenadas FIJAS de referencia
        
        # Según el handle arrastrado, modificar solo UNA esquina
        # La esquina opuesta queda FIJA (no se toca)
        
        if self.dragging_handle == 'nw':
            # NW se mueve con el ratón, SE queda fija
            x1, y1 = e.x, e.y
            # x2, y2 permanecen como estaban (fijos)
        
        elif self.dragging_handle == 'ne':
            # NE se mueve con el ratón, SW queda fija
            x2, y1 = e.x, e.y
            # x1, y2 permanecen como estaban (fijos)
        
        elif self.dragging_handle == 'sw':
            # SW se mueve con el ratón, NE queda fija
            x1, y2 = e.x, e.y
            # x2, y1 permanecen como estaban (fijos)
        
        elif self.dragging_handle == 'se':
            # SE se mueve con el ratón, NW queda fija
            x2, y2 = e.x, e.y
            # x1, y1 permanecen como estaban (fijos)
        
        # Asegurar que x1 < x2 y y1 < y2 (para que el bbox sea válido)
        # if x1 > x2:
        #     x1, x2 = x2, x1
        # if y1 > y2:
        #     y1, y2 = y2, y1
        
        # Aplicar según el tipo de figura
        tags = self.c.gettags(self.objeto_seleccionado)
        
        if 'circle' in tags:
            puntos = rectasCircunferencia(*[(x1, y1), (x2, y2)])
            self.c.coords(self.objeto_seleccionado, *puntos)
        elif 'rectangle' in tags:
            puntos = rectasRectangulo(*[(x1, y1), (x2, y2)], n=4)
            self.c.coords(self.objeto_seleccionado, *puntos)
        elif 'oval' in tags:
            self.c.coords(self.objeto_seleccionado, x1, y1, x2, y2)
        elif 'arc' in tags:
            self.c.coords(self.objeto_seleccionado, x1, y1, x2, y2)
        # Actualizar la posición visual de los 4 handles
        
        # Usar min/max para que los handles siempre estén en las esquinas correctas
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        # Actualizar la posición visual de los 4 handles
        if self.handle_nw:
            self.c.coords(self.handle_nw, x_min-6, y_min-6, x_min+6, y_min+6)
        if self.handle_ne:
            self.c.coords(self.handle_ne, x_max-6, y_min-6, x_max+6, y_min+6)
        if self.handle_sw:
            self.c.coords(self.handle_sw, x_min-6, y_max-6, x_min+6, y_max+6)
        if self.handle_se:
            self.c.coords(self.handle_se, x_max-6, y_max-6, x_max+6, y_max+6)

    # ================================================================
    # DESELECCIÓN Y RESTAURACIÓN
    # ================================================================
    def __restaurar_apariencia(self, item_id):
        try:
            tags = self.c.gettags(item_id)
            
            if self.tag_trazo_seleccionado:
                for seg_id in self.trazos.get(self.tag_trazo_seleccionado, []):
                    color = self.colores_originales.get(seg_id, self.color_fg)
                    self.c.itemconfig(seg_id, fill=color)
            elif self.tipo_seleccionado == 'line':
                color = self.colores_originales.get(item_id, self.color_fg)
                self.c.itemconfig(item_id, fill=color)
            else:
                color = self.colores_originales.get(item_id, self.color_fg)
                self.c.itemconfig(item_id, outline=color)
        except TclError:
            pass

    def __deseleccionar_todo(self):
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        
        self.c.delete('handle')
        
        self.objeto_seleccionado = None
        self.tipo_seleccionado = None
        self.tag_trazo_seleccionado = None
        
        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        
        self.dragging_handle = None
        self.dragging_line = False

    # ================================================================
    # FUNCIONES ORIGINALES
    # ================================================================
    def changeW(self, e):
        """Cambiar el grosor del pincel"""
        self.penwidth = float(e)
        config.set('Pen','default_width', str(self.penwidth))
        config.save()

    def clear(self):
        """limpia el canvas"""
        self.c.delete(ALL)
        self.objetos.clear()
        self.trazos.clear()
        self.colores_originales.clear()
        self.contador_trazos = 0

    def change_fg(self):
        """cambiar el color del pincel"""
        new_color = colorchooser.askcolor(color=self.color_fg)[1]
        if new_color:
            self.color_fg = new_color
            config.set('Pen','default_color_fg', new_color)

    def change_bg(self):
        """cambiar el color de fondo"""
        new_color = colorchooser.askcolor(color=self.color_bg)[1]
        if new_color:
            self.color_bg = new_color
            self.c['bg'] = new_color
            config.set('Pen','default_color_bg', new_color)
            config.save()

    def save(self, filepath=None):
        """Guardar documento en formato svg"""
        log.info('save function')
        if filepath is None:
            filepath = 'downloads/canvas.svg'
        
        saveall(filename='downloads/canvas.svg', canvas=self.c)
        self.statusbar.config(text=f"{filepath} saved ...")
        # guardar configuracion
        config.save_last_file(filepath)

    def muestra(self, filepath=None):
        """Carga archivo svg"""
        if filepath is None:
            filepath ='downloads/canvas.svg'
        if os.path.exists(filepath):
            try:
                canvas, ids_creados = loadSvg(filepath, self.c)
                # Añadir los ids a self.objetos
                for item_id in ids_creados:
                    if item_id not in self.objetos:
                        self.objetos.append(item_id)
                        log.info(f'Objetos {item_id} registrado desde SVG')

                self.statusbar['text']=f'{filepath} loaded ...({len(ids_creados)} objetos)'
                log.info(f"Total objetos en self.objeto: {len(self.objetos)}")
            except Exception as e:
                self.statusbar['text'] = f'file not found: {filepath}'
                log.error(f"error cargando SVG: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.statusbar['text'] = f"File not found: {filepath}"
            log.warning(f"Archivo no encontrado: {filepath}")

    def canvasconfig(self):
        log.info(f"Config canvas: {self.c}")
        options = self.c.config()
        log.info(f"stado: {self.c['state']}")
        self.c.configure(state='disabled')

    def __SelectStart__(self, event):
        self.originx = self.c.canvasx(event.x)
        self.originy = self.c.canvasy(event.y)
        self.selectBox = self.c.create_rectangle(
            self.originx, self.originy, self.originx, self.originy
        )

    def __SelectMotion__(self, event):
        xnew = self.c.canvasx(event.x)
        ynew = self.c.canvasy(event.y)
        if xnew < self.originx and ynew < self.originy:
            self.c.coords(self.selectBox, xnew, ynew, self.originx, self.originy)
        elif xnew < self.originx:
            self.c.coords(self.selectBox, xnew, self.originy, self.originx, ynew)
        elif ynew < self.originy:
            self.c.coords(self.selectBox, self.originx, ynew, xnew, self.originy)
        else:
            self.c.coords(self.selectBox, self.originx, self.originy, xnew, ynew)

    def __SelectRelease__(self, event):
        x1, y1, x2, y2 = self.c.coords(self.selectBox)
        self.c.delete(self.selectBox)
        selectedPointers = []
        for i in self.c.find_enclosed(x1, y1, x2, y2):
            points = self.c.coords(i)
            log.info(f"type selected: {self.c.type(i)}")
            tmp = self.c.itemconfigure(i)
            options = dict((v0, v4) for v0, v1, v2, v3, v4 in tmp.values())
            log.info(f"option object selected: {options}")
            self.c.itemconfig(i, {'state': DISABLED})
            selectedPointers.append(i)
        self.Callback(selectedPointers)

    def Callback(self, pointers):
        log.info(f"Callback: {pointers}")

    def changevariable(self, *args):
        """cuando cambia el modo de dibujo"""
        mode = self.modo.get()
        log.info(f"variable: {self.modo.get()}")
        config.set('General','default_mode', mode)
        config.save()

    def inicialize(self, width=800, height=600):
        """Inicializar la interfaz"""
        self.statusbar = ttk.Label(self.master, text="on the way ..",
                                   relief=SUNKEN, anchor=W)
        self.statusbar.pack(side=BOTTOM, fill=BOTH)
        
        self.controls = Frame(self.master, padx=5, pady=5)
        Label(self.controls, text='Pen Width:', font=('arial 9')).grid(row=0, column=0)
        self.slider = ttk.Scale(self.controls, from_=5, to=100,
                                command=self.changeW, orient=HORIZONTAL)
        self.slider.set(self.penwidth)
        self.slider.grid(row=0, column=1, ipadx=30)
        # controles de dibujo
        self.drawcontrols = Frame(self.controls, padx=5, pady=5)
        style = ttk.Style(self.drawcontrols)
        style.theme_use('default')
        style.configure('IndicatorOff.TRadiobutton',
                        indicatorrelief=FLAT,
                        indicatormargin=-10,
                        indicatordiameter=-1,
                        relief=RAISED,
                        focusthickness=0, highlightthickness=0, padding=5)
        style.map('IndicatorOff.TRadiobutton',
                  background=[('selected', 'white'), ('active', '#ececec')])
        
        MODES = [
            ("Select", "S", self.photo._move),
            ("Line", "L", self.photo._line),
            ("Pen", "P", self.photo._pen),
            ("Circle", "C", self.photo._circle),
            ("Rectangle", "R", self.photo._rectangle),
            ("Oval", "O", self.photo._oval),
            ("Arco", "A", self.photo._arco),
        ]
        # usar modo por defecto de configuracion.
        default_mode = config.get('General', 'default_mode', 'L')
        self.modo = StringVar(self.drawcontrols, "L")
        self.modo.trace('w', callback=self.changevariable)

        for text, mode, img in MODES:
            ttk.Radiobutton(self.drawcontrols, 
                            image=img, 
                            variable=self.modo,
                            value=mode, 
                            width=15,
                            style='IndicatorOff.TRadiobutton'
                            ).pack(side=LEFT)
        
        self.drawcontrols.grid(row=0, column=2, ipadx=30)
        self.controls.pack(side=TOP)
        
        # Canvas con tamaño de configuracion
        self.c = Canvas(self.master, 
                        width=width, 
                        height=height, 
                        bg=self.color_bg)
        self.c.pack(fill=BOTH, expand=True)
        
        # Menu
        menu = Menu(self.master)
        self.master.config(menu=menu)
        
        colormenu = Menu(menu)
        menu.add_cascade(label='Colors', menu=colormenu)
        colormenu.add_command(label='Brush Color', command=self.change_fg)
        colormenu.add_command(label='Background Color', command=self.change_bg)
        
        optionmenu = Menu(menu)
        menu.add_cascade(label='Options', menu=optionmenu)
        optionmenu.add_command(label='Clear Canvas', command=self.clear)
        optionmenu.add_separator()
        optionmenu.add_command(label='Save', command=self.save)
        optionmenu.add_command(label='Load', command=self.muestra)
        optionmenu.add_command(label='Config', command=self.canvasconfig)
        optionmenu.add_separator()
        optionmenu.add_command(label='Exit', command=self.master.destroy)


if __name__ == '__main__':
    root = Tk()
    App(root)
    root.title('Paint App')
    root.mainloop()