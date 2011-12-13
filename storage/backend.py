#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .models import Empleado, Area, Tarea
import datetime as dt
from pymongo import Connection
import sys

""" Especie de ORM entre MongoDB y la interfaz gráfica. """

# TODO: Crear un índice ascendente sobre la fecha de las tareas. Acelerará 
# las búsquedas. (http://api.mongodb.org/python/current/tutorial.html#indexing)

DBERROR = 1

# Primero, conectamos.
try:
    conn = Connection()                     # XXX: Comentar en producción.
    #conn = Connection("192.168.1.100")    # XXX: Descomentar en producción.
except Exception, e:
    txterror = "No se pudo conectar a la base de datos.\n"\
               "¿Está mongod ejecutándose?\nExcepción: %s\n" % e
    sys.stderr.write(txterror)
    sys.exit(DBERROR)

# Ahora, abrimos la base de datos (si es la primera vez, no se guardará nada 
# a disco hasta que algo se haya insertado).
data = conn.brunilda

def get_empleados():
    """
    Devuelve una lista con todos los empleados.
    """
    empleados = []
    for e in data.empleados.find():
        objetoEmpleado = Empleado(e['nombre'])
        if objetoEmpleado not in empleados:
            empleados.append(objetoEmpleado)
    return empleados

def get_areas():
    """
    Lista de todas las áreas.
    """
    areas = []
    for a in data.areas.find():
        objetoArea = Area(a['nombre'])
        if objetoArea not in areas:
            areas.append(objetoArea)
    return areas

def get_empleado(nombre):
    """
    Devuelve el _primer_ empleado cuyo nombre coincida con el buscado.
    Encapsula el "registro" en un objeto Empleado.
    """
    e = data.empleados.find_one({'nombre': nombre})
    if not e:
        raise ValueError, "El empleado no existe en la base de datos."
    else:
        # ¿No creará esto dos objetos Emplado independietes pero idénticos?
        # Respuesta corta: sí. Respuesta larga: Sí, pero... 
        # ¡da igual! Tengo que "olvidar" el paradigma relacional. Me basta 
        # con instanciar un nuevo empleado y llegar a las tareas del 
        # empleado con .find() de tareas. No es necesario guardar 
        # explícitamente la relación 1 a n porque en el diccionario ya 
        # tengo implícitament al empleado de cada tarea. Lo importante es 
        # delegar en los métodos de la clase la búsqueda en mongo cada vez 
        # que quiera recorrer las tareas de un empleado.
        # De hecho, en el model ya he estado trabajando así sin darme cuenta 
        # al usar para los ejemplos únicamente diccionarios. No uso para nada 
        # self en los métodos. Siempre recibo como parámetro los "objetos" 
        # "relacionados" (comilla abuse mode on) con los que voy a operar.
        return Empleado(e['nombre'])

def get_area(nombre):
    """
    Devuelve el _primer_ área cuyo nombre coincida con el buscado.
    Encapsula el "registro" en un objeto Area.
    """
    e = data.areas.find_one({'nombre': nombre})
    if not e:
        raise ValueError, "El área no existe en la base de datos."
    else:
        return Area(e['nombre'])

def get_raw_empleado(nombre):
    """
    Devuelve el primer registro mongo del empleado que tenga como nombre 
    el recibido o None si no se encuentra.
    """
    e = data.empleados.find_one({'nombre': nombre})
    return e

def get_raw_area(nombre):
    """
    Devuelve el primer registro mongo del empleado que tenga como nombre 
    el recibido o None si no se encuentra.
    """
    e = data.areas.find_one({'nombre': nombre})
    return e

def get_all_data():
    """
    En realidad devuelve la lista de todas las tareas, que son los objetos 
    que relacionan entre sí a todos los demás registros. Transforma registros 
    de Mongo a su clase correspondiente.
    """
    tareas = []
    for t in data.tareas.find():
        tareas.append(Tarea(t))
    return tareas

def get_all_raw_data():
    """
    En realidad devuelve la lista de todas las tareas, que son los objetos 
    que relacionan entre sí a todos los demás registros.
    """
    tareas = []
    for t in data.tareas.find():
        tareas.append(t)
    return tareas

def get_all_data_by_empleado():
    """
    Devuelve un diccionario de empleados. Los valores son tareas con 
    el área y fecha (día y hora).
    """
    tareas = get_all_data()
    res = {}
    for t in tareas:
        e = t.empleado
        try:
            res[e].append(t)
        except KeyError:
            res[e] = [t]
    return res
   
