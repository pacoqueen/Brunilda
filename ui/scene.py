#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
# Modified by (C) 2011 Francisco José Rodríguez Bogado <bogado@qinn.es>

"""
Gráfico de segmentos horizontales.
"""

DEBUG = False

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
            # Si continúa en el día siguiente, se dibuja en dos trozos.
            #if tarea.fin and tarea.ini.date() != tarea.fin.date():
            #    self.day_counts[tarea.fin.date()].append(tarea)
        self.lineas = [area[0] for area in sorted(lineas.items(), 
                                                  key=lambda item:item[1], 
                                                  reverse=True)]
        self.empleados = empleados.keys()
        self.bars = {}
        self.labels = {"empleados": {}, 
                       "totales": {}}
        self.grid = []
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def clrscr(self):
        for tarea in self.bars:
            bar = self.bars[tarea]
            try:
                self.remove_child(bar)
            except ValueError:
                pass    # Todavía no
        for tipolabel in self.labels:
            for empleado in self.labels[tipolabel]:
                try:
                    label = self.labels[tipolabel][empleado]
                except KeyError:
                    continue
                try:
                    self.remove_child(label)
                except ValueError:  # Todavía no
                    pass
        for line in self.grid:
            try:
                self.remove_child(line)
            except ValueError:
                pass
        self.grid = []

    def on_enter_frame(self, scene, context):
        if not self.data:
            return
        g = graphics.Graphics(context)
        g.set_line_style(width=1)
        start_date = self.data[0].ini.date()
        end_date = (self.data[-1].fin + dt.timedelta(2)).date()
        days = (end_date - start_date).days
        full_days = []
        offset_labels = 75  # píxeles. Pero reales, no los píxeles de la 
            # escena, que no van 1:1. Creo que es suficiente para los nombres.
        for day in range(days):
            current_date = start_date + dt.timedelta(days = day)
            #if not self.day_counts[current_date]:
            #    continue   # "Comprime" la gráfica ignorando días vacíos.
            full_days.append(self.day_counts[current_date])
        self.clrscr()
        day_pixel = float(self.width - offset_labels) / len(full_days)
        hour_pixel = day_pixel / 24 * 2 # Cada dos horas me interesa.
        cur_x = offset_labels
        pixel_width = max(round(day_pixel), 1)
        #pixel_width = max(round(hour_pixel), 1)
        bar_alto = 15
        bar_ancho = pixel_width 
        alto_label = 8
        for empleado in self.empleados:
            # FIXME: Esto debería ir en una función aparte. REFACTORIZAR.
            nombre = empleado.nombre
            lnombre = graphics.Label(nombre, alto_label, "#333", visible = True)
            self.labels["empleados"][empleado] = lnombre
            lnombre.x = 0
            lnombre.y = 27 + self.empleados.index(empleado) * bar_alto
            self.add_child(lnombre)
            hline = graphics.Rectangle(self.width, 1, fill = "#000")
            hline.x = 0
            hline.y = lnombre.y
            self.grid.append(hline)
            self.add_child(hline)
        if self.empleados:  # Una línea más debajo del último empleado
            hline = graphics.Rectangle(self.width, 1, fill = "#000")
            hline.x = 0
            hline.y = 27 + len(self.empleados) * bar_alto
            self.grid.append(hline)
            self.add_child(hline)
        for lista_tareas_day in full_days:
            cur_x += round(day_pixel)
            #cur_x += round(hour_pixel)
            #print "lista_tareas_day", lista_tareas_day
            vline = graphics.Rectangle(1, self.height, fill= "#000")
            vline.x = cur_x
            vline.y = 0
            self.grid.append(vline)
            self.add_child(vline)
            for j, tarea in enumerate(lista_tareas_day):
                #bar per empleado
                #g.rectangle(cur_x, 27 + self.empleados.index(fact.empleado) * 6, pixel_width, 6)
                bar = graphics.Rectangle(bar_ancho, bar_alto, 
                        fill = color_por_area(tarea.area, self.lineas), 
                        stroke = "#aaa")
                bar.x = cur_x
                bar.y = 27 + self.empleados.index(tarea.empleado) * bar_alto 
                bar.tarea = tarea
                if tarea.empleado in self.empleados:
                    bar.empleado = self.empleados.index(tarea.empleado)
                else:
                    bar.empleado = len(self.empleados)
                if DEBUG:
                    print j, tarea, "(%d, %d) - (%d, %d)" % (
                        bar.x, bar.y, bar.x + bar.width, bar.y + bar.height)
                self.add_child(bar)
                self.bars[tarea] = bar

                #bar per área
                #g.rectangle(cur_x, 102 + self.lineas.index(fact.area) * 6, pixel_width, 6)
                #number of empleados simultáneos en líneas
                g.rectangle(cur_x, self.height - 10 * (j+1), pixel_width, 10)
        g.fill("#ad0")
        if DEBUG:
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
            self.set_tooltip_text("")
            #self.set_tooltip_text(str(event.get_coords()))
        self.redraw()


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


def color_por_area(area, areas):
    """
    Devuelve un color único por cada línea.
    """
    indice = areas.index(area)
    #componentes = "0123456789abcdef"
    colores = ["#000000", "#0000ff", "#00ff00", "#ff0000", "#ff00ff", 
               "#ffffff", "#008800", "#880000", "#000088", "#888888"]
    color = colores[indice % len(colores)]
    return color


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

