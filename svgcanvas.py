# -*- coding: utf-8 -*-
"""
Tkinter canvas to SVG importer
license: BSD
author: Hernani
e-mail: afhernani@gmail.com
"""
from __future__ import division
from canvasvg import segment_to_line, segment_to_path

__author__ = "hernani <afhernani@gmail.com>"
__all__ = ["loadSvg"]

import tkinter
from tkinter.constants import *
from xml.dom import minidom
from xml.dom import Node
import string

PYTHON = 100
MODULE = 200
NONE = 300
warnings_mode = MODULE

def warnings(mode):
    global warnings_mode
    if mode not in [PYTHON, MODULE, NONE]:
        raise ValueError("Please use one of constants: PYTHON, MODULE, NONE")
    warnings_mode = mode

try:
    warn
except NameError:
    from warnings import warn

def emit_warning(msg):
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

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('svgcanvas')

def calculateMethodName(attr):
    name = attr
    name = name.replace(':', '')
    name = name.replace('-', '')
    name = 'set_' + name
    return name

def setAttributes(attrs, obj):
    for attr in list(attrs.keys()):
        try:
            if hasattr(obj, calculateMethodName(attr)):
                eval('obj.' + calculateMethodName(attr))(attrs[attr].value)
            else:
                print(calculateMethodName(attr) + ' not found in:' + obj._elementName)
        except Exception:
            emit_warning(f"not found in")


def addLineToCanvas(child_, objects):
    """Convierte un elemento SVG <line> a una línea de Tkinter"""
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        puntos_x = []
        puntos_y = []
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                if 'x' in attr:
                    puntos_x.append(attrs[attr].value)
                elif 'y' in attr:
                    puntos_y.append(attrs[attr].value)
                else:
                    options[attr] = attrs[attr].value
            
            options_line = {}
            options_line['fill'] = options.get('stroke', 'black')
            options_line['width'] = float(options.get('stroke-width', 1))
            options_line['capstyle'] = ROUND
            options_line['smooth'] = False
            options_line['tags'] = 'Line'
            
            lista_puntos = [float(puntos_x[0]), float(puntos_y[0]), 
                           float(puntos_x[1]), float(puntos_y[1])]
            
            log.info(f"lista_puntos = {lista_puntos}")
            item_id = objects.create_line(lista_puntos, options_line)
            log.info(f'create line, id={item_id}')
            return item_id
    
    return None


def addPolylineToCanvas(child_, objects):
    """Convierte un elemento SVG <polyline> a una línea de Tkinter"""
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
    """Convierte un elemento SVG <ellipse> a un óvalo de Tkinter"""
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
            
            log.info(f"Ovalo -- puntos: {ovalo}")
            
            opt = {}
            opt['outline'] = options.get('stroke', 'black')
            opt['fill'] = ''
            opt['width'] = float(options.get('stroke-width', 1))
            opt['tags'] = 'Ellipse'
            
            log.info(opt)
            item_id = objects.create_oval(ovalo, opt)
            log.info(f'create ellipse, id={item_id}')
            return item_id
    
    return None


def addRectToCanvas(child_, objects):
    """Convierte un elemento SVG <rect> a un rectángulo de Tkinter"""
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
            opt['tags'] = 'Rect'  # ✅ Cambiado a 'Rect'
            
            log.info(opt)
            item_id = objects.create_rectangle(rect_coords, opt)
            log.info(f'create rectangle, id={item_id}')
            return item_id
    
    return None


def addPathToCanvas(child_, objects):
    """Convierte un elemento SVG <path> a Tkinter (pendiente de implementación completa)"""
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options path = {options}")
            log.info("Nota: procesamiento de paths pendiente de implementación completa")
            
            # TODO: Implementar parser de paths SVG
            # Por ahora, retornar None
            return None
    
    return None


def drawPaths(options, objects):
    try:
        log.info('drawPaths')
    except Exception as ex:
        log.info(ex.args)


def addPathConstructor(options, objects):
    """Analizar los objetos 'd' """
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
        if k == 'number':
            obj.append(float(v))
        if k == 'symbol':
            conjunto_obj.append(obj)
    
    return conjunto_obj


def build(node_, objects, ids_creados=None):
    """Construye recursivamente el canvas procesando nodos XML.
    
    Args:
        node_: Nodo XML actual
        objects: Canvas de Tkinter
        ids_creados: Lista para acumular los IDs de objetos creados
    
    Returns:
        objects: Canvas modificado
    """
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
                
                # ✅ Capturar el ID si se creó un objeto
                if item_id is not None:
                    ids_creados.append(item_id)
                
            except Exception as e:
                print(f'Error processing {nodeName_}: {e}')
                import traceback
                traceback.print_exc()
                continue
        
        elif child_.nodeType == Node.TEXT_NODE:
            if child_.nodeValue is not None and child_.nodeValue.strip() != '':
                if hasattr(objects, 'appendTextContent'):
                    objects.appendTextContent(child_.nodeValue)
        
        elif child_.nodeType == Node.CDATA_SECTION_NODE:
            if hasattr(objects, 'appendTextContent'):
                objects.appendTextContent('<![CDATA[' + child_.nodeValue + ']]>')
        
        elif child_.nodeType == Node.COMMENT_NODE:
            if hasattr(objects, 'appendTextContent'):
                objects.appendTextContent('<!-- ' + child_.nodeValue + ' -->')
        
        else:
            print(f"Some node: {nodeName_} value: {child_.nodeValue}")
    
    return objects


def loadSvg(inFileName, canvas):
    """Carga un archivo SVG y lo dibuja en un canvas de Tkinter.
    
    Args:
        inFileName: Ruta del archivo SVG a cargar
        canvas: Canvas de Tkinter donde se dibujará
    
    Returns:
        tuple: (canvas, lista_de_ids_creados)
    """
    ids_creados = []
    
    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement
    
    build(rootNode, canvas, ids_creados)
    
    doc = None
    
    items = canvas.find_all()
    print(f"Total items in canvas: {len(items)}")
    print(f"Items creados desde SVG: {len(ids_creados)}")
    print(f"IDs creados: {ids_creados}")
    
    return canvas, ids_creados


if __name__ == '__main__':
    print('procesando ..')
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, background='yellow')
    canvas.pack()
    loadSvg("downloads/canvas.svg", canvas)
    root.mainloop()