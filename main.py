#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
painter-tk - Aplicación de dibujo vectorial con Tkinter

Punto de entrada principal de la aplicación.
Inicializa la configuración, la interfaz de usuario y arranca
el bucle principal de Tkinter.

Uso:
    python main.py
    python main.py archivo.svg  # Abre un archivo específico
"""

import sys
import os
import logging
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el path
# para poder importar los paquetes geometry, storage y ui
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuración del sistema de logging centralizado
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_DIR / 'painter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger('main')


def cargar_configuracion():
    """
    Carga la configuración de la aplicación.
    
    Returns:
        dict: Diccionario con la configuración cargada
    """
    log.info("Cargando configuración...")
    
    try:
        from configmanager import config
        return {
            'color_fg': config.get('Pen', 'default_color_fg', 'black'),
            'color_bg': config.get('Pen', 'default_color_bg', 'white'),
            'penwidth': config.getfloat('Pen', 'default_width', 5.0),
            'canvas_width': config.getint('General', 'canvas_width', 800),
            'canvas_height': config.getint('General', 'canvas_height', 600),
            'default_mode': config.get('General', 'default_mode', 'L'),
            'last_file': config.get('Recent', 'last_saved_file', ''),
        }
    except Exception as e:
        log.warning(f"No se pudo cargar configmanager, usando valores por defecto: {e}")
        return {
            'color_fg': 'black',
            'color_bg': 'white',
            'penwidth': 5.0,
            'canvas_width': 800,
            'canvas_height': 600,
            'default_mode': 'L',
            'last_file': '',
        }


def verificar_dependencias():
    """
    Verifica que todas las dependencias necesarias estén disponibles.
    
    Returns:
        bool: True si todas las dependencias están disponibles
    """
    dependencias_ok = True
    
    # Verificar Tkinter
    try:
        import tkinter
        log.info(f"Tkinter versión: {tkinter.TkVersion}")
    except ImportError as e:
        log.error(f"Tkinter no disponible: {e}")
        dependencias_ok = False
    
    # Verificar PIL/Pillow (para las imágenes de la toolbar)
    try:
        from PIL import Image
        log.info("PIL/Pillow disponible")
    except ImportError:
        log.warning("PIL/Pillow no disponible. Algunas funciones de imagen no funcionarán.")
    
    # Verificar módulos propios del proyecto
    modulos_proyecto = ['geometry', 'storage', 'ui', 'photos', 'utilitygraph']
    for modulo in modulos_proyecto:
        try:
            __import__(modulo)
            log.info(f"Módulo '{modulo}' disponible")
        except ImportError as e:
            log.warning(f"Módulo '{modulo}' no disponible: {e}")
    
    return dependencias_ok


def inicializar_directorios():
    """
    Crea los directorios necesarios para la aplicación si no existen.
    """
    directorios = [
        PROJECT_ROOT / 'logs',
        PROJECT_ROOT / 'downloads',
        PROJECT_ROOT / 'Images',
    ]
    
    for directorio in directorios:
        directorio.mkdir(exist_ok=True)
        log.debug(f"Directorio verificado: {directorio}")


def main():
    """
    Función principal de la aplicación.
    
    Flujo:
        1. Verificar dependencias
        2. Inicializar directorios
        3. Cargar configuración
        4. Crear e iniciar la aplicación Tkinter
    """
    log.info("=" * 60)
    log.info("Iniciando painter-tk")
    log.info("=" * 60)
    
    # Paso 1: Verificar dependencias
    if not verificar_dependencias():
        log.error("Faltan dependencias críticas. La aplicación no puede iniciarse.")
        sys.exit(1)
    
    # Paso 2: Inicializar directorios
    inicializar_directorios()
    
    # Paso 3: Cargar configuración
    config = cargar_configuracion()
    log.info(f"Configuración cargada: {config}")
    
    # Paso 4: Importar y crear la aplicación
    try:
        from ui import App
        
        # Crear la ventana raíz de Tkinter
        import tkinter as tk
        root = tk.Tk()
        root.title('Paint App')
        
        # Configurar tamaño de ventana según configuración
        root.geometry(f"{config['canvas_width']}x{config['canvas_height'] + 100}")
        
        # Crear la aplicación pasando la configuración
        app = App(root, config=config)
        
        # Si se pasó un archivo como argumento, abrirlo
        if len(sys.argv) > 1:
            archivo = sys.argv[1]
            if os.path.exists(archivo):
                log.info(f"Abriendo archivo: {archivo}")
                app.cargar_archivo(archivo)
            else:
                log.warning(f"Archivo no encontrado: {archivo}")
        
        # Iniciar el bucle principal de Tkinter
        log.info("Iniciando bucle principal de Tkinter...")
        root.mainloop()
        
    except Exception as e:
        log.exception(f"Error fatal al iniciar la aplicación: {e}")
        sys.exit(1)
    
    log.info("Aplicación finalizada correctamente")


if __name__ == '__main__':
    main()