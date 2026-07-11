# -*- coding: utf-8 -*-
"""
Importador de archivos SVG a Canvas de Tkinter

Basado en el módulo original svgcanvas.py
Adaptado y mejorado para painter-tk
"""

from __future__ import division

__author__ = "hernani <afhernani@gmail.com>"
__all__ = ["loadSvg"]

import tkinter
from tkinter.constants import *
from xml.dom import minidom
from xml.dom import Node
import string
import logging

log = logging.getLogger('SVGCanvas')

PYTHON = 100
MODULE = 200
NONE = 300
warnings_mode = MODULE

def warnings(mode):
    """Configura el modo de advertencias"""
    global warnings_mode
    if mode not in [PYTHON, MODULE, NONE]:
        raise ValueError("Please use one of constants: PYTHON, MODULE, NONE")
    warnings_mode = mode

try:
    warn
except NameError:
    from warnings import warn

def emit_warning(msg):
    """Emite una advertencia"""
    if warnings_mode == PYTHON:
        warn(msg)
    elif warnings_mode == MODULE:
        from sys import stderr
        stderr.write('svgcanvas warning: ')
        stderr.write(msg)
        stderr.write('\n')

SEGMENT_TO_LINE = 1000
SEGMENT_TO_PATH = 2000

def configure(*flags):
    """Configura el tipo de segmento"""
    global segment
    for flag in flags:
        if flag == SEGMENT_TO_LINE:
            segment = segment_to_line
        elif flag == SEGMENT_TO_PATH:
            segment = segment_to_path
        else:
            raise ValueError(
                "Please use one of constants: SEGMENT_TO_LINE, SEGMENT_TO_PATH"
            )

def calculateMethodName(attr):
    """Convierte un atributo SVG en nombre de método"""
    name = attr.replace(':', '').replace('-', '')
    return 'set_' + name

def setAttributes(attrs, obj):
    """Establece atributos en un objeto"""
    for attr in list(attrs.keys()):
        try:
            if hasattr(obj, calculateMethodName(attr)):
                eval('obj.' + calculateMethodName(attr))(attrs[attr].value)
            else:
                print(calculateMethodName(attr) + ' not found in:' + obj._elementName)
        except Exception:
            emit_warning(f"not found in")

def addLineToCanvas(child_, objects):
    """
    Convierte un elemento SVG <line> a una línea de Tkinter.
    
    Args:
        child_: Nodo XML del elemento line
        objects: Canvas de Tkinter
    
    Returns:
        ID del objeto creado o None
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        puntos_x = []
        puntos_y = []
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                if 'x' in attr:
                    puntos_x.append(float(attrs[attr].value))
                elif 'y' in attr:
                    puntos_y.append(float(attrs[attr].value))
                else:
                    options[attr] = attrs[attr].value
            
            options_line = {}
            options_line['fill'] = options.get('stroke', 'black')
            options_line['width'] = float(options.get('stroke-width', 1))
            options_line['capstyle'] = ROUND
            options_line['smooth'] = False
            options_line['tags'] = 'Line'
            
            lista_puntos = []
            for i in range(len(puntos_x)):
                lista_puntos.extend([puntos_x[i], puntos_y[i]])
            
            log.info(f"lista_puntos = {lista_puntos}")
            item_id = objects.create_line(lista_puntos, options_line)
            log.info(f'create line, id={item_id}')
            return item_id
    
    return None

def addPolylineToCanvas(child_, objects):
    """
    Convierte un elemento SVG <polyline> a una línea de Tkinter.
    
    Args:
        child_: Nodo XML del elemento polyline
        objects: Canvas de Tkinter
    
    Returns:
        ID del objeto creado o None
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options = {options}")
            
            options_line = {}
            options_line['fill'] = options.get('stroke', 'black')
            options_line['width'] = float(options.get('stroke-width', 1))
            options_line['capstyle'] = ROUND
            options_line['smooth'] = False
            options_line['tags'] = 'Polyline'
            
            coordenadas = options['points'].split(' ')
            datos = []
            for coordenada in coordenadas:
                cx, cy = coordenada.split(',')
                datos.extend([float(cx), float(cy)])
            
            log.info(f"datos = {datos}")
            item_id = objects.create_line(datos, options_line)
            log.info(f'create polyline, id={item_id}')
            return item_id
    
    return None

def addEllipseToCanvas(child_, objects):
    """
    Convierte un elemento SVG <ellipse> a un óvalo de Tkinter.
    
    Args:
        child_: Nodo XML del elemento ellipse
        objects: Canvas de Tkinter
    
    Returns:
        ID del objeto creado o None
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options = {options}")
            
            puntos = [float(options['cx']), float(options['cy']),
                      float(options['rx']), float(options['ry'])]
            ovalo = [puntos[0] - puntos[2], puntos[1] - puntos[3],
                     puntos[0] + puntos[2], puntos[1] + puntos[3]]
            
            log.info(f"Coordenadas Ovalo -- puntos: {ovalo}")
            
            opt = {}
            opt['outline'] = options.get('stroke', 'black')
            opt['fill'] = ''
            opt['width'] = float(options.get('stroke-width', 1))
            opt['tags'] = 'Ellipse'
            
            item_id = objects.create_oval(ovalo, opt)
            log.info(f'create ellipse, id={item_id}')
            return item_id
    
    log.warning("No se pudo crear Ellipse")
    return None

def addRectToCanvas(child_, objects):
    """
    Convierte un elemento SVG <rect> a un rectángulo de Tkinter.
    
    Args:
        child_: Nodo XML del elemento rect
        objects: Canvas de Tkinter
    
    Returns:
        ID del objeto creado o None
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options rect = {options}")
            
            x = float(options.get('x', 0))
            y = float(options.get('y', 0))
            width = float(options.get('width', 0))
            height = float(options.get('height', 0))
            
            rect_coords = [x, y, x + width, y + height]
            log.info(f"rect_coords = {rect_coords}")
            
            opt = {}
            opt['outline'] = options.get('stroke', 'black')
            opt['fill'] = options.get('fill', '')
            opt['width'] = float(options.get('stroke-width', 1))
            opt['tags'] = 'Rect'
            
            log.info(opt)
            item_id = objects.create_rectangle(rect_coords, opt)
            log.info(f'create rectangle, id={item_id}')
            return item_id
    
    return None

def addPathToCanvas(child_, objects):
    """
    Convierte un elemento SVG <path> a elementos de Tkinter.
    Soporta comandos: M (move), L (line), A (arc), Z (close)
    
    Args:
        child_: Nodo XML del elemento path
        objects: Canvas de Tkinter
    
    Returns:
        ID del último objeto creado o None
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options path = {options}")
            
            path_data = options.get('d', '')
            if not path_data:
                log.warning("Path sin datos 'd'")
                return None
            
            stroke = options.get('stroke', 'black')
            stroke_width = float(options.get('stroke-width', 1))
            
            from iterationlexica import lex
            tokens = list(lex(path_data))
            log.info(f"Tokens del path: {tokens}")
            
            current_x = 0
            current_y = 0
            start_x = 0
            start_y = 0
            last_id = None
            i = 0
            
            while i < len(tokens):
                token_type, token_value = tokens[i]
                
                if token_type == 'identificador':
                    comando = token_value
                    
                    if comando == 'M':
                        if i + 1 < len(tokens) and tokens[i + 1][0] == 'number':
                            current_x = float(tokens[i + 1][1])
                            i += 1
                        if i + 1 < len(tokens) and tokens[i + 1][0] == ',':
                            i += 1
                        if i + 1 < len(tokens) and tokens[i + 1][0] == 'number':
                            current_y = float(tokens[i + 1][1])
                            i += 1
                        
                        start_x = current_x
                        start_y = current_y
                        log.info(f"MoveTo: ({current_x}, {current_y})")
                    
                    elif comando == 'L':
                        end_x = current_x
                        end_y = current_y
                        
                        if i + 1 < len(tokens) and tokens[i + 1][0] == 'number':
                            end_x = float(tokens[i + 1][1])
                            i += 1
                        if i + 1 < len(tokens) and tokens[i + 1][0] == ',':
                            i += 1
                        if i + 1 < len(tokens) and tokens[i + 1][0] == 'number':
                            end_y = float(tokens[i + 1][1])
                            i += 1
                        
                        options_line = {
                            'fill': stroke,
                            'width': stroke_width,
                            'capstyle': ROUND,
                            'smooth': False,
                            'tags': 'Line'
                        }
                        
                        last_id = objects.create_line(
                            [current_x, current_y, end_x, end_y],
                            options_line
                        )
                        current_x = end_x
                        current_y = end_y
                        log.info(f"LineTo: ({end_x}, {end_y}), id={last_id}")
                    
                    elif comando == 'A':
                        rx = ry = 0
                        x_axis_rotation = 0
                        large_arc_flag = 0
                        sweep_flag = 0
                        end_x = current_x
                        end_y = current_y
                        
                        params = []
                        for j in range(7):
                            if i + 1 < len(tokens) and tokens[i + 1][0] == 'number':
                                params.append(float(tokens[i + 1][1]))
                                i += 1
                            elif i + 1 < len(tokens) and tokens[i + 1][0] == ',':
                                i += 1
                        
                        if len(params) >= 7:
                            rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, end_x, end_y = params
                            
                            import math
                            dx = end_x - current_x
                            dy = end_y - current_y
                            
                            bbox_x1 = min(current_x, end_x) - rx
                            bbox_y1 = min(current_y, end_y) - ry
                            bbox_x2 = max(current_x, end_x) + rx
                            bbox_y2 = max(current_y, end_y) + ry
                            
                            angle_start = math.degrees(math.atan2(
                                -(current_y - (bbox_y1 + bbox_y2)/2),
                                current_x - (bbox_x1 + bbox_x2)/2
                            ))
                            angle_end = math.degrees(math.atan2(
                                -(end_y - (bbox_y1 + bbox_y2)/2),
                                end_x - (bbox_x1 + bbox_x2)/2
                            ))
                            
                            extent = angle_end - angle_start
                            if large_arc_flag:
                                if extent > 0:
                                    extent -= 360
                                else:
                                    extent += 360
                            
                            options_arc = {
                                'outline': stroke,
                                'width': stroke_width,
                                'start': angle_start,
                                'extent': extent,
                                'style': ARC,
                                'tags': 'Arco'
                            }
                            
                            last_id = objects.create_arc(
                                [bbox_x1, bbox_y1, bbox_x2, bbox_y2],
                                options_arc
                            )
                            current_x = end_x
                            current_y = end_y
                            log.info(f"Arc: ({end_x}, {end_y}), id={last_id}")
                    
                    elif comando in ('Z', 'z'):
                        if current_x != start_x or current_y != start_y:
                            options_line = {
                                'fill': stroke,
                                'width': stroke_width,
                                'capstyle': ROUND,
                                'smooth': False,
                                'tags': 'Line'
                            }
                            
                            last_id = objects.create_line(
                                [current_x, current_y, start_x, start_y],
                                options_line
                            )
                            current_x = start_x
                            current_y = start_y
                            log.info(f"Close path, id={last_id}")
                
                i += 1
            
            log.info(f"Path completado, último id={last_id}")
            return last_id
    
    return None

def drawPaths(options, objects):
    """Dibuja paths (función auxiliar)"""
    try:
        log.info('drawPaths')
    except Exception as ex:
        log.info(ex.args)

def addPathConstructor(options, objects):
    """Analiza los objetos 'd' del path"""
    from iterationlexica import lex
    
    obj = []
    conjunto_obj = []
    
    for l in lex(options['d']):
        k, v = l
        if k == 'identificador':
            if len(obj) == 0:
                obj = []
            else:
                conjunto_obj.append(obj)
                obj = []
            
            if v == 'M':
                obj.append(v)
            if v == 'L':
                obj.append(v)
            if v == 'A':
                obj.append(v)
        elif k == 'number':
            obj.append(float(v))
        elif k == 'symbol':
            conjunto_obj.append(obj)
    
    return conjunto_obj

def build(node_, objects, ids_creados=None):
    """
    Construye recursivamente el canvas procesando nodos XML.
    
    Args:
        node_: Nodo XML actual
        objects: Canvas de Tkinter
        ids_creados: Lista para acumular los IDs de objetos creados
    
    Returns:
        Canvas modificado
    """
    if ids_creados is None:
        ids_creados = []
    
    log.debug(f"build: procesando nodo {node_.nodeName}")
    
    attrs = node_.attributes
    if attrs is not None:
        options = {}
        for attr in list(attrs.keys()):
            if attr == 'width':
                options[attr] = attrs[attr].value
            elif attr == 'height':
                options[attr] = attrs[attr].value
        
        objects.config(options)
        log.debug(f"Canvas configurado: {options}")
    
    for child_ in node_.childNodes:
        nodeName_ = child_.nodeName.split(':')[-1]
        
        if child_.nodeType == Node.ELEMENT_NODE:
            try:
                capitalLetter = nodeName_[0].upper()
                objectinstance = capitalLetter + nodeName_[1:]
                log.debug(f"Procesando elemento: {objectinstance}")
                
                item_id = None
                
                if objectinstance == 'Line':
                    item_id = addLineToCanvas(child_, objects)
                elif objectinstance == 'Polyline':
                    item_id = addPolylineToCanvas(child_, objects)
                elif objectinstance == 'Ellipse':
                    item_id = addEllipseToCanvas(child_, objects)
                elif objectinstance == 'Rect':
                    item_id = addRectToCanvas(child_, objects)
                elif objectinstance == 'Path':
                    item_id = addPathToCanvas(child_, objects)
                else:
                    log.warning(f"Elemento no soportado: {objectinstance}")
                
                if item_id is not None:
                    ids_creados.append(item_id)
                   