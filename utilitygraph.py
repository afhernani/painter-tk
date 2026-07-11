# -*- coding: utf-8 -*-
"""
Funciones gráficas auxiliares para painter-tk
Contiene funciones matemáticas para dibujar formas geométricas
"""
import math
import numpy as np


def polar_to_cartesian(r, theta):
    """
    Convierte coordenadas polares a cartesianas.
    
    Args:
        r: Radio (distancia al origen)
        theta: Ángulo en radianes
    
    Returns:
        Tupla (x, y) en coordenadas cartesianas
    """
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return (x, y)


def cartesian_to_polar(x, y):
    """
    Convierte coordenadas cartesianas a polares.
    
    Args:
        x: Coordenada x
        y: Coordenada y
    
    Returns:
        Tupla (r, theta) en coordenadas polares
    """
    r = math.sqrt(x**2 + y**2)
    theta = math.atan2(y, x)
    return (r, theta)


def distancia_entre_puntos(p1, p2):
    """
    Calcula la distancia euclidiana entre dos puntos.
    
    Args:
        p1: Tupla (x1, y1)
        p2: Tupla (x2, y2)
    
    Returns:
        Distancia entre los puntos
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def punto_medio(p1, p2):
    """
    Calcula el punto medio entre dos puntos.
    
    Args:
        p1: Tupla (x1, y1)
        p2: Tupla (x2, y2)
    
    Returns:
        Tupla (x, y) del punto medio
    """
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def rectasCircunferencia(p1, p2, n=100):
    """
    Genera los puntos de una circunferencia dados dos puntos.
    El primer punto es el centro y el segundo define el radio.
    
    Args:
        p1: Tupla (x1, y1) - Centro de la circunferencia
        p2: Tupla (x2, y2) - Punto en la circunferencia (define el radio)
        n: Número de puntos a generar (por defecto 100)
    
    Returns:
        Lista de coordenadas [x1, y1, x2, y2, ..., xn, yn]
    """
    # Calcular centro y radio
    cx, cy = p1
    radio = distancia_entre_puntos(p1, p2)
    
    # Generar puntos de la circunferencia
    puntos = []
    for i in range(n):
        theta = 2 * math.pi * i / n
        x = cx + radio * math.cos(theta)
        y = cy + radio * math.sin(theta)
        puntos.extend([x, y])
    
    return puntos


def rectasRectangulo(p1, p2, n=4):
    """
    Genera los puntos de un rectángulo dados dos puntos diagonales.
    
    Args:
        p1: Tupla (x1, y1) - Esquina superior izquierda
        p2: Tupla (x2, y2) - Esquina inferior derecha
        n: Número de puntos (por defecto 4 para un rectángulo)
    
    Returns:
        Lista de coordenadas [x1, y1, x2, y2, x3, y3, x4, y4]
    """
    x1, y1 = p1
    x2, y2 = p2
    
    # Asegurar que x1 < x2 y y1 < y2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    
    # Generar los 4 vértices del rectángulo
    puntos = [
        x1, y1,  # Esquina superior izquierda
        x2, y1,  # Esquina superior derecha
        x2, y2,  # Esquina inferior derecha
        x1, y2   # Esquina inferior izquierda
    ]
    
    return puntos


def generar_elipse(centro, radio_x, radio_y, n=100):
    """
    Genera los puntos de una elipse.
    
    Args:
        centro: Tupla (cx, cy) - Centro de la elipse
        radio_x: Radio en el eje x
        radio_y: Radio en el eje y
        n: Número de puntos a generar
    
    Returns:
        Lista de coordenadas [x1, y1, x2, y2, ..., xn, yn]
    """
    cx, cy = centro
    puntos = []
    
    for i in range(n):
        theta = 2 * math.pi * i / n
        x = cx + radio_x * math.cos(theta)
        y = cy + radio_y * math.sin(theta)
        puntos.extend([x, y])
    
    return puntos


def generar_arco(centro, radio, angulo_inicio, angulo_fin, n=50):
    """
    Genera los puntos de un arco.
    
    Args:
        centro: Tupla (cx, cy) - Centro del arco
        radio: Radio del arco
        angulo_inicio: Ángulo de inicio en radianes
        angulo_fin: Ángulo de fin en radianes
        n: Número de puntos a generar
    
    Returns:
        Lista de coordenadas [x1, y1, x2, y2, ..., xn, yn]
    """
    cx, cy = centro
    puntos = []
    
    for i in range(n):
        t = i / (n - 1)
        theta = angulo_inicio + t * (angulo_fin - angulo_inicio)
        x = cx + radio * math.cos(theta)
        y = cy + radio * math.sin(theta)
        puntos.extend([x, y])
    
    return puntos


def rotar_punto(punto, centro, angulo):
    """
    Rota un punto alrededor de un centro.
    
    Args:
        punto: Tupla (x, y) - Punto a rotar
        centro: Tupla (cx, cy) - Centro de rotación
        angulo: Ángulo de rotación en radianes
    
    Returns:
        Tupla (x, y) del punto rotado
    """
    x, y = punto
    cx, cy = centro
    
    # Trasladar al origen
    x_rel = x - cx
    y_rel = y - cy
    
    # Rotar
    x_rot = x_rel * math.cos(angulo) - y_rel * math.sin(angulo)
    y_rot = x_rel * math.sin(angulo) + y_rel * math.cos(angulo)
    
    # Trasladar de vuelta
    return (x_rot + cx, y_rot + cy)


def escalar_punto(punto, centro, factor):
    """
    Escala un punto respecto a un centro.
    
    Args:
        punto: Tupla (x, y) - Punto a escalar
        centro: Tupla (cx, cy) - Centro de escalado
        factor: Factor de escala
    
    Returns:
        Tupla (x, y) del punto escalado
    """
    x, y = punto
    cx, cy = centro
    
    x_esc = cx + (x - cx) * factor
    y_esc = cy + (y - cy) * factor
    
    return (x_esc, y_esc)


if __name__ == '__main__':
    # Pruebas de las funciones
    print("=== Pruebas de utilitygraph ===")
    
    # Prueba de distancia
    p1 = (0, 0)
    p2 = (3, 4)
    dist = distancia_entre_puntos(p1, p2)
    print(f"Distancia entre {p1} y {p2}: {dist}")
    
    # Prueba de punto medio
    medio = punto_medio(p1, p2)
    print(f"Punto medio: {medio}")
    
    # Prueba de circunferencia
    puntos_circ = rectasCircunferencia((0, 0), (1, 0), n=8)
    print(f"Puntos de circunferencia (8 puntos): {puntos_circ}")
    
    # Prueba de rectángulo
    puntos_rect = rectasRectangulo((0, 0), (10, 5))
    print(f"Puntos de rectángulo: {puntos_rect}")
    
    # Prueba de conversión polar-cartesiano
    x, y = polar_to_cartesian(5, math.pi/4)
    print(f"Polar (5, π/4) → Cartesiano ({x:.2f}, {y:.2f})")
    
    r, theta = cartesian_to_polar(3, 4)
    print(f"Cartesiano (3, 4) → Polar ({r:.2f}, {theta:.2f})")