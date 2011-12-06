#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, pygtk
from widgets import dayline
import random, datetime as dt
class Fact:
    def __init__(self, c):
        self.category = c
        self.start_time = dt.datetime.today() - dt.timedelta(random.randint(0, c))
        self.delta = dt.timedelta(random.random() + 0.1)
        self.activity = None

if __name__ == "__main__":
    w = gtk.Window()
    w.set_size_request(600, 300)
    w.connect("destroy", lambda *a, **k: gtk.main_quit())
    labels = {}
    filas = random.randint(5, 11)
    tabla = gtk.Table(rows = filas, columns = 2)
    facts = []
    for i in range(filas):
        facts.append(Fact(i))
    for i in range(filas):
        labels[i] = gtk.Label("label " + `i`)
        tabla.attach(labels[i], 0, 1, i, i+1, xoptions = 0)
    dayline = dayline.DayLine()
    dayline.plot(dt.date.today(), facts, dt.datetime.today(), dt.datetime.today())
    tabla.attach(dayline, 1, 2, 0, i+1)
    w.add(tabla)
    w.show_all()
    gtk.main()


