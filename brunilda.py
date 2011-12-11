#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
import storage
from ui.gui import Ventana

def main():
    """
    Crea la ventana principal y muestra los datos existentes del año en curso.
    """
    tareas = storage.get_all_data()
    ventana = Ventana(tareas)
    gtk.main()

if __name__ == "__main__":
    main()

