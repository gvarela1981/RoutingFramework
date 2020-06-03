from datetime import datetime 

from django.db import models
from django.utils import timezone

from django.contrib.gis.db import models
from django.conf import settings
from django.db.models import Manager as GeoManager
from django.contrib.gis.geos import GEOSGeometry, Point

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
	fecha_inicio = models.DateTimeField('Fecha de inicio',  default=timezone.now)
	fecha_fin = models.DateTimeField('Fecha de fin',  default=timezone.now)
	observacion = models.CharField('Observaciones', max_length=200, blank = True)
	nombre	= models.CharField('Costos', default='Costo', max_length=20, unique=True)
	inicio_servicio_diurno = models.TimeField('Inicio del servicio diurno', default='06:00:00')
	inicio_servicio_nocturno = models.TimeField('Inicio del servicio nocturno', default='22:00:00')
	bajada_bandera_diurna = models.FloatField('Valor de Bajada de bandera diurna', default=4)
	bajada_bandera_nocturna = models.FloatField('Valor de Bajada de bandera nocturna', default=6)
	valor_ficha_diurna = models.FloatField('Valor de ficha diurna', default=35)
	valor_ficha_nocturna = models.FloatField('Valor de ficha nocturna', default=46)
	porcentaje_diurno_ajuste = models.FloatField('Porcentaje de ajuste diurno', default=20)
	porcentaje_nocturno_ajuste = models.FloatField('Porcentaje de ajuste nocturno', default=20)
	distancia_por_ficha = models.FloatField('Distancia en la que se consume una ficha', default=100)
	
	fecha_creacion = models.DateTimeField('Fecha de Creacion', auto_now_add=True)
	fecha_modificacion = models.DateTimeField('Fecha de Modificacion',  default=timezone.now)

	class Meta:
		ordering = ['fecha_inicio']
		verbose_name = 'Parametro'
		verbose_name_plural = 'Parametros'

	def save(self, *args, **kwargs):
		resultado = dict()
		resultado['texto'] = ''
		resultado['resultadoOK'] = True
		fechas_en_conflicto_resultado = set()
		# Armo la consulta, buscar paramtros guardados en los 4 casos posibles de solapamiento de fechas
		# Caso 1, existe un conjunto de datos que inicia antes del nuevo fecha_inicio y finaliza despues del nuevo fecha_inicio y antes del nuevo fecha_fin
		# Caso 4, existe un conjunto de datos que inicia antes del nuevo fecha_inicio y finaliza despues del nuevo fecha_inicio y despues del nuevo fecha_fin
		fechas_en_conflicto = Costo.objects.filter(fecha_inicio__lt=self.fecha_inicio)
		fechas_en_conflicto = fechas_en_conflicto.filter(fecha_fin__gt=self.fecha_inicio)
		for i in fechas_en_conflicto:
			fechas_en_conflicto_resultado.add(i.nombre)
		# Caso 2, existe un conjunto de datos que inicia despues del nuevo fecha_inicio y finaliza antes del nuevo fecha_fin
		fechas_en_conflicto = Costo.objects.filter(fecha_inicio__gt=self.fecha_inicio)
		fechas_en_conflicto = fechas_en_conflicto.filter(fecha_fin__lt=self.fecha_fin)
		for i in fechas_en_conflicto:
			fechas_en_conflicto_resultado.add(i.nombre)
		# Caso 3, existe un conjunto de datos que inicia despues del nuevo fecha_inicio y antes del nuevo fecha_fin
		fechas_en_conflicto = Costo.objects.filter(fecha_inicio__gt=self.fecha_inicio)
		fechas_en_conflicto = fechas_en_conflicto.filter(fecha_inicio__lt=self.fecha_fin)
		fechas_en_conflicto = fechas_en_conflicto.filter(fecha_fin__gt=self.fecha_fin)
		for i in fechas_en_conflicto:
			fechas_en_conflicto_resultado.add(i.nombre)
		# Caso 5, la nueva fecha_fin es menor a la nueva fecha_inicio
		if(self.fecha_inicio > self.fecha_fin):
			fechas_en_conflicto_resultado.add('La fecha de inicio es posterior a la fecha de fin')

		# Si el set de parametros entra en conflicto con sigo mismo lo excluyo porque el cambio esta permitido
		if self.nombre in fechas_en_conflicto_resultado:
			fechas_en_conflicto_resultado.remove(self.nombre)
		# Si no hay set de parametros en conflicto de fechas lo grabo
		if(len(fechas_en_conflicto_resultado) == 0):
			# El mensaje de Ok lo envía la clase padre, solo procesamos el mensaje de error
			super(Costo, self).save(*args, **kwargs)
			resultado['texto'] = ''
		else:
			error_debug = 'No se puede grabar el registro porque hay ' + str(len(fechas_en_conflicto_resultado)) + ' parametros que se solapan con '
			error_debug += self.nombre + ' ' + str(fechas_en_conflicto_resultado)
			print(error_debug)
			resultado['texto'] = error_debug
			resultado['cant_registros'] = len(fechas_en_conflicto_resultado)
			resultado['resultadoOK'] = False
		return resultado

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
	def busquedaGeografica(cls, x, y, srid, radio):
		'''
		Con una funcion ST_Intersect devuelve el punto 
		de reingreso a CABA mas cercano al punto solicitado
		'''
		try:
			#punto = GEOSGeometry('SRID={2};POINT({0} {1})'.format(x, y, srid))
			# Generamos el punt con srid = 4326 de forma 
			# consistente con el formato de coordenadas aceptado
			punto = GEOSGeometry('SRID={2};POINT({1} {0})'.format(y, x, 4326))
			punto.transform(settings.SRID)
			if radio and radio is not 0:
				punto = punto.buffer(radio)
			response = {}
			result = Ruteo.objects.filter(the_geom__intersects=punto)
			if len(result) > 0:
				for ele in result:
					# Obtengo la columna latitud y longitud de la tabla Ruteos
					response.update({'latitud': ele.latitud, 'longitud': ele.longitud})
	    	# Si no hay interseccion se devuelve un diccionario en blanco
			else:
				response = {}
			return response
		except Exception as e:
			print(e)
			return {}

	#Metodo para borrado de Registro
	def delete(self):
		#ScheduleFTS.grabarDelete(self.dame_info_buscable())
		#ScheduleFTS.ejecutarAcciones()
		super(Ruteo, self).delete()
class Comuna(models.Model):
	nombre = models.CharField('Nombre', max_length=30, null=False, blank=False)
	nombre_original = models.CharField('Nombre Original', max_length=30, null=False, blank=True)
	barrios = models.CharField('Barrios', max_length=100, null=False, blank=True)
	the_geom = models.MultiPolygonField('geometría', null=True, blank=True, srid=settings.SRID)
	timestamp_alta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de alta')
	timestamp_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de última modificación')
	observaciones_publicables = models.TextField('observaciones publicables', null=False, blank=True, max_length=1000)
	observaciones_privadas = models.TextField('observaciones privadas', null=False, blank=True, max_length=1000)
	publicable = models.BooleanField('publicable', default=True)
	verificado = models.BooleanField('verificado', default=True)
	objects = GeoManager()

	class Meta:
		ordering = ['nombre']
		verbose_name = 'Comuna'
		verbose_name_plural = 'Comunas'

	def __str__(self):
		return '%s' % (self.nombre)

	def save(self, *args, **kwargs):
		if self.the_geom and isinstance(self.the_geom, Polygon):
			self.the_geom = MultiPolygon(self.the_geom)
		super(Comuna, self).save(*args, **kwargs)
		ScheduleFTS.grabarUpsert(self.dame_info_buscable())
		# return resultadoOK, resultado
		return True, dict()  # TODO: ver esto

	@classmethod
	def getGeoLayer(cls, **kwargs):
		if 'comunas' in kwargs:
			comunas = ['Comuna ' + str(x) for x in parsear_csi_input(kwargs['comunas'])]
			res = cls.objects.filter(publicable=True, nombre__in=comunas)
		else:
			res = cls.objects.filter(publicable=True)
		formato_datos = ['Id', 'Nombre', 'Comuna', 'Geom']
		datos = []
		for r in res:
			datos.append([str(r.id), r.__str__(), r.__str__().replace('Comuna ', ''), r.the_geom])
		### test gonzalo varela
		print('xxxxxxxxx ACA')
		print(datos)
		### fin test gonzalo varela
		#return armarRespuestaGeoLayer(datos, formato_datos, **kwargs)

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
	                             ['nombre', 'Nombre', obj.__str__()],
	                             ])
	    res['contenido'] = obj_cont.dame_detalle()
	    res['fechaAlta'] = obj.timestamp_alta.strftime(DATE_FORMAT_MF)
	    res['ubicacion'] = {'centroide': obj.the_geom.centroid.wkt if obj.the_geom else '', 'tipo': 'Punto'}
	    res['fechaUltimaModificacion'] = obj.timestamp_modificacion.strftime(DATE_FORMAT_MF)
	    res['id'] = str(obj.id)
	    res['direccionNormalizada'] = ''
	    return res


	def dame_info_buscable(self):
	    return {'categoria_normalizada': 'comunas',
	            'id_objeto': self.id,
	            'nombre_objeto': self.__str__(),
	            'clase': 'Comuna',
	            'id_clase': '1',
	            'the_geom': self.the_geom.centroid if self.the_geom else '',
	            'array_fts': [str(self.nombre), '', '', ''],
	            'publicable': self.publicable,
	            'autoindexar_metadatos': False,
	            }
	@classmethod
	def dame_objetos_buscables(cls):
	    return cls.objects.all()
	def delete(self):
	    ScheduleFTS.grabarDelete(self.dame_info_buscable())
	    super(Comuna, self).delete()

	@classmethod
	def busquedaGeografica(cls, x, y, srid, radio):
		try:
			#punto = GEOSGeometry('SRID={2};POINT({0} {1})'.format(x, y, srid))
			# Generamos el punt con srid = 4326 de forma 
			# consistente con el formato de coordenadas aceptado
			punto = GEOSGeometry('SRID={2};POINT({1} {0})'.format(y, x, 4326))
			punto.transform(settings.SRID)
			if radio and radio is not 0:
				punto = punto.buffer(radio)
			response = []
			result = Comuna.objects.filter(the_geom__intersects=punto)
			if len(result) > 0:
				for e in result:
					response.append(e.barrios)
	  	# Si no pertenece a caba, o no se encuentra una 
	  	# interseccion se devuelve un espacio en blanco
			else:
				response.append(' ')
			return response[0]
		except Exception as e:
			print('Error al buscar la comuna', e)
			return {}