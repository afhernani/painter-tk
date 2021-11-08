import numpy as np
from numpy import ones, vstack
from numpy.linalg import lstsq
import sympy as sm
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

def rectasRectangulo(*points, n=3):
    origen, final = points
    # segmt = sm.geometry.Segment(origen, final)
    # ptm = segmt.midpoint
    # Vptm = np.array([ptm.coordinates[0].evalf(), ptm.coordinates[1].evalf()])
    Vorigen = np.array([origen[0], origen[1]])
    Vfinal = np.array([final[0]-origen[0], final[1]-origen[1]])

    ModVfinal = np.linalg.norm(Vfinal)
    if ModVfinal == 0: ModVfinal=1
    Vunt = Vfinal / ModVfinal
    Vmedio = Vunt * (ModVfinal / 2)
    Vposm = Vmedio + Vorigen
    if n < 3: n=3
    r = ModVfinal / 2
    figura = sm.geometry.Polygon(Vposm, r, n=n)
    """# ---------
    x = Vposm
    y = np.array([-1, -1])
    th = np.arccos( np.dot(x, y) / (np.linalg.norm(x)*np.linalg.norm(y)) )
    log.info(f"polygon angule: {th}")
    # -------
    figura.spin(th)"""
    
    puntos = []
    
    for punto in figura.vertices:
        pp = np.array([punto.coordinates[0].evalf(),
                       punto.coordinates[1].evalf()])
        posix = pp
        log.info(f"posix: {posix}")
        puntos.extend([posix[0], posix[1]])

    if len(puntos)>0:
        puntos.extend([puntos[0], puntos[1]]) #cerramos el poligono
    # log.info(f"Vertices: {figura.vertices}")
    # log.info(f"segmento: {segmt}, rectasRectangulo: {ptm.coordinates}")
    # log.info(f"Vorigen: {Vorigen}, Vptm: {Vptm}")
    '''log.info(f"vorigen: {Vorigen}, vfinal: {Vfinal}, vpostr: {Vpostr}, NormalVpostr: {NormalVpostr}")
    log.info(f"Vunit_Vpostr: {Vunit_Vpostr}")
    log.info(f"posicion centro radio: {Vposm}")
    log.info(f"Puntos: {puntos}")'''
    return puntos

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
    #pc = rectasCircunferencia(*points)
    #print(pc); print(len(pc))
    puntos = rectasRectangulo(*points, n=4)
    log.info(f"puntos: {puntos}")

if __name__ == '__main__':
    main()