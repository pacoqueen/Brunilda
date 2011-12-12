#!/usr/bin/env python
# -*- coding: utf-8 -*-

import backend
from models import Tarea, Empleado, Area
#import sample
import datetime

def get_all_data():
    return backend.get_all_data()

def delete_all():
    backend.data.tareas.remove({})
    # He pensado que mejor no borrarlos para poder después asignar sin tener 
    # que volverlos a crear.
    #backend.data.empleados.remove({})
    #backend.data.lineas.remove({})

def delete_year(y):
    start = datetime.datetime(year = y, month = 1, day = 1)
    end = datetime.datetime(year = y + 1, month = 1, day = 1) 
    backend.data.tareas.remove({'fecha': {"$gte": start, 
                                          "$lt": end}})

def delete_month(y, m):
    start = datetime.datetime(year = y, month = m, day = 1)
    m += 1
    if m > 12:
        y += 1
        m = 1
    end = datetime.datetime(year = y, month = m, day = 1) 
    backend.data.tareas.remove({'fecha': {"$gte": start, 
                                          "$lt": end}})

def delete_day(y, m, d):
    start = datetime.datetime(year = y, month = m, day = d)
    end = start + datetime.timedelta(days = 1) 
    backend.data.tareas.remove({'fecha': {"$gte": start, 
                                          "$lt": end}})

def delete_tareas(ts):
    for t in ts:
        # Faster than "remove{t}"
        backend.data.tareas.remove({'_id': t._id})
        # backend.data.tareas.remove({'_id': t['_id']})

def limpiar_empleado(e, start, end):
    if not isinstance(start, datetime.datetime):
        # BSON (mongo) no entiende dates, solo datetimes.
        start = datetime.datetime(start.year, start.month, start.day)
    if not isinstance(end, datetime.datetime):
        # BSON (mongo) no entiende dates, solo datetimes.
        end = datetime.datetime(end.year, end.month, end.day)
    backend.data.tareas.remove({'empleado': {'nombre': e.nombre}, 
                                'fecha': {"$gte": start, 
                                          "$lt": end}})

def limpiar_linea(a, start, end):
    if not isinstance(start, datetime.datetime):
        # BSON (mongo) no entiende dates, solo datetimes.
        start = datetime.datetime(start.year, start.month, start.day)
    if not isinstance(end, datetime.datetime):
        # BSON (mongo) no entiende dates, solo datetimes.
        end = datetime.datetime(end.year, end.month, end.day)
    backend.data.tareas.remove({'area': {'nombre': a.nombre, 
                                         "descripcion": a.descripcion}, 
                                'fecha': {"$gte": start, 
                                          "$lt": end}})

def nueva_tarea(empleado, linea, duracion, fecha, hora):
    """
    Crea en el backend una nueva tarea y devuelve un objeto Tarea equivalente.
    """
    if isinstance(fecha, (datetime.date, datetime.datetime)):
        fecha = datetime.datetime(year = fecha.year, 
                                  month = fecha.month, 
                                  day = fecha.day, 
                                  hour = hora)
    if isinstance(empleado, Empleado):
        empleado = empleado.nombre
    if isinstance(linea, Area):
        linea = linea.nombre
    tarea = {'empleado': {'nombre': empleado}, 
             'area': {'nombre': linea, 
                      'descripcion': ''}, 
             'duracion': duracion, 
             'fecha': fecha}
    nueva_tarea_id = backend.data.tareas.insert(tarea)
    new_tarea = backend.data.tareas.find_one(nueva_tarea_id)
    return Tarea(new_tarea)

