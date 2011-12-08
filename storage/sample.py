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
    for i in range(7):
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
            for i in range(25):
                if random.randint(0, 1):    # Una de cada dos, gaussianamente más o menos...
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

def volcar_a_mongo():
    """
    Inserta todos los datos de prueba en la base de datos persistente.
    """
    # Aunque con guardar las tareas bastaría, voy a meter también los 
    # empleados y las áreas por separado, por si necesito hacer un recorrido 
    # o algo sobre ellas sin estar inspeccionando tareas.
    # 0.- Obtengo la conexión con Mongo (jejeje, ¡me encanta el nombre!)
    from .backend import data
    empleados = data.empleados
    areas = data.areas
    tareas = data.tareas
    # 1.- Inserto empleados
    for e in get_empleados():
        empleados.insert(e._to_dict())
    # 2.- Inserto áreas.
    # I feel less zen-pythonic, sometimes my oneliner soul comes out.
    areas.insert([a._to_dict() for a in get_areas()])
    # 3.- Inserto tareas. 
    tareas.insert([t._to_dict() for t in get_all_data()])

