# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import simpledialog, colorchooser, font
import math, copy
import logging
from utilitygraph import rectasCircunferencia, rectasRectangulo
from geometry.point import Punto
from geometry.pointshape import PointShape
from geometry.line import Linea
from geometry.circle import Circulo
from geometry.rectangle import Rectangulo
from geometry.ellipse import Elipse
from geometry.arco import Arco
from geometry.polyline import Polyline
from geometry.polygon import Poligono
from geometry.texto import Texto
from storage import save_project, load_project
from storage.json_storage import SHAPE_FACTORY, _reconstruir_puntos
from configmanager import config

log = logging.getLogger('Paint.CanvasView')


class CanvasView(tk.Canvas):
    """Canvas de dibujo integrado con el modelo geometry"""
    
    def __init__(self, parent, color_bg='white', width=800, height=600):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=color_bg,
            highlightthickness=0
        )
        self._mode = None
        self.shapes = []
        self.shape_seleccionada = None
        self.tag_trazo_seleccionado = None
        self.trazos = {}
        self.contador_trazos = 0
        self.linea_preview = None
        self.linea_p1 = None
        
        # Estado para modo Polyline
        self.polyline_puntos = []
        self.polyline_segmentos_ids = []
        self.polyline_preview_id = None
        
        # Estado para modo Polígono
        self.poligono_centro = None
        self.poligono_preview_id = None
        self.lados_poligono = None
        
        # Estado para modo Círculo
        self.circulo_centro = None
        self.circulo_preview_id = None
        
        # Estado para modo Rectángulo
        self.rectangulo_centro = None
        self.rectangulo_preview_id = None
        
        # Estado para modo Elipse
        self.elipse_centro = None
        self.elipse_preview_id = None
        
        # Estado para modo Arco
        self.arco_centro = None
        self.arco_p1 = None
        self.arco_radio = 0.0
        self.arco_angulo_inicio = 0.0
        self.arco_estado = 0
        self.arco_preview_id = None
        
        # Estado para modo Texto
        self.texto_preview_id = None
        self.texto_posicion = None
        
        # Modo duplicar
        self._colocando_duplicado = False
        self._figura_a_colocar = None
        self._id_fantasma = None
        
        self.lin_x = None
        self.lin_y = None
        self.old_x = None
        self.old_y = None
        self.linea = None
        self.puntos_trazo = []
        
        # Handles
        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        self.handles_polyline = []
        self.polyline_segmento_drag = None
        self.handle_circulo_centro = None
        self.handle_circulo_perimetro = None
        self.handle_poligono_centro = None
        self.handles_poligono = []
        self.handle_elipse_centro = None
        self.handle_elipse_eje_x = None
        self.handle_elipse_eje_y = None
        self.handle_arco_centro = None
        self.handle_arco_inicio = None
        self.handle_arco_final = None
        
        self.dragging_handle = None
        self.dragging_shape = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self._bbox_inicial = None
        self._on_status_message = None
        
        # Constante para tamaño de handles
        self.TAMANO_BASE = 12
        
        # Zoom y paneo (ENFOQUE MANUAL)
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.MIN_ZOOM = 0.1
        self.MAX_ZOOM = 10.0
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # Historial Undo/Redo
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50
        
        # Bindings
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_motion)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Enter>', lambda e: self._actualizar_cursor())
        self.bind('<Leave>', lambda e: self.configure(cursor=''))
        self.bind('<Delete>', lambda e: self.eliminar_shape_seleccionada())
        self.bind('<ButtonPress-3>', self._on_right_click)
        self.bind('<Escape>', lambda e: self._cancelar_dibujo())
        self.bind('<Motion>', self._on_mouse_move)
        self.bind('<Double-Button-1>', self._on_double_click)
        self.master.bind('<Control-z>', lambda e: self.undo())
        self.master.bind('<Control-y>', lambda e: self.redo())
        
        # Bindings para pan y zoom
        self._add_pan_zoom_bindings()
        
        self.focus_set()
        self._save_state()
        log.info("CanvasView inicializado")
    
    # ================================================================
    # CONVERSIÓN DE COORDENADAS (ENFOQUE MANUAL)
    # ================================================================
    
    def screen_to_world(self, sx, sy):
        """Convierte coordenadas de pantalla a coordenadas del mundo"""
        wx = (sx - self.pan_x) / self.zoom
        wy = (sy - self.pan_y) / self.zoom
        return wx, wy
    
    def world_to_screen(self, wx, wy):
        """Convierte coordenadas del mundo a coordenadas de pantalla"""
        sx = wx * self.zoom + self.pan_x
        sy = wy * self.zoom + self.pan_y
        return sx, sy
    
    def _get_world_coords(self, e):
        """Convierte coordenadas de pantalla a coordenadas del mundo"""
        return self.screen_to_world(e.x, e.y)
    
    def _make_world_event(self, e):
        """Crea un evento con coordenadas transformadas al mundo"""
        wx, wy = self._get_world_coords(e)
        
        class FakeEvent:
            pass
        
        fake = FakeEvent()
        fake.x = wx
        fake.y = wy
        fake.x_root = getattr(e, 'x_root', 0)
        fake.y_root = getattr(e, 'y_root', 0)
        fake.num = getattr(e, 'num', 1)
        fake.delta = getattr(e, 'delta', 0)
        fake.widget = getattr(e, 'widget', self)
        fake.type = getattr(e, 'type', None)
        
        return fake
    
    # ================================================================
    # PAN Y ZOOM (ENFOQUE MANUAL)
    # ================================================================
    
    def _add_pan_zoom_bindings(self):
        """Añade bindings para pan (botón central) y zoom (rueda)"""
        self.bind("<Button-2>", self._pan_start)
        self.bind("<B2-Motion>", self._pan_move)
        self.bind("<ButtonRelease-2>", self._pan_end)
        self.bind("<MouseWheel>", self._zoom)
        self.bind("<Button-5>", self._zoom)
        self.bind("<Button-4>", self._zoom)
    
    def _pan_start(self, event):
        """Inicia el pan"""
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self.config(cursor="fleur")
    
    def _pan_move(self, event):
        """Mueve el canvas durante el pan"""
        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        
        # Actualizar variables de paneo
        self.pan_x += dx
        self.pan_y += dy
        
        # Mover todos los items del canvas
        self.move("all", dx, dy)
    
    def _pan_end(self, event):
        """Finaliza el pan"""
        self.config(cursor="")
        if self.shape_seleccionada:
            self.after(10, self._actualizar_tamaño_handles)
    
    def _zoom(self, event):
        """Zoom con la rueda del ratón centrado en el cursor"""
        scale_factor = 1.1
        
        if hasattr(event, 'delta'):
            zoom_in = event.delta > 0
        else:
            zoom_in = event.num == 4
        
        factor = scale_factor if zoom_in else 1 / scale_factor
        nuevo_zoom = self.zoom * factor
        
        if self.MIN_ZOOM <= nuevo_zoom <= self.MAX_ZOOM:
            # Coordenadas del cursor en el mundo (antes del zoom)
            wx, wy = self.screen_to_world(event.x, event.y)
            
            # Actualizar zoom
            self.zoom = nuevo_zoom
            
            # Recalcular pan para que el punto bajo el cursor siga ahí
            self.pan_x = event.x - wx * self.zoom
            self.pan_y = event.y - wy * self.zoom
            
            # Redibujar todo con el nuevo zoom
            self._redraw_all_with_zoom()
            
            # Actualizar handles si hay algo seleccionado
            if self.shape_seleccionada:
                self._actualizar_tamaño_handles()
        
        log.info(f"Zoom: {self.zoom:.2f}, pan: ({self.pan_x:.1f}, {self.pan_y:.1f})")
    
    def _actualizar_tamaño_handles(self):
        """Reajusta el tamaño de los handles según el zoom"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        self._deseleccionar_todo()
        self.shape_seleccionada = shape
        self._seleccionar_shape(shape)
        self.update_idletasks()
    
    def _redraw_all_with_zoom(self):
        """Redibuja todas las figuras aplicando el zoom actual"""
        shape_seleccionada = self.shape_seleccionada
        
        # Borrar todo del canvas
        self.delete('all')
        
        # Redibujar todas las figuras
        for shape in self.shapes:
            shape.dibujar_en(self)
        
        # Restaurar selección
        if shape_seleccionada:
            self.shape_seleccionada = shape_seleccionada
            self._seleccionar_shape(shape_seleccionada)
    
    def _get_handle_radio(self):
        """Calcula el radio del handle según el zoom"""
        zoom = getattr(self, 'zoom', 1.0)
        return (self.TAMANO_BASE / 2) / zoom
    
    # ================================================================
    # CURSOR Y MODO
    # ================================================================
    
    def _actualizar_cursor(self):
        """Actualiza el cursor según el modo"""
        mode = self._get_mode()
        if mode == 'S':
            self.configure(cursor='cross')
        else:
            self.configure(cursor='tcross')
    
    def _get_mode(self):
        return self._mode
    
    def _set_mode(self, mode):
        self._mode = mode
        self._actualizar_cursor()
        log.info(f"Modo cambiado a {mode}")
    
    def _get_width(self):
        return 2.0
    
    def _get_color_fg(self):
        return 'black'
    
    def set_status_callback(self, callback):
        self._on_status_message = callback
    
    def _set_status(self, text):
        if self._on_status_message:
            self._on_status_message(text)
    
    def _find_shape_by_id(self, canvas_id):
        for shape in self.shapes:
            if shape._canvas_id == canvas_id:
                return shape
            if hasattr(shape, '_canvas_ids') and canvas_id in shape._canvas_ids:
                return shape
        return None
    
    def _get_polygon_sides(self):
        log.info(f"_get_polygon_sides:")
        return self.lados_poligono
    
    # ================================================================
    # MOUSE MOVE
    # ================================================================
    
    def _on_mouse_move(self, e):
        """Actualiza la línea preview para que siga al cursor"""
        e = self._make_world_event(e)
        self._set_status(f"{e.x, e.y}")
        mode = self._get_mode()
        
        if mode == 'L' and self.linea_p1 is not None and self.linea_preview is not None:
            self.coords(self.linea_preview, self.linea_p1.x, self.linea_p1.y, e.x, e.y)
            self._set_status(f"Línea: ({self.linea_p1.x}, {self.linea_p1.y}) -> ({e.x}, {e.y})")
        
        if mode == 'Pl' and self.polyline_puntos and self.polyline_preview_id is not None:
            ultimo_punto = self.polyline_puntos[-1]
            self.coords(self.polyline_preview_id, ultimo_punto.x, ultimo_punto.y, e.x, e.y)
            return
        
        if mode == 'G' and self.poligono_centro is not None and self.poligono_preview_id is not None:
            radio = math.hypot(e.x - self.poligono_centro.x, e.y - self.poligono_centro.y)
            coords = []
            self.lados_poligono = self._get_polygon_sides()
            angulo_paso = 2 * math.pi / self.lados_poligono
            offset = -math.pi / 2
            for i in range(self.lados_poligono):
                theta = i * angulo_paso + offset
                coords.append(self.poligono_centro.x + radio * math.cos(theta))
                coords.append(self.poligono_centro.y + radio * math.sin(theta))
            self.coords(self.poligono_preview_id, *coords)
            return
        
        if mode == 'C' and self.circulo_centro is not None and self.circulo_preview_id is not None:
            radio = math.hypot(e.x - self.circulo_centro.x, e.y - self.circulo_centro.y)
            x1 = self.circulo_centro.x - radio
            y1 = self.circulo_centro.y - radio
            x2 = self.circulo_centro.x + radio
            y2 = self.circulo_centro.y + radio
            self.coords(self.circulo_preview_id, x1, y1, x2, y2)
            return
        
        if mode == 'R' and self.rectangulo_centro is not None and self.rectangulo_preview_id is not None:
            x1 = 2 * self.rectangulo_centro.x - e.x
            y1 = 2 * self.rectangulo_centro.y - e.y
            self.coords(self.rectangulo_preview_id, x1, y1, e.x, e.y)
            return
        
        if mode == 'E' and self.elipse_centro is not None and self.elipse_preview_id is not None:
            rx = abs(e.x - self.elipse_centro.x)
            ry = abs(e.y - self.elipse_centro.y)
            x1 = self.elipse_centro.x - rx
            y1 = self.elipse_centro.y - ry
            x2 = self.elipse_centro.x + rx
            y2 = self.elipse_centro.y + ry
            self.coords(self.elipse_preview_id, x1, y1, x2, y2)
            return
        
        if mode == 'A' and self.arco_estado == 1:
            if self.arco_preview_id is not None:
                self.delete(self.arco_preview_id)
            r = self.arco_centro.distancia(Punto(e.x, e.y))
            self.arco_preview_id = self.create_oval(
                self.arco_centro.x - r, self.arco_centro.y - r,
                self.arco_centro.x + r, self.arco_centro.y + r,
                outline='gray', dash=(4, 4)
            )
            return
        
        if mode == 'A' and self.arco_estado == 2:
            if self.arco_preview_id is not None:
                self.delete(self.arco_preview_id)
            angulo_actual = math.degrees(math.atan2(
                -(e.y - self.arco_centro.y),
                e.x - self.arco_centro.x
            ))
            extension = angulo_actual - self.arco_angulo_inicio
            bbox = [
                self.arco_centro.x - self.arco_radio, self.arco_centro.y - self.arco_radio,
                self.arco_centro.x + self.arco_radio, self.arco_centro.y + self.arco_radio
            ]
            self.arco_preview_id = self.create_arc(
                *bbox,
                start=self.arco_angulo_inicio,
                extent=extension,
                style=tk.ARC,
                outline='gray',
                width=2
            )
            return
        
        if mode == 'T':
            if self.texto_preview_id is not None:
                self.delete(self.texto_preview_id)
            self.texto_preview_id = self.create_oval(
                e.x - 3, e.y - 3, e.x + 3, e.y + 3,
                fill='gray', outline=''
            )
            self._set_status(f"Texto: click para insertar en ({e.x}, {e.y})")
            return
    
    def _move_elemento_duplicado(self, e):
        """Mover la figura fantasma duplicada siguiendo al raton"""
        if not getattr(self, '_colocando_duplicado', False) or not self._figura_a_colocar:
            return
        
        shape = self._figura_a_colocar
        
        if self._id_fantasma is not None:
            if isinstance(self._id_fantasma, list):
                for fid in self._id_fantasma:
                    self.delete(fid)
            else:
                self.delete(self._id_fantasma)
        
        if isinstance(shape, Texto):
            shape.posicion = Punto(e.x, e.y)
        elif isinstance(shape, PointShape):
            if hasattr(shape, 'punto'):
                shape.punto = Punto(e.x, e.y)
            elif hasattr(shape, 'posicion'):
                shape.posicion = Punto(e.x, e.y)
        elif isinstance(shape, (Circulo, Arco)):
            shape.centro = Punto(e.x, e.y)
        elif isinstance(shape, Poligono):
            shape.centro = Punto(e.x, e.y)
        elif isinstance(shape, Elipse):
            shape.centro = Punto(e.x, e.y)
        elif isinstance(shape, Polyline):
            if shape.puntos:
                dx = e.x - shape.puntos[0].x
                dy = e.y - shape.puntos[0].y
                shape.mover(dx, dy)
        elif isinstance(shape, Rectangulo):
            if hasattr(shape, 'centro'):
                shape.centro = Punto(e.x, e.y)
            else:
                cx = (shape.p1.x + shape.p2.x) / 2
                cy = (shape.p1.y + shape.p2.y) / 2
                dx = e.x - cx
                dy = e.y - cy
                shape.p1 = Punto(shape.p1.x + dx, shape.p1.y + dy)
                shape.p2 = Punto(shape.p2.x + dx, shape.p2.y + dy)
        elif isinstance(shape, Linea):
            dx = e.x - shape.p1.x
            dy = e.y - shape.p1.y
            shape.p1 = Punto(e.x, e.y)
            shape.p2 = Punto(shape.p2.x + dx, shape.p2.y + dy)
        
        self._id_fantasma = shape.dibujar_en(self)
        
        try:
            if isinstance(self._id_fantasma, list):
                for fid in self._id_fantasma:
                    self.itemconfig(fid, dash=(4, 4), outline='gray')
            else:
                self.itemconfig(self._id_fantasma, dash=(4, 4))
                if hasattr(shape, 'relleno'):
                    self.itemconfig(self._id_fantasma, outline='gray', fill='')
                else:
                    self.itemconfig(self._id_fantasma, fill='gray')
        except tk.TclError:
            pass
    
    # ================================================================
    # PRESS
    # ================================================================
    
    def _on_press(self, e):
        """Al presionar el boton izquierdo del ratón"""
        e = self._make_world_event(e)
        self.focus_set()
        mode = self._get_mode()
        
        if self._iniciar_logica_colocar_duplicado(e):
            return
        
        log.info("_on_press: seguimos")
        
        if mode != 'S':
            self._deseleccionar_todo()
        
        if mode == 'S':
            self._press_select_mode(e)
            return
        
        if mode == 'L':
            if self.linea_p1 is None:
                self.linea_p1 = Punto(e.x, e.y)
                self.linea_preview = self.create_line(
                    e.x, e.y, e.x, e.y,
                    dash=(4, 2),
                    fill='gray',
                    width=1
                )
                self._set_status("Línea: mueve el cursor y haz click para el punto final (Esc para cancelar)")
            else:
                self._finalizar_linea(e.x, e.y)
            return
        
        if mode == 'G':
            if self.poligono_centro is None:
                self.poligono_centro = Punto(e.x, e.y)
                self.poligono_preview_id = self.create_polygon(
                    e.x, e.y, e.x, e.y, e.x, e.y,
                    outline='gray', width=1, fill=''
                )
                self._set_status(f"Polígono: centro en ({e.x}, {e.y}). Mueve el ratón y haz click para el radio")
            else:
                self._finalizar_poligono(e.x, e.y)
            return
        
        if mode == 'Pt':
            width = self._get_width()
            color = self._get_color_fg()
            punto = Punto(e.x, e.y)
            shape = PointShape(punto, radio=max(2.0, width/2), color=color, grosor=width)
            shape._tag = 'Point'
            shape.dibujar_en(self)
            self.shapes.append(shape)
            self._save_state()
            log.info(f"Punto creado: {shape}")
            return
        
        if mode == 'Pl':
            self._añadir_punto_polyline(e.x, e.y)
            return
        
        if mode == 'C':
            if self.circulo_centro is None:
                self.circulo_centro = Punto(e.x, e.y)
                self.circulo_preview_id = self.create_oval(
                    e.x, e.y, e.x, e.y,
                    outline='gray', width=1, fill=''
                )
                self._set_status(f"Círculo: centro en ({e.x}, {e.y}). Mueve el ratón y haz click para el radio")
            else:
                self._finalizar_circulo(e.x, e.y)
            return
        
        if mode == 'R':
            if self.rectangulo_centro is None:
                self.rectangulo_centro = Punto(e.x, e.y)
                self.rectangulo_preview_id = self.create_rectangle(
                    e.x, e.y, e.x, e.y, outline='gray', width=1, fill=''
                )
                self._set_status("Rectángulo: centro establecido. Mueve y haz click para la esquina.")
            else:
                self._finalizar_rectangulo(e.x, e.y)
            return
        
        if mode == 'E':
            if self.elipse_centro is None:
                self.elipse_centro = Punto(e.x, e.y)
                self.elipse_preview_id = self.create_oval(
                    e.x, e.y, e.x, e.y, outline='gray', width=1, fill=''
                )
                self._set_status("Elipse: centro establecido. Mueve y haz click para el borde.")
            else:
                self._finalizar_elipse(e.x, e.y)
            return
        
        if mode == 'A':
            if self.arco_estado == 0:
                self.arco_centro = Punto(e.x, e.y)
                self.arco_estado = 1
                self._set_status("Arco: centro establecido. Click para el punto inicial (radio + ángulo).")
            elif self.arco_estado == 1:
                self.arco_p1 = Punto(e.x, e.y)
                self.arco_radio = self.arco_centro.distancia(self.arco_p1)
                self.arco_angulo_inicio = math.degrees(math.atan2(
                    -(self.arco_p1.y - self.arco_centro.y),
                    self.arco_p1.x - self.arco_centro.x
                ))
                self.arco_estado = 2
                self._set_status("Arco: punto inicial establecido. Click para el punto final.")
            elif self.arco_estado == 2:
                self._finalizar_arco(e.x, e.y)
            return
        
        if mode == 'T':
            from tkinter import simpledialog
            if self.texto_preview_id is not None:
                self.delete(self.texto_preview_id)
                self.texto_preview_id = None
            
            texto_ingresado = simpledialog.askstring(
                "Insertar Texto",
                "Escribe el texto:",
                initialvalue="Texto"
            )
            
            if texto_ingresado:
                width = self._get_width()
                color = self._get_color_fg()
                tamaño = int(max(12, width*4))
                shape = Texto(
                    posicion=Punto(e.x, e.y),
                    texto=texto_ingresado,
                    color=color,
                    tamaño=tamaño
                )
                shape._tag = 'Texto'
                shape.dibujar_en(self)
                self.shapes.append(shape)
                self._save_state()
                log.info(f"Texto creado: {shape}")
            return
        
        if mode == 'P':
            self.puntos_trazo = [Punto(e.x, e.y)]
            self.old_x, self.old_y = e.x, e.y
            return
    
    def _iniciar_logica_colocar_duplicado(self, e):
        """Iniciar Lógica para colocar duplicado en la posicion del click"""
        if getattr(self, '_colocando_duplicado', False) and self._figura_a_colocar:
            shape = self._figura_a_colocar
            
            self._move_elemento_duplicado(e)
            
            if self._id_fantasma is not None:
                if isinstance(self._id_fantasma, list):
                    for fid in self._id_fantasma:
                        self.delete(fid)
                else:
                    self.delete(self._id_fantasma)
            
            shape.dibujar_en(self)
            self.shapes.append(shape)
            
            self._save_state()
            self._seleccionar_shape(shape)
            
            self._colocando_duplicado = False
            self._figura_a_colocar = None
            self._id_fantasma = None
            self._actualizar_cursor()
            
            log.info(f"Duplicado colocado con éxito en ({e.x}, {e.y})")
            return True
        
        return False
    
    def _on_right_click(self, e):
        """Click derecho: finaliza la polyline en progreso"""
        e = self._make_world_event(e)
        log.info(f"_on_right_click: {e.x}, {e.y}")
        mode = self._get_mode()
        self._cancelar_duplicado()
        
        if mode == 'Pl' and len(self.polyline_puntos) >= 2:
            self._finalizar_polyline()
        elif mode == 'Pl' and len(self.polyline_puntos) == 1:
            self._cancelar_polyline()
            self._set_status("Polyline cancelada: se necesitan al menos 2 puntos")
        
        if mode == 'S':
            halo = 8
            encontrados = self.find_overlapping(e.x - halo, e.y - halo, e.x + halo, e.y + halo)
            for item_id in reversed(encontrados):
                tags = self.gettags(item_id)
                if 'handle' in tags:
                    continue
                shape = self._find_shape_by_id(item_id)
                if shape is not None:
                    self._seleccionar_shape(shape)
                    self._mostrar_menu_contextual(shape, e)
                    return
            
            self._deseleccionar_todo()
    
    # ================================================================
    # MOTION
    # ================================================================
    
    def _on_motion(self, e):
        e = self._make_world_event(e)
        log.info(f"_on_motion: motion {e.x} - {e.y}")
        self._set_status(f"{e.x} - {e.y}")
        mode = self._get_mode()
        
        if mode == 'S':
            self._motion_select_mode(e)
            return
        
        if mode in ('R', 'E', 'A'):
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        
        if mode == 'P':
            if self.old_x is not None and self.old_y is not None:
                self.create_line(
                    self.old_x, self.old_y, e.x, e.y,
                    width=width, fill=color,
                    capstyle=tk.ROUND, smooth=False,
                    tags='trazo_actual'
                )
            self.puntos_trazo.append(Punto(e.x, e.y))
            self.old_x = e.x
            self.old_y = e.y
    
    # ================================================================
    # RELEASE
    # ================================================================
    
    def _on_release(self, e):
        e = self._make_world_event(e)
        self.old_x = None
        self.old_y = None
        mode = self._get_mode()
        
        if mode == 'S':
            if self.dragging_shape or self.dragging_handle:
                self._save_state()
            self.dragging_shape = False
            self.dragging_handle = None
            self._release_select_mode(e)
            return
        
        if mode == 'L':
            return
        
        if mode == 'Pl':
            return
        
        if mode in ('R', 'E', 'A'):
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        
        if mode == 'P' and len(self.puntos_trazo) > 1:
            self.delete('trazo_actual')
            shape = Polyline(self.puntos_trazo, color=color, grosor=width)
            tag_trazo = f'trazo_{self.contador_trazos}'
            self.contador_trazos += 1
            shape._tag = tag_trazo
            shape.dibujar_en(self)
            self.shapes.append(shape)
            self.trazos[tag_trazo] = shape
            log.info(f"Polyline creada: {tag_trazo}")
            self.puntos_trazo = []
        
        elif mode == 'A' and self.linea is not None:
            self.delete(self.linea)
            p1 = Punto(min(self.lin_x, e.x), min(self.lin_y, e.y))
            p2 = Punto(max(self.lin_x, e.x), max(self.lin_y, e.y))
            dx = e.x - self.lin_x
            dy = e.y - self.lin_y
            angulo_inicio = math.degrees(math.atan2(-dy, dx))
            shape = Arco(p1, p2, inicio=angulo_inicio, extension=90,
                         color=color, grosor=width)
            shape._tag = 'Arco'
            shape.dibujar_en(self)
            self.shapes.append(shape)
            log.info(f"Arco creado: {shape}")
        
        self.lin_x = self.lin_y = None
        self.linea = None
    
    # ================================================================
    # SELECCIÓN: PRESS
    # ================================================================
    
    def _press_select_mode(self, e):
        """Presionar y determinar que estamos seleccionando"""
        log.info(f"_press_select_mode: en ({e.x}, {e.y})")
        
        halo_handle = 15
        handle_items = self.find_overlapping(
            e.x - halo_handle, e.y - halo_handle,
            e.x + halo_handle, e.y + halo_handle
        )
        
        log.info(f"item encontrado en área de handle: {handle_items}")
        
        for item in handle_items:
            tags = self.gettags(item)
            log.info(f"Item {item} tiene tags: {tags}")
            
            handle_detectado = None
            
            if 'handle_punto' in tags:
                handle_detectado = 'punto'
            elif 'handle_start' in tags:
                handle_detectado = 'start'
            elif 'handle_end' in tags:
                handle_detectado = 'end'
            elif any(tag.startswith('handle_polyline_') for tag in tags):
                for tag in tags:
                    if tag.startswith('handle_polyline_'):
                        idx = int(tag.split('_')[-1])
                        handle_detectado = f'polyline_{idx}'
                        fig_tag = next((t for t in tags if t.startswith('fig_')), None)
                        if fig_tag and fig_tag != 'fig_None':
                            try:
                                fig_id = int(fig_tag.split('_')[1])
                                for shape in self.shapes:
                                    if hasattr(shape, '_canvas_ids') and fig_id in shape._canvas_ids:
                                        self._seleccionar_shape(shape)
                                        break
                                    elif shape._canvas_id == fig_id:
                                        self._seleccionar_shape(shape)
                                        break
                            except (ValueError, IndexError):
                                log.error(f"Error detectando polyline: tag = {fig_tag}")
                        break
            elif 'handle_poligono_centro' in tags:
                handle_detectado = 'poligono_centro'
            elif any(t.startswith('handle_poligono_vertice_') for t in tags):
                idx = int([t for t in tags if t.startswith('handle_poligono_vertice_')][0].split('_')[-1])
                handle_detectado = f'poligono_vertice_{idx}'
            elif 'handle_circulo_centro' in tags:
                handle_detectado = 'circulo_centro'
            elif 'handle_circulo_perimetro' in tags:
                handle_detectado = 'circulo_perimetro'
            elif 'handle_elipse_centro' in tags:
                handle_detectado = 'elipse_centro'
            elif 'handle_elipse_eje_x' in tags:
                handle_detectado = 'elipse_eje_x'
            elif 'handle_elipse_eje_y' in tags:
                handle_detectado = 'elipse_eje_y'
            elif 'handle_arco_centro' in tags:
                handle_detectado = 'arco_centro'
            elif 'handle_arco_inicio' in tags:
                handle_detectado = 'arco_inicio'
            elif 'handle_arco_final' in tags:
                handle_detectado = 'arco_final'
            elif 'handle_nw' in tags:
                handle_detectado = 'nw'
            elif 'handle_ne' in tags:
                handle_detectado = 'ne'
            elif 'handle_sw' in tags:
                handle_detectado = 'sw'
            elif 'handle_se' in tags:
                handle_detectado = 'se'
            
            if handle_detectado:
                log.info(f"Handle detectado: {handle_detectado}")
                fig_tag = next((t for t in tags if t.startswith('fig_')), None)
                if fig_tag and fig_tag != 'fig_None':
                    try:
                        fig_id = int(fig_tag.split('_')[1])
                        for shape in self.shapes:
                            if shape._canvas_id == fig_id:
                                self._seleccionar_shape(shape)
                                break
                    except (ValueError, IndexError):
                        log.error(f"Error in _pess_select_mode: tag = {fig_tag}")
                
                self.dragging_handle = handle_detectado
                
                if handle_detectado in ('nw', 'ne', 'sw', 'se') and self.shape_seleccionada:
                    self._bbox_inicial = self.shape_seleccionada.bbox()
                
                return
        
        halo = 8
        encontrados = self.find_overlapping(e.x - halo, e.y - halo, e.x + halo, e.y + halo)
        log.info(f"Items encontrados en área de figura: {encontrados}")
        
        shape_candidata = None
        for item_id in reversed(encontrados):
            tags = self.gettags(item_id)
            if 'handle' in tags:
                continue
            shape = self._find_shape_by_id(item_id)
            if shape is not None:
                shape_candidata = shape
                break
        
        if shape_candidata:
            log.info(f"Figura encontrada: {shape_candidata}")
            self._seleccionar_shape(shape_candidata)
            self.dragging_shape = True
            self.drag_start_x = e.x
            self.drag_start_y = e.y
            log.info(f"Arrastrando figura: {shape_candidata}")
            
            if isinstance(shape_candidata, Polyline):
                self._detectar_segmento_polyline(e.x, e.y)
                return
            
            if isinstance(shape_candidata, Poligono):
                segmento = self._detectar_segmento_poligono(e.x, e.y, shape_candidata)
                if segmento is not None:
                    self.dragging_handle = f'poligono_segmento_{segmento}'
                    self.drag_start_x = e.x
                    self.drag_start_y = e.y
                return
            
            return
        
        log.info("Click en vacio, deseleccionar")
        self._deseleccionar_todo()
    
    # ================================================================
    # SELECCIÓN: MOTION
    # ================================================================
    
    def _motion_select_mode(self, e):
        """Maneja el movimiento del ratón en modo Selección (S)"""
        log.info(f"_motion_select_mode: dragging_handle = {self.dragging_handle}, shape={self.shape_seleccionada}")
        
        if self.dragging_handle and self.shape_seleccionada is None:
            self.dragging_handle = None
            return
        
        if self.dragging_handle:
            if self.dragging_handle == 'punto':
                self._mover_punto(e)
            elif self.dragging_handle in ('start', 'end'):
                self._mover_handle_linea(e)
            elif self.dragging_handle.startswith('polyline_'):
                self._mover_handle_polyline(e)
            elif self.dragging_handle.startswith('poligono_'):
                if self.dragging_handle == 'poligono_centro':
                    self._mover_poligono_centro(e)
                elif self.dragging_handle.startswith('poligono_vertice_'):
                    self._mover_vertice_poligono(e)
                elif self.dragging_handle.startswith('poligono_segmento_'):
                    self._mover_segmento_poligono(e)
            elif self.dragging_handle == 'circulo_centro':
                log.info("Ejecutar _mover_circulo_centro")
                self._mover_circulo_centro(e)
            elif self.dragging_handle == 'circulo_perimetro':
                log.info("Ejecutar _mover_circulo_perimetro")
                self._mover_circulo_perimetro(e)
            elif self.dragging_handle == 'elipse_centro':
                self._mover_elipse_centro(e)
            elif self.dragging_handle == 'elipse_eje_x':
                self._mover_elipse_eje_x(e)
            elif self.dragging_handle == 'elipse_eje_y':
                self._mover_elipse_eje_y(e)
            elif self.dragging_handle == 'arco_centro':
                self._mover_arco_centro(e)
            elif self.dragging_handle == 'arco_inicio':
                self._mover_arco_inicio(e)
            elif self.dragging_handle == 'arco_final':
                self._mover_arco_final(e)
            elif self.dragging_handle in ('nw', 'ne', 'sw', 'se'):
                self._redimensionar_bbox(e)
            return
        
        if self.dragging_shape and self.shape_seleccionada is not None:
            dx = e.x - self.drag_start_x
            dy = e.y - self.drag_start_y
            
            self.shape_seleccionada.mover(dx, dy)
            self.shape_seleccionada.actualizar_en_canvas(self)
            
            handles_a_mover = [
                self.handle_start, self.handle_end,
                self.handle_nw, self.handle_ne,
                self.handle_sw, self.handle_se,
                self.handle_circulo_centro, self.handle_circulo_perimetro,
                self.handle_elipse_centro, self.handle_elipse_eje_x, self.handle_elipse_eje_y,
                self.handle_arco_centro, self.handle_arco_inicio, self.handle_arco_final,
                self.handle_poligono_centro
            ] + getattr(self, 'handles_polyline', []) + getattr(self, 'handles_poligono', [])
            
            for h in handles_a_mover:
                if h is not None:
                    if isinstance(h, tuple):
                        self.move(h[1], dx, dy)
                    else:
                        self.move(h, dx, dy)
            
            self.drag_start_x = e.x
            self.drag_start_y = e.y
    
    def _release_select_mode(self, e):
        self.dragging_handle = None
        self.dragging_shape = False
        self._bbox_inicial = None
    
    # ================================================================
    # SELECCIONAR SHAPE
    # ================================================================
    
    def _seleccionar_shape(self, shape):
        """Selecciona un objeto Shape del modelo"""
        log.info(f"_seleccionar_shape: shape = {shape}")
        
        if self.shape_seleccionada is not None:
            self._restaurar_apariencia(self.shape_seleccionada)
        
        self._deseleccionar_todo()
        self.shape_seleccionada = shape
        self.tag_trazo_seleccionado = None
        
        tag = getattr(shape, '_tag', '')
        log.info(f'Shape seleccionada: {shape}, tag: {tag}')
        
        if tag.startswith('trazo_'):
            self.tag_trazo_seleccionado = tag
        
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        elif shape.canvas_id is not None:
            if isinstance(shape, (Linea, Polyline)):
                self.itemconfig(shape.canvas_id, fill='red')
            else:
                self.itemconfig(shape.canvas_id, outline='red')
        
        if isinstance(shape, Linea) and not tag.startswith('trazo_'):
            self._mostrar_handles_linea(shape)
        elif isinstance(shape, Polyline):
            self._mostrar_handles_polyline(shape)
        elif isinstance(shape, Poligono):
            self._mostrar_handles_poligono(shape)
        elif isinstance(shape, Circulo):
            self._mostrar_handles_circulo(shape)
        elif isinstance(shape, Elipse):
            self._mostrar_handles_elipse(shape)
        elif isinstance(shape, Arco):
            self._mostrar_handles_arco(shape)
        elif isinstance(shape, PointShape):
            self._mostrar_handles_punto(shape)
        elif isinstance(shape, Texto):
            self._mostrar_handles_bbox(shape)
        else:
            self._mostrar_handles_bbox(shape)
        
        self._set_status(f"Seleccionado: {shape}")
    
    # ================================================================
    # HANDLES
    # ================================================================
    
    def _mostrar_handles_punto(self, shape):
        """Muestra handle en el punto"""
        self.delete('handle_punto')
        radio = self._get_handle_radio()
        self.handle_punto = self.create_oval(
            shape.punto.x - radio, shape.punto.y - radio,
            shape.punto.x + radio, shape.punto.y + radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_punto', f'fig_{shape._canvas_id}')
        )
        self.tag_raise('handle')
        log.info(f"Handle punto creado: {self.handle_punto}")
    
    def _mostrar_handles_para_shape(self, shape, tag):
        """Muestra los handles apropiados según el tipo de shape"""
        if tag.startswith('trazo_'):
            return
        
        if isinstance(shape, Linea):
            self._mostrar_handles_linea(shape)
        elif isinstance(shape, PointShape):
            pass
        else:
            self._mostrar_handles_bbox(shape)
    
    def _mostrar_handles_linea(self, shape):
        """Muestra handle en los estremos de la línea"""
        self.delete('handle_start')
        self.delete('handle_end')
        radio = self._get_handle_radio()
        
        self.handle_start = self.create_oval(
            shape.p1.x-radio, shape.p1.y-radio, shape.p1.x+radio, shape.p1.y+radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_start', f'fig_{shape._canvas_id}')
        )
        self.handle_end = self.create_oval(
            shape.p2.x-radio, shape.p2.y-radio, shape.p2.x+radio, shape.p2.y+radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_end', f'fig_{shape._canvas_id}')
        )
        self.tag_raise('handle')
        log.info(f"Handles línea creados: {self.handle_start}, {self.handle_end}")
    
    def _mover_handle_polyline(self, e):
        """Mueve un vértice de una polyline"""
        if not isinstance(self.shape_seleccionada, Polyline):
            return
        
        radio = self._get_handle_radio()
        shape = self.shape_seleccionada
        idx = int(self.dragging_handle.split('_')[-1])
        
        if 0 <= idx < len(shape.puntos):
            shape.puntos[idx].x = float(e.x)
            shape.puntos[idx].y = float(e.y)
            shape.actualizar_en_canvas(self)
            
            if idx < len(self.handles_polyline):
                self.coords(self.handles_polyline[idx], e.x-radio, e.y-radio, e.x+radio, e.y+radio)
    
    def _mostrar_handles_bbox(self, shape):
        bbox = shape.bbox()
        if bbox is None:
            return
        
        x1, y1, x2, y2 = bbox
        self.delete('handle')
        radio = self._get_handle_radio()
        
        self.handle_nw = self.create_oval(
            x1-radio, y1-radio, x1+radio, y1+radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}'))
        self.handle_ne = self.create_oval(
            x2-radio, y1-radio, x2+radio, y1+radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}'))
        self.handle_sw = self.create_oval(
            x1-radio, y2-radio, x1+radio, y2+radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}'))
        self.handle_se = self.create_oval(
            x2-radio, y2-radio, x2+radio, y2+radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_se', f'fig_{shape._canvas_id}'))
    
    def _mover_handle_linea(self, e):
        """Mueve un extremo de una línea del modelo"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Linea):
            return
        
        radio = self._get_handle_radio()
        
        if self.dragging_handle == 'start':
            shape.p1.x = float(e.x)
            shape.p1.y = float(e.y)
            shape.actualizar_en_canvas(self)
            self.coords(self.handle_start, e.x-radio, e.y-radio, e.x+radio, e.y+radio)
        elif self.dragging_handle == 'end':
            shape.p2.x = float(e.x)
            shape.p2.y = float(e.y)
            shape.actualizar_en_canvas(self)
            self.coords(self.handle_end, e.x-radio, e.y-radio, e.x+radio, e.y+radio)
    
    def _redimensionar_bbox(self, e):
        if self._bbox_inicial is None or self.shape_seleccionada is None:
            return
        
        x1, y1, x2, y2 = self._bbox_inicial
        
        if self.dragging_handle == 'nw':
            x1, y1 = e.x, e.y
        elif self.dragging_handle == 'ne':
            x2, y1 = e.x, e.y
        elif self.dragging_handle == 'sw':
            x1, y2 = e.x, e.y
        elif self.dragging_handle == 'se':
            x2, y2 = e.x, e.y
        
        shape = self.shape_seleccionada
        
        if isinstance(shape, Circulo):
            nuevo_cx = (x1 + x2) / 2
            nuevo_cy = (y1 + y2) / 2
            nuevo_radio = max(abs(x2 - x1), abs(y2 - y1)) / 2
            shape.centro.x = float(nuevo_cx)
            shape.centro.y = float(nuevo_cy)
            shape.radio = float(nuevo_radio)
        elif isinstance(shape, Rectangulo):
            shape.p1.x = float(min(x1, x2))
            shape.p1.y = float(min(y1, y2))
            shape.p2.x = float(max(x1, x2))
            shape.p2.y = float(max(y1, y2))
        elif isinstance(shape, Elipse):
            nuevo_cx = (x1 + x2) / 2
            nuevo_cy = (y1 + y2) / 2
            shape.centro.x = float(nuevo_cx)
            shape.centro.y = float(nuevo_cy)
            shape.radio_x = float(abs(x2 - x1) / 2)
            shape.radio_y = float(abs(y2 - y1) / 2)
        elif isinstance(shape, Arco):
            shape.p1.x = float(min(x1, x2))
            shape.p1.y = float(min(y1, y2))
            shape.p2.x = float(max(x1, x2))
            shape.p2.y = float(max(y1, y2))
        
        shape.actualizar_en_canvas(self)
        
        radio = self._get_handle_radio()
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        if self.handle_nw:
            self.coords(self.handle_nw, x_min-radio, y_min-radio, x_min+radio, y_min+radio)
        if self.handle_ne:
            self.coords(self.handle_ne, x_max-radio, y_min-radio, x_max+radio, y_min+radio)
        if self.handle_sw:
            self.coords(self.handle_sw, x_min-radio, y_max-radio, x_min+radio, y_max+radio)
        if self.handle_se:
            self.coords(self.handle_se, x_max-radio, y_max-radio, x_max+radio, y_max+radio)
    
    def _mostrar_handles_polyline(self, shape):
        """Muestra handles azules en cada vértice de la polyline"""
        if hasattr(self, 'handles_polyline'):
            for h in self.handles_polyline:
                if h is not None:
                    self.delete(h)
        
        radio = self._get_handle_radio()
        self.handles_polyline = []
        
        fig_id = shape._canvas_ids[0] if hasattr(shape, '_canvas_ids') and shape._canvas_ids else 'polyline'
        
        for i, punto in enumerate(shape.puntos):
            handle = self.create_oval(
                punto.x - radio, punto.y - radio, punto.x + radio, punto.y + radio,
                fill='blue', outline='white', width=2,
                tags=('handle', f'handle_polyline_{i}', f'fig_{fig_id}')
            )
            self.handles_polyline.append(handle)
        
        self.tag_raise('handle')
        log.info(f"Handles polyline creados: {len(self.handles_polyline)} handles")
    
    def _mostrar_handles_poligono(self, shape: Poligono):
        """Muestra handles en vértices y centro del polígono"""
        self.delete('handle_poligono_centro')
        
        if hasattr(self, 'handles_poligono'):
            for h in self.handles_poligono:
                if h is not None:
                    self.delete(h)
        
        self.handles_poligono = []
        radio = self._get_handle_radio()
        
        self.handle_poligono_centro = self.create_oval(
            shape.centro.x - radio, shape.centro.y - radio,
            shape.centro.x + radio, shape.centro.y + radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_poligono_centro', f'fig_{shape._canvas_id}')
        )
        
        vertices = shape.obtener_vertices()
        for i, v in enumerate(vertices):
            handle = self.create_oval(
                v.x - radio, v.y - radio, v.x + radio, v.y + radio,
                fill='blue', outline='white', width=2,
                tags=('handle', f'handle_poligono_vertice_{i}', f'fig_{shape._canvas_id}')
            )
            self.handles_poligono.append(handle)
        
        self.tag_raise('handle')
        log.info(f"Handles polígono creados: centro={self.handle_poligono_centro}, {len(self.handles_poligono)} vértices")
    
    # ================================================================
    # RESTAURAR
    # ================================================================
    
    def _restaurar_apariencia(self, shape):
        """Restaurar el color original de un shape"""
        try:
            if hasattr(shape, 'restaurar'):
                shape.restaurar(self)
            elif shape.canvas_id is not None:
                color = shape.color
                if isinstance(shape, (Linea, Polyline)):
                    self.itemconfig(shape.canvas_id, fill=color)
                else:
                    self.itemconfig(shape.canvas_id, outline=color)
        except tk.TclError:
            pass
    
    def _deseleccionar_todo(self):
        """Elimina handles y resetea la selección"""
        if self.shape_seleccionada is not None:
            self._restaurar_apariencia(self.shape_seleccionada)
        
        if self.handle_start: self.delete(self.handle_start)
        if self.handle_end: self.delete(self.handle_end)
        if self.handle_nw: self.delete(self.handle_nw)
        if self.handle_ne: self.delete(self.handle_ne)
        if self.handle_sw: self.delete(self.handle_sw)
        if self.handle_se: self.delete(self.handle_se)
        if self.handle_circulo_centro: self.delete(self.handle_circulo_centro)
        if self.handle_circulo_perimetro: self.delete(self.handle_circulo_perimetro)
        
        for h in getattr(self, 'handles_polyline', []):
            if isinstance(h, tuple): self.delete(h[1])
            else: self.delete(h)
        
        if hasattr(self, 'handle_poligono_centro') and self.handle_poligono_centro:
            self.delete(self.handle_poligono_centro)
            self.handle_poligono_centro = None
        
        for h in getattr(self, 'handles_poligono', []):
            if h is not None:
                self.delete(h)
        
        self.handles_poligono = []
        self.delete('handle')
        
        if self.texto_preview_id is not None:
            self.delete(self.texto_preview_id)
            self.texto_preview_id = None
        
        self.shape_seleccionada = None
        self.tag_trazo_seleccionado = None
        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        self.handle_poligono_centro = None
        self.handles_poligono = []
        self.handles_polyline = []
        self.polyline_segmento_drag = None
        self.dragging_handle = None
        self.dragging_shape = False
        self.handle_circulo_centro = None
        self.handle_circulo_perimetro = None
        self.handle_elipse_centro = None
        self.handle_elipse_eje_x = None
        self.handle_elipse_eje_y = None
        self.handle_arco_centro = None
        self.handle_arco_inicio = None
        self.handle_arco_final = None
        
        log.info(f"_deseleccionar_todo: --- limpiando entorno -----")
    
    # ================================================================
    # ELIMINAR
    # ================================================================
    
    def eliminar_shape_seleccionada(self):
        if self.shape_seleccionada is not None:
            shape = self.shape_seleccionada
            
            if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
                for cid in shape._canvas_ids:
                    self.delete(cid)
            elif shape.canvas_id is not None:
                self.delete(shape.canvas_id)
            
            if shape in self.shapes:
                self.shapes.remove(shape)
            
            tag = getattr(shape, '_tag', '')
            if tag.startswith('trazo_') and tag in self.trazos:
                del self.trazos[tag]
            
            self._deseleccionar_todo()
            self._set_status(f"Objeto eliminado: {shape}")
            log.info(f"Shape eliminada: {shape}")
    
    # ================================================================
    # PUNTO
    # ================================================================
    
    def _mover_punto(self, e):
        """Mueve el punto seleccionado"""
        shape = self.shape_seleccionada
        if not isinstance(shape, PointShape): return
        
        radio = self._get_handle_radio()
        
        if shape._canvas_id is not None:
            self.delete(shape._canvas_id)
        
        dx = e.x - shape.punto.x
        dy = e.y - shape.punto.y
        shape.mover(dx, dy)
        shape.dibujar_en(self)
        
        if self.handle_punto:
            self.coords(self.handle_punto,
                        shape.punto.x - radio, shape.punto.y - radio,
                        shape.punto.x + radio, shape.punto.y + radio)
        
        self._save_state()
    
    # ================================================================
    # LÍNEA
    # ================================================================
    
    def _finalizar_linea(self, x2, y2):
        """Borra la preview y crea la Linea definitiva"""
        width = self._get_width()
        color = self._get_color_fg()
        
        if self.linea_preview is not None:
            self.delete(self.linea_preview)
            self.linea_preview = None
        
        p2 = Punto(x2, y2)
        shape = Linea(self.linea_p1, p2, color=color, grosor=width)
        shape._tag = 'Line'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Línea creada: {shape} (p1={self.linea_p1}, p2={p2})")
        
        self.linea_p1 = None
        self._set_status("Línea creada. Click para otra línea o cambia de modo.")
        self._save_state()
    
    # ================================================================
    # POLYLINE
    # ================================================================
    
    def _añadir_punto_polyline(self, x, y):
        """Añade un punto a la polyline en progreso"""
        nuevo_punto = Punto(x, y)
        self.polyline_puntos.append(nuevo_punto)
        
        if len(self.polyline_puntos) >= 2:
            p_anterior = self.polyline_puntos[-2]
            width = self._get_width()
            color = self._get_color_fg()
            cid = self.create_line(
                p_anterior.x, p_anterior.y, x, y,
                fill=color, width=width, capstyle=tk.ROUND
            )
            self.polyline_segmentos_ids.append(cid)
        
        if self.polyline_preview_id is not None:
            self.delete(self.polyline_preview_id)
        
        self.polyline_preview_id = self.create_line(
            x, y, x, y,
            dash=(4, 4), fill='gray', width=1
        )
        
        self._save_state()
        self._set_status(f"Polyline: {len(self.polyline_puntos)} puntos. Click izq para añadir, click der para finalizar")
    
    def _detectar_segmento_polyline(self, x, y):
        """Detecta qué segmento de la polyline está más cerca del click"""
        if not isinstance(self.shape_seleccionada, Polyline):
            return
        
        shape = self.shape_seleccionada
        min_dist = float('inf')
        segmento_cercano = -1
        
        for i in range(len(shape.puntos) - 1):
            p1 = shape.puntos[i]
            p2 = shape.puntos[i + 1]
            dist = self._distancia_punto_a_segmento(x, y, p1.x, p1.y, p2.x, p2.y)
            if dist < min_dist:
                min_dist = dist
                segmento_cercano = i
        
        self.polyline_segmento_drag = segmento_cercano
    
    def _mover_segmento_poligono(self, e):
        """Mueve el polígono completo al arrastrar un segmento"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Poligono):
            return
        
        dx = e.x - self.drag_start_x
        dy = e.y - self.drag_start_y
        
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_poligono()
        
        self.drag_start_x = e.x
        self.drag_start_y = e.y
    
    def _finalizar_polyline(self):
        """Borra previews y crea la Polyline definitiva"""
        if self.polyline_preview_id is not None:
            self.delete(self.polyline_preview_id)
            self.polyline_preview_id = None
        
        for cid in self.polyline_segmentos_ids:
            self.delete(cid)
        
        self.polyline_segmentos_ids = []
        
        width = self._get_width()
        color = self._get_color_fg()
        shape = Polyline(self.polyline_puntos, color=color, grosor=width)
        tag_trazo = f'trazo_{self.contador_trazos}'
        self.contador_trazos += 1
        shape._tag = tag_trazo
        shape._original_color = color
        
        shape.dibujar_en(self)
        self.shapes.append(shape)
        self.trazos[tag_trazo] = shape
        
        log.info(f"Polyline creada: {tag_trazo} ({len(self.polyline_puntos)} puntos)")
        
        self.polyline_puntos = []
        self.polyline_segmentos_ids = []
        self._set_status(f"Polyline creada con {len(shape.puntos)} puntos")
    
    def _cancelar_polyline(self):
        """Cancela la polyline en progreso"""
        for cid in self.polyline_segmentos_ids:
            self.delete(cid)
        
        if self.polyline_preview_id is not None:
            self.delete(self.polyline_preview_id)
            self.polyline_preview_id = None
        
        self.polyline_puntos = []
        self.polyline_segmentos_ids = []
        self._set_status("Polyline cancelada")
    
    # ================================================================
    # CANCELAR DIBUJO
    # ================================================================
    
    def _cancelar_dibujo(self):
        """Cancela cualquier dibujo en progreso"""
        mode = self._get_mode()
        self._cancelar_duplicado()
        
        if mode == 'L':
            if self.linea_preview is not None:
                self.delete(self.linea_preview_id)
                self.linea_preview = None
            self.linea_p1 = None
            self._set_status("Línea cancelada")
            return
        
        if mode == 'Pl':
            self._cancelar_polyline()
            return
        
        if mode == 'C':
            if self.circulo_preview_id is not None:
                self.delete(self.circulo_preview_id)
                self.circulo_preview_id = None
            self.circulo_centro = None
            self._set_status("Círculo cancelado")
            return
        
        if mode == 'R':
            if self.rectangulo_preview_id is not None:
                self.delete(self.rectangulo_preview_id)
                self.rectangulo_preview_id = None
            self.rectangulo_centro = None
            self._set_status("Rectángulo cancelado")
            return
        
        if mode == 'E':
            if self.elipse_preview_id is not None:
                self.delete(self.elipse_preview_id)
                self.elipse_preview_id = None
            self.elipse_centro = None
            self._set_status("Elipse cancelada")
            return
        
        if mode == 'A':
            self._reset_arco_estado()
            self._set_status("Arco cancelado")
            return
        
        if mode == 'T':
            if self.texto_preview_id is not None:
                self.delete(self.texto_preview_id)
                self.texto_preview_id = None
            self._set_status("Texto cancelado")
            return
    
    def _cancelar_duplicado(self):
        """Cancela el duplicado de shape"""
        if self._colocando_duplicado:
            if self._id_fantasma is not None:
                self.delete(self._id_fantasma)
            self._colocando_duplicado = False
            self._figura_a_colocar = None
            self._id_fantasma = None
            self._actualizar_cursor()
            self._set_status("Duplicado cancelado")
            return
    
    # ================================================================
    # POLÍGONO
    # ================================================================
    
    def _finalizar_poligono(self, x, y):
        """Borra la preview y crea el Polígono definitivo"""
        if self.poligono_preview_id is not None:
            self.delete(self.poligono_preview_id)
            self.poligono_preview_id = None
        
        radio = math.hypot(x - self.poligono_centro.x, y - self.poligono_centro.y)
        
        if radio < 2:
            self.poligono_centro = None
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        shape = Poligono(
            self.poligono_centro,
            radio,
            lados=self.lados_poligono,
            color=color,
            grosor=width
        )
        shape._tag = 'Polygon'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Polígono creado: {shape} ({self.lados_poligono} lados)")
        
        self.poligono_centro = None
        self._set_status(f"Polígono creado con {self.lados_poligono} lados")
        self._save_state()
    
    def _mover_poligono_centro(self, e):
        """Mueve el centro del polígono"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Poligono): return
        
        dx = e.x - shape.centro.x
        dy = e.y - shape.centro.y
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_poligono()
    
    def _mover_vertice_poligono(self, e):
        """Mueve un vértice, recalculando el radio"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Poligono): return
        
        idx = int(self.dragging_handle.split('_')[-1])
        nuevo_punto = Punto(e.x, e.y)
        shape.actualizar_desde_vertice(idx, nuevo_punto)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_poligono()
    
    def _actualizar_handles_poligono(self):
        """Reposiciona los handles del polígono seleccionado"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Poligono): return
        
        radio = self._get_handle_radio()
        
        if self.handle_poligono_centro:
            self.coords(self.handle_poligono_centro,
                        shape.centro.x - radio, shape.centro.y - radio,
                        shape.centro.x + radio, shape.centro.y + radio)
        
        vertices = shape.obtener_vertices()
        for i, v in enumerate(vertices):
            if i < len(self.handles_poligono):
                self.coords(self.handles_poligono[i],
                            v.x - radio, v.y - radio, v.x + radio, v.y + radio)
    
    def _detectar_segmento_poligono(self, x, y, shape: Poligono):
        vertices = shape.obtener_vertices()
        min_dist = 10
        segmento_cercano = None
        
        for i in range(len(vertices)):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % len(vertices)]
            dist = self._distancia_punto_a_segmento(x, y, p1.x, p1.y, p2.x, p2.y)
            if dist < min_dist:
                min_dist = dist
                segmento_cercano = i
        
        return segmento_cercano
    
    # ================================================================
    # CÍRCULO
    # ================================================================
    
    def _finalizar_circulo(self, x, y):
        """Borra la preview y crea el Círculo definitivo"""
        if self.circulo_preview_id is not None:
            self.delete(self.circulo_preview_id)
            self.circulo_preview_id = None
        
        radio = math.hypot(x - self.circulo_centro.x, y - self.circulo_centro.y)
        
        if radio < 2:
            self.circulo_centro = None
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        shape = Circulo(
            self.circulo_centro,
            radio,
            color=color,
            grosor=width
        )
        shape._tag = 'Circle'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Círculo creado: {shape}")
        
        self.circulo_centro = None
        self._set_status("Círculo creado")
        self._save_state()
    
    # ================================================================
    # RECTÁNGULO
    # ================================================================
    
    def _finalizar_rectangulo(self, x, y):
        """Borra la preview y crea el Rectángulo definitivo"""
        if self.rectangulo_preview_id is not None:
            self.delete(self.rectangulo_preview_id)
            self.rectangulo_preview_id = None
        
        x1 = 2 * self.rectangulo_centro.x - x
        y1 = 2 * self.rectangulo_centro.y - y
        
        if abs(x - self.rectangulo_centro.x) < 2 or abs(y - self.rectangulo_centro.y) < 2:
            self.rectangulo_centro = None
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        shape = Rectangulo(
            Punto(x1, y1), Punto(x, y),
            color=color, grosor=width
        )
        shape._tag = 'Rectangle'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Rectángulo creado: {shape}")
        
        self.rectangulo_centro = None
        self._set_status("Rectángulo creado")
        self._save_state()
    
    def _mostrar_handles_rectangulo(self, shape):
        """Muestra handles en las esquinas del rectángulo"""
        for tag in ['handle_nw', 'handle_ne', 'handle_sw', 'handle_se']:
            self.delete(tag)
        
        radio = self._get_handle_radio()
        x1, y1 = min(shape.p1.x, shape.p2.x), min(shape.p1.y, shape.p2.y)
        x2, y2 = max(shape.p1.x, shape.p2.x), max(shape.p1.y, shape.p2.y)
        
        self.handle_nw = self.create_oval(
            x1 - radio, y1 - radio, x1 + radio, y1 + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}')
        )
        self.handle_ne = self.create_oval(
            x2 - radio, y1 - radio, x2 + radio, y1 + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}')
        )
        self.handle_sw = self.create_oval(
            x1 - radio, y2 - radio, x1 + radio, y2 + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}')
        )
        self.handle_se = self.create_oval(
            x2 - radio, y2 - radio, x2 + radio, y2 + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_se', f'fig_{shape._canvas_id}')
        )
        
        self.tag_raise('handle')
        log.info(f"Handles rectángulo creados: {self.handle_nw}, {self.handle_ne}, {self.handle_sw}, {self.handle_se}")
    
    # ================================================================
    # ELIPSE
    # ================================================================
    
    def _finalizar_elipse(self, x, y):
        """Borra la preview y crea la Elipse definitiva"""
        if self.elipse_preview_id is not None:
            self.delete(self.elipse_preview_id)
            self.elipse_preview_id = None
        
        rx = abs(x - self.elipse_centro.x)
        ry = abs(y - self.elipse_centro.y)
        
        if rx < 2 or ry < 2:
            self.elipse_centro = None
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        relleno = config.get('Pen', 'default_color_fill', '')
        
        shape = Elipse(
            self.elipse_centro, rx, ry,
            color=color, grosor=width,
            relleno=relleno
        )
        shape._tag = 'Elipse'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Elipse creada: {shape}")
        
        self.elipse_centro = None
        self._set_status("Elipse creada")
        self._save_state()
    
    def _mostrar_handles_elipse(self, shape: Elipse):
        """Muestra handles en el centro y en los ejes X e Y de la elipse"""
        log.info(f"Handles elipse creados: centro={self.handle_elipse_centro}, eje_x={self.handle_elipse_eje_x}, eje_y={self.handle_elipse_eje_y}")
        
        self.delete('handle_elipse_centro')
        self.delete('handle_elipse_eje_x')
        self.delete('handle_elipse_eje_y')
        
        radio = self._get_handle_radio()
        
        self.handle_elipse_centro = self.create_oval(
            shape.centro.x - radio, shape.centro.y - radio,
            shape.centro.x + radio, shape.centro.y + radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_elipse_centro', f'fig_{shape._canvas_id}')
        )
        
        self.handle_elipse_eje_x = self.create_oval(
            shape.centro.x + shape.radio_x - radio, shape.centro.y - radio,
            shape.centro.x + shape.radio_x + radio, shape.centro.y + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_elipse_eje_x', f'fig_{shape._canvas_id}')
        )
        
        self.handle_elipse_eje_y = self.create_oval(
            shape.centro.x - radio, shape.centro.y + shape.radio_y - radio,
            shape.centro.x + radio, shape.centro.y + shape.radio_y + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_elipse_eje_y', f'fig_{shape._canvas_id}')
        )
        
        self.tag_raise('handle')
        log.info(f"Handles elipse creados: centro={self.handle_elipse_centro}, eje_x={self.handle_elipse_eje_x}, eje_y={self.handle_elipse_eje_y}")
    
    def _mover_elipse_centro(self, e):
        """Mueve el centro de la elipse"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Elipse): return
        
        dx = e.x - shape.centro.x
        dy = e.y - shape.centro.y
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_elipse()
    
    def _mover_elipse_eje_x(self, e):
        """Modifica el radio horizontal (rx)"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Elipse): return
        
        shape.actualizar_radio_x_desde_punto(Punto(e.x, e.y))
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_elipse()
    
    def _mover_elipse_eje_y(self, e):
        """Modifica el radio vertical (ry)"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Elipse): return
        
        shape.actualizar_radio_y_desde_punto(Punto(e.x, e.y))
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_elipse()
    
    def _actualizar_handles_elipse(self):
        """Reposiciona los handles de la elipse seleccionada"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Elipse): return
        
        radio = self._get_handle_radio()
        
        if self.handle_elipse_centro:
            self.coords(self.handle_elipse_centro,
                        shape.centro.x - radio, shape.centro.y - radio,
                        shape.centro.x + radio, shape.centro.y + radio)
        
        if self.handle_elipse_eje_x:
            p = shape.obtener_punto_eje_x()
            self.coords(self.handle_elipse_eje_x,
                        p.x - radio, p.y - radio, p.x + radio, p.y + radio)
        
        if self.handle_elipse_eje_y:
            p = shape.obtener_punto_eje_y()
            self.coords(self.handle_elipse_eje_y,
                        p.x - radio, p.y - radio, p.x + radio, p.y + radio)
    
    # ================================================================
    # CÍRCULO HANDLES
    # ================================================================
    
    def _mostrar_handles_circulo(self, shape: Circulo):
        """Muestra handles en el centro y en el perímetro del círculo"""
        log.info(f"Mostrando handles del circulo: centro={shape.centro}, radio={shape.radio}")
        
        self.delete('handle_circulo_centro')
        self.delete('handle_circulo_perimetro')
        
        radio = self._get_handle_radio()
        
        self.handle_circulo_centro = self.create_oval(
            shape.centro.x - radio, shape.centro.y - radio,
            shape.centro.x + radio, shape.centro.y + radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_circulo_centro', f'fig_{shape._canvas_id}')
        )
        log.info(f"Handle centro creado: {self.handle_circulo_centro}")
        
        punto_perimetro = shape.obtener_punto_perimetro()
        self.handle_circulo_perimetro = self.create_oval(
            punto_perimetro.x - radio, punto_perimetro.y - radio,
            punto_perimetro.x + radio, punto_perimetro.y + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_circulo_perimetro', f'fig_{shape._canvas_id}')
        )
        log.info(f"Handle perímetro creado: {self.handle_circulo_perimetro} en {punto_perimetro}")
        
        self.tag_raise('handle')
    
    def _mover_circulo_centro(self, e):
        """Mueve el centro del círculo"""
        log.info(f"_mover_circulo_centro: e=({e.x}, {e.y}), shape={self.shape_seleccionada}")
        shape = self.shape_seleccionada
        if not isinstance(shape, Circulo):
            log.warning("No es un circulo")
            return
        
        dx = e.x - shape.centro.x
        dy = e.y - shape.centro.y
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_circulo()
        log.info(f"Circulo movido a centro= {shape.centro}")
    
    def _mover_circulo_perimetro(self, e):
        """Mueve el perímetro del círculo"""
        log.info(f"_mover_circulo_perimetro: e=({e.x}, {e.y}), shape={self.shape_seleccionada}")
        shape = self.shape_seleccionada
        if not isinstance(shape, Circulo):
            log.warning("No es un circulo")
            return
        
        nuevo_punto = Punto(e.x, e.y)
        shape.actualizar_radio_desde_punto(nuevo_punto)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_circulo()
        log.info(f"Circulo redimensionado a radio = {shape.radio}")
    
    def _actualizar_handles_circulo(self):
        """Reposiciona los handles del círculo seleccionado"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Circulo):
            return
        
        radio = self._get_handle_radio()
        
        if self.handle_circulo_centro is not None:
            self.coords(self.handle_circulo_centro,
                        shape.centro.x - radio, shape.centro.y - radio,
                        shape.centro.x + radio, shape.centro.y + radio)
        
        if self.handle_circulo_perimetro is not None:
            punto_perimetro = shape.obtener_punto_perimetro()
            self.coords(self.handle_circulo_perimetro,
                        punto_perimetro.x - radio, punto_perimetro.y - radio,
                        punto_perimetro.x + radio, punto_perimetro.y + radio)
    
    # ================================================================
    # ARCO
    # ================================================================
    
    def _finalizar_arco(self, x, y):
        """Crea el arco definitivo tras el tercer clic"""
        if self.arco_preview_id is not None:
            self.delete(self.arco_preview_id)
            self.arco_preview_id = None
        
        p2 = Punto(x, y)
        angulo_final = math.degrees(math.atan2(
            -(p2.y - self.arco_centro.y),
            p2.x - self.arco_centro.x
        ))
        extension = angulo_final - self.arco_angulo_inicio
        
        if self.arco_radio < 2 or abs(extension) < 1:
            self._reset_arco_estado()
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        relleno = config.get('Pen', 'default_color_fill', '')
        
        shape = Arco(
            centro=self.arco_centro,
            radio=self.arco_radio,
            angulo_inicio=self.arco_angulo_inicio,
            extension=extension,
            color=color,
            grosor=width,
            relleno=relleno
        )
        shape._tag = 'Arc'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        
        log.info(f"Arco creado: {shape}")
        
        self._reset_arco_estado()
        self._set_status("Arco creado")
        self._save_state()
    
    def _reset_arco_estado(self):
        """Resetea todas las variables del estado del arco"""
        self.arco_centro = None
        self.arco_p1 = None
        self.arco_radio = 0.0
        self.arco_angulo_inicio = 0.0
        self.arco_estado = 0
        
        if self.arco_preview_id is not None:
            self.delete(self.arco_preview_id)
            self.arco_preview_id = None
    
    def _mostrar_handles_arco(self, shape: Arco):
        """Muestra handles en el centro y en los extremos del arco"""
        log.info(f"Mostrando handles del arco: centro={shape.centro}, inicio={shape.angulo_inicio}°, ext={shape.extension}°")
        
        self.delete('handle_arco_centro')
        self.delete('handle_arco_inicio')
        self.delete('handle_arco_final')
        
        radio = self._get_handle_radio()
        
        self.handle_arco_centro = self.create_oval(
            shape.centro.x - radio, shape.centro.y - radio,
            shape.centro.x + radio, shape.centro.y + radio,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_arco_centro', f'fig_{shape._canvas_id}')
        )
        
        p_inicio = shape.obtener_punto_inicio()
        self.handle_arco_inicio = self.create_oval(
            p_inicio.x - radio, p_inicio.y - radio,
            p_inicio.x + radio, p_inicio.y + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_arco_inicio', f'fig_{shape._canvas_id}')
        )
        
        p_final = shape.obtener_punto_final()
        self.handle_arco_final = self.create_oval(
            p_final.x - radio, p_final.y - radio,
            p_final.x + radio, p_final.y + radio,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_arco_final', f'fig_{shape._canvas_id}')
        )
        
        self.tag_raise('handle')
        log.info(f"Handles arco creados: centro={self.handle_arco_centro}, inicio={self.handle_arco_inicio}, final={self.handle_arco_final}")
    
    def _mover_arco_centro(self, e):
        """Mueve el centro del arco"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Arco): return
        
        dx = e.x - shape.centro.x
        dy = e.y - shape.centro.y
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_arco()
    
    def _mover_arco_inicio(self, e):
        """Modifica el ángulo de inicio del arco"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Arco): return
        
        shape.actualizar_punto_inicio(Punto(e.x, e.y))
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_arco()
    
    def _mover_arco_final(self, e):
        """Modifica la extensión del arco"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Arco): return
        
        shape.actualizar_punto_final(Punto(e.x, e.y))
        shape.actualizar_en_canvas(self)
        self._actualizar_handles_arco()
    
    def _actualizar_handles_arco(self):
        """Reposiciona los handles del arco seleccionado"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Arco): return
        
        radio = self._get_handle_radio()
        
        if self.handle_arco_centro:
            self.coords(self.handle_arco_centro,
                        shape.centro.x - radio, shape.centro.y - radio,
                        shape.centro.x + radio, shape.centro.y + radio)
        
        if self.handle_arco_inicio:
            p = shape.obtener_punto_inicio()
            self.coords(self.handle_arco_inicio,
                        p.x - radio, p.y - radio, p.x + radio, p.y + radio)
        
        if self.handle_arco_final:
            p = shape.obtener_punto_final()
            self.coords(self.handle_arco_final,
                        p.x - radio, p.y - radio, p.x + radio, p.y + radio)
    
    # ================================================================
    # TEXTO
    # ================================================================
    
    def _mostrar_handles_texto(self, shape: Texto):
        """Muestra handles de bbox alrededor del texto"""
        radio = self._get_handle_radio()
        
        if shape._canvas_id:
            bbox = self.bbox(shape._canvas_id)
            if bbox:
                x1, y1, x2, y2 = bbox
                self.delete('handle')
                
                self.handle_nw = self.create_oval(
                    x1 - radio, y1 - radio, x1 + radio, y1 + radio,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}')
                )
                self.handle_ne = self.create_oval(
                    x2 - radio, y1 - radio, x2 + radio, y1 + radio,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}')
                )
                self.handle_sw = self.create_oval(
                    x1 - radio, y2 - radio, x1 + radio, y2 + radio,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}')
                )
                self.handle_se = self.create_oval(
                    x2 - radio, y2 - radio, x2 + radio, y2 + radio,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_se', f'fig_{shape._canvas_id}')
                )
                
                self.tag_raise('handle')
                log.info(f"Handles texto creados en bbox: {bbox}")
    
    # ================================================================
    # ACCIONES DEL MENÚ CONTEXTUAL
    # ================================================================
    
    def _actualizar_estado_menu_texto(self, shape: Texto):
        """Actualiza el estado de los checkbuttons del menú"""
        self.var_negrita.set(shape.negrita)
        self.var_cursiva.set(shape.cursiva)
        self.var_alineacion.set(shape.alineacion)
    
    def _editar_texto_seleccionado(self):
        """Abre diálogo para editar el contenido del texto"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        nuevo_texto = simpledialog.askstring(
            "Editar Texto",
            "Nuevo contenido:",
            initialvalue=shape.texto
        )
        
        if nuevo_texto is not None and nuevo_texto != shape.texto:
            shape.texto = nuevo_texto
            self.delete(shape._canvas_id)
            shape.dibujar_en(self)
            self._save_state()
            log.info(f"Texto editado: {shape}")
    
    def _cambiar_fuente_texto(self, nueva_fuente: str):
        """Cambia la fuente del texto seleccionado"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        shape.fuente = nueva_fuente
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        self._save_state()
        log.info(f"Fuente cambiada a {nueva_fuente} en {shape}")
    
    def _cambiar_tamano_texto(self, nuevo_tamano: int):
        """Cambia el tamaño del texto seleccionado"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        shape.tamaño = nuevo_tamano
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        self._save_state()
        log.info(f"Tamaño cambiado a {nuevo_tamano} en {shape}")
    
    def _cambiar_color_texto(self):
        """Abre color picker para cambiar el color del texto"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        color = colorchooser.askcolor(
            initialcolor=shape.color,
            title="Color del texto"
        )
        
        if color and color[1]:
            shape.color = color[1]
            self.delete(shape._canvas_id)
            shape.dibujar_en(self)
            self._save_state()
            log.info(f"Color cambiado a {color[1]} en {shape}")
    
    def _toggle_negrita_texto(self):
        """Activa/desactiva negrita en el texto seleccionado"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        shape.negrita = not shape.negrita
        self.var_negrita.set(shape.negrita)
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        self._save_state()
        log.info(f"Negrita {'activada' if shape.negrita else 'desactivada'} en {shape}")
    
    def _toggle_cursiva_texto(self):
        """Activa/desactiva cursiva en el texto seleccionado"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        shape.cursiva = not shape.cursiva
        self.var_cursiva.set(shape.cursiva)
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        self._save_state()
        log.info(f"Cursiva {'activada' if shape.cursiva else 'desactivada'} en {shape}")
    
    def _cambiar_alineacion_texto(self, nueva_alineacion: str):
        """Cambia la alineación del texto seleccionado"""
        if not self.shape_seleccionada or not isinstance(self.shape_seleccionada, Texto):
            return
        
        shape = self.shape_seleccionada
        shape.alineacion = nueva_alineacion
        self.var_alineacion.set(nueva_alineacion)
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        self._save_state()
        log.info(f"Alineación cambiada a {nueva_alineacion} en {shape}")
    
    def _cambiar_color_contorno(self):
        """Abre selector de color para el contorno"""
        if not self.shape_seleccionada: return
        
        color = colorchooser.askcolor(initialcolor=self.shape_seleccionada.color, title="Color de contorno")
        if color and color[1]:
            self.actualizar_color_seleccionado(color[1])
    
    def _cambiar_grosor_linea(self):
        """Abre diálogo para cambiar el grosor"""
        if not self.shape_seleccionada: return
        
        from tkinter import simpledialog
        nuevo_grosor = simpledialog.askfloat("Grosor de línea", "Nuevo grosor:", initialvalue=self.shape_seleccionada.grosor, minvalue=0.1, maxvalue=50.0)
        
        if nuevo_grosor is not None:
            self.actualizar_grosor_seleccionado(nuevo_grosor)
    
    def _cambiar_color_relleno(self):
        """Abre selector de color para el relleno"""
        if not self.shape_seleccionada: return
        
        color_inicial = getattr(self.shape_seleccionada, 'relleno', '') or '#ffffff'
        color = colorchooser.askcolor(initialcolor=color_inicial, title="Color de relleno")
        
        if color and color[1]:
            self.actualizar_relleno_seleccionado(color[1])
        elif color and color[1] is None:
            self.actualizar_relleno_seleccionado('')
    
    def _traer_al_frente(self):
        """Trae la figura seleccionada al frente"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        
        if shape._canvas_id is not None:
            self.tag_raise(shape._canvas_id)
        
        self.tag_raise('handle')
        log.info(f"Figura traída al frente: {shape}")
    
    def _enviar_al_fondo(self):
        """Envía la figura seleccionada al fondo"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        
        if shape._canvas_id is not None:
            self.tag_lower(shape._canvas_id)
        
        log.info(f"Figura enviada al fondo: {shape}")
    
    def _eliminar_shape_seleccionado(self):
        """Elimina la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        log.info(f"Eliminando figura: {shape}")
        
        self._save_state()
        
        if shape._canvas_id is not None:
            self.delete(shape._canvas_id)
        
        if shape in self.shapes:
            self.shapes.remove(shape)
        
        self._deseleccionar_todo()
        log.info(f"Figura eliminada: {shape}")
    
    def _duplicar_shape_seleccionado(self):
        """Duplica la figura seleccionada y la desplaza ligeramente"""
        if not self.shape_seleccionada:
            log.warning("No hay figura seleccioando para duplicar")
            return
        
        shape = self.shape_seleccionada
        log.info(f"Intentando duplicar figura: {shape}")
        
        try:
            data = shape.to_dict()
            shape_class = type(shape)
            
            if not hasattr(shape_class, 'from_dict'):
                log.error(f"La clase {shape_class.__name__} no tiene método from_dict")
                return
            
            nueva_shape = shape_class.from_dict(data)
            
            if hasattr(nueva_shape, 'mover'):
                nueva_shape.mover(20, 20)
            else:
                log.warning(f"La clase {shape_class.__name__} no tiene método mover")
            
            self.shapes.append(nueva_shape)
            nueva_shape.dibujar_en(self)
            
            self._save_state()
            self._seleccionar_shape(nueva_shape)
            
            log.info(f"Figura duplicada con éxito: {nueva_shape}")
        except Exception as e:
            log.error(f"Error al duplicar la figura: {e}", exc_info=True)
    
    # ================================================================
    # DUPLICADO
    # ================================================================
    
    def _iniciar_duplicado(self):
        """Prepara una copia de la figura seleccionada para colocar con un clic"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        log.info(f"Preparando duplicado de: {shape}")
        
        data = shape.to_dict()
        shape_class = type(shape)
        nueva_shape = shape_class.from_dict(data)
        
        self._figura_a_colocar = nueva_shape
        self._colocando_duplicado = True
        
        self.configure(cursor='crosshair')
        self._set_status("Clic izquierdo para colocar la copia, Escape para cancelar")
    
    # ================================================================
    # MÉTODOS AUXILIARES
    # ================================================================
    
    def _distancia_punto_a_segmento(self, px, py, x1, y1, x2, y2):
        """Calcula la distancia de un punto a un segmento"""
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return ((px - x1)**2 + (py - y1)**2) ** 0.5
        
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return ((px - proj_x)**2 + (py - proj_y)**2) ** 0.5
    
    # ================================================================
    # PÚBLICOS
    # ================================================================
    
    def clear_all(self):
        """Limpia completamente el canvas"""
        self.delete('all')
        self.shapes.clear()
        self.trazos.clear()
        self.contador_trazos = 0
        self._deseleccionar_todo()
        log.info("Canvas y modelo limpiados")
    
    def save_to_json(self, filepath):
        """Guarda el proyecto actual en JSON"""
        save_project(filepath, self.shapes)
    
    def load_from_json(self, filepath):
        """Carga un proyecto desde JSON"""
        self.clear_all()
        shapes = load_project(filepath)
        
        for shape in shapes:
            shape.dibujar_en(self)
            self.shapes.append(shape)
    
    # ================================================================
    # UNDO/REDO
    # ================================================================
    
    def _save_state(self):
        """Guarda el estado actual en la pila de deshacer"""
        current_state = [shape.to_dict() for shape in self.shapes]
        self.undo_stack.append(current_state)
        self.redo_stack.clear()
        
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        log.info(f"Estado guardado. undo_stack tiene {len(self.undo_stack)} elementos")
    
    def _restore_state(self, state):
        """Restaura el canvas y el modelo desde un estado guardado"""
        self.clear_all()
        
        for item in state:
            item_copy = copy.deepcopy(item)
            shape_type = item_copy.pop("type", None)
            
            cls = SHAPE_FACTORY.get(shape_type)
            if cls:
                item_copy = _reconstruir_puntos(item_copy)
                try:
                    shape = cls(**item_copy)
                    shape.dibujar_en(self)
                    self.shapes.append(shape)
                except Exception as e:
                    log.error(f"Error al restaurar figura {shape_type}: {e}")
    
    def undo(self):
        """Deshace la última acción"""
        if not self.undo_stack:
            log.info("Nada que deshacer")
            return
        
        current_state = [shape.to_dict() for shape in self.shapes]
        self.redo_stack.append(current_state)
        
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        log.info("Acción deshecha")
    
    def redo(self):
        """Rehace la última acción deshecha"""
        if not self.redo_stack:
            log.info("Nada que rehacer")
            return
        
        current_state = [shape.to_dict() for shape in self.shapes]
        self.undo_stack.append(current_state)
        
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)
        log.info("Acción rehecha")
    
    # ================================================================
    # ACTUALIZAR PROPIEDADES
    # ================================================================
    
    def actualizar_color_seleccionado(self, nuevo_color):
        """Actualiza el color de contorno de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        shape.color = nuevo_color
        
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            self.delete(shape._canvas_id)
            shape._canvas_id = None
        
        shape.dibujar_en(self)
        self._save_state()
        log.info(f"Color actualizado a {nuevo_color} en {shape}")
    
    def actualizar_relleno_seleccionado(self, nuevo_relleno):
        """Actualiza el color de relleno de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        shape.relleno = nuevo_relleno
        
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            self.delete(shape._canvas_id)
            shape._canvas_id = None
        
        shape.dibujar_en(self)
        
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        self._save_state()
        log.info(f"Relleno actualizado a '{nuevo_relleno}' en {shape}")
    
    def actualizar_grosor_seleccionado(self, nuevo_grosor):
        """Actualiza el grosor de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        shape.grosor = float(nuevo_grosor)
        
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            self.delete(shape._canvas_id)
            shape._canvas_id = None
        
        shape.dibujar_en(self)
        
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        self._save_state()
        log.info(f"Grosor actualizado a {nuevo_grosor} en {shape}")
    
    def redraw_shape(self, shape):
        """Borra y vuelve a dibujar una figura"""
        if not shape or shape._canvas_id is None:
            return
        
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        
        if self.shape_seleccionada == shape:
            if hasattr(shape, 'resaltar'):
                shape.resaltar(self, 'red')
            else:
                self.itemconfig(shape._canvas_id, outline='red')
        
        self._save_state()
    
    def _on_double_click(self, e):
        """Abre la ventana de propiedades"""
        e = self._make_world_event(e)
        
        if self.shape_seleccionada is not None:
            from ui.properties_window import PropertiesWindow
            PropertiesWindow(
                self.master,
                self,
                self.shape_seleccionada
            )