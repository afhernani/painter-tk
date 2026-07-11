# -*- coding: utf-8 -*-
"""
Sistema de logging centralizado para painter-tk
Configura el logging para escribir en archivo y consola
"""
import logging
import os
from datetime import datetime


# Directorio para logs
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Nombre del archivo de log con timestamp
LOG_FILE = os.path.join(
    LOG_DIR, 
    f'painter_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# Configuración del formato
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configuración del logger raíz
logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # También muestra en consola
    ]
)


def get_logger(name):
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (ej: 'Paint', 'SVGCanvas', 'Config')
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_exception(logger, exception, context=""):
    """
    Registra una excepción completa con traceback.
    
    Args:
        logger: Logger a usar
        exception: La excepción capturada
        context: Descripción del contexto donde ocurrió
    """
    import traceback
    logger.error(f"{context}: {exception}")
    logger.error(traceback.format_exc())


# Logger por defecto
default_logger = get_logger('Painter')


if __name__ == '__main__':
    # Prueba del sistema de logging
    test_logger = get_logger('Test')
    
    print("=== Prueba de Logger ===")
    test_logger.debug("Mensaje de debug")
    test_logger.info("Mensaje de info")
    test_logger.warning("Mensaje de warning")
    test_logger.error("Mensaje de error")
    
    print(f"\nLog guardado en: {LOG_FILE}")