#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
# (Deeply) modified by (C)2011 Francisco José Rodríguez Bogado <bogado@qinn.es>

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
        self.load_data(data)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def load_data(self, data = None):
        self.day_counts = defaultdict(list)
        lineas, empleados = defaultdict(int), defaultdict(int)
        if data: # Si no recibo datos, uso los que ya tengo (o debería tener).
            self.data = data
        self.data.sort(key = lambda i: i.ini)
        for tarea in self.data:
            self.day_counts[tarea.ini.date()].append(tarea)
            lineas[tarea.area] += 1
            empleados[tarea.empleado] += 1
            # Si continúa en el día siguiente, se dibuja en dos trozos.
            #if tarea.fin and tarea.ini.date() != tarea.fin.date():
            #    self.day_counts[tarea.fin.date()].append(tarea)
        # XXX self._lineas = lineas   # Esto es para las clases derivadas.
        self.lineas = [area[0] for area in sorted(lineas.items(), 
                                                  key=lambda item:item[1], 
                                                  reverse=True)]
        self.empleados = empleados.keys()
        self.empleados.sort(key = lambda e: e.nombre)
        self.lineas.sort(key = lambda a: a.nombre)
        self.bars = {}
        self.coords_y = {}  # coordenadas y de cada empleado/línea
        self.coords_dias = {}       # coordenadas x de cada día
        self.labels = {"empleados": {}, 
                       "totales": {}, 
                       "días": {}, 
                       "lineas": {}}    # No se usa en Scene, pero SceneArea
                                        # hereda este método tal cual. 
        self.grid = []
        if self.data:
            self.start_date = self.data[0].ini.date()
            self.end_date = (self.data[-1].fin + dt.timedelta(2)).date()
            if self.first_day:  # Valores de 0 a end_date en días.
                self.start_date += dt.timedelta(days = self.first_day)
            if self.zoom_level: 
                self.end_date = self.start_date + dt.timedelta(
                                                    days = self.zoom_level)
            # Supongamos que un día de trabajo empieza a las 6:00 y acaba a 
            # las 6:00 del día siguiente. Contamos las horas del turno 
            # completo en el día en el que empieza, da igual que acabe más 
            # tarde del inicio del día laboral siguiente. 
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

    def reload_data(self, new_data, event = None):
        """
        Como cargo las tareas al inicio, un simple redraw no va a refrescar 
        los datos mostrados. Hay que recargar los datos desde el backend y 
        redibujar después (el expose_event se encargará).
        """
        self.clrscr()
        self.data = new_data
        self.load_data()
        if not event:
            event = gtk.gdk.Event(gtk.gdk.EXPOSE)
        self.emit("expose-event", event)

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
            and t.fecha < self.end_datetime]
        tareas_empleado = [t for t in self.data if t.empleado == empleado]
        total = empleado.calcular_horas_asignadas(tareas_empleado_rango)
        total_totaloso = empleado.calcular_horas_asignadas(tareas_empleado)
        txttotal = "%d (%d)" % (int(total), int(total_totaloso))
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
        self.coords_y[lnombre.y] = empleado
        return ancho_label_nombre

    def create_vlines(self, full_days, x, fecha):
        """Líneas de días.""" 
        # Se invoca cada día, pero solo pinta cuando corresponde.
        self.coords_dias[x] = fecha
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
        alto = 10
        portion = graphics.Rectangle(pixel_width, alto, fill = "#ad0")
        portion.x = cur_x
        portion.y = self.height - 5 * (numtarea_del_dia + 1)
        self.add_child(portion)

    def on_enter_frame(self, scene, context):
        if not self.data:
            return
        self.context = context  # XXX
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
        lanno = graphics.Label(`self.start_date.year`, 16, "#999")
        offset_labels = max(offset_labels, 
                            lanno.measure(`self.start_date.year`)[0])
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
        # find if we are maybe on a bar
        active_bar = self.get_active_bar(*event.get_coords())
        if active_bar:
            self.set_tooltip_text(str(active_bar.tarea))
            #self.pintar_flechas_movimiento(active_bar)
        else:
            self.set_tooltip_text("")
            #try:
            #    self.borrar_flechas_movimiento()
            #except (AttributeError, NameError, ValueError): 
            #    # Unbound. No hay ninguna pintada.
            #    pass
            #self.set_tooltip_text(str(event.get_coords()))
        self.redraw()

    def pintar_flechas_movimiento(self, bar):
        return  # ¡Esto NO FUNCIONA Y NO SÉ POR QUÉ!
        izq = int(bar.x)
        der = izq + bar.width
        inf = int(bar.y)
        sup = inf + bar.height
        if bar.width > 10:
            i = graphics.Polygon(((izq, inf + ((sup - inf) / 2)), 
                                  (izq + 5, sup), 
                                  (izq + 5, inf)), 
                                 fill = "#000", stroke = "#FFF")
            d = graphics.Polygon(((der, inf + ((sup - inf) / 2)), 
                                  (der - 5, sup), 
                                  (der - 5, inf)), 
                                 fill = "#000", stroke = "#FFF")
            self.add_child(i)
            self.add_child(d)
            i.bring_to_front()
            d.bring_to_front()
            self.flechas = i, d
            i._draw(self.context)

    def borrar_flechas_movimiento(self):
        self.remove_child(self.flechas[0])
        self.remove_child(self.flechas[1])
        self.flechas = (None, None)

    def get_actives_bars(self, current_x, current_y):
        """
        Devuelve las barras de tareas que se encuentren bajo el cursor o la 
        lista vacía si el puntero está en una zona vacía.
        """
        actives_bars = []
        for tarea in self.bars:
            bar = self.bars[tarea]
            if ((bar.x < current_x < bar.x + bar.width) 
                and (bar.y < current_y < bar.y + bar.height)):
                actives_bars.append(bar)
        return actives_bars

    def get_active_bar(self, current_x, current_y):
        """
        Devuelve la tarea de la barra que esté bajo el cursor o None si está 
        en un área vacía.
        """
        #try:
        #    return self.get_actives_bars()[0]
        #except IndexError:
        #    return None
        # Optimización:
        active_bar = None
        for tarea in self.bars:
            bar = self.bars[tarea]
            if ((bar.x < current_x < bar.x + bar.width) 
                and (bar.y < current_y < bar.y + bar.height)):
                active_bar = bar
                break
        return active_bar

    def get_actives_tareas(self, x, y):
        """
        Devuelve una lista con las tareas de las barras bajo el cursor.
        """
        tareas = [b.tarea for b in self.get_actives_bars(x, y)]
        return tareas

    def get_active_tarea(self, x, y):
        """
        Devuelve la tarea activa. Si hay varias barras superpuestas en la 
        misma posición bajo el cursor, solo devuelve la tarea de la primera 
        de ellas.
        """
        return self.get_active_bar(x, y).tarea

    def get_anno_activo(self):
        """
        Siempre devuelve el año mostrado arriba a la izquierda, que es el año 
        del primer día de la gráfica.
        """
        return self.start_date.year

    def get_mes_activo(self, x = None, y = None):
        mes = self.start_date 
        if x:
            mes = self.get_active_day(x)
        return mes

    def get_dia_activo(self, x = None, y = None):
        dia = self.start_date
        if x:
            dia = self.get_active_day(x)
        return dia

    def get_active_empleado_or_linea(self, x, y = None):
        """
        Devuelve el empleado (o línea si estamos en la vista por línea) al 
        que corresponde la coordenada «y».
        """
        if y is None:
            y = x   # No ha mandado (x, y). Solo la y en el primer argumento.
        ys = self.coords_y.keys()
        ys.sort()
        try:
            empleado = self.coords_y[ys[0]]
        except (KeyError, IndexError):
            empleado = None     # No data?
        for yy in ys:
            if yy >= y:
                return empleado
            empleado = self.coords_y[yy]
        return empleado # Es el último, entonces.

    def get_active_day(self, x, y = None):
        """
        Devuelve el día al que corresponde la coordenada «x».
        """
        xs = self.coords_dias.keys()
        xs.sort()
        dia = None
        for xx in xs:
            if xx >= x:
                return dia
            dia = self.coords_dias[xx]
        return dia


def color_por_area(area, areas):
    """
    Devuelve un color único por cada línea.
    """
    # TODO: Único, lo que se dice único... como haya más áreas que 
    # colores harcoded, lo llevas claro.
    indice = sorted(areas).index(area)
    colores = ["#339", "#77a", "#66b", "#55c", "#44d", 
               "#22e", "#88f", "#8ad", "#8ae", "#8af"]
    color = colores[indice % len(colores)]
    return color

def color_tarea(tarea, z):
    """
    Devuelve siempre el mismo color para la misma duración de la tarea, 
    pero con "alpha"[*]. Así, el color se oscurece gradualmente cuantos 
    más operarios hay trabajando en la misma línea a la misma hora. 
    Además, permite también diferenciar a simple vista si algunos de ellos 
    tienen un turno más largo que los demás.
    [*] Como parece que no sé manejar el alpha en Cairo, hago un remedo: 
        cuanto más alta es la z, más alta en la lista de capas está la tarea y 
        más oscuro hago el color (porque se supone que se superpone al color 
        de la tarea inferior).
    """
    # z me va a servir para ver la "profundidad" de la tarea. La más baja es 
    # z = 1, la siguiente z = 2 y así sucesivamente.
    zcolor = hex(0xf - ((z-1) * 2)).split("x")[1]
    if tarea.horas <= 8:
        color = "#%s700" % zcolor
    else:
        color = "#%s000" % zcolor
    return color

class ScenePorArea(Scene):
    """
    «data» son tareas con un empleado, un área, una hora de inicio y una 
    duración.
    """
    def __init__(self, *args, **kw):
        Scene.__init__(self, *args, **kw)
        self.labels = {"lineas": {}, 
                       "totales": {}, 
                       "días": {}}
        # XXX self.lineas = sorted(self._lineas.keys())

    def reload_data(self, *args, **kw):
        Scene.reload_data(self, *args, **kw)
        self.labels.pop("empleados")
        self.labels["lineas"] = {} 

    def create_label_total(self, area, alto_label, alto_bar):
        """
        Crea la etiqueta que mostrará las horas asignadas al la línea dentro 
        del rango representado (que es un subconjunto del self.data).
        """
        tareas_area_rango = [t for t in self.data if
            t.area == area 
            and t.fecha >= self.start_datetime
            and t.fecha < self.end_datetime]
        total = area.calcular_horas_asignadas(tareas_area_rango)
        txttotal = str(int(total))
        label_total = graphics.Label(txttotal, alto_label, "#333", 
                                visible = True)
        self.labels["totales"][area] = label_total
        # Para label_total.x tengo que esperar a medir el offset_totales.
        label_total.y = 27 + self.lineas.index(area) * alto_bar
        self.add_child(label_total)
        ancho_label_total = label_total.measure(txttotal)[0]
        return ancho_label_total

    def create_label_area(self, area, alto_label, alto_bar, 
                              offset_totales):
        """
        Crea y coloca tanto el label del area como la línea horizontal.
        """
        nombre = area.nombre or ""
        lnombre = graphics.Label(nombre, alto_label, "#333", visible = True)
        self.labels["lineas"][area] = lnombre
        lnombre.x = 0
        lnombre.y = 27 + self.lineas.index(area) * alto_bar
        self.add_child(lnombre)
        hline = graphics.Rectangle(self.width +  offset_totales, 1, 
                                   fill = "#000")
        hline.x = 0
        hline.y = lnombre.y
        self.grid.append(hline)
        self.add_child(hline)
        ancho_label_nombre = lnombre.measure(nombre)[0]
        self.coords_y[lnombre.y] = area
        return ancho_label_nombre

    def create_bar(self, tarea, alto_bar, cur_x, j):
        # bar per area
        duracion_tarea_segundos = tarea.duracion.days * 24 * 60 * 60
        duracion_tarea_segundos += tarea.duracion.seconds
        duracion_tarea_horas = duracion_tarea_segundos / 60 / 60
        bar_ancho = self.hour_pixel * duracion_tarea_horas
        bar = graphics.Rectangle(bar_ancho, alto_bar, 
                fill = color_tarea(tarea, j), 
                stroke = "#FFEFEF00", #FIXME:El alpha pasa completamente de mí
                line_width = max(0, 4 - int(self.zoom_level / 31)), 
                corner_radius = 10)
        # cur_x está siempre en las 00:00. Avanzo hasta la hora de 
        # inicio real. 
        bar.x = cur_x + (tarea.fecha.hour * self.hour_pixel)
        bar.y = 27 + self.lineas.index(tarea.area) * alto_bar 
        bar.tarea = tarea
        if tarea.area in self.lineas:
            bar.area = self.lineas.index(tarea.area)
        else:
            bar.area = len(self.lineas)
        if DEBUG:
            print j, tarea, "(%d, %d) - (%d, %d)" % (
                bar.x, bar.y, bar.x + bar.width, bar.y + bar.height)
        self.add_child(bar)
        self.bars[tarea] = bar

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
        anchos_areas = []
        anchos_totales = []
        for area in self.lineas:
            # Totales. Necesito duplicar el bucle porque el ancho de los 
            # totales me hará falta después para las líneas horizontales.
            ancho_label_total = self.create_label_total(area, alto_label, 
                                                        alto_bar)
            anchos_totales.append(ancho_label_total)
        offset_totales = max(anchos_totales) + 5    # Por la derecha.
        for area in self.lineas:
            ancho_label_nombre = self.create_label_area(area, 
                                                        alto_label, 
                                                        alto_bar, 
                                                        offset_totales)
            anchos_areas.append(ancho_label_nombre)
        if self.lineas:  # Una línea más debajo del último area
            hline = graphics.Rectangle(self.width + offset_totales, 1, 
                                       fill = "#000")
            hline.x = 0
            hline.y = 27 + len(self.lineas) * alto_bar
            self.grid.append(hline)
            self.add_child(hline)
        offset_labels = max(anchos_areas) + 5 # píxeles. Pero reales, no 
            # los píxeles de la escena (day_pixel & co.), que no van 1:1. 
        lanno = graphics.Label(`self.start_date.year`, 16, "#999")
        offset_labels = max(offset_labels, 
                            lanno.measure(`self.start_date.year`)[0])
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
            self.create_vlines(full_days, cur_x, dia)
            # "Pinto" de la más larga a la más corta para distinguir cómo se 
            # superponen.
            zbuffer = calculate_zbuffer(lista_tareas_day)
            for numtarea_del_dia, tarea in enumerate(lista_tareas_day):
                self.create_bar(tarea, alto_bar, cur_x, zbuffer[tarea]) 
                self.create_portion_carga_linea(cur_x, numtarea_del_dia, 
                                                pixel_width)
            dia += dt.timedelta(days = 1)
            cur_x += round(pixel_width)
        # Una vez que está todo "pintado", es hora de ajustar bien el ancho y 
        # calcular la x donde se renderizarán los totales:
        for area in self.labels['totales']:
            ltotal = self.labels['totales'][area]
            ltotal.x = self.width - offset_totales
        if DEBUG:
            print "-" * 80

    def on_mouse_move(self, scene, event):
        # find if we are maybe on a bar(s)
        current_x, current_y = event.get_coords()
        actives_bars = self.get_actives_bars(current_x, current_y)
        if actives_bars:
            self.set_tooltip_text("\n".join(
                [str(a.tarea) for a in actives_bars]))
        else:
            self.set_tooltip_text("")
            #self.set_tooltip_text(str(event.get_coords()))
        self.redraw()


def calculate_zbuffer(ts):
    """
    En realidad devuelve el número de tareas que coinciden a la misma hora 
    en el mismo área.
    Las que se pisen de diferente duración no hay manera de que se coloreen 
    sin implementar un canal alfa real, porque no en todos los casos 
    una tarea más corta queda completamente superpuesta a una más larga. En 
    determinados casos la más corta termina después de la más larga, y ahí 
    una parte de la tarea corta sería de un color y otra de otra.
    """
    # John Carmack, no sabes cuánto te odio. Primero por tener un nombre tan 
    # jodidamente chanante. Y segundo por hacer magia con tu z-buffer y tan 
    # pocos recursos mientas que yo, con gigas de RAM y un lenguaje de alto 
    # nivel... ya ves la mierda que todavía ni he podido terminar.
    z = dict(zip(ts, (1, ) * len(ts)))
    # Dentro de cada área, organizo las tareas por hora de inicio.
    por_area = {}
    for t in ts:
        area = t.area
        ini = t.ini
        if area not in por_area:
            por_area[area] = defaultdict(lambda: 0)
        por_area[area][ini] += 1
    for t in ts:
        z[t] = por_area[t.area][t.ini]
    return z

