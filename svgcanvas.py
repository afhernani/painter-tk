# -*- coding: utf-8 -*-
# Tkinter canvas to SVG exporter
#
# license: BSD
#
# author: Hernani
# e-mail: afhernani@gmail.com
# WWW   : http://

from __future__ import division

__author__  = "hernani <afhernani@gmail.com>"

__all__ = ["loadSvg"]

try:
	# python3
	import tkinter
	from tkinter.constants import *
except ImportError:
	# python2
	import Tkinter as tkinter
	from Tkconstants import *

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

		stderr.write('canvas2svg warning: ')
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

def addPolylineToCanvas(child_, object):
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
            
            #print('options =', options)
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
            print(datos)
            object.create_line(datos, options_line)
            print('create polyline')

def addLineToCanvas(child_, object):
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
            
            print('options =', options)
            options_line = {}
            options_line['fill'] = options['stroke']
            options_line['width'] = options['stroke-width']
            options_line['capstyle'] = ROUND # BUTT # options['stroke-linecap']
            options_line['smooth'] = True
            options_line['tags'] = 'line'
            print('options_line =' , options_line)
            
            lista_puntos = [puntos_x[0], puntos_y[0], puntos_x[1], puntos_y[1]]
            '''for itemx in puntos_x:
                for itemy in puntos_y:
                    lista_puntos.extend([itemx, itemy])'''
            
            print(lista_puntos)
            object.create_line(lista_puntos, options_line)
            # object.create_line(attrs['x1'].value, attrs['y1'].value, attrs['x2'].value, attrs['y2'].value)
            print('create line')
        

def build(node_, objects):
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
                if objectinstance == 'Line':
                    addLineToCanvas(child_, objects)
                elif objectinstance == 'Polyline':
                    addPolylineToCanvas(child_, objects)
                elif objectinstance == 'Circulo':
                    pass
                # objectinstance=eval(capitalLetter+nodeName_[1:]) ()                
            except:
                print('no class for: '+ nodeName_)
                continue
            # object.addElement(build(child_,objectinstance))
        elif child_.nodeType == Node.TEXT_NODE:
            #print "TextNode:"+child_.nodeValue
            #if child_.nodeValue.startswith('\n'):
            #    print "TextNode starts with return:"+child_.nodeValue
            #else:
#            print "TextNode is:"+child_.nodeValue
            #object.setTextContent(child_.nodeValue)
            if child_.nodeValue != None and child_.nodeValue.strip() != '':
                # print(len(child_.nodeValue))
                objects.appendTextContent(child_.nodeValue)
        elif child_.nodeType == Node.CDATA_SECTION_NODE:  
            objects.appendTextContent('<![CDATA['+child_.nodeValue+']]>')          
        elif child_.nodeType == Node.COMMENT_NODE:  
            objects.appendTextContent('<!-- '+child_.nodeValue+' -->')          
        else:
            print("Some node:"+nodeName_+" value: "+child_.nodeValue)
    return objects

def loadSvg(inFileName, canvas):

    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement
    # rootObj = Svg()
    build(rootNode, canvas ) # rootObj )
    # Enable Python to collect the space used by the DOM.
    doc = None
    #print rootObj.getXML()
    items = canvas.find_all()
    print(items)
    return canvas # rootObj

if __name__ == '__main__':
    print('procesando ..')
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, background='yellow')
    canvas.pack()

    loadSvg("./canvasSVG/canvas.svg", canvas )

    root.mainloop()
