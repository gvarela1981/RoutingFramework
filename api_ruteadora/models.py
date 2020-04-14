import datetime 

from django.db import models
from django.utils import timezone


class Endpoint(models.Model):
    nombre = models.CharField('Nombre del Endpoint',max_length=20)
    url = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField('Fecha de Creacion') # agregar default
    fecha_modificacion = models.DateTimeField('Fecha de Modificacion') # agregar default
    descripcion = models.CharField(max_length=200)

    def __str__(self):
    	return self.nombre