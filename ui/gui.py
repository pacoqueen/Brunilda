#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
from .scene import Scene
from .widgets.dayline import DayLine
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
        self.b_salir = gtk.Button(stock = gtk.STOCK_QUIT)
        self.b_salir.connect("clicked", self.__salir)
        self.container.pack_start(self.b_salir, expand = False)
        self.ventana.add(self.container)
        self.ventana.show_all()

    def __salir(self, boton):
        self.ventana.destroy()

class UNUSABLE_VentanaPorEmpleado(Ventana):
    def __init__(self, tareas):
        Ventana.__init__(self)
        self.ventana.set_title("Vista por empleado")
        #self.grafica.add(Scene(tareas))
        tareas.sort(key = lambda t: t.fecha)
        oldest_fecha = tareas[2].fecha 
        dl = DayLine(start_time = oldest_fecha, 
                     #scope_hours = int(
                     #   (tareas[-1].fin - tareas[0].ini).total_seconds()/3600))
                     scope_hours = 24 * 4)
        self.grafica.add(dl)
        dl.plot(#datetime.date.today(), 
                oldest_fecha.date(), tareas, oldest_fecha)
                #, datetime.datetime.now())
        self.ventana.show_all()

class VentanaPorEmpleado(Ventana):
    def __init__(self, tareas):
        Ventana.__init__(self)
        self.ventana.set_title("Vista por empleado")
        #tareas.sort(key = lambda t: t.fecha)
        self.grafica.add(Scene(tareas))
        self.ventana.show_all()

class VentanaPorLinea(Ventana):
    def __init__(self):
        Ventana.__init__(self, tareas)
        self.ventana.set_title("Vista por línea")

