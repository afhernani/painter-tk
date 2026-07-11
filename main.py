#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada de la aplicación painter-tk.
"""

import sys
import os
import logging

# Asegurar que el directorio raíz esté en el path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import tkinter as tk
from ui import App


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()