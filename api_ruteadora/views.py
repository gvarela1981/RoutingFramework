
"""
.. module:: views
	 :platform: Unix, Windows
	 :synopsis: Un modulo utilizable.

.. moduleauthor:: Mi Nombre <scastellano10@gmail.com>


"""


from django.http import JsonResponse
import requests
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from api_ruteadora.models import Endpoint, Costo, Ruteo, Comuna
import math

import json as simplejson
import datetime
from django.contrib.gis.geos import GEOSGeometry, Point

# mensaje a devolver en el json cuando se produce un error
mensaje_error = ''
#APIs que se consumen, despues de actualizarlas se debe reiniciar servicio
try:
	#Server de ruteo
	objRuteo = Endpoint.objects.filter(nombre='Ruteo')
	server = objRuteo.values_list('url', flat=True).first()
	#Server autopista
	objRuteo = Endpoint.objects.filter(nombre='Filtro de Autopista')
	server_no_autopista = objRuteo.values_list('url', flat=True).first()
except Exception as e:
	mensaje_error += '\nSe produjo un error al obtener las direcciones de las API externas para realizar los calculos'
	print(mensaje_error+str(e))
	isRuteoOK = False

MAX_POINTS = settings.MAX_POINTS if hasattr(settings, 'MAX_POINTS') else 10
try:
	objSettings = Costo.objects.filter(nombre='Costo')
	inicio_servicio_diurno = objSettings.values_list('inicio_servicio_diurno', flat=True).first()
	inicio_servicio_nocturno = objSettings.values_list('inicio_servicio_nocturno', flat=True).first()
	bajada_bandera_diurna = objSettings.values_list('bajada_bandera_diurna', flat=True).first()
	bajada_bandera_nocturna = objSettings.values_list('bajada_bandera_nocturna', flat=True).first()
	valor_ficha_diurna = objSettings.values_list('valor_ficha_diurna', flat=True).first()
	valor_ficha_nocturna = objSettings.values_list('valor_ficha_nocturna', flat=True).first()
	porcentaje_diurno_ajuste = objSettings.values_list('porcentaje_diurno_ajuste', flat=True).first()
	porcentaje_nocturno_ajuste = objSettings.values_list('porcentaje_nocturno_ajuste', flat=True).first()
	distancia_por_ficha = objSettings.values_list('distancia_por_ficha', flat=True).first()
except Exception as e:
	mensaje_error += '\nSe produjo un error al obtener valor de los costos'
	mensaje_warn = ''
	print(mensaje_error+str(e))
	isRuteoOK = False

def validarPuntos(puntos, headers):
	locValidado = []
	for i in puntos:
		url = server_no_autopista + i[1] + ',' + i[0] + '?exclude=motorway'
		try:
			response = requests.request('GET', url, headers=headers, allow_redirects=False)
		except Exception as e:
			mensaje_warn = 'No se recibio respuesta de la API que filtra autopistas'
			print(mensaje_warn)
			raise Exception(mensaje_warn)

		resultado_du = response.json()
		# print('resultado json:  ' + str(resultado_du))
		punto_chequeado = resultado_du['waypoints'][0]['location']
		# un array con 3 strs, dos de lat lon y una ultima con lat,lon, todos habienso sido chequeados
		punto = [str(punto_chequeado[1]), str(punto_chequeado[0]),
						 str(punto_chequeado[1]) + ',' + str(punto_chequeado[0])]

		locValidado.append(punto)
	return locValidado

def armarRespuestaPuntos(datos,gml):
	"""Funcion que es llamada internamente y que arma diversas consultas a APIs externas
	para realizar el calculo de una traza definida por los puntos contenidos en datos.

	Args:
	``datos (array)``:  Coleccion de flotantes que representan los pares ordenados lat lon
	que serviran para la realización de la traza. No puede contener menos
	de cuatro numeros, ni una cantidad impar, esta verificacion se hace
	en la funcion llamadora.

	``gml (int)`` : Entero (0,1) que determina si en el json de salida se agrega o no la traza
	calculada entregada por el server de ruteo en formato gml.
	Returns:
	``json``
	"""

	n = 2
	# divido los datos en pares ordenados de coordenadas
	puntos = list(zip(*[iter(datos)] * n))

	headers = {
		'Content-Type': 'application/json'
	}
	# valido los puntos ingresados
	loc = validarPuntos(puntos, headers)
	destino = loc[-1]

	mensaje_error = ''
	isRuteoOK = True
	isRetornoOK = True

	# El while permite cortar la ejecucion con break cuando un calculo
	# importante no se pudo realizar
	while isRuteoOK:
		try:
			response = getRuteo(loc, headers)
		except Exception as e:
			isRuteoOK = False
			raise
			break
		resultado = response.json()
		total_time = resultado['routes'][0]['duration']
		total_distance = resultado['routes'][0]['distance']
		# Verificar si esta dentro o fuera de CABA el destino
		# si el ultimo punto esta fuera de caba se calcula el retorno
		try:
			destinoInCABA = destinoIsInCaba(destino, headers)
			print("destinoInCABA es", destinoInCABA)
		except Exception as e:
			print('Error al buscar si destino es en CABA', e)
			raise
			break
		if (destinoInCABA is False):
			
			# Consultar punto de retorno a CABA
			try:
				response = getRetornoCABA(destino, headers)
				list(response)
			except Exception as e:
				mensaje_error = 'No se recibio respuesta de Retorno a CABA\n'
				print(type(e))
				print(mensaje_error, e)
				isRetornoOK = False
				raise
				break

			# Formateando el punto de retornoCABA para el ruteo
			try:
				resultado_du = response
				retornoCABA = (resultado_du['latitud'], resultado_du['longitud'])
			except Exception as e:
				mensaje_error = 'La respuesta de Retorno a CABA no continene latitud y/o longitud:'
				print(mensaje_error, e)
				isRetornoOK = False
			# Si las coordenadas de retorno se recibieron bien, solicito ruteo hasta el retorno a CABA
			if(isRetornoOK):
				ruteoRetornoCABA = [destino]
				ruteoRetornoCABA.append([retornoCABA[0], retornoCABA[1], str(retornoCABA[0] + "," + retornoCABA[1])])
				try:
					response = getRuteo(ruteoRetornoCABA, headers)
				except Exception as e:
					isRuteoOK = False
					mensaje_error = 'La respuesta del ruteo hasta Retorno a CABA no respondio: '
					raise
					break
				resultado = response.json()
				retorno_caba_distance = resultado['routes'][0]['distance']
				retorno_caba_time = resultado['routes'][0]['duration']
			else:
				resultado_json = getResultadoEnCero()
				resultado_json["mensaje"] = mensaje_error
				return resultado_json
			# La coordenada de retorno está bien construida
		#el destino estuvo dentro de caba
		else:
			retorno_caba_time = 0
			retorno_caba_distance = 0

		resultado_json = {}
		
		if(isRuteoOK):
			resultado_json["total_tiempo"] = total_time
			resultado_json["total_distancia"] = total_distance
			resultado_json["retorno_caba_tiempo"] = retorno_caba_time
			resultado_json["retorno_caba_distancia"] = retorno_caba_distance
			if gml=='1':
				print('resultado gml')
				resultado_json["gml"] = resultado
			return resultado_json
			#return JsonResponse(resultado_json)
		else:
			resultado_json = getResultadoEnCero()
			resultado_json["mensaje"] = mensaje_error
		# se preparo el calculo de ruteo con valores o en cero
	# Fin de mecanismo while para cortar la ejecucion frente a errores

	return resultado_json
def getResultadoEnCero():
	resultado_json = {}
	# Ruteo no esta OK
	# Asegurar una respuesta y fin de consulta limpia
	# Si no se puede calcular el retorno no enviar costos
	resultado_json["total_tiempo"] = 0
	resultado_json["total_distancia"] = 0
	resultado_json["retorno_caba_tiempo"] = 0
	resultado_json["retorno_caba_distancia"] = 0
	resultado_json["mensaje"] = ''
	return resultado_json
def consultarCalculoRuta(request):
	'''
	Recibe la peticion de ruteo y valida que el formato sea correcto
	Si el request es correcto envía los datos para su calculo
	Formato:
	origen=x,y&punto1=x,y&punto2=x,y&punto3=x,y&destino=x,y
	varialble requerida: origen, destino
	variable opcional: punto1, punto2, punto3
	'''
	resultado_json = {}
	requestOk = False
	datos = []

	if (request.POST):
		#incluir el header crsf en la llamada ajax
		origen = request.POST.getlist('origen')
		parada1 = request.POST.getlist('parada1')
		parada2 = request.POST.getlist('parada2')
		parada3 = request.POST.getlist('parada3')
		destino = request.POST.getlist('destino')
		gml = request.POST.getlist('gml')
	else:
		origen = request.GET.getlist('origen')
		parada1 = request.GET.getlist('parada1')
		parada2 = request.GET.getlist('parada2')
		parada3 = request.GET.getlist('parada3')
		destino = request.GET.getlist('destino')
		gml = request.GET.get('gml')

	# verifica que request tenga origen y destino y que todas las coordenadas 
	# tengan 2 valores separados por comas
	response = verifcarRequestCoords(origen, destino, parada1, parada2, parada3)

	datos = response['datos']
	if(response['requestOk']):
		#gml = True
		print('gmll crudo')
		print(gml)
		# Consultar ruteo y distancia
		try:
			resultado_json = armarRespuestaPuntos(datos,gml)
		except TypeError as e:
			print(type(e))
			mensaje_error = 'No se recibio respuesta de Retorno a CABA, repita la consulta en otro momento'
			resultado_json = getResultadoEnCero()
			resultado_json['mensaje'] = mensaje_error
		except KeyError as e:
			print(type(e))
			mensaje_error = 'No se obutvo duration y/o distance del servidor de ruteo, repita la consulta en otro momento'
			resultado_json = getResultadoEnCero()
			resultado_json['mensaje'] = mensaje_error
		except AttributeError as e:
			print(type(e))
			resultado_json = getResultadoEnCero()
			resultado_json['mensaje'] = 'Respuesta no recibida de destino en CABA'
			print(resultado_json)
		except Exception as e:
			mensaje_error = str(e)
			print(type(e))
			print(resultado_json)
			resultado_json = getResultadoEnCero()
			resultado_json['mensaje'] = mensaje_error
		return JsonResponse(resultado_json)
	else:
		resultado_json["mensaje"] = response['mensaje_error']
		resultado_json["error"] = True
		return JsonResponse(resultado_json)
def verifcarRequestCoords(origen, destino, parada1, parada2, parada3):
	datos = []
	mensaje_error = ''
	requestOk = False
	response = {}

	if(len(origen) and len(destino)):
		origenLatLon = origen[0].split(',')
		destinoLatLon = destino[0].split(',')
		# verifica que origen y destino tenga exactamente 2 coordenadas separadas por coma
		while(len(origenLatLon) == 2 and len(destinoLatLon) == 2):
			try:
				punto =  Point(float(origenLatLon[1]), float(origenLatLon[0]), srid = 4326)
				datos.append(origenLatLon[0])
				datos.append(origenLatLon[1])
				origenLatLon.pop() # origenLatLon ya no tiene 2 elementos y termina el while
			except Exception as e:
				mensaje_error = 'El valor de origen no es correcto. Por favor verifique los valores.'
				print(mensaje_error, e)
				break
				raise Exception(mensaje_error)
			try:
				destinoLatLon[0].replace(" ", "")
				destinoLatLon[1].replace(" ", "")
				punto =  Point(float(destinoLatLon[1]), float(destinoLatLon[0]), srid = 4326)
				datos.append(destinoLatLon[0])
				datos.append(destinoLatLon[1])
				destinoLatLon.pop() # destinoLatLon ya no tiene 2 elementos y termina el while
			except Exception as e:
				mensaje_error = 'El valor de destino no es correcto. Por favor verifique los valores.'
				print(mensaje_error, e)
				break
				raise Exception(mensaje_error)
			requestOk = True
				
			# verificando valores de paradas intermedias para validar cada punto
			paradas = [ parada3, parada2, parada1, ]
			for coord in paradas:
				# si hay un string en parada1 o parada2 o parada3 se analiza
				if(len(coord) == 1):
					coordLatLon = coord[0].split(',')
					# si se tienen 2 coordenadas en el punto se agregan al listado de validacion de punto
					if(len(coordLatLon) == 2):
						datos.insert(2, coordLatLon[1])
						datos.insert(2, coordLatLon[0])
					# se agregó una coordenada al listado de coordenas
				# se termino de parsear una coordenada
			# se termino de analizar las 3 coordenadas
		# fin de while que se usa para cortar la ejecucion frente a un error
	else:
		mensaje_error = 'No pudimos determinar el origen y/o destino. Por favor verifique el formato de la petición'
	response['mensaje_error'] = mensaje_error
	response['datos'] = datos
	response['requestOk'] = requestOk
	return response

def verifcarRequestCoords_old(origen, destino, parada1, parada2, parada3):
	datos = []
	mensaje_error = ''
	requestOk = False
	response = {}

	if(len(origen) and len(destino)):
		origenLatLon = origen[0].split(',')
		destinoLatLon = destino[0].split(',')
		# verifica que origen y destino tenga exactamente 2 coordenadas separadas por coma
		if(len(origenLatLon) == 2 and len(destinoLatLon) == 2):
			datos.append(origenLatLon[0])
			datos.append(origenLatLon[1])
			datos.append(destinoLatLon[0])
			datos.append(destinoLatLon[1])
			requestOk = True

			# verificando valores de paradas intermedias para validar cada punto
			paradas = [ parada3, parada2, parada1, ]
			for coord in paradas:
				# si hay un string en parada1 o parada2 o parada3 se analiza
				if(len(coord) == 1):
					coordLatLon = coord[0].split(',')
					# si se tienen 2 coordenadas en el punto se agregan al listado de validacion de punto
					if(len(coordLatLon) == 2):
						datos.insert(2, coordLatLon[1])
						datos.insert(2, coordLatLon[0])
		else:
			mensaje_error = 'El valor de origen y/o destino no es correcto. Por favor verifique los valores.'
	else:
		mensaje_error = 'No pudimos determinar el origen y/o destino. Por favor verifique el formato de la petición'
	response['mensaje_error'] = mensaje_error
	response['datos'] = datos
	response['requestOk'] = requestOk
	return response

def consultarCalculoRutaTarifa(request):
	'''
	Recibe la peticion de ruteo y valida que el formato sea correcto
	Si el request es correcto envía los datos para su calculo
	Formato:
	origen=x,y&punto1=x,y&punto2=x,y&punto3=x,y&destino=x,y
	input: 
			varialble requerida: origen, destino, cant_pasajero y cant_equipaje
			variable opcional: punto1, punto2, punto3
	output:
		total_tiempo, total_distancia, retorno_caba_tiempo, 
		retorno_caba_distancia, total_tarifa, retorno_caba_tarifa
	'''
	
	if (request.POST):
		#incluir el header crsf en la llamada ajax
		origen = request.POST.getlist('origen')
		parada1 = request.POST.getlist('parada1')
		parada2 = request.POST.getlist('parada2')
		parada3 = request.POST.getlist('parada3')
		destino = request.POST.getlist('destino')
		cant_equipaje = request.POST.getlist('cant_equipaje')
		cant_pasajero = request.POST.getlist('cant_pasajero')
		gml = request.POST.getlist('gml')
	else:
		origen = request.GET.getlist('origen')
		parada1 = request.GET.getlist('parada1')
		parada2 = request.GET.getlist('parada2')
		parada3 = request.GET.getlist('parada3')
		destino = request.GET.getlist('destino')
		cant_equipaje = request.GET.getlist('cant_equipaje')
		cant_pasajero = request.GET.getlist('cant_pasajero')
		gml = request.GET.get('gml')

	cant_equipaje = cant_equipaje[0] if len(cant_equipaje) > 0 else 0
	cant_pasajero = cant_pasajero[0] if len(cant_pasajero) > 0 else 0

	resultado_json = {}
	# verifica que request tenga origen y destino y que todas las coordenadas 
	# tengan 2 valores separados por comas
	response = verifcarRequestCoords(origen, destino, parada1, parada2, parada3)
	print(response)
	datos = response['datos']

	if(response['requestOk']):
		#gml = True
		isCostoOK = False
		print('gmll crudo')
		print(gml)
		validarRespuestas = True
		# Se utiliza el while como mecanismo para cortar la ejecucion
		# frente a una respuesta con error
		while validarRespuestas:
			try:
				resultado_json = armarRespuestaPuntos(datos,gml)
				validarRespuestas = False
			except KeyError as e:
				print(type(e))
				print("e ...", e)
				mensaje_error = 'No se obutvo duration y/o distance del servidor de ruteo, repita la consulta en otro momento'
				resultado_json = getResultadoEnCero()
				resultado_json['mensaje'] = mensaje_error
				validarRespuestas = False
				break
			except AttributeError as e:
				print(type(e))
				resultado_json = getResultadoEnCero()
				resultado_json['mensaje'] = 'Respuesta no recibida de destino en CABA'
				validarRespuestas = False
				break
			except TypeError as e:
				print(type(e))
				mensaje_error = 'No se recibio respuesta de Retorno a CABA, repita la consulta en otro momento'
				resultado_json = getResultadoEnCero()
				resultado_json['mensaje'] = mensaje_error
			except Exception as e:
				#mensaje_error = 'No se obutvo respuesta de una API externa, repita la consulta en otro momento'
				mensaje_error = str(e)
				print(type(e), e)
				print(mensaje_error)
				resultado_json = getResultadoEnCero()
				resultado_json['mensaje'] = mensaje_error
				validarRespuestas = False
				break

			# Calcular el costo del viaje
			if(resultado_json['total_distancia'] > 0):
				try:
					costoParam = dict(distancia = resultado_json['total_distancia'], cant_equipaje = cant_equipaje, isRetorno = False)
					total_tarifa = getCostoViajeTaxi(costoParam)
					isCostoOK = True
					validarRespuestas = False
				except Exception as e:
					mensaje_error += '\nNo se recibió el costo hasta destino'
					print(mensaje_error+str(e))
					isCostoOK = False
					validarRespuestas = False
					break
				# se agregó el costo del recorrido a la respuesta
			else:
				total_tarifa = 0
				isCostoOK = False
			# se resolvio si se calcula el costo o no

			print(resultado_json['retorno_caba_distancia'])
			# Calcular el costo del retorno a CABA
			if(resultado_json['retorno_caba_distancia'] > 0):
				try:
					costoParam = dict(distancia = resultado_json['retorno_caba_distancia'], isRetorno = True)
					retorno_caba_tarifa = getCostoViajeTaxi(costoParam)
					validarRespuestas = False
				except Exception as e:
					mensaje_error += '\nNo se recibió el costo de retorno a CABA'
					print(mensaje_error, e)
					resultado_json = getResultadoEnCero()
					resultado_json['total_tarifa'] = 0
					resultado_json['retorno_caba_tarifa'] = 0
					resultado_json['error'] = True
					isCostoOK = False
					validarRespuestas = False
					break
			else:
				retorno_caba_tarifa = 0
				validarRespuestas = False

		# fin de validarRespuestas
		print(isCostoOK)
		if(isCostoOK):
			resultado_json["total_tarifa"] = total_tarifa
			resultado_json["retorno_caba_tarifa"] = retorno_caba_tarifa
		else:
			# Si isCostoOK = False resultado_json ya tiene mensaje preparado
			# seteo en cero tarifa_total y retorno_caba_tarifa
			resultado_json["total_tarifa"] = 0
			resultado_json["retorno_caba_tarifa"] = 0
		return JsonResponse(resultado_json)
	else:
		resultado_json = getResultadoEnCero()
		#mensaje_error = 'No se recibio el origen o el destino en el formato correcto'
		resultado_json['total_tarifa'] = 0
		resultado_json['retorno_caba_tarifa'] = 0
		resultado_json['mensaje'] = response['mensaje_error']
		resultado_json['error'] = True
		return JsonResponse(resultado_json)

def prepararMensajeRuteo(loc):
	"""
	Prepara el string para la consulta del ruteo
	"""
	mensaje ='/'
	print(type(loc))
	j = 0
	for i in loc:
		if j < len(loc):
			print(loc)
			mensaje = mensaje + loc[j][1] + "," + loc[j][0]
			print(mensaje)
		if(len(loc) > j + 1):
			mensaje = mensaje + ';' # la última coordenada no lleva ;
		j = j + 1
	mensaje = mensaje + '?overview=full&geometries=geojson'
	return mensaje
def prepararMensajeRuteo_old(loc):
	"""
	Prepara el string para la consulta del ruteo
	"""
	mensaje ='?output=json'
	j = 0
	for i in loc:
		if j < len(loc):
			mensaje = mensaje + '&loc=' + loc[j][2]
		j = j + 1
		# linea original de armado
		# mensaje = '?output=json&loc=' + loc[0][2] + '&loc=' + loc[1][2] + '&loc=' + loc[2][2] + '&loc=' + loc[3][2] +'&loc=' + loc[4][2] +  '&loc=' + loc[5][2]
	return mensaje
def getRuteo(loc, headers):
	"""
	Ejecuta la consulta a la ruta a la API de ruteo
	y controla que la respuesta tenga los datos requeridos
	"""
	validandoRespuesta = True
	mensaje = prepararMensajeRuteo(loc)
	# Realizamos la consulta
	url = server + mensaje
	print(url)
	while validandoRespuesta:
		try:
			response = requests.request('GET', url, headers=headers, allow_redirects=False)
			validandoRespuesta = False
		except Exception as e:
			print ('No se recibió respuesta de API Ruteo externa: ', e)
			validandoRespuesta = False
			raise Exception("No se recibió respuesta del server de Ruteo")
			break
		try:
			resultado = response.json()
			if(resultado["code"] == "InvalidQuery"):
				print(resultado["message"])
				raise Exception(resultado["message"])
				break
			print('distancia ')
			print(resultado['routes'][0]['duration'])
			print(resultado['routes'][0]['distance'])
			total_time = resultado['routes'][0]['duration']
			total_distance = resultado['routes'][0]['distance']
			validandoRespuesta = False
		except KeyError as e:
			print('No se recibio el valor duration y/o distance de la API de ruteo externa: ', e)
			print(type(e), e)
			validandoRespuesta = False
			raise
			break
		#respuesta validada
		return response
	# fin de while para cortar la ejecucion frente a un error

def getRuteo_old(loc, headers):
	"""
	Ejecuta la consulta a la ruta a la API de ruteo
	y controla que la respuesta tenga los datos requeridos
	"""
	validandoRespuesta = True
	mensaje = prepararMensajeRuteo(loc)
	# Realizamos la consulta
	url = server + mensaje
	while validandoRespuesta:
		try:
			response = requests.request('GET', url, headers=headers, allow_redirects=False)
			validandoRespuesta = False
		except Exception as e:
			print ('No se recibió respuesta de API Ruteo externa: ', e)
			validandoRespuesta = False
			raise
			break
		try:
			resultado = response.json()
			total_time = resultado['route_summary']['total_time']
			total_distance = resultado['route_summary']['total_distance']
			validandoRespuesta = False
		except KeyError as e:
			print('No se recibio el valor duration y/o distance de la API de ruteo externa: ', e)
			print(type(e))
			validandoRespuesta = False
			raise
			break
		#respuesta validada
		return response
	# fin de while para cortar la ejecucion frente a un error

def destinoIsInCaba(destino, headers):
	"""
	Consulta si el destino se encuentra dentro de CABA
	o si se debe calcular los costos de retorno a CABA
	"""
	x, y, srid = destino[1], destino[0], 97433
	try:
		comuna = Comuna.busquedaGeografica(x, y, srid, 0)
		# Si comuna no es string, entonces comuna.upper() da error 
		# y la busqueda geografica tuvo fallas, se captura excepcion
		# Si no se encontro una interseccion el metodo devuelve un string vacio
		test = comuna.upper()
	except Exception as e:
		print('No se recibio respuesta sobre la informacion de la comuna')
		raise
	try:
		if(comuna == ' '):
			destinoInCABA = False
		else:
			destinoInCABA = True
	except Exception as e:
		print(type(e))
		print('La respuesta sobre pudo incluir el campo la comuna')
	return destinoInCABA

def getRetornoCABA(destino, qheaders):
	"""
	Consultar el punto de retorno a CABA
	mas cercano al destino
	"""
	# Composición del punto
	x, y, srid = destino[1], destino[0], 97433
	retorno = Ruteo.busquedaGeografica(x, y, srid, 0)
	return retorno

def getBandaHoraria():
	Hora = datetime.datetime.now().time()
	if(Hora > inicio_servicio_diurno and Hora < inicio_servicio_nocturno):
		return 'diurna'
	else:
		return 'nocturna'
def getCostoViajeTaxi(costoParam) :
	'''
	Se calcula el costo diurno y nocturno
	debido a que el horario del calculo y del inicio del viaje
	puede diferir, por ahora se devuelve el costo de acuerdo al horario
	de la consulta para dedicir que hacer en la proxima etapa

	input: dict(distancia: num [isRetorno: True|Fals , cant_equipaje: num])
	'''
	total_distancia = costoParam['distancia']
	isRetorno = costoParam.get(isRetorno) if "isRetrno" in costoParam else False
	cant_equipaje = int(costoParam['cant_equipaje']) if "cant_equipaje" in costoParam else 0
	costo = 0
	tarifa_diurna_en_centavos = valor_ficha_diurna * 100
	tarifa_nocturna_en_centavos = valor_ficha_nocturna * 100

	# cada distancia_por_ficha se cobra una nueva ficha
	# si total_distancia es igual a distancia_por ficha cant_fichas es 1
	# si total_distancia es el doble de distancia_por_ficha cant_fichas es 2
	# si cant_fichas no es entero se redondea para arriba
	# La primer ficha no se cobra, solo se cobra bajada de bandera
	cant_fichas = math.ceil(total_distancia / distancia_por_ficha)
	costo_diurno_sin_bajada_bandera = ((tarifa_diurna_en_centavos * cant_fichas) - tarifa_diurna_en_centavos) / 100 # se descuenta el valor de una ficha, la primera no se cobra
	costo_nocturno_sin_bajada_bandera = ((tarifa_nocturna_en_centavos * cant_fichas ) - tarifa_diurna_en_centavos) / 100  # se descuenta el valor de una ficha, la primera no se cobra
	if(isRetorno == True):
		# en el retorno no hay bajada de bandera y se cobra la primer ficha
		costo_diurno = (tarifa_diurna_en_centavos * cant_fichas) / 100 
		costo_nocturno = (tarifa_nocturna_en_centavos * cant_fichas) / 100
	else:
		costo_diurno = costo_diurno_sin_bajada_bandera + bajada_bandera_diurna
		costo_nocturno = costo_nocturno_sin_bajada_bandera + bajada_bandera_nocturna
		if(cant_equipaje > 1):	
			# si solo tiene un equipaje no se le aplica el costo
			# Por cada equipaje adicional se suma el valor de 5 fichas
			equipaje_a_cobrar = cant_equipaje - 1
			costo_diurno = costo_diurno + valor_ficha_diurna * 5 * equipaje_a_cobrar
			costo_nocturno = costo_nocturno + valor_ficha_nocturna * 5 * equipaje_a_cobrar
		# Se calculo el costo hasta destino y se suma el equipaje
	# Se calculo tanto el viaje hasta destino como hasta retorno a CABA
	costo_diurno += costo_diurno * porcentaje_diurno_ajuste / 100
	costo_nocturno += costo_nocturno * porcentaje_nocturno_ajuste / 100
	if(getBandaHoraria() == 'diurna'):
		costo = costo_diurno
	else:
		costo = costo_nocturno
	return costo