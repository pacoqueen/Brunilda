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
        self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        while gtk.events_pending(): gtk.main_iteration(False)
        self.vista_por_empleado = not boton.get_active()
        if self.vista_por_empleado:
            lvista = "Ver por línea"
            self.ventana.set_title("Vista por empleado")
        else:
            lvista = "Ver por empleado"
            self.ventana.set_title("Vista por línea")
        boton.set_label(lvista)
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()
        self.ventana.window.set_cursor(None)

    def _update_zoom(self, range):
        self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        while gtk.events_pending(): gtk.main_iteration(False)
        self.zoom_level = range.get_value()
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()
        self.ventana.window.set_cursor(None)

    def _update_first_day(self, range):
        """
        Mueve el primer día mostrado.
        """
        self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        while gtk.events_pending(): gtk.main_iteration(False)
        self.first_day = range.get_value()
        self.grafica.remove(self.escena)
        self.load_escena()
        self.grafica.add(self.escena)
        self.grafica.show_all()
        self.ventana.window.set_cursor(None)

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
                    ("Asignar por lotes", self.asignar_por_lotes), 
                   )
        self.menuitems = {}
        for o, callback in opciones:
            menuitem = gtk.MenuItem(o)
            self.menuitems[o] = menuitem
            popup_menu.add(menuitem)
            menuitem.connect("activate", callback)
        # PORASQUI: Asignar uno a uno los turnos puede ser desesperante. Hay que pensar en un "acelerador". Furhermore: hasta que tenga claro cómo hacerlo, esta opción está deshabilitada:
        self.menuitems["Asignar por lotes"].set_sensitive(False)
        popup_menu.show_all()
        return popup_menu

    def limpiar_todo(self, item):
        # TODO: Según las HIG de gnome debería advertir antes.
        storage.delete_all()
        # Tengo que recargar los datos para ser coherente con los de la escena.
        self.refresh_escena()
        
    def limpiar_anno(self, item):
        anno = self.escena.get_anno_activo()
        storage.delete_year(anno)
        self.refresh_escena()

    def limpiar_mes(self, item):
        fecha = self.escena.get_mes_activo(self.clic_x)
        storage.delete_month(fecha.year, fecha.month)
        self.refresh_escena()

    def limpiar_dia(self, item):
        dia = self.escena.get_dia_activo(self.clic_x)
        storage.delete_day(dia.year, dia.month, dia.day)
        self.refresh_escena()

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
        e = self.escena.get_active_empleado_or_linea(self.clic_y)
        ini = self.escena.start_date
        fin = self.escena.end_date + datetime.timedelta(days = 1) 
        storage.limpiar_empleado(e, ini, fin)
        self.refresh_escena()

    def limpiar_linea(self, item):
        """
        Limpia todas las tareas de la línea de la tarea bajo el cursor entre 
        las fechas mostradas.
        Solo activo si estamos en vista por línea.
        """
        # a = self.escena.get_active_tarea(self.clic_x, self.clic_y).area
        a = self.escena.get_active_empleado_or_linea(self.clic_y)
        ini = self.escena.start_date
        fin = self.escena.end_date + datetime.timedelta(days = 1) 
        # linea = área
        storage.limpiar_linea(a, ini, fin)
        self.refresh_escena()
    
    def borrar_tarea(self, item):
        tareas = self.escena.get_actives_tareas(self.clic_x, self.clic_y)
        storage.delete_tareas(tareas)
        self.refresh_escena()

    def asignar(self, item):
        fecha = self.escena.get_active_day(self.clic_x, self.clic_y)
        if fecha:
            if self.vista_por_empleado:
                empleado = self.escena.get_active_empleado_or_linea(
                            self.clic_x, self.clic_y)
                if empleado:
                    linea, duracion, hora = self.seleccionar_linea_y_duracion(
                        fecha, empleado) 
                    if linea:
                        storage.nueva_tarea(empleado, linea, duracion, fecha, 
                                            hora)
                        self.refresh_escena()
            else:
                linea = self.escena.get_active_empleado_or_linea(self.clic_x, 
                                                                 self.clic_y)
                if linea:
                    empleado, duracion, hora \
                        = self.seleccionar_empleado_y_duracion(
                            fecha, linea)
                    if empleado:
                        storage.nueva_tarea(empleado, linea, duracion, fecha, 
                                            hora)
                        self.refresh_escena()

    def refresh_escena(self):
        self.tareas = storage.get_all_data()
        self.escena.reload_data(self.tareas)

    def seleccionar_linea_y_duracion(self, fecha, empleado):
        lineas = [a.nombre for a in storage.backend.get_areas()]
        texto = "Va a asignar a %s el %s.\n\n" % (
            empleado.nombre, fecha.strftime("%A, %d de %B de %Y")) 
        texto += "Seleccione o teclee un área de trabajo:" 
        linea, duracion, hora = dialogo_entrada_combo(titulo = "ASIGNAR TURNO", 
                            texto = texto, 
                            ops = lineas, 
                            padre = self.ventana)
        return linea, duracion, hora

    def seleccionar_empleado_y_duracion(self, fecha, linea):
        empleados = [a.nombre for a in storage.backend.get_empleados()]
        texto = "Va a asignar a %s el %s.\n\n" % (
            empleado.nombre, fecha.strftime("%A, %d de %B de %Y")) 
        texto += "Seleccione o teclee un empleado:"
        empleado, duracion, hora = dialogo_entrada_combo(
                            titulo = "ASIGNAR TURNO", 
                            texto = texto, 
                            ops = empleados, 
                            padre = self.ventana)
        return empleado, duracion, hora

    def asignar_por_lotes(self, item):
        """
        Asigna repetitivamente un empleado a una línea según una frecuencia 
        especificada por el usuario.
        """
        # TODO
        pass

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
        elif event.button == 1 and self.vista_por_empleado: 
            # Mover barra 2 horas a la izq. o der.
            barstareas = self.escena.get_actives_bars(x, y)
            for b in barstareas:
                xini = b.x
                xfin = b.x + b.width
                pivote = xini + ((xfin - xini) / 2)
                if b.tarea.horas == 12:
                    horas_inicio_validas = (6, 18)
                elif b.tarea.horas == 8:
                    horas_inicio_validas = (6, 14, 22)
                else:
                    horas_inicio_validas = [i for i in range(24) if i % 2 == 0]
                if x < pivote:
                    # con delta voy a redondear a las horas de los turnos.
                    hini = b.tarea.ini.hour - 2
                    delta = -2
                    while hini not in horas_inicio_validas:
                        delta -= 2
                        hini -= 2
                    # self.mover_barra_tarea(b, -2)
                    self.mover_barra_tarea(b, delta)
                elif x > pivote:
                    hini = b.tarea.ini.hour + 2
                    delta = 2
                    while hini not in horas_inicio_validas:
                        delta += 2
                        hini += 2
                    # self.mover_barra_tarea(b, +2)
                    self.mover_barra_tarea(b, delta)

    def mover_barra_tarea(self, barra, horas):
        """
        Mueve la barra la cantidad de horas especificada, así como la hora de 
        inicio de la tarea a la que corresponde.
        """
        obj_tarea = barra.tarea
        if not isinstance(horas, datetime.timedelta):
            delta = datetime.timedelta(hours = horas)
        storage.modificar(obj_tarea, 
                          ('fecha', 
                           obj_tarea.fecha + delta))
        pixels = self.escena.hour_pixel * horas
        barra.x += pixels
        #self.refresh_escena()
        # Tengo que actualizar el dato que guarda la escena. Creo que es más
        # rápido que volver a recrear la gráfica completa. 
        for t in self.escena.data:
            if t == obj_tarea:
                t.fecha += datetime.timedelta(hours=horas)

def dialogo_entrada_combo(titulo = 'Seleccione una opción', 
                          texto = '', 
                          ops = ['Sin opciones'], 
                          padre = None, 
                          valor_por_defecto = None):
    """
    Muestra un diálogo modal con un combobox con las opciones pasadas.
    Devuelve el texto tecleado o None si se cancela.
    Si valor_por_defecto != None, debe ser una cadena.
    """
    res = [None, 8, 6]
    de = gtk.Dialog(titulo,
                    padre,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_OK, gtk.RESPONSE_OK,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    #-------------------------------------------------------------------#
    def respuesta_ok_cancel_combo(dialog, response, res, ocho, doce):
        if response == gtk.RESPONSE_OK:
            combo = dialog.vbox.get_children()[1]
            if ocho.get_active():
                radio = 8
            else:
                radio = 12
            if h6.get_active():
                radio_horas = 6
            elif h14.get_active():
                radio_horas = 14
            elif h18.get_active():
                radio_horas = 18
            else:
                radio_horas = 22
            res[0] = combo.child.get_text()
            res[1] = radio
            res[2] = radio_horas
        else:
            res[0] = None
            res[1] = 0
            res[2] = 0
    #-------------------------------------------------------------------#
    def pasar_foco(completion, model, iter):                            #
        de.action_area.get_children()[1].grab_focus()                   #
    #-------------------------------------------------------------------#
    txt = gtk.Label("\n%s\n" % texto)
    model = gtk.ListStore(str)
    for t in ops:
        model.append((t, ))
    combo = gtk.ComboBoxEntry(model)
    completion = gtk.EntryCompletion()
    completion.set_model(model)
    combo.child.set_completion(completion)
        #-------------------------------------------------------#
    def match_func(completion, key, iter, (column, entry)):
        model = completion.get_model()
        text = model.get_value(iter, column)
        if text == None:
            return False
        key = entry.get_text()
        try:
            key = unicode(key, "utf").lower()               #
        except:                                             #
            key = key.lower()                               #
        try:                                                #
            text = unicode(text, "utf").lower()             #
        except:                                             #
            text = text.lower()                             #
        try:                                                #
            return key in text                              #
        except:                                             #
            # Error de codificación casi seguro.            #
            print key                                       #
            print text                                      #
            return False                                    #
    #-------------------------------------------------------#
    completion.set_text_column(0)
    completion.set_match_func(match_func, (0, combo.child))
    # completion.set_minimum_key_length(2)
    # completion.set_inline_completion(True)
    #---------------------------------------------------#
    def iter_seleccionado(completion, model, iter):     #
        combo.child.set_text(model[iter][0])            #
    #---------------------------------------------------#
    completion.connect('match-selected', iter_seleccionado)
    if valor_por_defecto != None:
        model = combo.get_model()
        iter = model.get_iter_first()
        while iter != None \
              and model[model.get_path(iter)] != valor_por_defecto:
            iter = model.iter_next()
        combo.set_active_iter(iter)
    input = combo.child.get_completion()
    input.connect("match_selected", pasar_foco)
    hbox = gtk.HBox(spacing = 5)
    icono = gtk.Image()
    icono.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icono)
    hbox.pack_start(txt)
    de.vbox.pack_start(hbox)
    combo.show()
    de.vbox.pack_start(combo)
    radio_duracion = gtk.HBox(spacing = 5)
    radio_duracion.pack_start(gtk.Label("Duración del turno:"))
    radio_horas = gtk.HBox()
    radio_horas.pack_start(gtk.Label("Hora de inicio:"))
    def deshabilitar_horas(r, ocho, doce, h6, h14, h18, h22):
        h6.set_sensitive(ocho.get_active() or doce.get_active())
        h14.set_sensitive(ocho.get_active())
        h18.set_sensitive(doce.get_active())
        h22.set_sensitive(ocho.get_active())
        for h in (h6, h14, h18, h22):
            if not h.get_sensitive() and h.get_active():
                h6.set_active(True)
    ocho = gtk.RadioButton(label = "8 horas")
    doce = gtk.RadioButton(ocho, "12 horas")
    h6 = gtk.RadioButton(label = "6:00")
    h14 = gtk.RadioButton(h6, "14:00")
    h18 = gtk.RadioButton(h6, "18:00")
    h18.set_sensitive(False)    # Por defecto, turnos de 8 horas.
    h22 = gtk.RadioButton(h6, "22:00")
    ocho.connect("toggled", deshabilitar_horas, ocho, doce, h6, h14, h18, h22)
    doce.connect("toggled", deshabilitar_horas, ocho, doce, h6, h14, h18, h22)
    radio_duracion.pack_start(ocho)
    radio_duracion.pack_start(doce)
    radio_horas.pack_start(h6)
    radio_horas.pack_start(h14)
    radio_horas.pack_start(h18)
    radio_horas.pack_start(h22)
    de.vbox.pack_start(radio_duracion)
    de.vbox.pack_start(radio_horas)
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    hbox.show_all()
    de.vbox.show_all()
    de.connect("response", respuesta_ok_cancel_combo, res, ocho, doce)
    de.run()
    de.destroy()
    return res

