#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Conjunto de datos de ejemplo.
En lenguaje natural, cada empleado trabaja en un área durante un periodo de 
8 ó 12 horas en un día determinado y haciendo una tarea concreta.
"""

from .models import Empleado, Area, Tarea
import random
import datetime as dt

def get_empleados():
    """
    Devuelve una lista con todos los empleados.
    """
    empleados = []
    for i in range(10):
        empleados.append(Empleado("Empleado " + `i`))
    return empleados

def get_areas():
    """
    Lista de todas las áreas.
    """
    areas = []
    for i in range(5):
        areas.append(Area("Área " + `i`))
    return areas

def asignar_tareas_ejemplo(empleados, areas, aleatorio = False):
    """
    Asigna tareas de ejemplo aleatorias a los empleados en las áreas.
    """
    tareas = []
    if not aleatorio:
        random.seed("Isa")  # Misma semilla para reproducir resultados. No 
                            # significa que no sea aleatorio en abosluto.
    for e in empleados:
        for a in areas:
            #if random.randint(0, 1):    # Una de cada dos, más o menos...
            if True: 
                duracion = random.randrange(8, 13, 4) # 8 ó 12 horas de turno.
                if duracion == 8:
                    hora = (6, 14, 22)[random.randrange(0, 3)]
                else:
                    hora = (6, 18)[random.randrange(0, 2)]
                while True:
                    try:
                        f = dt.datetime(year = 2012, 
                                        #month = random.randint(1, 12), 
                                        month = random.randint(1, 2), 
                                        day = random.randint(1, 31), 
                                        hour = hora)
                    except ValueError:
                        pass    # Fecha inválida. Vuelvo a intentarlo
                    else:
                        break
                d = dt.timedelta(duracion / 24.0)
                t = Tarea(e, a, f, d)
                if not t.solapa(tareas):
                    tareas.append(t)
    return tareas

def get_all_data():
    empleados = get_empleados()
    areas = get_areas()
    return asignar_tareas_ejemplo(empleados, areas)

def get_all_data_by_empleado():
    """
    Devuelve un diccionario de empleados. Los valores son tareas con 
    el área y fecha (día y hora).
    """
    empleados = get_empleados()
    areas = get_areas()
    tareas = asignar_tareas_ejemplo(empleados, areas)
    res = {}
    for t in tareas:
        e = t.empleado
        try:
            res[e].append(t)
        except KeyError:
            res[e] = [t]
    return res

