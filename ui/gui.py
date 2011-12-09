#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
from .scene import Scene
import datetime

class Ventana:
    def __init__(self):
        self.ventana = gtk.Window()
        self.ventana.set_size_request(600, 300)
        self.ventana.connect("delete_event", lambda *a, **kw: gtk.main_quit())
        self.ventana.connect("destroy", lambda *a, **kw: gtk.main_quit())
        self.container = gtk.VBox()
        self.grafica = gtk.EventBox()
        self.container.pack_start(self.grafica)
        self.controls = gtk.HBox()
        self.b_salir = gtk.Button(stock = gtk.STOCK_QUIT)
        self.b_salir.connect("clicked", self.__salir)
        self.controls.add(self.b_salir)
        # El valor más alto que se puede obtener es upper - page_size 
        self.zoom = gtk.Adjustment(62.0, 1.0, 365.0 + 31.0, 1.0, 31.0, 31.0)
        self.zoom_level = 62
        self.slider = gtk.HScale(self.zoom)
        self.slider.set_digits(0)
        for i in range(31, 365, 31):
            self.slider.add_mark(i, gtk.POS_TOP, None)
        self.controls.add(self.slider)
        self.slider.connect("value-changed", self.__update_zoom)
        self.container.pack_start(self.controls, expand = False)
        self.ventana.add(self.container)
        self.ventana.show_all()

    def __update_zoom(self, range):
        self.zoom_level = range.get_value()
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()

    def __salir(self, boton):
        self.ventana.destroy()

    def load_escena(self):
        # Premature optimization is the root of all evil. Pero más adelante tal vez debería estringir las tareas únicamente al zoom_level, para no tener que cargar todas en memoria si no las voy a mostrar.
        self.escena = Scene(self.tareas, self.zoom_level)

class VentanaPorEmpleado(Ventana):
    def __init__(self, tareas):
        Ventana.__init__(self)
        self.ventana.set_title("Vista por empleado")
        #tareas.sort(key = lambda t: t.fecha)
        self.tareas = tareas
        self.load_escena()
        self.grafica.add(self.escena)
        self.ventana.show_all()

class VentanaPorLinea(Ventana):
    def __init__(self):
        Ventana.__init__(self, tareas)
        self.ventana.set_title("Vista por línea")

