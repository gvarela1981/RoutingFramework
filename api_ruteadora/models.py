from datetime import datetime 

from django.db import models
from django.utils import timezone

from django.contrib.gis.db import models
from django.conf import settings
from django.db.models import Manager as GeoManager
# from commons.commons import normalizar_texto, armarRespuestaGeoLayer, ObjectContent
# from util.geoUtils import normalizarGeocodificarYConsultarDelimitaciones
# from api.settings import DATE_FORMAT_MF

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

class Ruteo(models.Model):
	the_geom = models.MultiPolygonField('Mapa', null=True, blank=True, srid=settings.SRID)
	# nombre = models.CharField('Nombre', max_length=200, null=True, blank=True, default='Recuperador Urbano')
	# codigo = models.IntegerField('Código Calle', max_length=254, null=True, blank=True, default='')
	nomoficial = models.CharField('Nombre', max_length=254, null=True, blank=True, default='')    
	latitud = models.CharField('Latitud', max_length=254, null=True, blank=True, default='')   
	longitud = models.CharField('Longitud', max_length=254, null=True, blank=True, default='')   

	#Datos USIG
	timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
	timestamp_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de última modificación')
	observaciones_publicables = models.TextField('observaciones publicables', null=False, blank=True, max_length=1000)
	observaciones_privadas = models.TextField('observaciones privadas', null=False, blank=True, max_length=1000)
	publicable = models.BooleanField('publicable', default=True)
	verificado = models.BooleanField('verificado', default=True)

	objects = GeoManager()

	class Meta:
		ordering = ['id']
		verbose_name = 'Ruteo'
		verbose_name_plural = 'Ruteo'

	def __str__(self):
		return str(self.nomoficial)


	def save(self, *args, **kwargs):
		resultadoOK = True
		resultado = dict()
		resultado['texto'] = ''        
		super(Ruteo, self).save(*args, **kwargs)
		return resultadoOK, resultado
	@classmethod
	def getGeoLayer(cls, **kwargs):
	    res = cls.objects.filter(publicable=True)

	    formato_datos = ['Id', 'Nombre', 'Geom']
	    datos = []
	    for r in res:
	        datos.append([str(r.id), r.nomoficial, r.the_geom])
	    return armarRespuestaGeoLayer(datos, formato_datos, **kwargs)

	@classmethod
	# dado un id de objeto, devuelve un diccionario con el contenido del objeto y otros datos
	# el llamador luego agregará más datos según datos de la API
	def getObjectContent(cls, id):
	    try:
	        obj = cls.objects.filter(publicable=True).get(id=id)
	    except:
	        return {}

	    res = dict()
	    obj_cont = ObjectContent([   
	                             ['nombre', 'Nombre', obj.nomoficial],
	                             ['latitud', 'Latitud', obj.latitud],
	                                                                  
	                             ])                                                                        
	    res['contenido'] = obj_cont.dame_detalle()
	    res['fechaAlta'] = obj.timestamp_alta.strftime(DATE_FORMAT_MF)
	    res['ubicacion'] = {'centroide': obj.the_geom.wkt, 'tipo': 'Poligono'}
	    res['fechaUltimaModificacion'] = obj.timestamp_modificacion.strftime(DATE_FORMAT_MF)
	    res['id'] = str(obj.id)
	    res['direccionNormalizada'] = str(obj.direccion_normalizada)
	    return res


	def dame_info_buscable(self):
	    return {'categoria_normalizada': 'ruteos',
	            'id_objeto': self.id,
	            'nombre_objeto': self.__str__(),
	            'clase': u'Ruteo',
	            'id_clase': '1',
	            'the_geom': self.the_geom,
	            'array_fts': ['', '', self.__str__(), ''],
	            'publicable': self.publicable,
	            'autoindexar_metadatos': True,
	            }


	@classmethod
	def dame_objetos_buscables(cls):
	    return cls.objects.all()


	@classmethod
	def busquedaGeografica(cls, x, y, srid, radio):

		try:
			punto = GEOSGeometry('SRID={2};POINT({0} {1})'.format(x, y, srid))

			if srid != settings.SRID:
				punto.transform(settings.SRID)
			if radio:
				punto_con_buffer = punto.buffer(radio)
			return Ruteo.objects.filter(the_geom__intersects=punto_con_buffer)
		except Exception as e:
			print(e)
			return {}

	#Metodo para borrado de Registro
	def delete(self):
		#ScheduleFTS.grabarDelete(self.dame_info_buscable())
		#ScheduleFTS.ejecutarAcciones()
		super(Ruteo, self).delete()