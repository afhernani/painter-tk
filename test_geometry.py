#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el paquete geometry
Verifica que todas las clases geométricas funcionen correctamente
"""
import tkinter as tk
from geometry import Punto, Linea, Circulo, Rectangulo, Elipse, Arco, Polyline


def main():
    # Crear ventana y canvas
    root = tk.Tk()
    root.title("Test Geometry - Prueba de clases geométricas")
    root.geometry("800x600")
    
    canvas = tk.Canvas(root, width=800, height=600, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Título
    canvas.create_text(400, 20, text="Prueba de Clases Geométricas", 
                       font=('Arial', 14, 'bold'), fill='blue')
    
    # ============================================================
    # PRUEBA 1: Punto
    # ============================================================
    print("\n=== PRUEBA 1: Clase Punto ===")
    p1 = Punto(100, 100)
    p2 = Punto(200, 200)
    print(f"Punto 1: {p1}")
    print(f"Punto 2: {p2}")
    print(f"Distancia entre p1 y p2: {p1.distancia_a(p2):.2f}")
    
    # Dibujar puntos
    canvas.create_oval(95, 95, 105, 105, fill='red', outline='red')
    canvas.create_oval(195, 195, 205, 205, fill='red', outline='red')
    canvas.create_text(100, 80, text="P1(100,100)", fill='red')
    canvas.create_text(200, 180, text="P2(200,200)", fill='red')
    
    # ============================================================
    # PRUEBA 2: Línea
    # ============================================================
    print("\n=== PRUEBA 2: Clase Linea ===")
    linea = Linea(Punto(50, 150), Punto(250, 150), color='green', grosor=3)
    print(f"Línea: {linea}")
    linea.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 3: Círculo
    # ============================================================
    print("\n=== PRUEBA 3: Clase Circulo ===")
    circulo = Circulo(Punto(400, 150), radio=50, color='blue', grosor=2)
    print(f"Círculo: {circulo}")
    circulo.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 4: Rectángulo
    # ============================================================
    print("\n=== PRUEBA 4: Clase Rectangulo ===")
    rect = Rectangulo(Punto(500, 100), Punto(700, 200), color='purple', grosor=2)
    print(f"Rectángulo: {rect}")
    rect.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 5: Elipse
    # ============================================================
    print("\n=== PRUEBA 5: Clase Elipse ===")
    elipse = Elipse(Punto(150, 350), radio_x=80, radio_y=40, color='orange', grosor=2)
    print(f"Elipse: {elipse}")
    elipse.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 6: Arco
    # ============================================================
    print("\n=== PRUEBA 6: Clase Arco ===")
    arco = Arco(Punto(400, 300), Punto(500, 400), inicio=0, extension=180, 
                color='red', grosor=3)
    print(f"Arco: {arco}")
    arco.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 7: Polyline (trazo libre)
    # ============================================================
    print("\n=== PRUEBA 7: Clase Polyline ===")
    puntos_trazo = [
        Punto(600, 300),
        Punto(620, 320),
        Punto(640, 310),
        Punto(660, 330),
        Punto(680, 320),
        Punto(700, 340)
    ]
    polyline = Polyline(puntos_trazo, color='brown', grosor=2)
    print(f"Polyline: {polyline}")
    polyline.dibujar_en(canvas)
    
    # ============================================================
    # PRUEBA 8: Mover objetos
    # ============================================================
    print("\n=== PRUEBA 8: Mover objetos ===")
    print("Moviendo línea 50 píxeles a la derecha...")
    linea.mover(50, 0)
    linea.actualizar_en_canvas(canvas)
    
    print("Moviendo círculo 30 píxeles abajo...")
    circulo.mover(0, 30)
    circulo.actualizar_en_canvas(canvas)
    
    # ============================================================
    # PRUEBA 9: Bounding Box
    # ============================================================
    print("\n=== PRUEBA 9: Bounding Box ===")
    print(f"BBox de línea: {linea.bbox()}")
    print(f"BBox de círculo: {circulo.bbox()}")
    print(f"BBox de rectángulo: {rect.bbox()}")
    
    # Dibujar bounding boxes
    bbox_linea = linea.bbox()
    canvas.create_rectangle(*bbox_linea, outline='gray', dash=(2, 2))
    
    bbox_circulo = circulo.bbox()
    canvas.create_rectangle(*bbox_circulo, outline='gray', dash=(2, 2))
    
    # Etiquetas
    canvas.create_text(400, 500, text="Línea roja movida 50px derecha", 
                       fill='red')
    canvas.create_text(400, 520, text="Círculo azul movido 30px abajo", 
                       fill='blue')
    canvas.create_text(400, 540, text="Líneas punteadas grises = Bounding Boxes", 
                       fill='gray')
    
    # ============================================================
    # PRUEBA 10: Copiar punto
    # ============================================================
    print("\n=== PRUEBA 10: Copiar punto ===")
    p3 = p1.copiar()
    print(f"Punto original: {p1}")
    print(f"Punto copiado: {p3}")
    print(f"¿Son iguales? {p1 == p3}")
    
    # Modificar copia
    p3.x = 300
    print(f"Después de modificar copia: {p3}")
    print(f"Original sigue igual: {p1}")
    
    print("\n✅ Todas las pruebas completadas!")
    print("Cierra la ventana para terminar.")
    
    root.mainloop()


if __name__ == '__main__':
    main()