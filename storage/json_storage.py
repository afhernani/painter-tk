# -*- coding: utf-8 -*-
"""
Módulo de persistencia en formato JSON.
Se encarga de guardar y cargar proyectos completos.
"""
import json
import logging
from geometry import Punto, Linea, Circulo, Poligono, Polyline, Rectangulo, Elipse, Arco, PointShape

log = logging.getLogger('Storage.JSON')

# Factory: mapa de tipos → clases
SHAPE_FACTORY = {
    "Circulo": Circulo,
    "Poligono": Poligono,
    "Linea": Linea,
    "Polyline": Polyline,
    "Rectangulo": Rectangulo,
    "Elipse": Elipse,
    "Arco": Arco,
    "Point": PointShape,
    "Punto": PointShape,
}


def save_project(filepath, shapes):
    """
    Guarda una lista de figuras Shape en un archivo JSON.
    
    Args:
        filepath: ruta del archivo .json
        shapes: lista de objetos Shape (deben implementar to_dict())
    """
    data = [shape.to_dict() for shape in shapes]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    log.info(f"Proyecto guardado en JSON: {filepath} ({len(data)} figuras)")


def load_project(filepath):
    """
    Carga una lista de figuras desde un archivo JSON.
    
    Args:
        filepath: ruta del archivo .json
        
    Returns:
        lista de objetos Shape reconstruidos
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    shapes = []
    for item in data:
        # usar pop para sacar el tipo y borrarlo del diccionario
        shape_type = item.pop("type", None)
        if not shape_type:
            continue
        
        cls = SHAPE_FACTORY.get(shape_type)
        
        if not cls:
            log.warning(f"Tipo de figura desconocido: {shape_type}")
            continue
        
        # Reconstruir objetos Punto donde aparezcan
        item = _reconstruir_puntos(item)
        
        try:
            shape = cls(**item)
            shapes.append(shape)
        except Exception as e:
            log.error(f"Error al reconstruir {shape_type}: {e}")
    
    log.info(f"Proyecto cargado desde JSON: {filepath} ({len(shapes)} figuras)")
    return shapes


def _reconstruir_puntos(item):
    """
    Recorre un diccionario de figura y convierte los diccionarios
    con clave 'x','y' en objetos Punto.
    """
    # Punto único (ej: PointShape)
    if "punto" in item and isinstance(item["punto"], dict) and "x" in item["punto"]:
        item["punto"] = Punto.from_dict(item["punto"])
    
    # Centro (Circulo, Poligono)
    if "centro" in item and isinstance(item["centro"], dict) and "x" in item["centro"]:
        item["centro"] = Punto.from_dict(item["centro"])
    
    # Extremos (Linea)
    if "p1" in item and isinstance(item["p1"], dict) and "x" in item["p1"]:
        item["p1"] = Punto.from_dict(item["p1"])
    if "p2" in item and isinstance(item["p2"], dict) and "x" in item["p2"]:
        item["p2"] = Punto.from_dict(item["p2"])
    
    # Lista de puntos (Polyline)
    if "puntos" in item and isinstance(item["puntos"], list):
        item["puntos"] = [
            Punto.from_dict(p) if isinstance(p, dict) and "x" in p else p
            for p in item["puntos"]
        ]
    
    return item