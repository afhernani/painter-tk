from tkinter import *
from tkinter import ttk, colorchooser
from canvasvg import saveall, convert
import logging
import tksvg
from enum import Enum
from photos import Photos
from utilitygraph import *
from svgcanvas import loadSvg
# Requisitos: pip install svglib, svgpathtools
# Analisis: libreria pyinkscape -pypi


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('Paint')
# log.setLevel(logging.DEBUG)

'''class Modos(Enum):
    LINE = 1
    PEN = 2
    SQUARE = 3
    RECTANGLE = 4
    OVALO = 5
    CIRCLE = 6
    DRAW = 7
    MODIF = 8
    FREE = 9 '''

class main:
    def __init__(self,master):
        self.master = master
        self.modo = None
        self.photo = Photos()
        self.color_fg = 'black'
        self.color_bg = 'white'
        self.old_x = None
        self.old_y = None
        self.lin_x, self.lin_y = None, None
        self.penwidth = 5
        self.dragging_handle = 0  # 0 = no arrastrado, 1 = arrastrado
        self.inicialize()
        self.c.bind('<ButtonPress-1>', self.__selectstart)
        self.c.bind('<B1-Motion>',self.__paint) #drwaing the line 
        self.c.bind('<ButtonRelease-1>',self.__reset) # sali
        # used to record where dragging from
        self.selectBox = None
        self.linea = None
        self.originx, self.originy = 0, 0
        self.c.bind("<ButtonPress-3>", self.__SelectStart__)
        self.c.bind("<B3-Motion>", self.__SelectMotion__)
        self.c.bind("<ButtonRelease-3>", self.__SelectRelease__)
        self.c.bind("<Enter>", self.__entercanvas)
        self.c.bind("<Leave>", self.__leavecanvas)
        self.c.bind('<B1-Motion>', self.__edit_mode_handler)
        # Registro de todos los objetos dibujados
        self.objetos = []          # Lista de IDs de canvas
        self.objeto_seleccionado = None  # ID del objeto seleccionado
        self.modo_edicion = False  # ¿Estamos en modo edición?

    def __entercanvas(self, *args):
        self.c.configure(cursor="tcross")

    def __leavecanvas(self, *args):
        self.c.configure(cursor="")

    def __paint(self, e):
        """Button-1 mouse Motion """
        # Si hay un objeto seleccionado, MOVERLO
        if self.modo.get() == 'S' and self.objeto_seleccionado:
            dx = e.x - self.drag_start_x
            dy = e.y - self.drag_start_y
            self.c.move(self.objeto_seleccionado, dx, dy)
            self.drag_start_x = e.x
            self.drag_start_y = e.y
            return  # No dibujar nada nuevo

        if self.modo.get() == 'P':
            if self.old_x and self.old_y:
                self.c.create_line(self.old_x, self.old_y, e.x, e.y, 
                                   width=self.penwidth,fill=self.color_fg, 
                                   capstyle=ROUND, smooth=False, tags='lapiz'
                                   )

        elif self.modo.get() == 'L':
            if self.linea:
                self.c.coords(self.linea, self.lin_x, self.lin_y, e.x, e.y)

        elif self.modo.get() == 'C':
            if self.lin_x and self.lin_y:
                puntos = rectasCircunferencia(*[(self.lin_x, self.lin_y), (e.x, e.y)])
                self.c.coords(self.linea, *puntos)
        elif self.modo.get()== 'R':
            if self.lin_x and self.lin_y:
                puntos = rectasRectangulo(*[(self.lin_x, self.lin_y), (e.x, e.y)], n=4)
                self.c.coords(self.linea, *puntos)
        elif self.modo.get() == 'O':
            if self.lin_x and self.lin_y:
                puntos = [self.lin_x, self.lin_y, e.x, e.y]
                self.c.coords(self.linea, *puntos )
        elif self.modo.get() == 'A':
            if self.lin_x and self.lin_y:
                puntos = [self.lin_x, self.lin_y, e.x, e.y]
                self.c.coords(self.linea, *puntos)

        self.old_x = e.x
        self.old_y = e.y
        self.statusbar['text'] = f"{e.x} - {e.y}"

    def __selectstart(self, e):
        """Button-1 mouse press, start action draw"""
        self.lin_x, self.lin_y = e.x, e.y
        if self.modo.get() == 'L':
            self.linea = self.c.create_line(self.lin_x, self.lin_y, 
                                            self.lin_x, self.lin_y
                                            )
        elif self.modo.get() == 'C':
            puntos = rectasCircunferencia(*[(self.lin_x, self.lin_y), (self.lin_x, self.lin_y)])
            self.linea = self.c.create_line(*puntos)
            log.info(f"linea: {self.linea}")
        elif self.modo.get() == 'R':
            puntos = rectasRectangulo(*[(self.lin_x, self.lin_y), (self.lin_x, self.lin_y)], n=4)
            self.linea = self.c.create_line(*puntos)
        elif self.modo.get() == 'O':
            self.linea = self.c.create_oval(self.lin_x, self.lin_y, e.x, e.y)
        elif self.modo.get() == 'A':
            self.linea = self.c.create_arc(self.lin_x, self.lin_y, e.x, e.y)

    def __reset(self, e):    #reseting or cleaning the canvas 
        """('<ButtonRelease-1>',self.__reset) mouse button soltar """
        self.old_x = None
        self.old_y = None
        if self.modo.get() == 'L':
            x1, y1, x2, y2 = self.c.coords(self.linea)
            self.c.delete(self.linea)
            # guardar id devuelto por create_lien
            n_id = self.c.create_line(x1, y1, x2, y2,
                            width=self.penwidth,fill=self.color_fg, 
                            capstyle=ROUND, smooth=False, tags='linea'
                            )
            # self.lin_x, self.lin_y = None, None
            self.objetos.append(n_id) # hay que hacer todo esto a todos
        elif self.modo.get() == 'P':
            pass
        elif self.modo.get() == 'C':
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            self.c.create_line(*puntos, width=self.penwidth, fill=self.color_fg,
                                capstyle=ROUND, smooth=False, tags='circle')
            # self.lin_x = self.lin_y = None
        elif self.modo.get() == 'R':
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            self.c.create_line(*puntos, width=self.penwidth, fill=self.color_fg,
                                capstyle=ROUND, smooth=False, tags='rectangle')
            # self.lin_x = self.lin_y = None
        elif self.modo.get() == 'O':
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            self.c.create_oval(*puntos, width=self.penwidth, outline=self.color_fg,
                                fill='', tags='oval')
            self.statusbar.config(text=f"Puntos Ovalo = {puntos}")
        elif self.modo.get() == 'A':
            puntos = self.c.coords(self.linea)
            self.c.delete(self.linea)
            self.c.create_arc(*puntos, width=self.penwidth, outline=self.color_fg,
                                fill='', tags='oval')                        

        self.lin_x = self.lin_y = None

    def changeW(self,e): #change Width of pen through slider
        self.penwidth = e
           

    def clear(self):
        self.c.delete(ALL)

    def change_fg(self):  #changing the pen color
        self.color_fg=colorchooser.askcolor(color=self.color_fg)[1]

    def change_bg(self):  #changing the background color canvas
        self.color_bg=colorchooser.askcolor(color=self.color_bg)[1]
        self.c['bg'] = self.color_bg

    def save(self):
        """Guarda docuemtno en formato svg"""
        log.info('save function')
        saveall(filename='downloads/canvas.svg', canvas=self.c)
        self.statusbar.config(text="canvas.svg saved ...")

    def muestra(self):
        """load svg file, infileName, and canvas"""
        '''items = self.c.find_all()
        log.info(f"items canvas: {items}")
        img = tksvg.SvgImage(file='canvas.svg')
        log.info(f"tksvg: {dir(tksvg)}")
        w, h = img.width() / 2 , img.height() / 2
        self.c.create_image( w, h, image=img)
        self.c.image = img'''
        loadSvg('canvas.svg', self.c)
        self.statusbar['text'] = "canvas.svg loaded ..."

    def canvasconfig(self):
        log.info(f"Config canvas: {self.c}")
        options = self.c.config()
        # for k, v in options.items():
        #    log.info(f"{k}: {v}")
        log.info(f"stado: {self.c['state']}") 
        self.c.configure(state='disabled')
        # state = self.c.itemcget(self.c, 'state')
        # log.info(f"stado: {state}") 

    # binding for drag select
    def __SelectStart__(self, event):
        self.originx = self.c.canvasx(event.x)
        self.originy = self.c.canvasy(event.y)
        self.selectBox = self.c.create_rectangle(self.originx, self.originy, self.originx, self.originy)
        # MODO SELECCIÓN: buscar si hay un objeto bajo el cursor
        if self.modo.get() == 'S':
            self.__seleccionar_objeto(event)
            return  # No dibujar nada nuevo
        
        self.lin_x, self.lin_y = event.x, event.y
    
        if self.modo.get() == 'L':
            self.linea = self.c.create_line(...)

    def __seleccionar_objeto(self, e):
        """Busca objetos que realmente toquen el punto del click"""
        halo = 8  # Radio de tolerancia en píxeles
        
        # Busca todos los objetos en un pequeño cuadrado alrededor del click
        encontrados = self.c.find_overlapping(
            e.x - halo, e.y - halo,
            e.x + halo, e.y + halo
        )
        
        # Filtrar solo los que son nuestros objetos
        candidatos = [item for item in encontrados if item in self.objetos]
        
        if candidatos:
            # Seleccionar el primero (el de arriba en el z-order)
            self.objeto_seleccionado = candidatos[-1]
            self.c.itemconfig(self.objeto_seleccionado, fill='red')
            self.drag_start_x = e.x
            self.drag_start_y = e.y
        else:
            self.statusbar['text'] = "Ningún objeto bajo el cursor"

    # binding for drag select
    def __SelectMotion__(self, event):
        xnew = self.c.canvasx(event.x)
        ynew = self.c.canvasy(event.y)
        # correct cordinates so it gives (upper left, lower right)
        if xnew < self.originx and ynew < self.originy:
            self.c.coords(self.selectBox, xnew, ynew, self.originx, self.originy)
        elif xnew < self.originx:
            self.c.coords(self.selectBox,xnew,self.originy,self.originx,ynew)
        elif ynew < self.originy:
            self.c.coords(self.selectBox, self.originx, ynew, xnew, self.originy)
        else:
            self.c.coords(self.selectBox, self.originx, self.originy, xnew, ynew)

    # binding for drag select
    def __SelectRelease__(self, event):
        x1, y1, x2, y2 = self.c.coords(self.selectBox)
        self.c.delete(self.selectBox)
        # find all objects within select box
        selectedPointers = []
        for i in self.c.find_enclosed(x1, y1, x2, y2):
            points = self.c.coords(i)
            log.info(f"type selected: {self.c.type(i)}")
            tmp     = self.c.itemconfigure(i)
            options = dict((v0, v4) for v0, v1, v2, v3, v4 in tmp.values())
            log.info(f"option object selected: {options}")
            self.c.itemconfig(i, {'state': DISABLED} )
            # if x3>x1 and x4<x2 and y3>y1 and y4<y2:
            selectedPointers.append(i)
        self.Callback(selectedPointers)

    # function to receive IDs of selected items
    def Callback(self, pointers):
        log.info(f"Callback: {pointers}")

    def changevariable(self, *args):
        log.info(f"variable: {self.modo.get()}")

    def inicialize(self):
        # barra de estado
        self.statusbar = ttk.Label(self.master, text="on the way ..", relief=SUNKEN, anchor=W)
        self.statusbar.pack(side=BOTTOM, fill=BOTH)
        # otros botones
        self.controls = Frame(self.master,padx = 5,pady = 5)
        Label(self.controls, text='Pen Width:',font=('arial 9')).grid(row=0,column=0)
        self.slider = ttk.Scale(self.controls,from_= 5, to = 100,command=self.changeW,orient=HORIZONTAL)
        self.slider.set(self.penwidth)
        self.slider.grid(row=0,column=1,ipadx=30)
        # self.sv = ttk.Button(self.controls, text="Save", command=self.save).grid(row=1, column=0)
        # creamos un style
        self.drawcontrols = Frame(self.controls,padx = 5,pady = 5)
        style = ttk.Style(self.drawcontrols)
        style.theme_use('default')  # 'aqua', 'step', 'clam', 'alt', 'default', 'classic'

        style.configure('IndicatorOff.TRadiobutton',
                        indicatorrelief=FLAT,
                        indicatormargin=-10,
                        indicatordiameter=-1,
                        relief=RAISED,
                        focusthickness=0, highlightthickness=0, padding=5)

        style.map('IndicatorOff.TRadiobutton',
                  background=[('selected', 'white'), ('active', '#ececec')])

        MODES = [("Line", "L", self.photo._line),
                 ("Pen", "P", self.photo._pen),
                 ("Circle", "C", self.photo._circle),
                 ("Rectangle", "R", self.photo._rectangle),
                 ("Oval", "O", self.photo._oval),
                 ("Arco", "A", self.photo._arco),
                 ("Select", "S", self.photo._select)
                 ]

        self.modo = StringVar(self.drawcontrols, "L")  # initialize
        self.modo.trace('w', callback=self.changevariable)

        for text, mode, img in MODES:
            ttk.Radiobutton(self.drawcontrols, image=img, variable=self.modo, value=mode, width=15,
                            style='IndicatorOff.TRadiobutton').pack(side=LEFT)
        self.drawcontrols.grid(row=0,column=2,ipadx=30)
        self.controls.pack(side=TOP)
        
        self.c = Canvas(self.master,width=500,height=500,bg=self.color_bg,)
        self.c.pack(fill=BOTH,expand=True)

        menu = Menu(self.master)
        self.master.config(menu=menu)
        filemenu = Menu(menu)
        colormenu = Menu(menu)
        menu.add_cascade(label='Colors',menu=colormenu)
        colormenu.add_command(label='Brush Color',command=self.change_fg)
        colormenu.add_command(label='Background Color',command=self.change_bg)
        optionmenu = Menu(menu)
        menu.add_cascade(label='Options',menu=optionmenu)
        optionmenu.add_command(label='Clear Canvas',command=self.clear)
        optionmenu.add_separator()
        optionmenu.add_command(label='Save', command=self.save)
        optionmenu.add_command(label='Load', command=self.muestra)
        optionmenu.add_command(label='Config', command=self.canvasconfig)
        optionmenu.add_separator()
        optionmenu.add_command(label='Exit',command=self.master.destroy)

    def select_item(self, item_id):
        """Selecciona una línea y muestra puntos de control"""
        coords = self.c.coords(item_id)
        x1, y1, x2, y2 = coords
        
        # Dibujar handles (círculos pequeños) en los extremos
        self.handle1 = self.c.create_oval(x1-5, y1-5, x1+5, y1+5, 
                                        fill='blue', tags='handle')
        self.handle2 = self.c.create_oval(x2-5, y2-5, x2+5, y2+5, 
                                        fill='blue', tags='handle')

    def __edit_mode_handler(self, e):
        """Maneja el arrastre según qué se está editando"""
        if getattr(self, 'dragging_handle', 0) == 1:
        # if self.dragging_handle == 1:
            # Mover primer extremo
            self.c.coords(self.linea, e.x, e.y, self.x2, self.y2)
        if getattr(self, 'dragging_handle', 0) == 2:
        # elif self.dragging_handle == 2:
            # Mover segundo extremo
            self.c.coords(self.linea, self.x1, self.y1, e.x, e.y)

    # En paint.py, agregar estos métodos a la clase main:

    def select_mode(self, e):
        """Maneja el click en modo selección"""
        if self.modo.get() != 'S':
            return
            
        # Limpiar selección anterior
        self.deselect_all()
        
        # Buscar objeto cercano al click
        items = self.c.find_closest(e.x, e.y, halo=8)
        
        for item in items:
            tags = self.c.gettags(item)
            if 'linea' in tags or 'lapiz' in tags:
                self.selected_item = item
                self.show_handles(item)
                break

    def show_handles(self, item_id):
        """Muestra puntos de control en la línea"""
        coords = self.c.coords(item_id)
        
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            
            # Handle del inicio
            self.handle_start = self.c.create_oval(
                x1-6, y1-6, x1+6, y1+6,
                fill='blue', outline='white', width=2,
                tags=('handle', 'handle_start')
            )
            
            # Handle del final
            self.handle_end = self.c.create_oval(
                x2-6, y2-6, x2+6, y2+6,
                fill='blue', outline='white', width=2,
                tags=('handle', 'handle_end')
            )

    def deselect_all(self):
        """Elimina handles y deselecciona"""
        self.c.delete('handle')
        self.selected_item = None


if __name__ == '__main__':
    root = Tk()
    main(root)
    root.title('Paint App')
    root.mainloop()

    













    
