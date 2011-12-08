#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
from storage import sample
from storage import backend
from ui.gui import VentanaPorEmpleado
from lib import graphics

def main():
    """
    Crea la ventana principal y muestra los datos existentes del año en curso.
    """
    # tareas = sample.get_all_data()
    tareas = backend.get_all_data()
    ventana = VentanaPorEmpleado(tareas)
    gtk.main()

if __name__ == "__main__":
    main()

