#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, pygtk
import datetime as dt

if __name__ == "__main__":
    w = gtk.Window()
    #w.set_size_request(600, 300)
    w.connect("destroy", lambda *a, **k: gtk.main_quit())
    filas = 31
    columnas = 3 * 24 / 2 # Celda cada 2 horas.
    tabla = gtk.Table(filas, columnas)
    for x in range(columnas):
        for y in range(filas):
            entry = gtk.Entry()
            entry.set_text("(%d, %d)" % (x, y))
            tabla.attach(entry, x, x+1, y, y+1, xoptions = 0)
    w.add(tabla)
    w.show_all()
    gtk.main()


