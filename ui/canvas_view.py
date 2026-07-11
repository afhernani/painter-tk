# -*- coding: utf-8 -*-
"""
CanvasView - Lienzo de dibujo con lógica de interacción.

Responsabilidades:
- Dibujar formas (línea, círculo, rectángulo, óvalo, arco, lápiz)
- Seleccionar objetos existentes
- Editar objetos seleccionados (mover, redimensionar)
- Mantener el registro de objetos dibujados
- Actualizar la barra de estado con coordenadas y mensajes

Se comunica con Toolbar (lee modo, color, grosor) y StatusBar
(envía mensajes de estado).
"""

import tkinter as tk
from tkinter import ttk
import logging

from utilitygraph import rectasCircunferencia, rectasRectangulo

log = logging.getLogger('Paint.CanvasView')


class CanvasView:
    """Lienzo de dibujo con gestión de objetos y selección."""
    
    def __init__(self, parent, toolbar, statusbar):
        """
        Crea el lienzo de dibujo.
        
        Args:
            parent: Widget padre
            toolbar: Instancia de Toolbar para leer el estado
            statusbar: Instancia de StatusBar para mostrar mensajes
        """
        self.toolbar = toolbar
        self.statusbar = statusbar
        
        # Referencias a objetos del canvas
        self.linea = None  # Objeto temporal durante el dibujo
        
        # Registro de objetos dibujados
        self.objetos = []
        self.objeto_seleccionado = None
        self.tipo_seleccionado = None
        self.tag_trazo_seleccionado = None
        self.trazos = {}
        self.contador_trazos = 0
        self.colores_originales = {}
        
        # Handles de control (círculos de edición)
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
        self._bbox_inicial = None
        
        # Variables temporales para dibujo
        self.lin_x = None
        self.lin_y = None
        self.old_x = None
        self.old_y = None
        
        # Selección múltiple con botón derecho
        self.selectBox = None
        self.originx = 0
        self.originy = 0
        
        # Crear el canvas
        self.canvas = tk.Canvas(
            parent,
            width=800,
            height=600,
            bg=self.toolbar.color_bg
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Binds de eventos
        self.canvas.bind('<ButtonPress-1>', self.__on_press)
        self.canvas.bind('<B1-Motion>', self.__on_motion)
        self.canvas.bind('<ButtonRelease-1>', self.__on_release)
        
        self.canvas.bind('<ButtonPress-3>', self.__select_start)
        self.canvas.bind('<B3-Motion>', self.__select_motion)
        self.canvas.bind('<ButtonRelease-3>', self.__select_release)
        
        self.canvas.bind('<Enter>', self.__on_enter)
        self.canvas.bind('<Leave>', self.__on_leave)
        
        log.info("CanvasView inicializado")
    
    # ================================================================
    # Eventos de cursor
    # ================================================================
    def __on_enter(self, event):
        self.canvas.configure(cursor="tcross")
    
    def __on_leave(self, event):
        self.canvas.configure(cursor="")
    
    # ================================================================
    # Handler de ButtonPress-1
    # ================================================================
    def __on_press(self, event):
        """Inicia una acción de dibujo o selección."""
        modo = self.toolbar.get_mode()
        
        if modo == 'S':
            self.__press_select_mode(event)
            return
        
        # Guardar posición inicial
        self.lin_x = event.x
        self.lin_y = e.y if False else event.y  # corrección abajo
        self.lin_x, self.lin_y = event.x, event.y
        
        # Crear objeto temporal según el modo
        if modo == 'L':
            self.linea = self.canvas.create_line(
                self.lin_x, self.lin_y, self.lin_x, self.lin_y
            )
        elif modo == 'P':
            pass  # El lápiz dibuja en motion
        elif modo == 'C':
            puntos = rectasCircunferencia(
                (self.lin_x, self.lin_y), (self.lin_x, self.lin_y)
            )
            self.linea = self.canvas.create_line(*puntos)
        elif modo == 'R':
            puntos = rectasRectangulo(
                (self.lin_x, self.lin_y), (self.lin_x, self.lin_y), n=4
            )
            self.linea = self.canvas.create_line(*puntos)
        elif modo == 'O':
            self.linea = self.canvas.create_oval(
                self.lin_x, self.lin_y, event.x, event.y
            )
        elif modo == 'A':
            self.linea = self.canvas.create_arc(
                self.lin_x, self.lin_y, event.x, event.y
        )
    
    # ================================================================
    # Handler de B1-Motion
    # ================================================================
    def __on_motion(self, event):
        """Actualiza el dibujo o mueve la selección."""
        # Actualizar barra de estado con coordenadas
        self.statusbar.set_text(f"{event.x} - {event.y}")
        
        modo = self.toolbar.get_mode()
        
        if modo == 'S':
            self.__motion_select_mode(event)
            return
        
        # Actualizar objeto temporal según el modo
        if modo == 'P':
            if self.old_x is not None and self.old_y is not None:
                self.canvas.create_line(
                    self.old_x, self.old_y, event.x, event.y,
                    width=self.toolbar.get_penwidth(),
                    fill=self.toolbar.color_fg,
                    capstyle=tk.ROUND,
                    smooth=False,
                    tags=('lapiz', 'trazo_actual')
                )
        elif modo == 'L' and self.linea is not None:
            self.canvas.coords(
                self.linea, self.lin_x, self.lin_y, event.x, event.y
            )
        elif modo == 'C' and self.linea is not None:
            puntos = rectasCircunferencia(
                (self.lin_x, self.lin_y), (event.x, event.y)
            )
            self.canvas.coords(self.linea, *puntos)
        elif modo == 'R' and self.linea is not None:
            puntos = rectasRectangulo(
                (self.lin_x, self.lin_y), (event.x, event.y), n=4
            )
            self.canvas.coords(self.linea, *puntos)
        elif modo == 'O' and self.linea is not None:
            self.canvas.coords(
                self.linea, self.lin_x, self.lin_y, event.x, event.y
            )
        elif modo == 'A' and self.linea is not None:
            self.canvas.coords(
                self.linea, self.lin_x, self.lin_y, event.x, event.y
            )
        
        self.old_x = event.x
        self.old_y = event.y
    
    # ================================================================
    # Handler de ButtonRelease-1
    # ================================================================
    def __on_release(self, event):
        """Finaliza el dibujo y registra el objeto."""
        self.old_x = None
        self.old_y = None
        
        modo = self.toolbar.get_mode()
        
        if modo == 'S':
            self.__release_select_mode(event)
            return
        
        color = self.toolbar.color_fg
        width = self.toolbar.get_penwidth()
        
        # Registrar objeto según el modo
        if modo == 'L' and self.linea is not None:
            x1, y1, x2, y2 = self.canvas.coords(self.linea)
            self.canvas.delete(self.linea)
            n_id = self.canvas.create_line(
                x1, y1, x2, y2,
                width=width, fill=color,
                capstyle=tk.ROUND, smooth=False, tags='Line'
            )
            self.objetos.append(n_id)
            self.colores_originales[n_id] = color
        
        elif modo == 'P':
            # Registrar todos los segmentos del lápiz
            segmentos = self.canvas.find_withtag('lapiz')
            for seg in segmentos:
                if seg not in self.objetos:
                    self.objetos.append(seg)
                    self.colores_originales[seg] = color
        
        elif modo == 'C' and self.linea is not None:
            puntos = self.canvas.coords(self.linea)
            self.canvas.delete(self.linea)
            n_id = self.canvas.create_line(
                *puntos, width=width, fill=color,
                capstyle=tk.ROUND, smooth=False, tags='Ellipse'
            )
            self.objetos.append(n_id)
            self.colores_originales[n_id] = color
        
        elif modo == 'R' and self.linea is not None:
            puntos = self.canvas.coords(self.linea)
            self.canvas.delete(self.linea)
            n_id = self.canvas.create_line(
                *puntos, width=width, fill=color,
                capstyle=tk.ROUND, smooth=False, tags='Rect'
            )
            self.objetos.append(n_id)
            self.colores_originales[n_id] = color
        
        elif modo == 'O' and self.linea is not None:
            puntos = self.canvas.coords(self.linea)
            self.canvas.delete(self.linea)
            n_id = self.canvas.create_oval(
                *puntos, width=width, outline=color,
                fill='', tags='Ellipse'
            )
            self.objetos.append(n_id)
            self.colores_originales[n_id] = color
        
        elif modo == 'A' and self.linea is not None:
            puntos = self.canvas.coords(self.linea)
            self.canvas.delete(self.linea)
            n_id = self.canvas.create_arc(
                *puntos, width=width, outline=color,
                fill='', tags='Arco'
            )
            self.objetos.append(n_id)
            self.colores_originales[n_id] = color
        
        self.lin_x = None
        self.lin_y = None
        self.linea = None
    
    # ================================================================
    # MODO SELECCIÓN - Press
    # ================================================================
    def __press_select_mode(self, event):
        """Inicia la selección o edición de un objeto."""
        # 1. ¿Click sobre un handle?
        handle_items = self.canvas.find_overlapping(
            event.x - 6, event.y - 6, event.x + 6, event.y + 6
        )
        for item in handle_items:
            tags = self.canvas.gettags(item)
            if 'handle_start' in tags:
                self.dragging_handle = 'start'
                return
            if 'handle_end' in tags:
                self.dragging_handle = 'end'
                return
            if 'handle_nw' in tags:
                self.dragging_handle = 'nw'
                self._bbox_inicial = self.canvas.bbox(self.objeto_seleccionado)
                return
            if 'handle_ne' in tags:
                self.dragging_handle = 'ne'
                self._bbox_inicial = self.canvas.bbox(self.objeto_seleccionado)
                return
            if 'handle_sw' in tags:
                self.dragging_handle = 'sw'
                self._bbox_inicial = self.canvas.bbox(self.objeto_seleccionado)
                return
            if 'handle_se' in tags:
                self.dragging_handle = 'se'
                self._bbox_inicial = self.canvas.bbox(self.objeto_seleccionado)
                return
        
        # 2. ¿Click sobre una figura existente?
        halo = 8
        encontrados = self.canvas.find_overlapping(
            event.x - halo, event.y - halo,
            event.x + halo, event.y + halo
        )
        candidatos = [i for i in encontrados if i in self.objetos]
        
        if candidatos:
            item_id = candidatos[-1]
            tags = self.canvas.gettags(item_id)
            
            # Detectar si es un trazo de lápiz
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
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            return
        
        # 3. Click en vacío → deseleccionar
        self.__deseleccionar_todo()
    
    # ================================================================
    # MODO SELECCIÓN - Motion
    # ================================================================
    def __motion_select_mode(self, event):
        """Mueve handles o el objeto seleccionado."""
        if self.dragging_handle:
            if self.dragging_handle in ('start', 'end'):
                self.__mover_handle_linea(event)
            elif self.dragging_handle in ('nw', 'ne', 'sw', 'se'):
                self.__redimensionar_bbox(event)
            return
        
        if self.dragging_line and self.objeto_seleccionado is not None:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            if self.tag_trazo_seleccionado:
                for seg_id in self.trazos[self.tag_trazo_seleccionado]:
                    self.canvas.move(seg_id, dx, dy)
            else:
                self.canvas.move(self.objeto_seleccionado, dx, dy)
            
            # Mover también los handles
            for h in [self.handle_start, self.handle_end,
                      self.handle_nw, self.handle_ne,
                      self.handle_sw, self.handle_se]:
                if h is not None:
                    self.canvas.move(h, dx, dy)
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def __release_select_mode(self, event):
        """Finaliza la edición por selección."""
        self.dragging_handle = None
        self.dragging_line = False
        self._bbox_inicial = None
    
    # ================================================================
    # SELECCIÓN DE OBJETOS
    # ================================================================
    def __seleccionar_objeto(self, item_id):
        """Selecciona un objeto y muestra sus handles."""
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        self.__deseleccionar_todo()
        
        self.objeto_seleccionado = item_id
        self.tipo_seleccionado = self.canvas.type(item_id)
        self.tag_trazo_seleccionado = None
        
        tags = self.canvas.gettags(item_id)
        log.info(f'Tags del objeto {item_id}: {tags}')
        
        # Resaltar visualmente
        color_original = self.colores_originales.get(
            item_id, self.toolbar.color_fg
        )
        if self.tipo_seleccionado == 'line':
            self.canvas.itemconfig(item_id, fill='red')
        else:
            self.canvas.itemconfig(item_id, outline='red')
        
        # Mostrar handles según el tipo
        if self.tipo_seleccionado == 'line':
            self.__mostrar_handles_linea(item_id)
        else:
            self.__mostrar_handles_bbox(item_id)
        
        self.statusbar.set_text(
            f"Objeto {item_id} ({self.tipo_seleccionado}) seleccionado"
        )
    
    def __seleccionar_trazo_lapiz(self, tag_trazo):
        """Selecciona todos los segmentos de un trazo de lápiz."""
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        self.__deseleccionar_todo()
        
        self.tag_trazo_seleccionado = tag_trazo
        segmentos = self.trazos.get(tag_trazo, [])
        
        if segmentos:
            self.objeto_seleccionado = segmentos[0]
            for seg_id in segmentos:
                self.canvas.itemconfig(seg_id, fill='red')
        
        self.statusbar.set_text(
            f"Trazo {tag_trazo} seleccionado ({len(segmentos)} segmentos)"
        )
    
    def __mostrar_handles_linea(self, item_id):
        """Muestra 2 handles azules en los extremos de una línea."""
        coords = self.canvas.coords(item_id)
        if len(coords) < 4:
            return
        
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        self.canvas.delete('handle')
        
        self.handle_start = self.canvas.create_oval(
            x1 - 6, y1 - 6, x1 + 6, y1 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_start')
        )
        self.handle_end = self.canvas.create_oval(
            x2 - 6, y2 - 6, x2 + 6, y2 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_end')
        )
    
    def __mostrar_handles_bbox(self, item_id):
        """Muestra 4 handles verdes en las esquinas del bbox."""
        bbox = self.canvas.bbox(item_id)
        if bbox is None:
            return
        
        x1, y1, x2, y2 = bbox
        self.canvas.delete('handle')
        
        self.handle_nw = self.canvas.create_oval(
            x1 - 6, y1 - 6, x1 + 6, y1 + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_nw')
        )
        self.handle_ne = self.canvas.create_oval(
            x2 - 6, y1 - 6, x2 + 6, y1 + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_ne')
        )
        self.handle_sw = self.canvas.create_oval(
            x1 - 6, y2 - 6, x1 + 6, y2 + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_sw')
        )
        self.handle_se = self.canvas.create_oval(
            x2 - 6, y2 - 6, x2 + 6, y2 + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_se')
        )
    
    # ================================================================
    # EDICIÓN
    # ================================================================
    def __mover_handle_linea(self, event):
        """Mueve un extremo de una línea."""
        coords = self.canvas.coords(self.objeto_seleccionado)
        if len(coords) < 4:
            return
        
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        
        if self.dragging_handle == 'start':
            self.canvas.coords(
                self.objeto_seleccionado, event.x, event.y, x2, y2
            )
            self.canvas.coords(
                self.handle_start,
                event.x - 6, event.y - 6, event.x + 6, event.y + 6
            )
        elif self.dragging_handle == 'end':
            self.canvas.coords(
                self.objeto_seleccionado, x1, y1, event.x, event.y
            )
            self.canvas.coords(
                self.handle_end,
                event.x - 6, event.y - 6, event.x + 6, event.y + 6
            )
    
    def __redimensionar_bbox(self, event):
        """Redimensiona una figura manteniendo fija la esquina opuesta."""
        if self._bbox_inicial is None:
            return
        
        x1, y1, x2, y2 = self._bbox_inicial
        
        if self.dragging_handle == 'nw':
            x1, y1 = event.x, event.y
        elif self.dragging_handle == 'ne':
            x2, y1 = event.x, event.y
        elif self.dragging_handle == 'sw':
            x1, y2 = event.x, event.y
        elif self.dragging_handle == 'se':
            x2, y2 = event.x, event.y
        
        # Aplicar según el tipo de figura
        tags = self.canvas.gettags(self.objeto_seleccionado)
        
        if 'Ellipse' in tags:
            puntos = rectasCircunferencia((x1, y1), (x2, y2))
            self.canvas.coords(self.objeto_seleccionado, *puntos)
        elif 'Rect' in tags:
            puntos = rectasRectangulo((x1, y1), (x2, y2), n=4)
            self.canvas.coords(self.objeto_seleccionado, *puntos)
        elif self.tipo_seleccionado == 'oval':
            self.canvas.coords(
                self.objeto_seleccionado, x1, y1, x2, y2
            )
        elif self.tipo_seleccionado == 'arc':
            self.canvas.coords(
                self.objeto_seleccionado, x1, y1, x2, y2
            )
        
        # Actualizar posición de los handles
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        if self.handle_nw:
            self.canvas.coords(
                self.handle_nw, x_min - 6, y_min - 6, x_min + 6, y_min + 6
            )
        if self.handle_ne:
            self.canvas.coords(
                self.handle_ne, x_max - 6, y_min - 6, x_max + 6, y_min + 6
            )
        if self.handle_sw:
            self.canvas.coords(
                self.handle_sw, x_min - 6, y_max - 6, x_min + 6, y_max + 6
            )
        if self.handle_se:
            self.canvas.coords(
                self.handle_se, x_max - 6, y_max - 6, x_max + 6, y_max + 6
            )
    
    # ================================================================
    # DESELECCIÓN Y RESTAURACIÓN
    # ================================================================
    def __restaurar_apariencia(self, item_id):
        """Restaura el color original de un objeto."""
        try:
            if self.tag_trazo_seleccionado:
                for seg_id in self.trazos.get(
                    self.tag_trazo_seleccionado, []
                ):
                    color = self.colores_originales.get(
                        seg_id, self.toolbar.color_fg
                    )
                    self.canvas.itemconfig(seg_id, fill=color)
            elif self.tipo_seleccionado == 'line':
                color = self.colores_originales.get(
                    item_id, self.toolbar.color_fg
                )
                self.canvas.itemconfig(item_id, fill=color)
            else:
                color = self.colores_originales.get(
                    item_id, self.toolbar.color_fg
                )
                self.canvas.itemconfig(item_id, outline=color)
        except tk.TclError:
            pass
    
    def __deseleccionar_todo(self):
        """Elimina handles y resetea el estado de selección."""
        if self.objeto_seleccionado is not None:
            self.__restaurar_apariencia(self.objeto_seleccionado)
        
        self.canvas.delete('handle')
        
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
    # SELECCIÓN MÚLTIPLE (botón derecho)
    # ================================================================
    def __select_start(self, event):
        self.originx = self.canvas.canvasx(event.x)
        self.originy = self.canvas.canvasy(event.y)
        self.selectBox = self.canvas.create_rectangle(
            self.originx, self.originy, self.originx, self.originy
        )
    
    def __select_motion(self, event):
        xnew = self.canvas.canvasx(event.x)
        ynew = self.canvas.canvasy(event.y)
        
        if xnew < self.originx and ynew < self.originy:
            self.canvas.coords(
                self.selectBox, xnew, ynew, self.originx, self.originy
            )
        elif xnew < self.originx:
            self.canvas.coords(
                self.selectBox, xnew, self.originy, self.originx, ynew
            )
        elif ynew < self.originy:
            self.canvas.coords(
                self.selectBox, self.originx, ynew, xnew, self.originy
            )
        else:
            self.canvas.coords(
                self.selectBox, self.originx, self.originy, xnew, ynew
            )
    
    def __select_release(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.selectBox)
        self.canvas.delete(self.selectBox)
        
        selected = []
        for i in self.canvas.find_enclosed(x1, y1, x2, y2):
            log.info(f"Tipo seleccionado: {self.canvas.type(i)}")
            self.canvas.itemconfig(i, {'state': tk.DISABLED})
            selected.append(i)
        
        log.info(f"Objetos seleccionados: {selected}")
    
    # ================================================================
    # Métodos públicos para App
    # ================================================================
    def clear(self):
        """Limpia el canvas y resetea el registro de objetos."""
        self.canvas.delete(tk.ALL)
        self.objetos.clear()
        self.trazos.clear()
        self.colores_originales.clear()
        self.contador_trazos = 0
        log.info("Canvas limpiado")
    
    def load_from_svg(self, filepath):
        """
        Carga objetos desde un archivo SVG.
        
        Args:
            filepath: Ruta al archivo SVG
        
        Returns:
            int: Número de objetos cargados
        """
        from svgcanvas import loadSvg
        
        self.canvas.delete(tk.ALL)
        self.objetos.clear()
        self.trazos.clear()
        self.colores_originales.clear()
        
        try:
            canvas_ref, ids_creados = loadSvg(filepath, self.canvas)
            
            for item_id in ids_creados:
                if item_id not in self.objetos:
                    self.objetos.append(item_id)
                    self.colores_originales[item_id] = self.toolbar.color_fg
            
            log.info(f"Cargados {len(ids_creados)} objetos desde {filepath}")
            return len(ids_creados)
        except Exception as e:
            log.error(f"Error cargando SVG: {e}")
            return 0
    
    def save_to_svg(self, filepath):
        """
        Guarda el canvas en un archivo SVG.
        
        Args:
            filepath: Ruta del archivo de salida
        """
        from canvasvg import saveall
        saveall(filename=filepath, canvas=self.canvas)
        log.info(f"Guardado en {filepath}")