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
        self.bars = {}
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def on_enter_frame(self, scene, context):
        if not self.data:
            return
        g = graphics.Graphics(context)
        g.set_line_style(width=1)
        start_date = self.data[0].ini.date()
        end_date = (self.data[-1].fin + dt.timedelta(1)).date()
        days = (end_date - start_date).days
        full_days = []
        for day in range(days):
            current_date = start_date + dt.timedelta(days = day)
            if not self.day_counts[current_date]:
                continue
            full_days.append(self.day_counts[current_date])
        for tarea in self.bars:
            bar = self.bars[tarea]
            self.remove_child(bar)  # TODO: Al redimensionar se superponen todas las barras. Esto no funciona para borrarlas primero :(
        day_pixel = float(self.width) / len(full_days)
        cur_x = 0
        pixel_width = max(round(day_pixel), 1)
        for lista_tareas_day in full_days:
            cur_x += round(day_pixel)
            #print "lista_tareas_day", lista_tareas_day
            for j, tarea in enumerate(lista_tareas_day):
                #bar per empleado
                #g.rectangle(cur_x, 27 + self.empleados.index(fact.empleado) * 6, pixel_width, 6)
                bar_alto = 6
                bar_ancho = pixel_width 
                bar = graphics.Rectangle(bar_ancho, bar_alto, fill = "#aaa", 
                                         stroke = "#aaa")
                bar.x = cur_x
                bar.y = 27 + self.empleados.index(tarea.empleado) * bar_alto 
                bar.tarea = tarea
                if tarea.empleado in self.empleados:
                    bar.empleado = self.empleados.index(tarea.empleado)
                else:
                    bar.empleado = len(self.empleados)
                print j, tarea, "(%d, %d) - (%d, %d)" % (
                    bar.x, bar.y, bar.x + bar.width, bar.y + bar.height)
                self.add_child(bar)
                self.bars[tarea] = bar

                #bar per área
                #g.rectangle(cur_x, 102 + self.lineas.index(fact.area) * 6, pixel_width, 6)
                #number of empleados simultáneos en líneas
                g.rectangle(cur_x, self.height - 3 * (j+1), pixel_width, 3)
        g.fill("#aaa")
        print "-" * 80

    def on_mouse_move(self, scene, event):
        active_bar = None
        # find if we are maybe on a bar
        current_x, current_y = event.get_coords()
        for tarea in self.bars:
            bar = self.bars[tarea]
            if ((bar.x < current_x < bar.x + bar.width) 
                and (bar.y < current_y < bar.y + bar.height)):
                active_bar = bar
                break
        if active_bar:
            self.set_tooltip_text(str(active_bar.tarea))
        else:
            # self.set_tooltip_text("")
            self.set_tooltip_text(str(event.get_coords()))
        self.redraw()


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

