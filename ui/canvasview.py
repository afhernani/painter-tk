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
        
        self.linea_preview = None  # id de linea previa (temporal)
        self.linea_p1 = None       # primer punto de linea (punto 1)
        # Estado para modo Polyline (click izq → añadir punto, click der → finalizar)
        self.polyline_puntos = []          # Puntos acumulados [Punto, Punto, ...]
        self.polyline_segmentos_ids = []   # IDs de segmentos ya confirmados en canvas
        self.polyline_preview_id = None    # ID del segmento preview (punteado)
        # Estado para modo Polígono (click → move → click)
        self.poligono_centro = None        # Punto central (Punto)
        self.poligono_preview_id = None    # ID de la preview temporal
        self.lados_poligono = None           # Número de lados por defecto
        # Estado para modo Círculo (click → move → click)
        self.circulo_centro = None
        self.circulo_preview_id = None
        # Estado para modo Rectángulo (click → move → click)
        self.rectangulo_centro = None
        self.rectangulo_preview_id = None

        # Estado para modo Elipse (click → move → click)
        self.elipse_centro = None
        self.elipse_preview_id = None
        # Estado para modo Arco (3 clics: centro → p1 → p2)
        self.arco_centro = None
        self.arco_p1 = None
        self.arco_radio = 0.0
        self.arco_angulo_inicio = 0.0
        self.arco_estado = 0  # 0: esperando centro, 1: esperando p1, 2: esperando p2
        self.arco_preview_id = None
        # Estado para modo Texto
        self.texto_preview_id = None
        self.texto_posicion = None
        # modo duplicar elemento
        self._colocando_duplicado = False
        self._figura_a_colocar = None
        self._id_fantasma = None

        self.lin_x = None
        self.lin_y = None
        self.old_x = None
        self.old_y = None
        self.linea = None
        self.puntos_trazo = []

        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        self.handles_polyline = []  # Lista de handles para vértices de polyline
        self.polyline_segmento_drag = None
        self.handle_circulo_centro = None  # Handle verde del centro
        self.handle_circulo_perimetro = None  # Handle azul del perímetro
        # Handles del Polígono
        self.handle_poligono_centro = None  # 
        self.handles_poligono = []
        # manejadores elipse -ovalo
        self.handle_elipse_centro = None
        self.handle_elipse_eje_x = None
        self.handle_elipse_eje_y = None
        # Handles del Arco
        self.handle_arco_centro = None
        self.handle_arco_inicio = None
        self.handle_arco_final = None

        self.dragging_handle = None
        self.dragging_shape = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self._bbox_inicial = None

        self._on_status_message = None

        # Historial de Undo/Redo
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50  # Límite para no consumir mucha memoria
        
        # ----------
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_motion)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Enter>', lambda e: self._actualizar_cursor())
        self.bind('<Leave>', lambda e: self.configure(cursor=''))
        #self.bind('<Button-1>', self._on_click)
        self.bind('<Delete>', lambda e: self.eliminar_shape_seleccionada())
        self.bind('<ButtonPress-3>', self._on_right_click)   # Click derecho → finalizar
        self.bind('<Escape>', lambda e: self._cancelar_dibujo())
        self.bind('<Motion>', self._on_mouse_move) # sigue el raton
        self.bind('<Double-Button-1>', self._on_double_click)
        # En app.py o donde tengas los binds
        self.master.bind('<Control-z>', lambda e: self.undo())
        self.master.bind('<Control-y>', lambda e: self.redo())
        # establecer el foco en el canvasview
        self.focus_set()
        # guardar estado inicial
        self._save_state()
        
        log.info("CanvasView inicializado")

    # def _on_click(self, event):
    #     log.info("_on_click: click")
    #     self.focus_set()

    def _mostrar_menu_contextual(self, shape, e):
        """Construye y muestra el menú contextual según el tipo de figura"""
        # Destruir menú anterior si existe para evitar duplicados
        if hasattr(self, 'menu_contextual_actual'):
            self.menu_contextual_actual.destroy()
        
        self.menu_contextual_actual = tk.Menu(self, tearoff=0)
        
        # ─ Opciones específicas para Texto ──
        if isinstance(shape, Texto):
            self.menu_contextual_actual.add_command(label="✏️ Editar texto...", command=self._editar_texto_seleccionado)
            self.menu_contextual_actual.add_separator()
            
            # Submenú Fuentes
            submenu_fuente = tk.Menu(self.menu_contextual_actual, tearoff=0)
            for f in ["Arial", "Times New Roman", "Courier New", "Verdana", "Georgia"]:
                submenu_fuente.add_command(label=f, command=lambda fn=f: self._cambiar_fuente_texto(fn))
            self.menu_contextual_actual.add_cascade(label="🔤 Fuente", menu=submenu_fuente)
            
            # Submenú Tamaños
            submenu_tamano = tk.Menu(self.menu_contextual_actual, tearoff=0)
            for t in [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72]:
                submenu_tamano.add_command(label=str(t), command=lambda sz=t: self._cambiar_tamano_texto(sz))
            self.menu_contextual_actual.add_cascade(label="📏 Tamaño", menu=submenu_tamano)
            
            # Alineación
            submenu_alineacion = tk.Menu(self.menu_contextual_actual, tearoff=0)
            self.var_alineacion = tk.StringVar(value=shape.alineacion if hasattr(shape, 'alineacion') else "center")
            submenu_alineacion.add_radiobutton(label="⬅ Izquierda", variable=self.var_alineacion, value="left", command=lambda: self._cambiar_alineacion_texto("left"))
            submenu_alineacion.add_radiobutton(label="↔ Centro", variable=self.var_alineacion, value="center", command=lambda: self._cambiar_alineacion_texto("center"))
            submenu_alineacion.add_radiobutton(label=" Derecha", variable=self.var_alineacion, value="right", command=lambda: self._cambiar_alineacion_texto("right"))
            self.menu_contextual_actual.add_cascade(label="📐 Alineación", menu=submenu_alineacion)
            
            self.menu_contextual_actual.add_separator()
            self.var_negrita = tk.BooleanVar(value=shape.negrita)
            self.var_cursiva = tk.BooleanVar(value=shape.cursiva)
            self.menu_contextual_actual.add_checkbutton(label="**B** Negrita", variable=self.var_negrita, command=self._toggle_negrita_texto)
            self.menu_contextual_actual.add_checkbutton(label="*I* Cursiva", variable=self.var_cursiva, command=self._toggle_cursiva_texto)
            self.menu_contextual_actual.add_separator()

        # ── Opciones Comunes para TODAS las figuras (Color, Grosor, Relleno) ──
        # (Incluye Texto también si quieres, o puedes ponerlo en un 'else' si solo quieres para formas)
        
        self.menu_contextual_actual.add_command(label="🎨 Color contorno...", command=self._cambiar_color_contorno)
        self.menu_contextual_actual.add_command(label="📏 Grosor línea...", command=self._cambiar_grosor_linea)
        
        # El relleno solo tiene sentido si la figura lo soporta (no líneas ni puntos usualmente, pero lo dejamos genérico)
        if not isinstance(shape, (Linea, Polyline, PointShape)):
            self.menu_contextual_actual.add_command(label="🪣 Color relleno...", command=self._cambiar_color_relleno)
        
        self.menu_contextual_actual.add_separator()
    
        # NUEVAS OPCIONES: Orden y Eliminar
        self.menu_contextual_actual.add_command(label="⬆️ Traer al frente", command=self._traer_al_frente)
        self.menu_contextual_actual.add_command(label="️ Enviar al fondo", command=self._enviar_al_fondo)
        self.menu_contextual_actual.add_command(label="📋 Duplicar", command=self._iniciar_duplicado) # antiguo: _duplicar_shape_seleccionado
        self.menu_contextual_actual.add_separator()
        self.menu_contextual_actual.add_command(label="🗑️ Eliminar", command=self._eliminar_shape_seleccionado)
        

        # Mostrar el menú en la posición del ratón
        self.menu_contextual_actual.post(e.x_root, e.y_root)


    def _actualizar_cursor(self):
        """Actualiza el cursor según el modo actual"""
        mode = self._get_mode()
        
        if mode == 'S':
            # Modo selección: flecha normal
            self.configure(cursor='cross')
        else:
            # Resto de modos: cruz de dibujo
            self.configure(cursor='tcross')

    def _get_mode(self):
        return self._mode

    def _set_mode(self, mode):
        """Cambia el modo de dibujo y actualiza el cursor"""
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
            # También buscar en _canvas_ids (para Polyline y Circulo)
            if hasattr(shape, '_canvas_ids') and canvas_id in shape._canvas_ids:
                return shape
        return None
    
    def _get_polygon_sides(self):
        """Devuelve el número de lados del polígono (conectado desde App)"""
        log.info(f"_get_polygon_sides:")
        return self.lados_poligono
    
    # Valor por defecto
    # ---------------
    # Mover raton
    # ----------------
    def _on_mouse_move(self, e):
        """Actualiza la línea preview para que siga al cursor"""
        self._set_status(f"{e.x, e.y}")
        mode = self._get_mode()

        #self._move_elemento_duplicado(e)
        
        # Si estamos en modo línea y ya hemos hecho el primer click
        if mode == 'L' and self.linea_p1 is not None and self.linea_preview is not None:
            self.coords(self.linea_preview, self.linea_p1.x, self.linea_p1.y, e.x, e.y)
            self._set_status(f"Línea: ({self.linea_p1.x}, {self.linea_p1.y}) -> ({e.x}, {e.y})")
        
        # Preview de polyline
        if mode == 'Pl' and self.polyline_puntos and self.polyline_preview_id is not None:
            ultimo_punto = self.polyline_puntos[-1]
            self.coords(self.polyline_preview_id, ultimo_punto.x, ultimo_punto.y, e.x, e.y)
            return

        # Preview de polígono
        if mode == 'G' and self.poligono_centro is not None and self.poligono_preview_id is not None:
            radio = math.hypot(e.x - self.poligono_centro.x, e.y - self.poligono_centro.y)
            coords = []
            self.lados_poligono = self._get_polygon_sides() # llama al metodo
            angulo_paso = 2 * math.pi / self.lados_poligono
            offset = -math.pi / 2  # Empezar desde arriba
            
            for i in range(self.lados_poligono):
                theta = i * angulo_paso + offset
                coords.append(self.poligono_centro.x + radio * math.cos(theta))
                coords.append(self.poligono_centro.y + radio * math.sin(theta))
            
            self.coords(self.poligono_preview_id, *coords)
            return

        # Preview de círculo
        if mode == 'C' and self.circulo_centro is not None and self.circulo_preview_id is not None:
            radio = math.hypot(e.x - self.circulo_centro.x, e.y - self.circulo_centro.y)
            x1 = self.circulo_centro.x - radio
            y1 = self.circulo_centro.y - radio
            x2 = self.circulo_centro.x + radio
            y2 = self.circulo_centro.y + radio
            self.coords(self.circulo_preview_id, x1, y1, x2, y2)
            return
        
        # Preview de Rectángulo
        if mode == 'R' and self.rectangulo_centro is not None and self.rectangulo_preview_id is not None:
            # Calculamos la esquina opuesta para que el centro sea el punto medio
            x1 = 2 * self.rectangulo_centro.x - e.x
            y1 = 2 * self.rectangulo_centro.y - e.y
            self.coords(self.rectangulo_preview_id, x1, y1, e.x, e.y)
            return

        # Preview de Elipse
        if mode == 'E' and self.elipse_centro is not None and self.elipse_preview_id is not None:
            rx = abs(e.x - self.elipse_centro.x)
            ry = abs(e.y - self.elipse_centro.y)
            x1 = self.elipse_centro.x - rx
            y1 = self.elipse_centro.y - ry
            x2 = self.elipse_centro.x + rx
            y2 = self.elipse_centro.y + ry
            self.coords(self.elipse_preview_id, x1, y1, x2, y2)
            return
        
        # Arco
        # Preview de Arco - Etapa 1: mostrando radio hasta el ratón
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

        # Preview de Arco - Etapa 2: mostrando el arco hasta el ángulo del ratón
        if mode == 'A' and self.arco_estado == 2:
            if self.arco_preview_id is not None:
                self.delete(self.arco_preview_id)
            # correccion negativo de (e.y - centro.y)
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
        # Preview de Texto (solo muestra un punto donde se creará)
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
        # log.info(f"_move_elemento_duplicado: {e.x}, {e.y}")
        if not getattr(self, '_colocando_duplicado', False) or not self._figura_a_colocar:
            return
        
        shape = self._figura_a_colocar
        
        # 1. Borrar el fantasma anterior
        if self._id_fantasma is not None:
            if isinstance(self._id_fantasma, list):
                for fid in self._id_fantasma:
                    self.delete(fid)
            else:
                self.delete(self._id_fantasma)
        
        # 2. Actualizar la posición según el tipo de figura (usando isinstance para precisión)
        if isinstance(shape, Texto):
            # Texto: punto de referencia = posicion
            shape.posicion = Punto(e.x, e.y)
            
        elif isinstance(shape, PointShape):
            # Punto: punto de referencia = punto (o posicion)
            if hasattr(shape, 'punto'):
                shape.punto = Punto(e.x, e.y)
            elif hasattr(shape, 'posicion'):
                shape.posicion = Punto(e.x, e.y)
                
        elif isinstance(shape, (Circulo, Arco)):
            # Círculo y Arco: punto de referencia = centro
            shape.centro = Punto(e.x, e.y)
            
        elif isinstance(shape, Poligono):
            # Polígono: punto de referencia = centro (NO los vértices)
            shape.centro = Punto(e.x, e.y)
            
        elif isinstance(shape, Elipse):
            # Elipse: punto de referencia = centro (con rx, ry)
            shape.centro = Punto(e.x, e.y)
        
        elif isinstance(shape, Polyline):
            # Polyline: punto de referencia = primer punto (manteniendo la forma)
            if shape.puntos:
                dx = e.x - shape.puntos[0].x
                dy = e.y - shape.puntos[0].y
                shape.mover(dx, dy)  # Usar el método mover en lugar de crear nuevos puntos
            
        elif isinstance(shape, Rectangulo):
            # Rectángulo: punto de referencia = centro (calculado desde p1, p2)
            if hasattr(shape, 'centro'):
                shape.centro = Punto(e.x, e.y)
            else:
                # Calcular offset desde el centro actual
                cx = (shape.p1.x + shape.p2.x) / 2
                cy = (shape.p1.y + shape.p2.y) / 2
                dx = e.x - cx
                dy = e.y - cy
                shape.p1 = Punto(shape.p1.x + dx, shape.p1.y + dy)
                shape.p2 = Punto(shape.p2.x + dx, shape.p2.y + dy)
                
        elif isinstance(shape, Linea):
            # Línea: punto de referencia = p1 (manteniendo la forma)
            dx = e.x - shape.p1.x
            dy = e.y - shape.p1.y
            shape.p1 = Punto(e.x, e.y)
            shape.p2 = Punto(shape.p2.x + dx, shape.p2.y + dy)
            
        
        # 3. Dibujar el nuevo fantasma en la nueva posición
        self._id_fantasma = shape.dibujar_en(self)
        
        # 4. Intentar darle estilo de "fantasma" (línea punteada y color gris)
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
            pass  # Si el item no soporta dash o fill, lo dejamos normal

    # ================================================================
    # PRESS
    # ================================================================
    def _on_press(self, e):
        """Al presionar el boton izquierdo del ratón"""
        # log.info(f'_on_press: press {e.x},{e.y}')
        self.focus_set()
        mode = self._get_mode()
        
        # Si estamos en modo colocar duplicado, lo colocamos y SALIMOS.
        if self._iniciar_logica_colocar_duplicado(e):
            return
        log.info("_on_press: seguimos")
        # si no estamos en modo seleccion, cualquier click empieza una accion nueva.
        if mode != 'S':
            self._deseleccionar_todo()

        if mode == 'S':
            self._press_select_mode(e)
            return

        # ── MODO LÍNEA: patrón click → move → click ──
        if mode == 'L':
            if self.linea_p1 is None:
                # PRIMER CLICK: guardar punto inicial
                self.linea_p1 = Punto(e.x, e.y)
                # Crear línea preview (temporal, punteada)
                self.linea_preview = self.create_line(
                    e.x, e.y, e.x, e.y,
                    dash=(4, 2),          # Línea punteada
                    fill='gray',
                    width=1
                )
                self._set_status("Línea: mueve el cursor y haz click para el punto final (Esc para cancelar)")
            else:
                # SEGUNDO CLICK: finalizar línea con geometry.Linea
                self._finalizar_linea(e.x, e.y)
            return

        # ── MODO POLÍGONO: click (centro) → move → click (radio) ──
        if mode == 'G':
            if self.poligono_centro is None:
                # PRIMER CLICK: guardar centro
                self.poligono_centro = Punto(e.x, e.y)
                # Crear preview inicial (puntos dummy)
                self.poligono_preview_id = self.create_polygon(
                    e.x, e.y, e.x, e.y, e.x, e.y,
                    outline='gray', width=1, fill=''
                )
                self._set_status(f"Polígono: centro en ({e.x}, {e.y}). Mueve el ratón y haz click para el radio")
            else:
                # SEGUNDO CLICK: finalizar polígono
                self._finalizar_poligono(e.x, e.y)
            return


        # ── MODO PUNTO: dibujar inmediatamente con un solo click ──
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
            return  # ← Salir inmediatamente, no necesita drag
        
        # ── MODO POLYLINE: click izq añade punto, click der finaliza ──
        if mode == 'Pl':
            self._añadir_punto_polyline(e.x, e.y)
            return
        
        if mode == 'G':
            # Crear polígono preview con puntos dummy (se actualizará en motion)
            self.linea = self.create_polygon(
                e.x, e.y, e.x, e.y, e.x, e.y,
                outline='gray', width=1, fill=''
            )
            return

        # ── MODO CÍRCULO: click (centro) → move → click (radio) ──
        if mode == 'C':
            if self.circulo_centro is None:
                # PRIMER CLICK: guardar centro
                self.circulo_centro = Punto(e.x, e.y)
                # Crear preview inicial (círculo de radio 0)
                self.circulo_preview_id = self.create_oval(
                    e.x, e.y, e.x, e.y,
                    outline='gray', width=1, fill=''
                )
                self._set_status(f"Círculo: centro en ({e.x}, {e.y}). Mueve el ratón y haz click para el radio")
            else:
                # SEGUNDO CLICK: finalizar círculo
                self._finalizar_circulo(e.x, e.y)
            return

        # ── MODO RECTÁNGULO: click (centro) → move → click (esquina) ──
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

        # ── MODO ELIPSE: click (centro) → move → click (borde) ──
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

        # ── MODO ARCO: 3 clics (centro → p1 → p2) ──
        if mode == 'A':
            if self.arco_estado == 0:
                # Primer clic: centro
                self.arco_centro = Punto(e.x, e.y)
                self.arco_estado = 1
                self._set_status("Arco: centro establecido. Click para el punto inicial (radio + ángulo).")
            elif self.arco_estado == 1:
                # Segundo clic: punto inicial (define radio y ángulo de inicio)
                self.arco_p1 = Punto(e.x, e.y)
                self.arco_radio = self.arco_centro.distancia(self.arco_p1)
                # negar (e.y - centro.y) para compensar el eje y invertirlo
                self.arco_angulo_inicio = math.degrees(math.atan2(
                    -(self.arco_p1.y - self.arco_centro.y),
                    self.arco_p1.x - self.arco_centro.x
                ))
                self.arco_estado = 2
                self._set_status("Arco: punto inicial establecido. Click para el punto final.")
            elif self.arco_estado == 2:
                # Tercer clic: punto final → crear arco
                self._finalizar_arco(e.x, e.y)
            return

        # ── MODO TEXTO: click → abre diálogo → crea texto ──
        if mode == 'T':
            from tkinter import simpledialog
            # Limpiar preview
            if self.texto_preview_id is not None:
                self.delete(self.texto_preview_id)
                self.texto_preview_id = None
            # Abrir diálogo para escribir el texto
            texto_ingresado = simpledialog.askstring(
                "Insertar Texto",
                "Escribe el texto:",
                initialvalue="Texto"
            )
            
            if texto_ingresado:  # Si el usuario no canceló
                width = self._get_width()
                color = self._get_color_fg()
                tamaño = int(max(12, width*4))  # Escalar tamaño basado en grosor
                
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
            self.old_x, self.old_y = e.x, e.y   # Inicializar para el primer segmento
            return

    def _iniciar_logica_colocar_duplicado(self, e):
        """Iniciar Lógica para colocar duplicado en la posicion del click"""
        # log.info(f"_iniciar_logica_colocar_dupliado: {e.x}, {e.y}")
        
        if getattr(self, '_colocando_duplicado', False) and self._figura_a_colocar:
            shape = self._figura_a_colocar
            
            # mover la figura a la posición exacta del clic antes de dibujarla
            self._move_elemento_duplicado(e)
            
            # Borrar el fantasma
            if self._id_fantasma is not None:
                if isinstance(self._id_fantasma, list):
                    for fid in self._id_fantasma:
                        self.delete(fid)
                else:
                    self.delete(self._id_fantasma)
            
            # Dibujar la figura definitivamente
            shape.dibujar_en(self)
            self.shapes.append(shape)
            
            # Guardar estado y seleccionar la nueva figura
            self._save_state()
            self._seleccionar_shape(shape)
            
            # Resetear estado
            self._colocando_duplicado = False
            self._figura_a_colocar = None
            self._id_fantasma = None
            self._actualizar_cursor()
            
            log.info(f"Duplicado colocado con éxito en ({e.x}, {e.y})")
            return True
        
        return False

    def _on_right_click(self, e):
        """Click derecho: finaliza la polyline en progreso"""
        log.info(f"_on_right_click: {e.x}, {e.y}")
        mode = self._get_mode()

        self._cancelar_duplicado()
        
        # Solo actuamos si estamos en modo Polyline
        if mode == 'Pl' and len(self.polyline_puntos) >= 2:
            self._finalizar_polyline()
        elif mode == 'Pl' and len(self.polyline_puntos) == 1:
            # Solo hay un punto, no se puede crear polyline
            self._cancelar_polyline()
            self._set_status("Polyline cancelada: se necesitan al menos 2 puntos")
        
        # Si estamos en modo Selección, verificar si hay un Texto bajo el cursor
        if mode == 'S':
            # Buscar si hay un Texto en la posición del clic
            halo = 8
            encontrados = self.find_overlapping(e.x - halo, e.y - halo, e.x + halo, e.y + halo)
            
            for item_id in reversed(encontrados):
                tags = self.gettags(item_id)
                if 'handle' in tags:
                    continue
                shape = self._find_shape_by_id(item_id)
                if shape is not None:
                    # ¡Figura encontrada! Seleccionarla y mostrar menú
                    self._seleccionar_shape(shape)
                    self._mostrar_menu_contextual(shape, e)
                    return
            
            # Si no es un Texto, deseleccionar
            self._deseleccionar_todo()

    # ================================================================
    # MOTION
    # ================================================================
    def _on_motion(self, e):
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
        log.info(f'_on_release: release ...{e.x} : {e.y}')

        self.old_x = None
        self.old_y = None
        
        mode = self._get_mode()

        if mode == 'S':
            if self.dragging_shape or self.dragging_handle:
                # La acción de mover/redimensionar terminó, guardamos estado
                self._save_state() 
                
            self.dragging_shape = False
            self.dragging_handle = None

        if mode == 'S':
            self._release_select_mode(e)
            return
        
        # ── MODO LÍNEA: no hace nada (se finaliza en el 2do click) ──
        if mode == 'L':
            return
        
        # ── MODO POLYLINE (Pl): no hace nada al soltar, se controla con clicks ──
        if mode == 'Pl':
            return

        if mode in ('R', 'E', 'A'):
            return
        
        width = self._get_width()
        color = self._get_color_fg()

        
        # ── LÁPIZ ──
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

        # ── ARCO ──
        elif mode == 'A' and self.linea is not None:
            self.delete(self.linea)
            p1 = Punto(min(self.lin_x, e.x), min(self.lin_y, e.y))
            p2 = Punto(max(self.lin_x, e.x), max(self.lin_y, e.y))
            # Ángulo dinámico desde el punto inicial al final
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
        
        # 1. ¿Click sobre un handle?
        halo_handle = 15
        handle_items = self.find_overlapping(
            e.x - halo_handle, e.y - halo_handle,
            e.x + halo_handle, e.y + halo_handle
        )
        log.info(f"item encontrado en área de handle: {handle_items}")
        
        for item in handle_items:
            tags = self.gettags(item)
            log.info(f"Item {item} tiene tags: {tags}")
            
            # Detectar qué handle es (ANTES de borrar nada)
            handle_detectado = None
            
            # Punto
            if 'handle_punto' in tags:
                handle_detectado = 'punto'
            # Línea
            elif 'handle_start' in tags:
                handle_detectado = 'start'
            elif 'handle_end' in tags:
                handle_detectado = 'end'
            # Polyline
            elif any(tag.startswith('handle_polyline_') for tag in tags):
                for tag in tags:
                    if tag.startswith('handle_polyline_'):
                        idx = int(tag.split('_')[-1])
                        handle_detectado = f'polyline_{idx}'
                        # ✅ Buscar la polyline correcta usando el tag fig_{id}
                        fig_tag = next((t for t in tags if t.startswith('fig_')), None)
                        if fig_tag and fig_tag != 'fig_None':
                            try:
                                fig_id = int(fig_tag.split('_')[1])
                                for shape in self.shapes:
                                    # Las Polylines usan _canvas_ids (lista), no _canvas_id
                                    if hasattr(shape, '_canvas_ids') and fig_id in shape._canvas_ids:
                                        self._seleccionar_shape(shape)
                                        break
                                    elif shape._canvas_id == fig_id:
                                        self._seleccionar_shape(shape)
                                        break
                            except (ValueError, IndexError):
                                log.error(f"Error detectando polyline: tag = {fig_tag}")
                        break
            # Polígono
            elif 'handle_poligono_centro' in tags:
                handle_detectado = 'poligono_centro'
            elif any(t.startswith('handle_poligono_vertice_') for t in tags):
                idx = int([t for t in tags if t.startswith('handle_poligono_vertice_')][0].split('_')[-1])
                handle_detectado = f'poligono_vertice_{idx}'
            # Círculo
            elif 'handle_circulo_centro' in tags:
                handle_detectado = 'circulo_centro'
            elif 'handle_circulo_perimetro' in tags:
                handle_detectado = 'circulo_perimetro'
            # Elipse
            elif 'handle_elipse_centro' in tags:
                handle_detectado = 'elipse_centro'
            elif 'handle_elipse_eje_x' in tags:
                handle_detectado = 'elipse_eje_x'
            elif 'handle_elipse_eje_y' in tags:
                handle_detectado = 'elipse_eje_y'
            # Arco
            elif 'handle_arco_centro' in tags:
                handle_detectado = 'arco_centro'
            elif 'handle_arco_inicio' in tags:
                handle_detectado = 'arco_inicio'
            elif 'handle_arco_final' in tags:
                handle_detectado = 'arco_final'
            # Bbox
            elif 'handle_nw' in tags:
                handle_detectado = 'nw'
            elif 'handle_ne' in tags:
                handle_detectado = 'ne'
            elif 'handle_sw' in tags:
                handle_detectado = 'sw'
            elif 'handle_se' in tags:
                handle_detectado = 'se'
            
            # Si se detectó un handle, procesarlo
            if handle_detectado:
                log.info(f"Handle detectado: {handle_detectado}")
                
                # Buscar la figura asociada al handle
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
                
                # AHORA sí, establecer el handle a arrastrar
                self.dragging_handle = handle_detectado
                
                # Guardar bbox inicial si es un handle de bbox
                if handle_detectado in ('nw', 'ne', 'sw', 'se') and self.shape_seleccionada:
                    self._bbox_inicial = self.shape_seleccionada.bbox()
                
                return
        
        # 2. ¿Click sobre una figura (NO es un handle)?
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
        # Si no hay figura seleccionada, cancelar cualquier arrastre de handle inmediatamente
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
            elif self.dragging_handle == 'circulo_centro':  # 
                log.info("Ejecutar _mover_circulo_centro")
                self._mover_circulo_centro(e)
            elif self.dragging_handle == 'circulo_perimetro':  #
                log.info("Ejecutar _mover_circulo_perimetro")
                self._mover_circulo_perimetro(e)
            elif self.dragging_handle == 'elipse_centro':
                self._mover_elipse_centro(e)
            elif self.dragging_handle == 'elipse_eje_x':
                self._mover_elipse_eje_x(e)
            elif self.dragging_handle == 'elipse_eje_y':
                self._mover_elipse_eje_y(e)
            # handles de arco.
            elif self.dragging_handle == 'arco_centro':
                self._mover_arco_centro(e)
            elif self.dragging_handle == 'arco_inicio':
                self._mover_arco_inicio(e)
            elif self.dragging_handle == 'arco_final':
                self._mover_arco_final(e)
            # Handles de bbox
            elif self.dragging_handle in ('nw', 'ne', 'sw', 'se'):
                self._redimensionar_bbox(e)
            return
        # si no es un handle, pero estamos arrastrando la figura completa
        if self.dragging_shape and self.shape_seleccionada is not None:
            dx = e.x - self.drag_start_x
            dy = e.y - self.drag_start_y
            
            # Mover el shape usando el modelo
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
                        self.move(h[1], dx, dy) # para handles en tuplas
                    else:
                        self.move(h, dx, dy)
            
            self.drag_start_x = e.x
            self.drag_start_y = e.y

    def _release_select_mode(self, e):
        self.dragging_handle = None
        self.dragging_shape = False
        self._bbox_inicial = None

    # ================================================================
    # SELECCIONAR SHAPE (polimórfico)
    # ================================================================

    def _seleccionar_shape(self, shape):
        """Selecciona un objeto Shape del modelo"""
        log.info(f"_seleccionar_shape: shape = {shape}")
        # 1. Deseleccionar la shape anterior si existe
        if self.shape_seleccionada is not None:
            self._restaurar_apariencia(self.shape_seleccionada)
        
        # 2. Resetear estado de selección
        self._deseleccionar_todo()
        self.shape_seleccionada = shape
        self.tag_trazo_seleccionado = None
        
        # 3. Detectar si es un trazo de lápiz
        tag = getattr(shape, '_tag', '')
        log.info(f'Shape seleccionada: {shape}, tag: {tag}')
        # detectar trazo
        if tag.startswith('trazo_'):
            self.tag_trazo_seleccionado = tag
        
        # 4. Resaltar visualmente usando polimorfismo
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        elif shape.canvas_id is not None:
            if isinstance(shape, (Linea, Polyline)):
                self.itemconfig(shape.canvas_id, fill='red')
            else:
                self.itemconfig(shape.canvas_id, outline='red')
                
        # 5. Mostrar handles específicos
        if isinstance(shape, Linea) and not tag.startswith('trazo_'):
            self._mostrar_handles_linea(shape)
        elif isinstance(shape, Polyline):
            self._mostrar_handles_polyline(shape)  # Los trazos de lápiz no tienen handles por ahora
        elif isinstance(shape, Poligono):
            self._mostrar_handles_poligono(shape)
        elif isinstance(shape, Circulo):  # manejo de circulo.
            self._mostrar_handles_circulo(shape)
        elif isinstance(shape, Elipse):  # Manejo de Elipse.
            self._mostrar_handles_elipse(shape)
        elif isinstance(shape, Arco): # manejo de arco
            self._mostrar_handles_arco(shape)
        elif isinstance(shape, PointShape):
            self._mostrar_handles_punto(shape)
            #pass # PointShape no tiene manejadores
        elif isinstance(shape, Texto):
            self._mostrar_handles_bbox(shape)  # Texto usa bbox estándar
        else:
            self._mostrar_handles_bbox(shape)
            
        self._set_status(f"Seleccionado: {shape}")
    # ================================================================
    # HANDLES
    # ================================================================
    def _mostrar_handles_punto(self, shape):
        """Muestra handle en el punto"""
        self.delete('handle_punto')
        
        self.handle_punto = self.create_oval(
            shape.punto.x - 6, shape.punto.y - 6,
            shape.punto.x + 6, shape.punto.y + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_punto', f'fig_{shape._canvas_id}')
        )
        self.tag_raise('handle')
        log.info(f"Handle punto creado: {self.handle_punto}")
    
    def _mostrar_handles_para_shape(self, shape, tag):
        """Muestra los handles apropiados según el tipo de shape"""
        # Los trazos de lápiz no tienen handles editables
        if tag.startswith('trazo_'):
            return
        
        # Las líneas tienen handles en los extremos
        if isinstance(shape, Linea):
            self._mostrar_handles_linea(shape)
        # PointShape no tiene handles (es un punto, no se redimensiona)
        elif isinstance(shape, PointShape):
            pass
        # El resto de shapes tienen handles en las esquinas del bbox
        else:
            self._mostrar_handles_bbox(shape)
    
    def _mostrar_handles_linea(self, shape):
        """Muestra handle en los estremos de la línea"""
        self.delete('handle_start')
        self.delete('handle_end')
        self.handle_start = self.create_oval(
            shape.p1.x-6, shape.p1.y-6, shape.p1.x+6, shape.p1.y+6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_start', f'fig_{shape._canvas_id}')
        )
        self.handle_end = self.create_oval(
            shape.p2.x-6, shape.p2.y-6, shape.p2.x+6, shape.p2.y+6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_end', f'fig_{shape._canvas_id}')
        )
        self.tag_raise('handle')
        log.info(f"Handles línea creados: {self.handle_start}, {self.handle_end}")

    def _mover_handle_polyline(self, e):
        """Mueve un vértice de una polyline"""
        if not isinstance(self.shape_seleccionada, Polyline):
            return
        
        shape = self.shape_seleccionada
        idx = int(self.dragging_handle.split('_')[-1])
        
        if 0 <= idx < len(shape.puntos):
            # Actualizar el punto en el modelo
            shape.puntos[idx].x = float(e.x)
            shape.puntos[idx].y = float(e.y)
            
            # Actualizar los segmentos conectados en el canvas
            shape.actualizar_en_canvas(self)
            
            # Mover el handle visual
            if idx < len(self.handles_polyline):
                self.coords(self.handles_polyline[idx], e.x-6, e.y-6, e.x+6, e.y+6)

    def _mostrar_handles_bbox(self, shape):
        bbox = shape.bbox()
        if bbox is None:
            return
        x1, y1, x2, y2 = bbox
        self.delete('handle')
        self.handle_nw = self.create_oval(
            x1-6, y1-6, x1+6, y1+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}'))
        self.handle_ne = self.create_oval(
            x2-6, y1-6, x2+6, y1+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}'))
        self.handle_sw = self.create_oval(
            x1-6, y2-6, x1+6, y2+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}'))
        self.handle_se = self.create_oval(
            x2-6, y2-6, x2+6, y2+6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_se', f'fig_{shape._canvas_id}'))

    def _mover_handle_linea(self, e):
        """Mueve un extremo de una línea del modelo"""
        shape = self.shape_seleccionada
        if not isinstance(shape, Linea):
            return
            
        if self.dragging_handle == 'start':
            # Actualizar el modelo (Punto p1)
            shape.p1.x = float(e.x)
            shape.p1.y = float(e.y)
            # Actualizar la vista (Canvas)
            shape.actualizar_en_canvas(self)
            # Mover el handle visual
            self.coords(self.handle_start, e.x-6, e.y-6, e.x+6, e.y+6)
            
        elif self.dragging_handle == 'end':
            # Actualizar el modelo (Punto p2)
            shape.p2.x = float(e.x)
            shape.p2.y = float(e.y)
            # Actualizar la vista (Canvas)
            shape.actualizar_en_canvas(self)
            # Mover el handle visual
            self.coords(self.handle_end, e.x-6, e.y-6, e.x+6, e.y+6)

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

        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        if self.handle_nw:
            self.coords(self.handle_nw, x_min-6, y_min-6, x_min+6, y_min+6)
        if self.handle_ne:
            self.coords(self.handle_ne, x_max-6, y_min-6, x_max+6, y_min+6)
        if self.handle_sw:
            self.coords(self.handle_sw, x_min-6, y_max-6, x_min+6, y_max+6)
        if self.handle_se:
            self.coords(self.handle_se, x_max-6, y_max-6, x_max+6, y_max+6)

    def _mostrar_handles_polyline(self, shape):
        """Muestra handles azules en cada vértice de la polyline"""
        # Limpiar handles anteriores
        if hasattr(self, 'handles_polyline'):
            for h in self.handles_polyline:
                if h is not None:
                    self.delete(h)
        
        self.handles_polyline = []
        # Usar el primer segmento como ID (si existe)
        fig_id = shape._canvas_id if shape._canvas_id else (shape._canvas_ids[0] if hasattr(shape, '_canvas_ids') and shape._canvas_ids else 'polyline')
    
        
        for i, punto in enumerate(shape.puntos):
            handle = self.create_oval(
                punto.x - 6, punto.y - 6, punto.x + 6, punto.y + 6,
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
        
        # Handle del centro (guardado en su propia variable, no en la lista)
        self.handle_poligono_centro = self.create_oval(
            shape.centro.x - 6, shape.centro.y - 6,
            shape.centro.x + 6, shape.centro.y + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_poligono_centro', f'fig_{shape._canvas_id}')
        )
        
        # Handles de vértices (guardados en la lista)
        vertices = shape.obtener_vertices()
        for i, v in enumerate(vertices):
            handle = self.create_oval(
                v.x - 6, v.y - 6, v.x + 6, v.y + 6,
                fill='blue', outline='white', width=2,
                tags=('handle', f'handle_poligono_vertice_{i}', f'fig_{shape._canvas_id}')
            )
            self.handles_poligono.append(handle)
            
        self.tag_raise('handle')
        log.info(f"Handles polígono creados: centro={self.handle_poligono_centro}, {len(self.handles_poligono)} vértices")
    # ================================================================
    # RESTAURAR (polimórfico)
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
        
        # self.delete('handle')
        # NO borrar todos los handles, solo los específicos
        if self.handle_start: self.delete(self.handle_start)
        if self.handle_end: self.delete(self.handle_end)
        if self.handle_nw: self.delete(self.handle_nw)
        if self.handle_ne: self.delete(self.handle_ne)
        if self.handle_sw: self.delete(self.handle_sw)
        if self.handle_se: self.delete(self.handle_se)
        
        if self.handle_circulo_centro: self.delete(self.handle_circulo_centro)
        if self.handle_circulo_perimetro: self.delete(self.handle_circulo_perimetro)

        # Borrar handles de polyline (pueden ser IDs o tuplas)
        for h in getattr(self, 'handles_polyline', []):
            if isinstance(h, tuple): self.delete(h[1])
            else: self.delete(h)
        # Borrar handles de polígono
        # Borrar handles de polígono
        if hasattr(self, 'handle_poligono_centro') and self.handle_poligono_centro:
            self.delete(self.handle_poligono_centro)
            self.handle_poligono_centro = None
            
        for h in getattr(self, 'handles_poligono', []):
            if h is not None:
                self.delete(h)
        self.handles_poligono = []

        # 3. Como red de seguridad, intentar borrar por tag también
        self.delete('handle')
        # Limpiar preview de texto
        if self.texto_preview_id is not None:
            self.delete(self.texto_preview_id)
            self.texto_preview_id = None
        # resetear todas las variables de estado.
        self.shape_seleccionada = None
        self.tag_trazo_seleccionado = None
        self.handle_start = None
        self.handle_end = None
        self.handle_nw = None
        self.handle_ne = None
        self.handle_sw = None
        self.handle_se = None
        self.handle_poligono_centro = None
        self.handles_poligono = []  # limpiar handles de poligono
        self.handles_polyline = []  # Limpiar handles de polyline
        self.polyline_segmento_drag = None  # Limpiar segmento
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
            # Eliminar todos los canvas_ids (para Polyline y Circulo)
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
    # -------------
    # Punto
    # -------------
    def _mover_punto(self, e):
        """Mueve el punto seleccionado"""
        shape = self.shape_seleccionada
        if not isinstance(shape, PointShape): return
        
        # Borrar el punto anterior
        if shape._canvas_id is not None:
            self.delete(shape._canvas_id)
        
        # Mover el punto
        dx = e.x - shape.punto.x
        dy = e.y - shape.punto.y
        shape.mover(dx, dy)
        
        # Redibujar el punto
        shape.dibujar_en(self)
        
        # Actualizar el handle
        if self.handle_punto:
            self.coords(self.handle_punto,
                        shape.punto.x - 6, shape.punto.y - 6,
                        shape.punto.x + 6, shape.punto.y + 6)
        self._save_state()
            
    # -------------------------
    # Línea
    # -------------------------
    def _finalizar_linea(self, x2, y2):
        """
        Borra la preview y crea la Linea definitiva del modelo geometry
        """
        width = self._get_width()
        color = self._get_color_fg()

        # Borrar preview punteada
        if self.linea_preview is not None:
            self.delete(self.linea_preview)
            self.linea_preview = None

        # Crear línea definitiva del modelo geometry
        p2 = Punto(x2, y2)
        shape = Linea(self.linea_p1, p2, color=color, grosor=width)
        shape._tag = 'Line'
        shape.dibujar_en(self)
        self.shapes.append(shape)
        log.info(f"Línea creada: {shape} (p1={self.linea_p1}, p2={p2})")

        # Resetear estado → listo para la siguiente línea
        self.linea_p1 = None
        self._set_status("Línea creada. Click para otra línea o cambia de modo.")
        self._save_state()

    # -----------------
    # polyline
    # -------------------
    def _añadir_punto_polyline(self, x, y):
        """Añade un punto a la polyline en progreso"""
        nuevo_punto = Punto(x, y)
        self.polyline_puntos.append(nuevo_punto)
        
        # Si ya hay un punto anterior, crear segmento confirmado
        if len(self.polyline_puntos) >= 2:
            p_anterior = self.polyline_puntos[-2]
            width = self._get_width()
            color = self._get_color_fg()
            cid = self.create_line(
                p_anterior.x, p_anterior.y, x, y,
                fill=color, width=width, capstyle=tk.ROUND
            )
            self.polyline_segmentos_ids.append(cid)
        
        # Crear/actualizar preview punteada desde el último punto
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
            # Calcular distancia del punto (x, y) al segmento p1-p2
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
            
        # Calcular el desplazamiento desde la última posición
        dx = e.x - self.drag_start_x
        dy = e.y - self.drag_start_y
        
        # Mover el polígono
        shape.mover(dx, dy)
        shape.actualizar_en_canvas(self)
        
        # Actualizar los handles para que sigan al polígono
        self._actualizar_handles_poligono()
        
        # Actualizar la posición de inicio para el siguiente frame
        self.drag_start_x = e.x
        self.drag_start_y = e.y

    def _finalizar_polyline(self):
        """Borra previews y crea la Polyline definitiva del modelo"""
        # Borrar preview punteada
        if self.polyline_preview_id is not None:
            self.delete(self.polyline_preview_id)
            self.polyline_preview_id = None
        
        # Borrar segmentos temporales ya dibujados (para evitar dibujo doble)
        for cid in self.polyline_segmentos_ids:
            self.delete(cid)
        self.polyline_segmentos_ids = []
        
        # Crear Polyline del modelo geometry
        width = self._get_width()
        color = self._get_color_fg()
        
        shape = Polyline(self.polyline_puntos, color=color, grosor=width)
        tag_trazo = f'trazo_{self.contador_trazos}'
        self.contador_trazos += 1
        shape._tag = tag_trazo
        shape._original_color = color # Guardar color original
        
        # Dibujar en canvas (crea todos los segmentos con el tag único)
        shape.dibujar_en(self)
        self.shapes.append(shape)
        self.trazos[tag_trazo] = shape
        
        log.info(f"Polyline creada: {tag_trazo} ({len(self.polyline_puntos)} puntos)")
        
        # Resetear estado
        self.polyline_puntos = []
        self.polyline_segmentos_ids = []
        self._set_status(f"Polyline creada con {len(shape.puntos)} puntos")

    def _cancelar_polyline(self):
        """Cancela la polyline en progreso"""
        # Borrar segmentos ya dibujados
        for cid in self.polyline_segmentos_ids:
            self.delete(cid)
        # Borrar preview
        if self.polyline_preview_id is not None:
            self.delete(self.polyline_preview_id)
            self.polyline_preview_id = None
        # Resetear estado
        self.polyline_puntos = []
        self.polyline_segmentos_ids = []
        self._set_status("Polyline cancelada")

    # -----------------
    # Cancelar dibujo
    # -----------------
    def _cancelar_dibujo(self):
        """Cancela cualquier dibujo en progreso (línea o polyline)"""
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
        """Canelar el duplicado de shape"""
        if self._colocando_duplicado:
            if self._id_fantasma is not None:
                self.delete(self._id_fantasma)
            self._colocando_duplicado = False
            self._figura_a_colocar = None
            self._id_fantasma = None
            self._actualizar_cursor()
            self._set_status("Duplicado cancelado")
            return

    # ----------------
    # Poligono
    # ----------------
    def _finalizar_poligono(self, x, y):
        """Borra la preview y crea el Polígono definitivo del modelo"""
        # Borrar preview
        if self.poligono_preview_id is not None:
            self.delete(self.poligono_preview_id)
            self.poligono_preview_id = None
        
        # Calcular radio
        radio = math.hypot(x - self.poligono_centro.x, y - self.poligono_centro.y)
        
        # Evitar polígonos de radio 0
        if radio < 2:
            self.poligono_centro = None
            return
        
        # Crear Polígono del modelo
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
        
        # Resetear estado
        self.poligono_centro = None
        self._set_status(f"Polígono creado con {self.lados_poligono} lados")
        self._save_state()

    def _mover_poligono_centro(self, e):
        """Mueve el centro del polígono (traslada todo)"""
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
        
        # 1. Actualizar handle centro
        if self.handle_poligono_centro:
            self.coords(self.handle_poligono_centro,
                        shape.centro.x - 6, shape.centro.y - 6,
                        shape.centro.x + 6, shape.centro.y + 6)
        
        # 2. Actualizar handles vértices
        vertices = shape.obtener_vertices()
        for i, v in enumerate(vertices):
            if i < len(self.handles_poligono):
                self.coords(self.handles_poligono[i],
                            v.x - 6, v.y - 6, v.x + 6, v.y + 6)

    def _detectar_segmento_poligono(self, x, y, shape: Poligono):
        vertices = shape.obtener_vertices()
        min_dist = 10  # Umbral de proximidad
        segmento_cercano = None
        for i in range(len(vertices)):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % len(vertices)]
            dist = self._distancia_punto_a_segmento(x, y, p1.x, p1.y, p2.x, p2.y)
            if dist < min_dist:
                min_dist = dist
                segmento_cercano = i
        return segmento_cercano

    # ------------------
    # circulo
    # ------------------
    def _finalizar_circulo(self, x, y):
        """Borra la preview y crea el Círculo definitivo del modelo"""
        # Borrar preview
        if self.circulo_preview_id is not None:
            self.delete(self.circulo_preview_id)
            self.circulo_preview_id = None
        
        # Calcular radio
        radio = math.hypot(x - self.circulo_centro.x, y - self.circulo_centro.y)
        
        # Evitar círculos de radio 0
        if radio < 2:
            self.circulo_centro = None
            return
        
        # Crear Círculo del modelo
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
        
        # Resetear estado
        self.circulo_centro = None
        self._set_status("Círculo creado")
        self._save_state()

    # --------------
    # Rectangulo
    #---------------
    def _finalizar_rectangulo(self, x, y):
        """Borra la preview y crea el Rectángulo definitivo"""
        if self.rectangulo_preview_id is not None:
            self.delete(self.rectangulo_preview_id)
            self.rectangulo_preview_id = None
        
        x1 = 2 * self.rectangulo_centro.x - x
        y1 = 2 * self.rectangulo_centro.y - y
        
        # Evitar rectángulos de tamaño 0
        if abs(x - self.rectangulo_centro.x) < 2 or abs(y - self.rectangulo_centro.y) < 2:
            self.rectangulo_centro = None
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        
        # Asumiendo que tu constructor es Rectangulo(p1, p2, ...)
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
        
        x1, y1 = min(shape.p1.x, shape.p2.x), min(shape.p1.y, shape.p2.y)
        x2, y2 = max(shape.p1.x, shape.p2.x), max(shape.p1.y, shape.p2.y)
        
        self.handle_nw = self.create_oval(
            x1 - 6, y1 - 6, x1 + 6, y1 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}')
        )
        self.handle_ne = self.create_oval(
            x2 - 6, y1 - 6, x2 + 6, y1 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}')
        )
        self.handle_sw = self.create_oval(
            x1 - 6, y2 - 6, x1 + 6, y2 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}')
        )
        self.handle_se = self.create_oval(
            x2 - 6, y2 - 6, x2 + 6, y2 + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_se', f'fig_{shape._canvas_id}')
        )
        
        self.tag_raise('handle')
        log.info(f"Handles rectángulo creados: {self.handle_nw}, {self.handle_ne}, {self.handle_sw}, {self.handle_se}")

    # ----------------
    # Elipse
    # ----------------
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
        
        # Asumiendo que tu constructor es Elipse(centro, radio_x, radio_y, ...)
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
        # Limpiar handles anteriores
        self.delete('handle_elipse_centro')
        self.delete('handle_elipse_eje_x')
        self.delete('handle_elipse_eje_y')
        
        # 1. Handle del centro (Verde)
        self.handle_elipse_centro = self.create_oval(
            shape.centro.x - 6, shape.centro.y - 6,
            shape.centro.x + 6, shape.centro.y + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_elipse_centro', f'fig_{shape._canvas_id}')
        )
        
        # 2. Handle Eje X (Azul - Borde derecho)
        self.handle_elipse_eje_x = self.create_oval(
            shape.centro.x + shape.radio_x - 6, shape.centro.y - 6,
            shape.centro.x + shape.radio_x + 6, shape.centro.y + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_elipse_eje_x', f'fig_{shape._canvas_id}')
        )
        
        # 3. Handle Eje Y (Azul - Borde inferior)
        self.handle_elipse_eje_y = self.create_oval(
            shape.centro.x - 6, shape.centro.y + shape.radio_y - 6,
            shape.centro.x + 6, shape.centro.y + shape.radio_y + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_elipse_eje_y', f'fig_{shape._canvas_id}')
        )
        
        # Traer al frente para que sean clicables
        self.tag_raise('handle')
        log.info(f"Handles elipse creados: centro={self.handle_elipse_centro}, eje_x={self.handle_elipse_eje_x}, eje_y={self.handle_elipse_eje_y}")

    def _mover_elipse_centro(self, e):
        """Mueve el centro de la elipse (traslación)"""
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
        
        # Actualizar centro
        if self.handle_elipse_centro:
            self.coords(self.handle_elipse_centro,
                        shape.centro.x - 6, shape.centro.y - 6,
                        shape.centro.x + 6, shape.centro.y + 6)
        
        # Actualizar Eje X
        if self.handle_elipse_eje_x:
            p = shape.obtener_punto_eje_x()
            self.coords(self.handle_elipse_eje_x,
                        p.x - 6, p.y - 6, p.x + 6, p.y + 6)
        
        # Actualizar Eje Y
        if self.handle_elipse_eje_y:
            p = shape.obtener_punto_eje_y()
            self.coords(self.handle_elipse_eje_y,
                        p.x - 6, p.y - 6, p.x + 6, p.y + 6)


    # ----------------------
    # Manejadores de circulo
    # ----------------------
    def _mostrar_handles_circulo(self, shape: Circulo):
        """Muestra handles en el centro y en el perímetro del círculo"""
        log.info(f"Mostrando handles del circulo: centro={shape.centro}, radio={shape.radio}")
        #self.delete('handle')
        # NO borrar todos los handles, solo los de círculo
        self.delete('handle_circulo_centro')
        self.delete('handle_circulo_perimetro')
        
        # Handle del centro (verde)
        self.handle_circulo_centro = self.create_oval(
            shape.centro.x - 6, shape.centro.y - 6,
            shape.centro.x + 6, shape.centro.y + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_circulo_centro', f'fig_{shape._canvas_id}')
        )
        
        log.info(f"Handle centro creado: {self.handle_circulo_centro}")

        # Handle del perímetro (azul) - a la derecha del centro
        punto_perimetro = shape.obtener_punto_perimetro()
        self.handle_circulo_perimetro = self.create_oval(
            punto_perimetro.x - 6, punto_perimetro.y - 6,
            punto_perimetro.x + 6, punto_perimetro.y + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_circulo_perimetro', f'fig_{shape._canvas_id}')
        )
        log.info(f"Handle perímetro creado: {self.handle_circulo_perimetro} en {punto_perimetro}")
    
        # Traer los handles al frente para que sean visibles
        self.tag_raise('handle')

    def _mover_circulo_centro(self, e):
        """Mueve el centro del círculo (traslada todo)"""
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
        """Mueve el perímetro del círculo (cambia el radio)"""
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
        
        # Actualizar handle centro
        if self.handle_circulo_centro is not None:
            self.coords(self.handle_circulo_centro,
                        shape.centro.x - 6, shape.centro.y - 6,
                        shape.centro.x + 6, shape.centro.y + 6)
        
        # Actualizar handle perímetro
        if self.handle_circulo_perimetro is not None:
            punto_perimetro = shape.obtener_punto_perimetro()
            self.coords(self.handle_circulo_perimetro,
                        punto_perimetro.x - 6, punto_perimetro.y - 6,
                        punto_perimetro.x + 6, punto_perimetro.y + 6)

    # -------------
    # Arco
    #--------------
    def _finalizar_arco(self, x, y):
        """Crea el arco definitivo tras el tercer clic"""
        # Borrar preview
        if self.arco_preview_id is not None:
            self.delete(self.arco_preview_id)
            self.arco_preview_id = None
        
        # Calcular ángulo final
        p2 = Punto(x, y)
        # correccion negativa (p2 - centro.y)
        angulo_final = math.degrees(math.atan2(
            -(p2.y - self.arco_centro.y),
            p2.x - self.arco_centro.x
        ))
        extension = angulo_final - self.arco_angulo_inicio
        
        # Evitar arcos de tamaño 0
        if self.arco_radio < 2 or abs(extension) < 1:
            self._reset_arco_estado()
            return
        
        width = self._get_width()
        color = self._get_color_fg()
        relleno = config.get('Pen', 'default_color_fill', '')
        
        # Crear la figura del modelo
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
        
        # Limpiar handles anteriores
        self.delete('handle_arco_centro')
        self.delete('handle_arco_inicio')
        self.delete('handle_arco_final')
        
        # 1. Handle del centro (Verde)
        self.handle_arco_centro = self.create_oval(
            shape.centro.x - 6, shape.centro.y - 6,
            shape.centro.x + 6, shape.centro.y + 6,
            fill='green', outline='white', width=2,
            tags=('handle', 'handle_arco_centro',f'fig_{shape._canvas_id}')
        )
        
        # 2. Handle del punto inicial (Azul)
        p_inicio = shape.obtener_punto_inicio()
        self.handle_arco_inicio = self.create_oval(
            p_inicio.x - 6, p_inicio.y - 6,
            p_inicio.x + 6, p_inicio.y + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_arco_inicio', f'fig_{shape._canvas_id}')
        )
        
        # 3. Handle del punto final (Azul)
        p_final = shape.obtener_punto_final()
        self.handle_arco_final = self.create_oval(
            p_final.x - 6, p_final.y - 6,
            p_final.x + 6, p_final.y + 6,
            fill='blue', outline='white', width=2,
            tags=('handle', 'handle_arco_final', f'fig_{shape._canvas_id}')
        )
        
        # Traer al frente
        self.tag_raise('handle')
        log.info(f"Handles arco creados: centro={self.handle_arco_centro}, inicio={self.handle_arco_inicio}, final={self.handle_arco_final}")

    def _mover_arco_centro(self, e):
        """Mueve el centro del arco (traslación)"""
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
        
        # Actualizar centro
        if self.handle_arco_centro:
            self.coords(self.handle_arco_centro,
                        shape.centro.x - 6, shape.centro.y - 6,
                        shape.centro.x + 6, shape.centro.y + 6)
        
        # Actualizar punto inicial
        if self.handle_arco_inicio:
            p = shape.obtener_punto_inicio()
            self.coords(self.handle_arco_inicio,
                        p.x - 6, p.y - 6, p.x + 6, p.y + 6)
        
        # Actualizar punto final
        if self.handle_arco_final:
            p = shape.obtener_punto_final()
            self.coords(self.handle_arco_final,
                        p.x - 6, p.y - 6, p.x + 6, p.y + 6)

    # ---------------
    # Texto Manejo
    # ---------------
    def _mostrar_handles_texto(self, shape: Texto):
        """Muestra handles de bbox alrededor del texto"""
        # Obtener bbox real del canvas
        if shape._canvas_id:
            bbox = self.bbox(shape._canvas_id)
            if bbox:
                x1, y1, x2, y2 = bbox
                self.delete('handle')
                
                self.handle_nw = self.create_oval(
                    x1 - 6, y1 - 6, x1 + 6, y1 + 6,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_nw', f'fig_{shape._canvas_id}')
                )
                self.handle_ne = self.create_oval(
                    x2 - 6, y1 - 6, x2 + 6, y1 + 6,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_ne', f'fig_{shape._canvas_id}')
                )
                self.handle_sw = self.create_oval(
                    x1 - 6, y2 - 6, x1 + 6, y2 + 6,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_sw', f'fig_{shape._canvas_id}')
                )
                self.handle_se = self.create_oval(
                    x2 - 6, y2 - 6, x2 + 6, y2 + 6,
                    fill='blue', outline='white', width=2,
                    tags=('handle', 'handle_se', f'fig_{shape._canvas_id}')
                )
                
                self.tag_raise('handle')
                log.info(f"Handles texto creados en bbox: {bbox}")

    # Acciones del menu contextual
    def _actualizar_estado_menu_texto(self, shape: Texto):
        """Actualiza el estado de los checkbuttons del menú según el texto seleccionado"""
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
            # Redibujar
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
        
        if color and color[1]:  # color[1] es el hex string
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
        
        # Redibujar
        self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        
        # Si está resaltada, volver a resaltar
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        self._save_state()
        log.info(f"Alineación cambiada a {nueva_alineacion} en {shape}")

    def _cambiar_color_contorno(self):
        """Abre selector de color para el contorno"""
        if not self.shape_seleccionada: return
        color = colorchooser.askcolor(initialcolor=self.shape_seleccionada.color, title="Color de contorno")
        if color and color[1]:
            self.actualizar_color_seleccionado(color[1]) # Ya tienes este método implementado

    def _cambiar_grosor_linea(self):
        """Abre diálogo para cambiar el grosor"""
        if not self.shape_seleccionada: return
        from tkinter import simpledialog
        nuevo_grosor = simpledialog.askfloat("Grosor de línea", "Nuevo grosor:", initialvalue=self.shape_seleccionada.grosor, minvalue=0.1, maxvalue=50.0)
        if nuevo_grosor is not None:
            self.actualizar_grosor_seleccionado(nuevo_grosor) # Ya tienes este método implementado

    def _cambiar_color_relleno(self):
        """Abre selector de color para el relleno"""
        if not self.shape_seleccionada: return
        
        # Color inicial (si no tiene, usar blanco o transparente)
        color_inicial = getattr(self.shape_seleccionada, 'relleno', '') or '#ffffff'
        
        color = colorchooser.askcolor(initialcolor=color_inicial, title="Color de relleno")
        if color and color[1]:
            self.actualizar_relleno_seleccionado(color[1]) # Ya tienes este método implementado
        elif color and color[1] is None: 
            # Si el usuario elige "Transparente" o cancela de cierta forma en algunos OS
            self.actualizar_relleno_seleccionado('') 

    def _traer_al_frente(self):
        """Trae la figura seleccionada al frente (encima de todas las demás)"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        
        # Traer al frente en el canvas
        if shape._canvas_id is not None:
            self.tag_raise(shape._canvas_id)
        
        # También traer al frente los handles si están visibles
        self.tag_raise('handle')
        
        log.info(f"Figura traída al frente: {shape}")

    def _enviar_al_fondo(self):
        """Envía la figura seleccionada al fondo (debajo de todas las demás)"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        
        # Enviar al fondo en el canvas
        if shape._canvas_id is not None:
            self.tag_lower(shape._canvas_id)
        
        log.info(f"Figura enviada al fondo: {shape}")

    def _eliminar_shape_seleccionado(self):
        """Elimina la figura seleccionada del canvas y de la lista"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        log.info(f"Eliminando figura: {shape}")
        
        # Guardar estado ANTES de eliminar (para que el Undo funcione)
        self._save_state()
        
        # Borrar del canvas
        if shape._canvas_id is not None:
            self.delete(shape._canvas_id)
        
        # Borrar de la lista de shapes
        if shape in self.shapes:
            self.shapes.remove(shape)
        
        # Limpiar la selección
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
            # 1. Serializar y deserializar para crear una copia independiente
            data = shape.to_dict()
            shape_class = type(shape)
            
            if not hasattr(shape_class, 'from_dict'):
                log.error(f"La clase {shape_class.__name__} no tiene método from_dict")
                return
                
            nueva_shape = shape_class.from_dict(data)
            
            # 2. Desplazar la copia 20 píxeles para que sea visible
            if hasattr(nueva_shape, 'mover'):
                nueva_shape.mover(20, 20)
            else:
                log.warning(f"La clase {shape_class.__name__} no tiene método mover")
            
            # 3. Añadir a la lista y dibujar
            self.shapes.append(nueva_shape)
            nueva_shape.dibujar_en(self)
            
            # 4. Guardar estado y seleccionar
            self._save_state()
            self._seleccionar_shape(nueva_shape)
            
            log.info(f"Figura duplicada con éxito: {nueva_shape}")
            
        except Exception as e:
            # Esto imprimirá el error exacto en la consola si algo falla
            log.error(f"Error al duplicar la figura: {e}", exc_info=True)

    # ----------------------
    # duplicado de shape
    # ----------------------
    def _iniciar_duplicado(self):
        """Prepara una copia de la figura seleccionada para colocar con un clic"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        log.info(f"Preparando duplicado de: {shape}")
        
        # 1. Crear la copia usando serialización
        data = shape.to_dict()
        shape_class = type(shape)
        nueva_shape = shape_class.from_dict(data)
        
        # 2. Guardar en variables temporales (NO dibujar todavía)
        self._figura_a_colocar = nueva_shape
        self._colocando_duplicado = True
        
        # 3. Cambiar el cursor para indicar que estamos "colocando"
        self.configure(cursor='crosshair')
        self._set_status("Clic izquierdo para colocar la copia, Escape para cancelar")

    # ------------------
    # Metodos auxiliar
    # ------------------
    def _distancia_punto_a_segmento(self, px, py, x1, y1, x2, y2):
        """Calcula la distancia de un punto (px, py) a un segmento (x1,y1)-(x2,y2)"""
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
    
    # --------------
    # Deshacer / Rehacer (Undo / Redo)
    # -------------
    def _save_state(self):
        """Guarda el estado actual en la pila de deshacer"""
        # Serializamos las figuras actuales a diccionarios (copias limpias)
        current_state = [shape.to_dict() for shape in self.shapes]
        
        self.undo_stack.append(current_state)
        self.redo_stack.clear()  # Una acción nueva invalida el rehacer
        
        # Limitar el tamaño del historial
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        log.info(f"Estado guardado. undo_stack tiene {len(self.undo_stack)} elementos")

    def _restore_state(self, state):
        """Restaura el canvas y el modelo desde un estado guardado"""
        self.clear_all()  # Limpia canvas y listas
        
        # Reconstruir figuras (usando la lógica de json_storage)
        for item in state:
            # Copiamos para no mutar el original al hacer pop
            item_copy = copy.deepcopy(item)
            shape_type = item_copy.pop("type", None)
            
            # Necesitamos el factory. Puedes importarlo de storage.json_storage
            # o tenerlo definido aquí. Asumimos que importas SHAPE_FACTORY y _reconstruir_puntos
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
            
        # Guardar estado actual en rehacer
        current_state = [shape.to_dict() for shape in self.shapes]
        self.redo_stack.append(current_state)
        
        # Restaurar el anterior
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        log.info("Acción deshecha")

    def redo(self):
        """Rehace la última acción deshecha"""
        if not self.redo_stack:
            log.info("Nada que rehacer")
            return
            
        # Guardar estado actual en deshacer
        current_state = [shape.to_dict() for shape in self.shapes]
        self.undo_stack.append(current_state)
        
        # Restaurar el siguiente
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)
        log.info("Acción rehecha")
    
    # Actualizar color de linea / relleno objetos seleccionados.
    def actualizar_color_seleccionado(self, nuevo_color):
        """Actualiza el color de contorno de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        shape = self.shape_seleccionada
        shape.color = nuevo_color
        
        # Borrar todos los canvas IDs de la figura
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            # Figuras con múltiples IDs (Polyline, etc.)
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            # Figuras con un solo ID
            self.delete(shape._canvas_id)
            shape._canvas_id = None
        
        # Redibujar la figura
        shape.dibujar_en(self)
        
        # Si está seleccionada, aplicar resaltado visual
        # if self.shape_seleccionada == shape:
        #     if isinstance(shape, (Linea, Polyline)):
        #         # Para líneas, el resaltado usa fill
        #         self.itemconfig(shape._canvas_id, fill='red', width=shape.grosor + 1)
        #     else:
        #         # Para otras figuras, usa outline
        #         self.itemconfig(shape._canvas_id, outline='red', width=shape.grosor + 1)


        # Si está resaltada (seleccionada), volver a resaltar
        # if hasattr(shape, 'resaltar'):
        #     shape.resaltar(self, 'red')
        
        # Guardar estado para undo/redo
        self._save_state()
        log.info(f"Color actualizado a {nuevo_color} en {shape}")

    def actualizar_relleno_seleccionado(self, nuevo_relleno):
        """Actualiza el color de relleno de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        shape.relleno = nuevo_relleno
        
        # Borrar todos los canvas IDs de la figura
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            self.delete(shape._canvas_id)
            shape._canvas_id = None

        # Redibujar la figura
        #self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        
        # Si está resaltada (seleccionada), volver a resaltar
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        # Guardar estado para undo/redo
        self._save_state()
        
        log.info(f"Relleno actualizado a '{nuevo_relleno}' en {shape}")
    
    def actualizar_grosor_seleccionado(self, nuevo_grosor):
        """Actualiza el grosor de la figura seleccionada"""
        if not self.shape_seleccionada:
            return
        
        shape = self.shape_seleccionada
        shape.grosor = float(nuevo_grosor)
        
        # Borrar todos los canvas IDs de la figura
        if hasattr(shape, '_canvas_ids') and shape._canvas_ids:
            for cid in shape._canvas_ids:
                self.delete(cid)
            shape._canvas_ids = []
        elif hasattr(shape, '_canvas_id') and shape._canvas_id is not None:
            self.delete(shape._canvas_id)
            shape._canvas_id = None

        # Redibujar la figura
        # self.delete(shape._canvas_id)
        shape.dibujar_en(self)
        
        # Si está resaltada, volver a resaltar
        if hasattr(shape, 'resaltar'):
            shape.resaltar(self, 'red')
        
        # Guardar estado
        self._save_state()
        
        log.info(f"Grosor actualizado a {nuevo_grosor} en {shape}")

    # Metodos para modificar propiedades.
    def redraw_shape(self, shape):
        """Borra y vuelve a dibujar una figura manteniendo su estado de selección"""
        if not shape or shape._canvas_id is None:
            return
            
        # 1. Borramos la figura antigua del canvas
        self.delete(shape._canvas_id)
        
        # 2. La volvemos a dibujar con las nuevas propiedades
        shape.dibujar_en(self)
        
        # 3. Restauramos el resaltado visual de selección
        if self.shape_seleccionada == shape:
            if hasattr(shape, 'resaltar'):
                shape.resaltar(self, 'red') 
            else:
                self.itemconfig(shape._canvas_id, outline='red')
                
        # 4. Guardamos el estado para el Undo/Redo
        self._save_state()
    
    # doble click para propiedades
    def _on_double_click(self, e):
        """Abre la ventana de propiedades si hay algo seleccionado bajo el ratón"""
        if self.shape_seleccionada is not None:
            from ui.properties_window import PropertiesWindow
            
            # Verificar que el doble clic fue sobre la figura seleccionada (opcional pero recomendado)
            # Por simplicidad, si hay algo seleccionado, abrimos sus propiedades.
            PropertiesWindow(
                self.master,
                self,
                self.shape_seleccionada
            )