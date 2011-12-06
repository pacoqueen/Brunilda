#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk

class Ventana:
    def __init__(self):
        self.ventana = gtk.Window()
        self.ventana.connect("destroy", lambda *a, **kw: gtk.main_quit())
        self.ventana.show_all()

class VentanaPorEmpleado(Ventana):
    def __init__(self):
        Ventana.__init__(self)
        self.ventana.set_title("Vista por empleado")

class VentanaPorLinea(Ventana):
    def __init__(self):
        Ventana.__init__(self)
        self.ventana.set_title("Vista por línea")

