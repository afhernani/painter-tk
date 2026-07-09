# -*- coding: utf-8 -*-
# Tkinter canvas to SVG exporter
#
# license: BSD
#
# author: Hernani
# e-mail: afhernani@gmail.com

from __future__ import division

from canvasvg import segment_to_line, segment_to_path

__author__  = "hernani <afhernani@gmail.com>"

__all__ = ["loadSvg"]

import tkinter
from tkinter.constants import *


from xml.dom import minidom
from xml.dom import Node
import string

PYTHON = 100
MODULE = 200
NONE   = 300
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

		stderr.write('sgvcanvas warning: ')
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
    name=attr
    name=name.replace(':','_')
    name=name.replace('-','_')
    name='set_'+name
    return name


def setAttributes(attrs, obj):
    for attr in list(attrs.keys()):
        try:
            if hasattr(obj, calculateMethodName(attr)):
                eval ('obj.'+calculateMethodName(attr))(attrs[attr].value)
            else:
                print(calculateMethodName(attr)+' not found in:'+obj._elementName)
        except Exception:
            emit_warning(f"not found in")


def addPolylineToCanvas(child_, objects):
    nodeName_ = child_.nodeName
    if child_.hasAttributes():
        attrs = child_.attributes
        if attrs != None:
            # print(attrs.values())
            # options = dict((v0, v4) for v0, v1, v2, v3, v4 in attrs.values())
            # print(options)
            options = {}
            for attr in list(attrs.keys()):
                # print(attr)
               options[attr]=attrs[attr].value
            
            log.info(f"options =, {options}")

            options_line = {}
            # options_line['points'] = [options['points']]
            options_line['fill'] = options['stroke']
            options_line['width'] = options['stroke-width']
            options_line['capstyle'] = ROUND # BUTT # options['stroke-linecap']
            options_line['smooth'] = False
            options_line['tags'] = 'polyline'
            #print('options_line =' , options_line)
            # determinar las coordenadas ...
            coordenadas = options['points'].split(' ')
            # print(coordenadas)
            datos = []
            for coordenada in coordenadas:
                cx, cy = coordenada.split(',')
                datos.extend([float(cx), float(cy)])

            log.info(f"datos = {datos}")
            
            item_id = objects.create_line(datos, options_line)
            log.info(f'create polyline, id={item_id}')
            
            return item_id
    return None

def addLineToCanvas(child_, objects):
    """Convertir un elemento SVG <line> a una linea de tkinter"""
    nodeName_ = child_.nodeName

    if child_.hasAttributes():
        attrs = child_.attributes
        puntos_x = []
        puntos_y = []
        if attrs != None:
            # print(attrs.values())
            # options = dict((v0, v4) for v0, v1, v2, v3, v4 in attrs.values())
            # print(options)
            options = {}
            for attr in list(attrs.keys()):
                # print(attr)
                if 'x' in attr :
                    puntos_x.append(attrs[attr].value)
                elif 'y' in attr:
                    puntos_y.append(attrs[attr].value)
                else:
                    options[attr]=attrs[attr].value
            
            # print('options =', options)
            options_line = {}
            options_line['fill'] = options['stroke']
            options_line['width'] = options['stroke-width']
            options_line['capstyle'] = ROUND # BUTT # options['stroke-linecap']
            options_line['smooth'] = True
            options_line['tags'] = 'line'
            # print('options_line =' , options_line)
            
            lista_puntos = [puntos_x[0], puntos_y[0], puntos_x[1], puntos_y[1]]
            '''for itemx in puntos_x:
                for itemy in puntos_y:
                    lista_puntos.extend([itemx, itemy])'''
            
            log.info(f"lista_puntos = {lista_puntos}")

            item_id=objects.create_line(lista_puntos, options_line)
            # object.create_line(attrs['x1'].value, attrs['y1'].value, attrs['x2'].value, attrs['y2'].value)
            log.info(f'create line, id={item_id}')
            return item_id
        
    return None


def addPathToCanvas(child_, objects):
    """Convertir un elemento SVG <ellipse> a un óvalo de tkinter"""
    nodeName_ = child_.nodeName
    if child_.hasAttributes():
        attrs = child_.attributes
        if attrs != None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr]=attrs[attr].value

            log.info(f"options = {options}")
            puntos = [float(options['cx']),
                            float(options['cy']),
                            float(options['rx']),
                            float(options['ry'])
                            ]
            ovalo = [puntos[0] - puntos[2],
                     puntos[1] - puntos[3],
                     ]
            log.info(f'Ovalo -- puntos: {ovalo}')

            opt = {}
            opt['outline'] = options['stroke']
            opt['fill'] = ''
            opt['width'] = float(options['stroke-width'])
            opt['tags'] = 'arc'

            log.info(f'{opt}')

            # crear ovalo y guardar el id
            item_id = objects.create_oval(ovalo, opt)
            log.info(f'create arco, id={item_id}')
            # Nota:create interprete lexico sintactico.
            # log.info("Nota: pendiente de proceso")
            # graphs = addPathConstructor(options, objects)
            # log.info(graphs)
            # options['d']=graphs
            # log.info(options)
            # drawPaths(options, objects)
            return item_id
        
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


def addEllipseToCanvas(child_, objects):
    nodeName_ = child_.nodeName
    if child_.hasAttributes():
        attrs = child_.attributes
        if attrs != None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr]=attrs[attr].value
            log.info(f"options = {options}")
            puntos = [ float(options['cx']), float(options['cy']),
                       float(options['rx']), float(options['ry'])]
            ovalo = [ puntos[0]-puntos[2], puntos[1]-puntos[3],
                      puntos[0]+puntos[2], puntos[1]+puntos[3]
                      ]
            log.info(f"Ovalo -- puntos: {ovalo}")
            opt = {}
            opt['outline'] = options['stroke']
            # opt['dash'] = (4, 1)
            opt['fill'] = ''
            opt['width'] = float(options['stroke-width'])
            opt['tags'] = 'arc'
            log.info(opt)
            objects.create_oval(ovalo, opt)
            log.info('create arco')


def addRectToCanvas(child_, objects):
    """
    Convierte un elemento SVG <rect> a un rectángulo de Tkinter.
    
    SVG rect tiene: x, y, width, height
    Tkinter necesita: [x1, y1, x2, y2] donde x2=x+width, y2=y+height
    """
    nodeName_ = child_.nodeName
    
    if child_.hasAttributes():
        attrs = child_.attributes
        
        if attrs is not None:
            options = {}
            for attr in list(attrs.keys()):
                options[attr] = attrs[attr].value
            
            log.info(f"options rect = {options}")
            
            # Extraer coordenadas del rectángulo
            x = float(options.get('x', 0))
            y = float(options.get('y', 0))
            width = float(options.get('width', 0))
            height = float(options.get('height', 0))
            
            # Calcular bounding box para Tkinter
            rect_coords = [x, y, x + width, y + height]
            
            log.info(f"rect_coords = {rect_coords}")
            
            # Configurar opciones para Tkinter
            opt = {}
            opt['outline'] = options.get('stroke', 'black')
            opt['fill'] = options.get('fill', '')
            opt['width'] = float(options.get('stroke-width', 1))
            opt['tags'] = 'rectangle'
            
            log.info(opt)
            
            # Crear rectángulo en el canvas
            item_id = objects.create_rectangle(rect_coords, opt)
            log.info(f'create rectangle, id={item_id}')
            
            return item_id
    
    return None


def build(node_, objects, ids_creados=None):
    """Construye recursivamente el canvas procesando nodos XML.
    
    Args:
        node_: Nodo XML actual
        objects: Canvas de Tkinter
        ids_creados: Lista para acumular los IDs de objetos creados
    
    Returns:
        objects: Canvas modificado """
    if ids_creados is None:
         ids_creados = []
    
    attrs = node_.attributes
    
    if attrs != None:
        options = {}
        for attr in list(attrs.keys()):
            if attr == 'width':
                options[attr]=attrs[attr].value
            elif attr == 'height':
                options[attr]=attrs[attr].value

        objects.config(options)

        # setAttributes(attrs, object)
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
                
                elif objectinstance == 'Rect':  # Añadir este caso
                    item_id = addRectToCanvas(child_, objects)

                elif objectinstance == 'Path':
                    addPathToCanvas(child_, objects) # quitamos el item_id
                # objectinstance=eval(capitalLetter+nodeName_[1:]) ()
                if item_id is not None:
                     ids_creados.append(item_id)

            except Exception as e:
                print(f'no class for: {nodeName_}, error: {e}')
                continue

            # object.addElement(build(child_,objectinstance))

        elif child_.nodeType == Node.TEXT_NODE:
            #print "TextNode:"+child_.nodeValue
            #if child_.nodeValue.startswith('\n'):
            #    print "TextNode starts with return:"+child_.nodeValue
            #else:
            #    print "TextNode is:"+child_.nodeValue
            #object.setTextContent(child_.nodeValue)
            if child_.nodeValue is not None and child_.nodeValue.strip() != '':
                if hasattr(object, 'appendTextContent'):
                     # print(len(child_.nodeValue))
                    objects.appendTextContent(child_.nodeValue)

        elif child_.nodeType == Node.CDATA_SECTION_NODE:
            if hasattr(object, 'appendTextContent'):
                 objects.appendTextContent('<![CDATA['+child_.nodeValue+']]>')          

        elif child_.nodeType == Node.COMMENT_NODE:
            if hasattr(object, 'appendTextContent'):
                objects.appendTextContent('<!-- '+child_.nodeValue+' -->')          
        else:
            print(f"Some node: {nodeName_} value: {child_.nodeValue}")

    return objects


def loadSvg(inFileName, canvas):
    """
    Carga un archivo SVG y lo dibuja en un canvas de Tkinter.
    
    Args:
        inFileName: Ruta del archivo SVG a cargar
        canvas: Canvas de Tkinter donde se dibujará
    
    Returns:
        tuple: (canvas, lista_de_ids_creados)
    """
    # lista para acumular los ids de objetos
    ids_creados = []

    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement

    # rootObj = Svg()
    build(rootNode, canvas, ids_creados ) # rootObj )
    # Enable Python to collect the space used by the DOM.
    doc = None
    
    #print rootObj.getXML()
    items = canvas.find_all()
    # print(items)
    print(f"Total items in canvas: {len(items)}")
    print(f"Items creados desde SVG: {len(ids_creados)}")
    print(f"IDs creados: {ids_creados}")
    # devolver el canvas y lista de ids
    return canvas, ids_creados # rootObj


if __name__ == '__main__':
    print('procesando ..')
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, background='yellow')
    canvas.pack()

    loadSvg("downloads/canvas.svg", canvas )

    root.mainloop()
