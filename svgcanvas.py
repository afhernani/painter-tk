# -*- coding: utf-8 -*-
"""
Tkinter canvas to SVG importer
"""
from __future__ import division

__author__ = "hernani <afhernani@gmail.com>"
__all__ = ["loadSvg"]

import tkinter
from tkinter.constants import *
from xml.dom import minidom
from xml.dom import Node
import logging

log = logging.getLogger('SVGCanvas')


def addLineToCanvas(child_, objects):
    """Convierte un elemento SVG <line> a una línea de Tkinter"""
    if child_.hasAttributes():
        attrs = child_.attributes
        puntos_x = []
        puntos_y = []
        options = {}
        
        for attr in list(attrs.keys()):
            if 'x' in attr:
                puntos_x.append(float(attrs[attr].value))
            elif 'y' in attr:
                puntos_y.append(float(attrs[attr].value))
            else:
                options[attr] = attrs[attr].value
        
        options_line = {
            'fill': options.get('stroke', 'black'),
            'width': float(options.get('stroke-width', 1)),
            'capstyle': ROUND,
            'smooth': False,
            'tags': 'Line'
        }
        
        lista_puntos = []
        for i in range(len(puntos_x)):
            lista_puntos.extend([puntos_x[i], puntos_y[i]])
        
        item_id = objects.create_line(lista_puntos, options_line)
        return item_id
    return None


def addPolylineToCanvas(child_, objects):
    """Convierte un elemento SVG <polyline> a una línea de Tkinter"""
    if child_.hasAttributes():
        attrs = child_.attributes
        options = {}
        
        for attr in list(attrs.keys()):
            options[attr] = attrs[attr].value
        
        options_line = {
            'fill': options.get('stroke', 'black'),
            'width': float(options.get('stroke-width', 1)),
            'capstyle': ROUND,
            'smooth': False,
            'tags': 'Polyline'
        }
        
        coordenadas = options['points'].split(' ')
        datos = []
        for coordenada in coordenadas:
            cx, cy = coordenada.split(',')
            datos.extend([float(cx), float(cy)])
        
        item_id = objects.create_line(datos, options_line)
        return item_id
    return None


def addEllipseToCanvas(child_, objects):
    """Convierte un elemento SVG <ellipse> a un óvalo de Tkinter"""
    if child_.hasAttributes():
        attrs = child_.attributes
        options = {}
        
        for attr in list(attrs.keys()):
            options[attr] = attrs[attr].value
        
        puntos = [float(options['cx']), float(options['cy']),
                  float(options['rx']), float(options['ry'])]
        ovalo = [puntos[0] - puntos[2], puntos[1] - puntos[3],
                 puntos[0] + puntos[2], puntos[1] + puntos[3]]
        
        opt = {
            'outline': options.get('stroke', 'black'),
            'fill': '',
            'width': float(options.get('stroke-width', 1)),
            'tags': 'Ellipse'
        }
        
        item_id = objects.create_oval(ovalo, opt)
        return item_id
    return None


def addRectToCanvas(child_, objects):
    """Convierte un elemento SVG <rect> a un rectángulo de Tkinter"""
    if child_.hasAttributes():
        attrs = child_.attributes
        options = {}
        
        for attr in list(attrs.keys()):
            options[attr] = attrs[attr].value
        
        x = float(options.get('x', 0))
        y = float(options.get('y', 0))
        width = float(options.get('width', 0))
        height = float(options.get('height', 0))
        rect_coords = [x, y, x + width, y + height]
        
        opt = {
            'outline': options.get('stroke', 'black'),
            'fill': options.get('fill', ''),
            'width': float(options.get('stroke-width', 1)),
            'tags': 'Rect'
        }
        
        item_id = objects.create_rectangle(rect_coords, opt)
        return item_id
    return None


def addPathToCanvas(child_, objects):
    """Convierte un elemento SVG <path> a elementos de Tkinter"""
    if child_.hasAttributes():
        attrs = child_.attributes
        options = {}
        
        for attr in list(attrs.keys()):
            options[attr] = attrs[attr].value
        
        path_data = options.get('d', '')
        if not path_data:
            return None
        
        stroke = options.get('stroke', 'black')
        stroke_width = float(options.get('stroke-width', 1))
        
        from iterationlexica import lex
        tokens = list(lex(path_data))
        
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
                    
                elif comando == 'A':
                    rx = ry = 0
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
                        bbox_x1 = min(current_x, end_x) - rx
                        bbox_y1 = min(current_y, end_y) - ry
                        bbox_x2 = max(current_x, end_x) + rx
                        bbox_y2 = max(current_y, end_y) + ry
                        
                        angle_start = math.degrees(math.atan2(
                            -(current_y - (bbox_y1 + bbox_y2)/2),
                            current_x - (bbox_x1 + bbox_x2)/2))
                        angle_end = math.degrees(math.atan2(
                            -(end_y - (bbox_y1 + bbox_y2)/2),
                            end_x - (bbox_x1 + bbox_x2)/2))
                        
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
            
            i += 1
        
        return last_id
    return None


def build(node_, objects, ids_creados=None):
    """Construye el canvas procesando nodos XML"""
    if ids_creados is None:
        ids_creados = []
    
    attrs = node_.attributes
    if attrs is not None:
        options = {}
        for attr in list(attrs.keys()):
            if attr == 'width':
                options[attr] = attrs[attr].value
            elif attr == 'height':
                options[attr] = attrs[attr].value
        objects.config(options)
    
    for child_ in node_.childNodes:
        nodeName_ = child_.nodeName.split(':')[-1]
        
        if child_.nodeType == Node.ELEMENT_NODE:
            try:
                capitalLetter = nodeName_[0].upper()
                objectinstance = capitalLetter + nodeName_[1:]
                
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
                
                if item_id is not None:
                    ids_creados.append(item_id)
            except Exception as e:
                log.error(f"Error procesando {nodeName_}: {e}")
                continue
    
    return objects


def loadSvg(inFileName, canvas):
    """Carga un archivo SVG y lo dibuja en un canvas de Tkinter"""
    ids_creados = []
    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement
    build(rootNode, canvas, ids_creados)
    doc = None
    return canvas, ids_creados


if __name__ == '__main__':
    print('procesando ..')
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, background='yellow')
    canvas.pack()
    loadSvg("downloads/canvas.svg", canvas)
    root.mainloop()