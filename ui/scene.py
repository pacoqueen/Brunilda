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
        self.empleados.sort(key = lambda e: e.nombre)
        self.bars = {}
        self.labels = {"empleados": {}, 
                       "totales": {}, 
                       "días": {}}
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
        offset_totales = 25 # píxeles por la derecha, para los totales.
        for day in range(days):
            current_date = start_date + dt.timedelta(days = day)
            #if not self.day_counts[current_date]:
            #    continue   # "Comprime" la gráfica ignorando días vacíos.
            full_days.append(self.day_counts[current_date])
        self.clrscr()
        day_pixel = float(self.width - offset_labels) / len(full_days)
        hour_pixel = day_pixel / 24 
        cur_x = offset_labels
        pixel_width = max(round(day_pixel), 1)
        #pixel_width = max(round(hour_pixel), 1)
        bar_alto = 15
        alto_label = 8
        for empleado in self.empleados:
            # FIXME: Esto debería ir en una función aparte. REFACTORIZAR.
            nombre = empleado.nombre
            lnombre = graphics.Label(nombre, alto_label, "#333", visible = True)
            self.labels["empleados"][empleado] = lnombre
            lnombre.x = 0
            lnombre.y = 27 + self.empleados.index(empleado) * bar_alto
            self.add_child(lnombre)
            hline = graphics.Rectangle(self.width +  offset_totales, 1, 
                                       fill = "#000")
            hline.x = 0
            hline.y = lnombre.y
            self.grid.append(hline)
            self.add_child(hline)
            # Totales
            total = empleado.calcular_horas_asignadas(
                        [t for t in self.data if t.empleado == empleado])
            ltotal = graphics.Label(str(int(total)), alto_label, "#333", 
                                    visible = True)
            self.labels["totales"][empleado] = ltotal
            ltotal.x = self.width - offset_totales
            ltotal.y = lnombre.y
            self.add_child(ltotal)
        if self.empleados:  # Una línea más debajo del último empleado
            hline = graphics.Rectangle(self.width + offset_totales, 1, 
                                       fill = "#000")
            hline.x = 0
            hline.y = 27 + len(self.empleados) * bar_alto
            self.grid.append(hline)
            self.add_child(hline)
        dia = start_date
        for lista_tareas_day in full_days:
            cur_x += round(day_pixel)
            #cur_x += round(hour_pixel)
            #print "lista_tareas_day", lista_tareas_day
            # Líneas de días. 
            if len(full_days) <= 7: # Si muestro una semana, las pongo todas.
                self.pintar_linea_vertical(cur_x, 
                                           label = self.build_label_fecha(dia))
            elif 7 < len(full_days) <= 31:  # Si un mes, todas. Lunes completo.
                if dia.weekday() == 0:
                    self.pintar_linea_vertical(cur_x, altura = self.height, 
                        label = self.build_label_fecha(dia))
                else:
                    self.pintar_linea_vertical(cur_x, altura = self.height - 27)
            elif 31 < len(full_days) <= 93: # Tres meses. Lunes completo.
                if dia.weekday() == 0: 
                    self.pintar_linea_vertical(cur_x, altura = self.height, 
                        label = self.build_label_fecha(dia))
                elif dia.weekday() == 5:  # Y línea los viernes.
                    self.pintar_linea_vertical(cur_x, altura = self.height - 27)
            else:   # Más de un mes. Solo primeros de mes completos.
                if dia.day == 1:
                    self.pintar_linea_vertical(cur_x, altura = self.height, 
                        label = self.build_label_fecha(dia))
                elif dia.weekday() == 0:  # Y raya cada lunes.
                    self.pintar_linea_vertical(cru_x, alto = self.height - 27)
            for j, tarea in enumerate(lista_tareas_day):
                #bar per empleado
                duracion_tarea_segundos = tarea.duracion.days * 24 * 60 * 60
                duracion_tarea_segundos += tarea.duracion.seconds
                duracion_tarea_horas = duracion_tarea_segundos / 60 / 60
                bar_ancho = hour_pixel * duracion_tarea_horas
                bar = graphics.Rectangle(bar_ancho, bar_alto, 
                        fill = color_por_area(tarea.area, self.lineas), 
                        stroke = "#aaa")
                # cur_x está siempre en las 00:00. Avanzo hasta la hora de 
                # inicio real. 
                bar.x = cur_x + (tarea.fecha.hour * hour_pixel)
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
                g.rectangle(cur_x, self.height - 5 * (j+1), day_pixel, 10)
            dia += dt.timedelta(days = 1)
        g.fill("#ad0")
        if DEBUG:
            print "-" * 80

    def build_label_fecha(self, d):
        """
        Devuelve una cadena con el nombre y fecha del día «d».
        """
        return d.strftime("%d <small><sup>%b</sup></small>")

    def pintar_linea_vertical(self, cur_x, altura = None, label = None):
        if altura is None:
            altura = self.height
        vline = graphics.Rectangle(1, altura, fill= "#000")
        vline.x = cur_x
        vline.y = self.height - altura
        self.grid.append(vline)
        self.add_child(vline)
        if label:   # Añado arriba del todo una etiqueta con el texto recibido.
            ldia = graphics.Label(label, 10, "#999", visible = True)
            self.labels["días"][label] = ldia
            self.add_child(ldia)
            ldia.x = cur_x + 1
            ldia.y = 8

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
        window.set_size_request(800, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


def color_por_area(area, areas):
    """
    Devuelve un color único por cada línea.
    """
    indice = areas.index(area)
    #componentes = "0123456789abcdef"
    colores = ["#339", "#77a", "#66b", "#55c", "#44d", 
               "#22e", "#88f", "#8ad", "#8ae", "#8af"]
    color = colores[indice % len(colores)]
    return color


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

