#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
# Modified by (C) 2011 Francisco José Rodríguez Bogado <bogado@qinn.es>

"""
Gráfico de segmentos horizontales.
"""

import gtk
from lib import graphics

import time, datetime as dt
from collections import defaultdict

class Scene(graphics.Scene):
    """
    «data» son tareas con un empleado, un área, una hora de inicio y una 
    duración.
    """
    def __init__(self, data = []):
        graphics.Scene.__init__(self)
        self.day_counts = defaultdict(list)
        lineas, empleados = defaultdict(int), defaultdict(int)
        self.data = data
        self.data.sort(key = lambda i: i.ini)
        for tarea in self.data:
            self.day_counts[tarea.ini.date()].append(tarea)
            lineas[tarea.area] += 1
            empleados[tarea.empleado] += 1
            if tarea.fin and tarea.ini.date() != tarea.fin.date():
                self.day_counts[tarea.fin.date()].append(tarea)
        self.lineas = [area[0] for area in sorted(lineas.items(), 
                                                  key=lambda item:item[1], 
                                                  reverse=True)]
        self.empleados = empleados.keys()
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        if not self.data:
            return
        g = graphics.Graphics(context)
        g.set_line_style(width=1)
        start_date = self.data[0].ini.date()
        end_date = (self.data[-1].ini + self.data[-1].duracion).date()
        days = (end_date - start_date).days
        full_days = []
        for day in range(days):
            current_date = start_date + dt.timedelta(days = day)
            if not self.day_counts[current_date]:
                continue
            full_days.append(self.day_counts[current_date])
        day_pixel = float(self.width) / len(full_days)
        cur_x = 0
        pixel_width = max(round(day_pixel), 1)
        for day in full_days:
            cur_x += round(day_pixel)
            for j, fact in enumerate(day):
                #bar per empleado
                g.rectangle(cur_x, 27 + self.empleados.index(fact.empleado) * 6, pixel_width, 6)
                #bar per área
                g.rectangle(cur_x, 102 + self.lineas.index(fact.area) * 6, pixel_width, 6)
                #number of lineas
                g.rectangle(cur_x, self.height - 3 * j, pixel_width, 3)
            g.fill("#aaa")


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

