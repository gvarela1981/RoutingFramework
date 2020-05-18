
"""
.. module:: views
   :platform: Unix, Windows
   :synopsis: Un modulo utilizable.

.. moduleauthor:: Mi Nombre <scastellano10@gmail.com>


"""


from django.http import JsonResponse
import requests
from django.shortcuts import render
#from modules.modules2.parametros import constantes
from django.conf import settings
# para implementar la vista de idex
from django.http import HttpResponse
from api_ruteadora.models import Endpoint, Costo, Ruteo, Comuna
import math

import json as simplejson
import datetime
# from commons.commons import aplicar_callback
# from commons.commons import armarEstructuraGeoLayer
from django.contrib.gis.geos import GEOSGeometry

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
    print(mensaje_error+str(e))
    isRuteoOK = False

# index

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

#render swagger de mapa de puntos taxi
def puntosmapa_sw(request):
    return render(request, 'ingresopuntos/puntosmapassw.html', {})
#Puntos de la busqueda
def ingresarPuntosMapa(request):
    """Funcion que randeriza el frontend para ingreso de puntos en leaflet y envio ajax hacia
    la url calculo_ruta->consultarPuntos. Es llamada desde el ruteador con la url puntosMapas.

    Args:
        ``request`` :  Sin uso.


    Returns:
        render html.
        """
    return render(request, 'ingresopuntos/index2.html', {})
def ingresarPuntos(request):
    #return JsonResponse({'santi': 'ssssss'})
    return render(request, 'ingresopuntos/ingresopuntos.html', {})

def validarPuntos(puntos, headers):
    locValidado = []
    for i in puntos:
        url = server_no_autopista + i[1] + ',' + i[0] + '?exclude=motorway'

        response = requests.request('GET', url, headers=headers, allow_redirects=False)

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
    isRuteoOK = True

    # valido los puntos ingresados
    loc = validarPuntos(puntos, headers)
    destino = loc[-1]

    try:
        response = getRuteo(loc, headers)
        resultado = response.json()
    except Exception as e:
        print('Ruteo no recibido'+str(e))
        isRuteoOK = False
    try:
        total_time = resultado['route_summary']['total_time']
        total_distance = resultado['route_summary']['total_distance']
    except Exception as e:
        print ('consulta rechazada en el server de ruteo: '+str(e))
        isRuteoOK = False

    # Verificar si esta dentro o fuera de CABA el ultimo punto
    # si el ultimo punto esta fuera de caba se calcula el retorno
    try:
        destinoInCABA = destinoIsInCaba(destino, headers)
        print("destinoInCABA es", destinoInCABA)
    except Exception as e:
        print('Respuesta no recibida de destino en CABA'+str(e))

    if (destinoInCABA is False):

        # Consultar punto de retorno a CABA
        try:
            response = getRetornoCABA(destino, headers)
            resultado_du = response 
        except Exception as e:
            print('No se recibio respuesta de Retorno a CABA'+str(e))
                
        # Formateando el punto de retornoCABA para el ruteo
        try:
            retornoCABA = (resultado_du['latitud'], resultado_du['longitud'])
        except Exception as e:
            print('La respuesta de Retorno a CABA no continene latitudo y/o longitud'+str(e))
            isRuteoOK = False

        ruteoRetornoCABA = [destino]
        ruteoRetornoCABA.append([retornoCABA[0], retornoCABA[1], str(retornoCABA[0] + "," + retornoCABA[1])])
        
        print('debaguear')

        try:
            response = getRuteo(ruteoRetornoCABA, headers)
            resultado = response.json()
        except Exception as e:
            print('No se recibió respuesta de Ruteo'+str(e))
            isRuteoOK = False
        print('resultado gml')

        try:
            retorno_caba_distance = resultado['route_summary']['total_distance']
            retorno_caba_time = resultado['route_summary']['total_time']
        except Exception as e:
            mensaje_error += '\nLa respuesta de Ruteo no continene la distancia o el tiempo total'
            print(mensaje_error+str(e))
            isRuteoOK = False

    #el punto final esta dentro de caba
    else:
        retorno_caba_time = 0
        retorno_caba_distance = 0

    resultado_json = {}
    if(isRuteoOK):
        
        resultado_json["total_time"] = total_time
        resultado_json["total_distance"] = total_distance
        resultado_json["return_caba_time"] = retorno_caba_time
        resultado_json["return_caba_distance"] = retorno_caba_distance
        resultado_json["total_tiempo"] = total_time
        resultado_json["total_distancia"] = total_distance
        resultado_json["retorno_caba_tiempo"] = retorno_caba_time
        resultado_json["retorno_caba_distancia"] = retorno_caba_distance
        if gml=='1':
            resultado_json["gml"] = resultado

        resul = resultado_json

        return resul
        #return JsonResponse(resul)
    else:
        # Asegurar una respuesta y fin de consulta limpia
        # Si no se puede calcular el retorno no enviar costos
        resultado_json["total_time"] = 0
        resultado_json["total_distance"] = 0
        resultado_json["return_caba_time"] = 0
        resultado_json["return_caba_distance"] = 0
        resultado_json["total_tiempo"] = 0
        resultado_json["total_distancia"] = 0
        resultado_json["retorno_caba_tiempo"] = 0
        resultado_json["retorno_caba_distancia"] = 0
        resultado_json["total_tarifa"] = 0
        resultado_json["retorno_caba_tarifa"] = 0
        resultado_json["mensaje"] = mensaje_error

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
		res = armarRespuestaPuntos(datos,gml)
		return JsonResponse(res)
	else:
	 	resultado_json["mensaje"] = mensaje_error
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
			print(mensaje_error)
	else:
		mensaje_error = 'No se recibio datos de origen y/o destino.'
		print(mensaje_error)
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
	datos = response['datos']
	requestOk = response['requestOk']

	print('requestOk =', requestOk)    
	if(requestOk):
	    #gml = True
	    isRuteoOK = False
	    print('gmll crudo')
	    print(gml)
	    res = armarRespuestaPuntos(datos,gml)
	    # Calcular el costo del viaje
	    try:
	    	costoParam = dict(distancia = res['total_distancia'], cant_equipaje = cant_equipaje, isRetorno = False)
	    	total_tarifa = getCostoViajeTaxi(costoParam)
	    	isRuteoOK = True
	    except Exception as e:
	    	mensaje_error += '\nNo se recibió el costo de retorno a CABA'
	    	print(mensaje_error+str(e))
	    	isRuteoOK = False

	    # Calcular el costo del retorno a CABA
	    if(res['retorno_caba_distancia'] > 0):
		    try:
		    	costoParam = dict(distancia = res['retorno_caba_distancia'], isRetorno = True)
	    		retorno_caba_tarifa = getCostoViajeTaxi(costoParam)
		    except Exception as e:
		    	mensaje_error += '\nNo se recibió el costo de retorno a CABA'
		    	print(mensaje_error+str(e))
		    	isRuteoOK = False
	    else:
	    	retorno_caba_tarifa = 0

	    if(isRuteoOK):
	    	res["total_tarifa"] = total_tarifa
	    	res["retorno_caba_tarifa"] = retorno_caba_tarifa
	    	return JsonResponse(res)
	    else:
	    	resultado_json["mensaje"] = mensaje_error
	    	resultado_json["error"] = True
	    	return JsonResponse(resultado_json)
	else:
		mensaje_error = 'No se recibio el origen o el destino en el formato correcto'
		resultado_json['mensaje'] = mensaje_error
		print(resultado_json['mensaje'])
		resultado_json['error'] = True
		return JsonResponse(resultado_json)

def prepararMensajeRuteo(loc):
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
    """
    mensaje = prepararMensajeRuteo(loc)
    url = server + mensaje
    # Realizamos la consulta
    response = requests.request('GET', url, headers=headers, allow_redirects=False)
    return response

def destinoIsInCaba(destino, headers):
    """
    Consulta si el destino se encuentra dentro de CABA
    o si se debe calcular los costos de retorno a CABA
    """
    x, y, srid = destino[1], destino[0], 97433
    comuna = Comuna.busquedaGeografica(x, y, srid, 0)
    if(comuna == ' '):
        destinoInCABA = False
    else:
        destinoInCABA = True
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

def buscarInformacionRuteo(request):
    try:

        callback = str(request.get('callback', ''))
        x = request.get('x', 0)
        y = request.get('y', 0)
        srid = request.get('srid', 4326)
        radio = request.get('radio', 0)
        orden = request.get('orden', 'distancia')
        limite = request.get('limite', 10)
        fullInfo = request.get('fullInfo', 'False')
        formato = request.get('formato', 'json')
        
        response = {"totalFull": 0, "instancias": [], 'total': 0}
        
        try:

            x = float(x)
            y = float(y)

            if not x != 0 or not y != 0:
                x = 0
                y = 0

        except Exception:
            x = 0
            y = 0

        try:
            srid = int(srid)

        except Exception:
            srid = 4326

        try:
            radio = float(radio)

            if radio > 0:
                if radio > 50:
                    radio = 1
            else:
                radio = 1

        except Exception:
            radio = 1

        try:
            limite = int(limite)

            if limite < 0:
                limite = 10

        except Exception:
            limite = 10
        
        punto = GEOSGeometry('SRID={2};POINT({0} {1})'.format(x, y, srid))

        if srid != settings.SRID:
            punto.transform(settings.SRID)

        objetos_ruteo = Ruteo.busquedaGeografica(x, y, srid, radio)

        obj = objetos_ruteo[0]

        latitud = obj.latitud
        longitud = obj.longitud
        

        instancia = {                
                "latitud" : latitud,
                "longitud" : longitud
        }

        response['instancias'].append(instancia)
        response['totalFull'] += 1
        response['total'] += 1

        if formato == 'geojson':

            if response['instancias']:
                res = response['instancias']
            # Implementar excepcion respuesta vacia
            else:
                res = armarEstructuraGeoLayer([], [], '', 'geojson')

            res = simplejson.dumps(res)
            #res = aplicar_callback(res, callback)
            return HttpResponse(res, mimetype="application/json")

        response_str = simplejson.dumps(response)
        #response = aplicar_callback(response, callback)
        #return HttpResponse(response, mimetype="application/json")
        return response['instancias']
    except Exception as e:
        response = simplejson.dumps({'error': e.__str__()})
        response = aplicar_callback(response, callback)
        return HttpResponse(response, mimetype="application/json")
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
        # en el retorno no hay bajada de bandera, se cobra la primer ficha
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
    costo_diurno += costo_diurno * porcentaje_diurno_ajuste / 100
    costo_nocturno += costo_nocturno * porcentaje_nocturno_ajuste / 100
    if(getBandaHoraria() == 'diurna'):
        costo = costo_diurno
    else:
        costo = costo_nocturno
    return costo