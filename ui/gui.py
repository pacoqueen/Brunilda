#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk, gtk, pango
from .scene import Scene, ScenePorArea
import datetime
import storage

class Ventana:
    def __init__(self, tareas):
        """
        days es el número de días totales que se pueden representar. Los que 
        actualmente se muestren depende del zoom aplicado.
        tareas es el conjunto de datos *inicial* a ser mostrado. El valor en 
        cada momento (self.tareas) puede ser diferente en función de las 
        operaciones con el backend.
        """
        self.ventana = gtk.Window()
        self.ventana.set_size_request(800, 400)
        self.ventana.connect("delete_event", lambda *a, **kw: gtk.main_quit())
        self.ventana.connect("destroy", lambda *a, **kw: gtk.main_quit())
        self.container = gtk.VBox()
        self.grafica = gtk.HBox()
        self.container.pack_start(self.grafica)
        self.container.set_property("border-width", 5)
        self.controls = gtk.VBox()
        self.lower_controls = gtk.HBox()
        self.lower_controls.set_property("homogeneous", True)
        self.lower_controls.set_property("spacing", 10)
        self.b_salir = gtk.Button(stock = gtk.STOCK_QUIT)
        self.b_salir.connect("clicked", self.__salir)
        self.lower_controls.add(self.b_salir)
        # El valor más alto que se puede obtener es upper - page_size 
        self.zoom = gtk.Adjustment(62.0, 1.0, 365.0 + 31.0, 1.0, 31.0, 31.0)
        self.zoom_level = 62
        self.slider = gtk.HScale(self.zoom)
        self.slider.set_digits(0)
        self.slider.get_layout().set_font_description(
            pango.FontDescription("monospace 8"))
        for i in range(31, 365, 31):
            self.slider.add_mark(i, gtk.POS_TOP, None)
        self.lower_controls.add(self.slider)
        self.slider.connect("value-changed", self._update_zoom)
        days = (max(tareas, key = lambda t: t.fin).fin  
                - min(tareas, key = lambda t: t.ini).ini).days
        self.scrollbar = gtk.HScrollbar()
        self.adj_scroll = gtk.Adjustment(0, 0, days + 10, 1, 10, 10)
        self.scrollbar.set_adjustment(self.adj_scroll)
        self.controls.pack_start(self.scrollbar, expand = False)
        self.first_day = 0
        self.adj_scroll.connect("value-changed", self._update_first_day)
        self.b_vista = gtk.ToggleButton("Ver por línea")
        self.b_vista.connect("toggled", self._cambiar_vista)
        self.lower_controls.pack_end(self.b_vista, expand = False)
        self.controls.pack_start(self.lower_controls, expand = False)
        self.container.pack_start(self.controls, expand = False)
        self.ventana.add(self.container)
        self.ventana.set_title("Vista por empleado")
        self.vista_por_empleado = True
        #tareas.sort(key = lambda t: t.fecha)
        self.tareas = tareas
        self.load_escena()
        self.grafica.add(self.escena)
        self.ventana.show_all()
        # ¿Método de más de 20 líneas? ¡¿PERO ESTO QUÉ ES?!

    def _cambiar_vista(self, boton):
        self.vista_por_empleado = not boton.get_active()
        if self.vista_por_empleado:
            lvista = "Ver por empleado"
            self.ventana.set_title("Vista por empleado")
        else:
            lvista = "Ver por línea"
            self.ventana.set_title("Vista por línea")
        boton.set_label(lvista)
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()

    def _update_zoom(self, range):
        self.zoom_level = range.get_value()
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()

    def _update_first_day(self, range):
        """
        Mueve el primer día mostrado.
        """
        self.first_day = range.get_value()
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()

    def __salir(self, boton):
        self.ventana.destroy()

    def load_escena(self):
        # Premature optimization is the root of all evil. Pero más adelante tal vez debería estringir las tareas únicamente al zoom_level, para no tener que cargar todas en memoria si no las voy a mostrar.
        if self.vista_por_empleado:
            self.escena = Scene(self.tareas, self.zoom_level, self.first_day)
        else:
            self.escena = ScenePorArea(self.tareas, self.zoom_level, 
                                       self.first_day)
        self.popup_menu = self.build_popup_menu()
        # From http://faq.pygtk.org/index.py?req=show&file=faq11.002.htp
        self.popup_menu.attach_to_widget(self.escena, lambda *args, **kw: None)
        self.escena.connect("button-press-event", self._popup)

    def build_popup_menu(self):
        """
        Construye el menú contextual. Por defecto, las opciones relativas a 
        una tarea(s) en concreto están deshabilitadas. Se activarán cuando 
        se haga clic secundario en alguna de ellas (ver callback del evento).
        """
        popup_menu = gtk.Menu() 
        opciones = (("Limpiar todo", self.limpiar_todo), 
                    ("Limpiar año", self.limpiar_anno), 
                    ("Limpiar mes", self.limpiar_mes), 
                    ("Limpiar día", self.limpiar_dia), 
                    ("Borrar asignación", self.borrar_tarea), 
                    ("Borrar empleado", self.limpiar_empleado), 
                    ("Borrar línea", self.limpiar_linea), 
                    ("Asignar", self.asignar),
                   )
        self.menuitems = {}
        for o, callback in opciones:
            menuitem = gtk.MenuItem(o)
            self.menuitems[o] = menuitem
            popup_menu.add(menuitem)
            menuitem.connect("activate", callback)
        popup_menu.show_all()
        return popup_menu

    def limpiar_todo(self, item):
        # TODO: Según las HIG de gnome debería advertir antes.
        storage.delete_all()
        # Tengo que recargar los datos para ser coherente con los de la escena.
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)
        
    def limpiar_anno(self, item):
        anno = self.escena.get_anno_activo()
        storage.delete_year(anno)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def limpiar_mes(self, item):
        fecha = self.escena.get_mes_activo(self.clic_x)
        storage.delete_month(fecha.year, fecha.month)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def limpiar_dia(self, item):
        dia = self.escena.get_dia_activo(self.clic_x)
        storage.delete_day(dia.year, dia.month, dia.day)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def limpiar_empleado(self, item):
        """
        Limpia todas las tareas del empleado de la tarea bajo el cursor entre 
        las fechas mostradas en ese momento en la escena.
        Solo habilitado si estamos en vista por empleado y hay una tarea 
        bajo el cursor.
        """
        # FIXME: Limpiar un empleado implica que ya no se vuelve a mostrar
        # nunca más al no tener tareas activas. Esto es así por cómo construye 
        # la lista de empleados la clase Scene.
        # e = self.escena.get_active_tarea(self.clic_x, self.clic_y).empleado
        e = self.escena.get_active_empleado(self.clic_y)
        ini = self.escena.start_date
        fin = self.escena.end_date + datetime.timedelta(days = 1) 
        storage.limpiar_empleado(e, ini, fin)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def limpiar_linea(self, item):
        """
        Limpia todas las tareas de la línea de la tarea bajo el cursor entre 
        las fechas mostradas.
        Solo activo si estamos en vista por línea.
        """
        # a = self.escena.get_active_tarea(self.clic_x, self.clic_y).area
        a = self.escena.get_active_empleado(self.clic_y) # area, en realidad
        ini = self.escena.start_date
        fin = self.escena.end_date + datetime.timedelta(days = 1) 
        # linea = área
        storage.limpiar_linea(a, ini, fin)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)
    
    def borrar_tarea(self, item):
        tareas = self.escena.get_actives_tareas(self.clic_x, self.clic_y)
        storage.delete_tareas(tareas)
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def asignar(self, item):
        # PORASQUI: Asignar uno a uno los turnos puede ser desesperante. Hay que pensar en un "acelerador". Furthermore: si un empleado no tiene tareas actualmente, no aparece en la gráfica, por tanto es imposible asignarle nada.
        if self.vista_por_empleado:
            print "Asignar línea al empleado de la fila."
        else:
            print "Asignar empleado a la línea de la fila."

    def _popup(self, widget, event):
        self.clic_x = x = int(event.x)
        self.clic_y = y = int(event.y)
        if event.button == 3:
            tareas = self.escena.get_actives_tareas(x, y)
            # Habilito o deshabilito algunas entradas del menú según dónde 
            # haya pinchado el usuario.
            self.menuitems["Borrar asignación"].set_sensitive(
                bool(tareas))
            self.menuitems["Borrar empleado"].set_sensitive(
                self.vista_por_empleado)
            self.menuitems["Borrar línea"].set_sensitive(
                not self.vista_por_empleado)
            self.popup_menu.popup(None, None, None, event.button, event.time)

