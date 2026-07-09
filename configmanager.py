# -*- coding: utf-8 -*-
# Tkinter canvas to SVG exporter

import configparser
import os
from pathlib import Path

__author__  = "hernani <afhernani@gmail.com>"

__all__ = ["ConfigManager"]

class ConfigManager:
    """Gestiona la configuración de la aplicación usando configparser"""
    
    def __init__(self, config_file='config.ini'):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Valores por defecto
        self._set_defaults()
        
        # Cargar configuración existente si existe
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            # Si no existe, crear con valores por defecto
            self.save()
    
    def _set_defaults(self):
        """Establece valores por defecto"""
        self.config['General'] = {
            'canvas_width': '800',
            'canvas_height': '600',
            'default_mode': 'L',
            'last_save_path': 'downloads/'
        }
        
        self.config['Pen'] = {
            'default_width': '5',
            'default_color_fg': 'black',
            'default_color_bg': 'white'
        }
        
        self.config['Recent'] = {
            'last_opened_file': '',
            'last_saved_file': ''
        }
        
        self.config['Display'] = {
            'show_grid': 'False',
            'grid_color': 'lightgray',
            'grid_spacing': '20'
        }
    
    def get(self, section, key, fallback=None):
        """
        Obtiene un valor de la configuración.
        
        Args:
            section: Sección del archivo (ej: 'General', 'Pen')
            key: Clave a buscar
            fallback: Valor por defecto si no existe
        
        Returns:
            El valor como string
        """
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section, key, fallback=0):
        """Obtiene un valor entero"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getfloat(self, section, key, fallback=0.0):
        """Obtiene un valor flotante"""
        return self.config.getfloat(section, key, fallback=fallback)
    
    def getboolean(self, section, key, fallback=False):
        """Obtiene un valor booleano"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def set(self, section, key, value):
        """
        Establece un valor en la configuración.
        
        Args:
            section: Sección del archivo
            key: Clave a establecer
            value: Valor a guardar (se convierte a string)
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
    
    def save(self):
        """Guarda la configuración en el archivo"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_canvas_size(self):
        """Obtiene el tamaño del canvas"""
        width = self.getint('General', 'canvas_width', 800)
        height = self.getint('General', 'canvas_height', 600)
        return width, height
    
    def get_pen_defaults(self):
        """Obtiene los valores por defecto del pincel"""
        return {
            'width': self.getint('Pen', 'default_width', 5),
            'color_fg': self.get('Pen', 'default_color_fg', 'black'),
            'color_bg': self.get('Pen', 'default_color_bg', 'white')
        }
    
    def save_last_file(self, filepath):
        """Guarda la ruta del último archivo"""
        self.set('Recent', 'last_saved_file', filepath)
        self.save()
    
    def get_last_file(self):
        """Obtiene la ruta del último archivo"""
        return self.get('Recent', 'last_saved_file', '')


# Instancia global para usar en toda la aplicación
config = ConfigManager()