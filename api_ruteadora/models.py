from datetime import datetime 

from django.db import models
from django.utils import timezone


class Endpoint(models.Model):
    nombre = models.CharField('Nombre del Endpoint',max_length=20, unique=True)
    url = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField('Fecha de Creacion') # agregar default
    fecha_modificacion = models.DateTimeField('Fecha de Modificacion') # agregar default
    descripcion = models.CharField(max_length=200)

    def __str__(self):
    	return self.nombre

class Costo(models.Model):
	"""
	Modelo de costos, los valores se usan para calcular el costo del viaje
	las variables que inician con el prefijo "conf" son puramente descriptivas
	y no tienen impacto en el comportamiento
	"""
	nombre	= models.CharField('Costos', default='Costo', max_length=20, unique=True)
	INICIO_SERVICIO_DIURNO = models.TimeField('Inicio del servicio diurno', default='06:00:00')
	conf_fecha_inicio_incio_diurno = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_incio_diurno = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_inicio_diurno	= models.CharField('Observaciones', max_length=200, blank = True)

	INICIO_SERVICIO_NOCTURNO = models.TimeField('Inicio del servicio nocturno', default='22:00:00')
	conf_fecha_inicio_incio_nocturno = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_incio_nocturno = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_inicio_nocturno	= models.CharField('Observaciones', max_length=200, blank = True)

	BAJADA_BANDERA_DIURNA = models.FloatField('Valor de Bajada de bandera diurna', default=4)
	conf_fecha_inicio_bajada_diurna = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_bajada_diurna = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_bajada_diurna	= models.CharField('Observaciones', max_length=200, blank = True)

	BAJADA_BANDERA_NOCTURNA = models.FloatField('Valor de Bajada de bandera nocturna', default=6)
	conf_fecha_inicio_bajada_nocturna = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_bajada_nocturna = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_bajada_nocturna = models.CharField('Observaciones', max_length=200, blank = True)

	VALOR_FICHA_DIURNA = models.FloatField('Valor de ficha diurna', default=35)
	conf_fecha_inicio_valor_ficha_diurna = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_valor_ficha_diurna = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_valor_ficha_diurna	= models.CharField('Observaciones', max_length=200, blank = True)

	VALOR_FICHA_NOCTURNA = models.FloatField('Valor de ficha nocturna', default=46)
	conf_fecha_inicio_valor_ficha_nocturna = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_valor_ficha_nocturna = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_valor_ficha_nocturna	= models.CharField('Observaciones', max_length=200, blank = True)

	PORCENTAJE_DIURNO_AJUSTE = models.FloatField('Porcentaje de ajuste diurno', default=20)
	conf_fecha_inicio_ajuste_diurno = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_ajuste_diurno = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_ajuste_diurno	= models.CharField('Observaciones', max_length=200, blank = True)

	PORCENTAJE_NOCTURNO_AJUSTE = models.FloatField('Porcentaje de ajuste nocturno', default=20)
	conf_fecha_inicio_ajuste_nocturno = models.DateTimeField('Fecha de inicio del valor',  default=timezone.now)
	conf_fecha_fin_ajuste_nocturno = models.DateTimeField('Fecha de fin del valor',  default=timezone.now)
	conf_observacion_ajuste_nocturno	= models.CharField('Observaciones', max_length=200, blank = True)

	fecha_creacion = models.DateTimeField('Fecha de Creacion', auto_now_add=True)
	fecha_modificacion = models.DateTimeField('Fecha de Modificacion',  default=timezone.now)

	def __str__(self):
		return self.nombre