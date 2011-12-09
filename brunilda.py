#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk
from storage import sample
from storage import backend
from ui.gui import Ventana

def main():
    """
    Crea la ventana principal y muestra los datos existentes del año en curso.
    """
    # tareas = sample.get_all_data()
    tareas = backend.get_all_data()
    ventana = Ventana(tareas)
    gtk.main()

if __name__ == "__main__":
    main()

