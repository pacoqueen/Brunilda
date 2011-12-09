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
    def __init__(self, data = [], zoom_level = None, first_day = None):
        self.zoom_level = zoom_level
        self.first_day = first_day
        graphics.Scene.__init__(self)
        self.width = 500
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
        if self.data:
            self.start_date = self.data[0].ini.date()
            self.end_date = (self.data[-1].fin + dt.timedelta(2)).date()
            if self.first_day:  # Valores de 0 a end_date en días.
                self.start_date += dt.timedelta(days = self.first_day)
            if self.zoom_level: 
                self.end_date = self.start_date + dt.timedelta(
                                                    days = self.zoom_level)
            # Supongamos que un día de trabajo empieza a las 6:00 y acaba a las 
            # 6:00 del día siguiente. Contamos las horas del turno completo en 
            # el día en el que empieza, da igual que acabe más tarde del inicio 
            # del día laboral siguiente. 
            self.start_datetime = dt.datetime(year = self.start_date.year, 
                                              month = self.start_date.month, 
                                              day = self.start_date.day) 
            self.start_datetime += dt.timedelta(6 / 24.0)
            self.end_datetime = dt.datetime(year = self.end_date.year, 
                                            month = self.end_date.month, 
                                            day = self.end_date.day) 
            self.end_datetime += dt.timedelta(6 / 24.0)
        else:
            self.start_date = self.end_date = self.start_datetime \
                = self.end_datetime = None
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def clrscr(self):
        self.clear()
        self.grid = []

    def create_label_total(self, empleado, alto_label, alto_bar):
        """
        Crea la etiqueta que mostrará las horas asignadas al empleado dentro 
        del rango representado (que es un subconjunto del self.data).
        """
        tareas_empleado_rango = [t for t in self.data if
            t.empleado == empleado 
            and t.fecha >= self.start_datetime
            and t.fecha <= self.end_datetime]
        total = empleado.calcular_horas_asignadas(tareas_empleado_rango)
        txttotal = str(int(total))
        label_total = graphics.Label(txttotal, alto_label, "#333", 
                                visible = True)
        self.labels["totales"][empleado] = label_total
        # Para label_total.x tengo que esperar a medir el offset_totales.
        label_total.y = 27 + self.empleados.index(empleado) * alto_bar
        self.add_child(label_total)
        ancho_label_total = label_total.measure(txttotal)[0]
        return ancho_label_total

    def create_label_empleado(self, empleado, alto_label, alto_bar, 
                              offset_totales):
        """
        Crea y coloca tanto el label del empleado como la línea horizontal.
        """
        nombre = empleado.nombre
        lnombre = graphics.Label(nombre, alto_label, "#333", visible = True)
        self.labels["empleados"][empleado] = lnombre
        lnombre.x = 0
        lnombre.y = 27 + self.empleados.index(empleado) * alto_bar
        self.add_child(lnombre)
        hline = graphics.Rectangle(self.width +  offset_totales, 1, 
                                   fill = "#000")
        hline.x = 0
        hline.y = lnombre.y
        self.grid.append(hline)
        self.add_child(hline)
        ancho_label_nombre = lnombre.measure(nombre)[0]
        return ancho_label_nombre

    def create_vlines(self, full_days, x, fecha):
        """Líneas de días.""" 
        if len(full_days) <= 7: # Si muestro una semana, las pongo todas.
            self.pintar_linea_vertical(x, 
                                       label = self.build_label_fecha(fecha))
        elif 7 < len(full_days) <= 31:  # Si un mes, todas. Lunes completo.
            if fecha.weekday() == 0:
                self.pintar_linea_vertical(x, altura = self.height, 
                    label = self.build_label_fecha(fecha))
            else:
                self.pintar_linea_vertical(x, altura = self.height - 27)
        elif 31 < len(full_days) < 31 * 4: # Tres meses. Lunes completo.
            if fecha.weekday() == 0: 
                self.pintar_linea_vertical(x, altura = self.height, 
                    label = self.build_label_fecha(fecha))
            elif fecha.weekday() == 5:  # Y línea los viernes.
                self.pintar_linea_vertical(x, altura = self.height - 27)
        elif 93 < len(full_days) < 31 * 7: # Más de un trimestre. 
            if fecha.day == 1:    # Solo primeros de mes completos.
                self.pintar_linea_vertical(x, altura = self.height, 
                    label = self.build_label_fecha(fecha))
            elif fecha.day == 15: # Y raya cada quince días.
                self.pintar_linea_vertical(x, altura = self.height - 27)
        else:   # Más de seis meses, solo separo y pongo nobres de meses.
            if fecha.day == 1:
                self.pintar_linea_vertical(x, altura = self.height, 
                    label = self.build_label_fecha(fecha, solo_mes = True))
        if len(full_days) <= 3: # Además de las líneas del día, pinto horas
            for hora in range(0, 25, 2):
                if hora in (6, 14, 22):
                    labelhora = "<small>%02d:00</small>" % (
                        hora < 24 and hora or 0)
                else:
                    labelhora = None
                self.pintar_linea_vertical(x + hora * self.hour_pixel, 
                                           altura = self.height - 27, 
                                           label = labelhora, 
                                           label_center = True)

    def create_bar(self, tarea, alto_bar, cur_x, j):
        # bar per empleado
        duracion_tarea_segundos = tarea.duracion.days * 24 * 60 * 60
        duracion_tarea_segundos += tarea.duracion.seconds
        duracion_tarea_horas = duracion_tarea_segundos / 60 / 60
        bar_ancho = self.hour_pixel * duracion_tarea_horas
        bar = graphics.Rectangle(bar_ancho, alto_bar, 
                fill = color_por_area(tarea.area, self.lineas), 
                stroke = "#aaa")
        # cur_x está siempre en las 00:00. Avanzo hasta la hora de 
        # inicio real. 
        bar.x = cur_x + (tarea.fecha.hour * self.hour_pixel)
        bar.y = 27 + self.empleados.index(tarea.empleado) * alto_bar 
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

    def create_portion_carga_linea(self, cur_x, numtarea_del_dia, pixel_width):
        """
        Dibuja un rectángulo que representa la porción de barra vertical del 
        número de empleados trabajando en una línea (área) simultáneamente el 
        mismo día (no necesariamente en el mismo turno).
        Todas las porciones, que se dibujan justo después de la barra de la 
        tarea de cada empleado, al apilarse forman la barra vertical total.
        """
        # number of empleados simultáneos en líneas
        #g.rectangle(cur_x, self.height - 5 * (numtarea_del_dia+1), pixel_width, 
        #            10)
        alto = 10
        portion = graphics.Rectangle(pixel_width, alto, fill = "#ad0")
        portion.x = cur_x
        portion.y = self.height - 5 * (numtarea_del_dia + 1)
        self.add_child(portion)

    def on_enter_frame(self, scene, context):
        if not self.data:
            return
        g = graphics.Graphics(context)
        g.set_line_style(width=1)
        days = (self.end_date - self.start_date).days
        full_days = []
        self.clrscr()
        alto_bar = 15
        alto_label = 8
        anchos_empleados = []
        anchos_totales = []
        for empleado in self.empleados:
            # Totales. Necesito duplicar el bucle porque el ancho de los 
            # totales me hará falta después para las líneas horizontales.
            ancho_label_total = self.create_label_total(empleado, alto_label, 
                                                        alto_bar)
            anchos_totales.append(ancho_label_total)
        offset_totales = max(anchos_totales) + 5    # Por la derecha.
        for empleado in self.empleados:
            ancho_label_nombre = self.create_label_empleado(empleado, 
                                                            alto_label, 
                                                            alto_bar, 
                                                            offset_totales)
            anchos_empleados.append(ancho_label_nombre)
        if self.empleados:  # Una línea más debajo del último empleado
            hline = graphics.Rectangle(self.width + offset_totales, 1, 
                                       fill = "#000")
            hline.x = 0
            hline.y = 27 + len(self.empleados) * alto_bar
            self.grid.append(hline)
            self.add_child(hline)
        offset_labels = max(anchos_empleados) + 5 # píxeles. Pero reales, no 
            # los píxeles de la escena (day_pixel & co.), que no van 1:1. 
        lanno = graphics.Label(`self.start_date.year`, 16, "#999", visible = True)
        lanno.y = 0
        lanno.x = offset_labels - lanno.measure(`self.start_date.year`)[0]
        self.add_child(lanno)
        # Cuento el número de barras que tendré que dibujar cada día:
        for day in range(days):
            current_date = self.start_date + dt.timedelta(days = day)
            #if not self.day_counts[current_date]:
            #    continue   # "Comprime" la gráfica ignorando días vacíos.
            full_days.append(self.day_counts[current_date])
        # Y ahora calculo las dimensiones en función de los días a representar.
        # El +1 es porque al haber tantos datos representados, la división 
        # sale a veces (las más) un poco al alza, provocando que las barras 
        # vayan más allá del borde del canvas. 
        self.day_pixel = (float(self.width 
                           - offset_labels 
                           - offset_totales) / (len(full_days) + 1))
        self.hour_pixel = self.day_pixel / 24 
        cur_x = offset_labels
        pixel_width = max(round(self.day_pixel), 1)
        dia = self.start_date
        for lista_tareas_day in full_days:
            #cur_x += round(self.hour_pixel)
            #print "lista_tareas_day", lista_tareas_day
            for numtarea_del_dia, tarea in enumerate(lista_tareas_day):
                self.create_bar(tarea, alto_bar, cur_x, 
                                numtarea_del_dia)
                self.create_portion_carga_linea(cur_x, numtarea_del_dia, 
                                                pixel_width)
            self.create_vlines(full_days, cur_x, dia)
            dia += dt.timedelta(days = 1)
            cur_x += round(pixel_width)
        # Una vez que está todo "pintado", es hora de ajustar bien el ancho y 
        # calcular la x donde se renderizarán los totales:
        for empleado in self.labels['totales']:
            ltotal = self.labels['totales'][empleado]
            ltotal.x = self.width - offset_totales
        if DEBUG:
            print "-" * 80

    def build_label_fecha(self, d, solo_mes = False):
        """
        Devuelve una cadena con el nombre y fecha del día «d».
        """
        if not solo_mes:
            label = d.strftime("%d <small><sup>%b</sup></small>")
        else:
            label = d.strftime("%b")
        return label

    def pintar_linea_vertical(self, cur_x, altura = None, label = None, 
                              label_center = False):
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
            if not label_center:
                ldia.x = cur_x + 2
                ldia.y = 3
            else:
                ldia.x = cur_x - (ldia.measure(label)[0] / 2)
                ldia.y = 13

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


def color_por_area(area, areas):
    """
    Devuelve un color único por cada línea.
    """
    indice = areas.index(area)
    colores = ["#339", "#77a", "#66b", "#55c", "#44d", 
               "#22e", "#88f", "#8ad", "#8ae", "#8af"]
    color = colores[indice % len(colores)]
    return color


