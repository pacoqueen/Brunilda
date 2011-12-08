#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt

OCHO_HORAS = dt.timedelta(8.0 / 24)
DOCE_HORAS = dt.timedelta(0.5)

class Empleado(object):
    _instances = {}
    def __new__(cls, nombre):
        """
        Redefino el constructor para no crear múltiples instancias del 
        mismo empleado.
        """
        # Esto vendría a ser una especie de patrón Singleton pero con 
        # varias instancias únicas en vez de una sola.
        if isinstance(nombre, dict):    # Viene de Mongo
            nombre = nombre['nombre']
        if not nombre in cls._instances:
            cls._instances[nombre] = super(Empleado, cls).__new__(cls, nombre)
        return cls._instances[nombre]

    def __init__(self, nombre):
        if isinstance(nombre, dict):    # Viene de Mongo
            nombre = nombre['nombre']
        self.nombre = nombre

    def calcular_horas_asignadas(self, tareas):
        """
        Devuelve un entero con las horas asignadas mediante tareas.
        """
        res = 0
        hpa = self.calcular_horas_por_area(tareas)
        for a in hpa:
            res += hpa[a]
        return res

    def calcular_horas_por_area(self, tareas):
        """
        Devuelve un diccionario con las horas asignadas en cada área.
        """
        res = {}
        for t in tareas:
            try:
                res[t.area] += t.horas
            except KeyError:
                res[t.area] = t.horas
        return res

    def _to_dict(self):
        """
        Devuelve un diccionario que representa al objeto para la inserción 
        en MongoDB
        """
        res = {'nombre': self.nombre}
        return res


class Area:
    def __new__(cls, nombre, *args, **kw):
        """
        Redefino el constructor para no crear múltiples instancias de la 
        misma área.
        """
        if isinstance(nombre, dict):    # Viene de Mongo
            nombre = nombre['nombre']
        if not nombre in cls._instances:
            cls._instances[nombre] = super(Area, cls).__new__(cls, nombre, 
                                                              *args, **kw)
        return cls._instances[nombre]

    def __init__(self, nombre, descripcion = ""):
        if isinstance(nombre, dict):    # Viene de Mongo
            descripcion = nombre['descripcion']
            nombre = nombre['nombre']
        self.nombre = nombre
        self.descripcion = descripcion

    def _to_dict(self):
        """
        Representación en diccionario del área.
        """
        res = {'nombre': self.nombre, 
               'descripcion': self.descripcion}
        return res


class Tarea:
    """
    Relaciona un empleado con un área en una tarea concreta de una 
    duración determinada y una fecha dada (día y hora).
    """
    def __init__(self, empleado, area = None, fecha = None, 
                 duracion = OCHO_HORAS):
        if isinstance(empleado, dict):  # Viene de Mongo
            duracion = empleado['duracion']
            fecha = empleado['fecha']
            area = Area(empleado['area'])
            empleado = Empleado(empleado['empleado'])
        else:   # Compruebo que trae al menos área y fecha:
            if area is None or fecha is None: 
                raise TypeError, "__init__() takes at least 4 arguments"
        self.empleado = empleado
        self.area = area
        self.fecha = fecha
        if not isinstance(duracion, dt.timedelta):
            duracion = dt.timedelta(seconds = duracion * 60 * 60)
        self.duracion = duracion

    @property
    def fin(self):
        return self.fecha + self.duracion

    @property
    def ini(self):
        return self.fecha

    def __solapa_horas(self, f, d):
        """
        Comprueba si las horas de la tarea actual con la duración que 
        tiene se solapa con las de la fecha «f» y duración «d».
        """
        ini1 = self.fecha
        fin1 = self.fecha + self.duracion
        ini2 = f
        fin2 = f + d
        # Condiciones para que se solapen: cuatro casos.
        # 1.º Se solapan por el final
        # 2.º Se solapan por el principio
        # 3.º 1 está contenido en 2
        # 4.º 2 está contenido en 1
        # Si nos fijamos en los extremos, las condiciones se reducen a:
        res = ((ini1 <= ini2 and ini2 <= fin1) or 
               (ini2 <= ini1 and ini1 <= fin2))
        # TODO: Definitivamente necesito pruebas unitarias. 
        return res

    def solapa(self, tareas):
        """
        Comprueba que la tarea se solapa con alguna para el mismo empleado
        y a la misma hora de la lista de tareas recibida.
        """
        # TODO: No estaría mal empezar a escribir unittests YA. 
        solapada = False
        for t in tareas:
            if (t.empleado == self.empleado 
                and self.__solapa_horas(t.fecha, t.duracion)):
                solapada = True
                break   # Evito iteraciones innecesarias.
        return solapada

    def __str__(self):
        # FIXME: ipython se hace la picha un lío con los unicode de Mongo y 
        # peta al intentar pasar su prettyprint por esta cadena UTF-8 por 
        # culpa de la tilde de «Área 0» en el conjunto de datos de ejemplo.
        return u"%s en %s el %s de %s a %s." % (
            self.empleado.nombre, self.area.nombre, 
            self.fecha.strftime("%d/%m/%Y"),
            self.fecha.strftime("%H:%M"), 
            (self.fecha + self.duracion).strftime("%H:%M"))
 
    def __repr__(self):
        return self.__str__()
    
    @property
    def horas(self):
        """
        Devuelve un float con las horas de duración de la tarea.
        """
        dias = self.duracion.days
        segundos = self.duracion.seconds
        total_segundos = segundos + (dias * 24 * 60 * 60)
        horas = total_segundos / 60.0 / 60.0
        return horas

    def _to_dict(self):
        """
        Representación en diccionario de la tarea. Los objetos Empleado y 
        Área son convertidos también en diccionario enviándoles el mensaje 
        correspondiente.
        """
        res = {'empleado': self.empleado._to_dict(), 
               'area': self.area._to_dict(), 
               'fecha': self.fecha, 
               'duracion': self.horas}  
                # InvalidDocument: Cannot encode object: datetime.timedelta
                # Para la operación inversa tendré que convertir el float 
                # de nuevo a timedelta. :(
        return res

