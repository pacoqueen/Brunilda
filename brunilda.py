#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
from storage import sample
from ui.gui import VentanaPorEmpleado

def main():
    """
    Crea la ventana principal y muestra los datos existentes del año en curso.
    """
    ventana = VentanaPorEmpleado()
    gtk.main()

if __name__ == "__main__":
    main()

