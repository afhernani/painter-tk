import numpy as np
from numpy import ones, vstack
from numpy.linalg import lstsq
import math
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('ecu')


def ecu_linea(*points):
    x_coords, y_coords = zip(*points)
    log.info(f"x_coords_list: {x_coords}")
    log.info(f"y_coords_list: {y_coords}")
    A = vstack([x_coords, ones(len(x_coords))]).T
    m, c = lstsq(A, y_coords, rcond=-1)[0]
    ecuacion = "y = {m:.4f}·x + {c:.4f}".format(m=m,c=c)
    log.info(f"Line Solution is {ecuacion}")
    return (m, c, ecuacion)

def distancia(*points):
    x_coords, y_coords = points
    x = y_coords[0] - x_coords[0]
    y = y_coords[1] - x_coords[1]
    return math.sqrt(x*x + y*y)

def pMedio(*points):
    x_coords, y_coords = points
    x = (x_coords[0] + y_coords[0]) / 2
    y = (x_coords[1] + y_coords[1]) / 2
    return (x, y)

def razonMedia(*points, r=2):
    '''puntos [(x1, y1), (x2, y2)]
       razon de la division '''
    x_coords, y_coords = points
    x = (x_coords[0] + y_coords[0]) /  r
    y = (x_coords[1] + y_coords[1]) /  r
    return (x, y)

def cartesian_to_polar(x, y): 
   # rr = sym.sqrt(x**2 + y**2)
   rr = np.math.sqrt(x**2 + y**2)
   #theta = sym.atan2(y, x)#import numpy as np
   theta = np.math.atan2(y, x)
   return(rr, theta)

def polar_to_cartesian(r, theta): # 'def' nos permite 'crear' nuestras propias funciones en Python.
   # xx = r * sym.cos(theta)
   xx = r * np.math.cos(theta)
   ## yy = r * sym.sin(theta)
   yy = r * np.math.sin(theta)
   return(xx, yy)

def vectorP(*points):
    origen, final = points
    return final[0]-origen[0], final[1]-origen[1]

def rectasCircunferencia(*points):
    origen, final = points
    vector = vectorP(*points)
    d = math.sqrt(vector[0]*vector[0]+ vector[1]*vector[1])
    log.info(f"vector: {vector}, dist: {d}")
    if d == 0: d=1
    vectorU = (vector[0] / d , vector[1] / d)
    log.info(f"vector unitario: {vectorU}")
    vectorM = (d / 2 * vectorU[0] , d / 2 * vectorU[1])
    log.info(f"vector medio: {vectorM}")
    vectorG = ( origen[0] + vectorM[0], origen[1]+vectorM[1])
    
    coordenadas = []
    r = d/2

    angulos = np.arange(0, 2*math.pi, 0.03)
    for thao in angulos:
        cc = polar_to_cartesian(r, thao)
        
        vvx, vvy = cc[0] + vectorG[0] , cc[1] + vectorG[1]
        coordenadas.append(vvx)
        coordenadas.append(vvy)
        
    return coordenadas


def main():
    points = [(-4, 3),(6, -2)]
    m, c, ecu = ecu_linea(*points)
    log.info(f"m: {m}, c: {c}")
    d = distancia(*points)
    log.info(f"dist: {d}")
    m = pMedio(*points)
    log.info(f"punto medio: {m}")
    rm = razonMedia(*points, r=3)
    log.info(f"razon: {rm}")
    pc = rectasCircunferencia(*points)
    print(pc); print(len(pc))


if __name__ == '__main__':
    main()