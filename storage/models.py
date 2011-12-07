#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt

OCHO_HORAS = dt.timedelta(8.0 / 24)
DOCE_HORAS = dt.timedelta(0.5)

class Empleado:
    def __init__(self, nombre):
        self.nombre = nombre

class Area:
    def __init__(self, nombre, descripcion = ""):
        self.nombre = nombre
        self.descripcion = descripcion

class Tarea:
    """
    Relaciona un empleado con un área en una tarea concreta de una 
    duración determinada y una fecha dada (día y hora).
    """
    def __init__(self, empleado, area, fecha, duracion = OCHO_HORAS):
        self.empleado = empleado
        self.area = area
        self.fecha = fecha
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
        return "%s en %s el %s de %s a %s." % (
            self.empleado.nombre, self.area.nombre, 
            self.fecha.strftime("%d/%m/%Y"),
            self.fecha.strftime("%H:%M"), 
            (self.fecha + self.duracion).strftime("%H:%M"))
 
    def __repr__(self):
        return self.__str__()

