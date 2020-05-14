
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
        
        # Calcular el costo del retorno a CABA
        try:
            retorno_caba_tarifa = getCostoViaje(retorno_caba_distance)
        except Exception as e:
            mensaje_error += '\nNo se recibió el costo de retorno a CABA'
            print(mensaje_error+str(e))
            isRuteoOK = False

    #el punto final esta dentro de caba
    else:
        retorno_caba_time = 0
        retorno_caba_distance = 0
        retorno_caba_tarifa = 0

    resultado_json = {}
    if(isRuteoOK):
        # Calcular el costo del viaje
        total_cost = getCostoViaje(total_distance)

        resultado_json["total_time"] = total_time
        resultado_json["total_distance"] = total_distance
        resultado_json["return_caba_time"] = retorno_caba_time
        resultado_json["return_caba_distance"] = retorno_caba_distance
        resultado_json["total_tiempo"] = total_time
        resultado_json["total_distancia"] = total_distance
        resultado_json["retorno_caba_tiempo"] = retorno_caba_time
        resultado_json["retorno_caba_distancia"] = retorno_caba_distance
        resultado_json["total_tarifa"] = total_cost
        resultado_json["retorno_caba_tarifa"] = retorno_caba_tarifa
        if gml=='1':
            resultado_json["gml"] = resultado

        resul = resultado_json
        print(resul)

        return JsonResponse(resul)
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

def consultarPuntos(request):
	'''
	Recibe la peticion de ruteo y valida que el formato sea correcto
	Si el request es correcto envía los datos para su calculo
	Formato:
	origen=x,y&punto1=x,y&punto2=x,y&punto3=x,y&destino=x,y
	'''
	requestOk = False
	datos = []

	if (request.POST):
		#incluir el header crsf en la llamada ajax
		origen = request.POST.getlist('origen')
		punto1 = request.POST.getlist('punto1')
		punto2 = request.POST.getlist('punto2')
		punto3 = request.POST.getlist('punto3')
		destino = request.POST.getlist('destino')
		gml = request.POST.getlist('gml')
	else:
		origen = request.GET.getlist('origen')
		punto1 = request.GET.getlist('punto1')
		punto2 = request.GET.getlist('punto2')
		punto3 = request.GET.getlist('punto3')
		destino = request.GET.getlist('destino')
		gml = request.GET.get('gml')
	
	# verifica que request tenga origen y destino
	if(len(origen) and len(destino)):
		print('hay origen y destino')
		origenLatLon = origen[0].split(',')
		destinoLatLon = destino[0].split(',')
		# verifica que origen y destino tenga exactamente 2 coordenadas separadas por coma
		if(len(origenLatLon) == 2 and len(destinoLatLon) == 2):
			datos.append(origenLatLon[0])
			datos.append(origenLatLon[1])
			datos.append(destinoLatLon[0])
			datos.append(destinoLatLon[1])
			requestOk = True
			print(datos)

			# verificando valores de paradas intermedias para validar cada punto
			paradas = [ punto3, punto2, punto1, ]
			for coord in paradas:
				# si hay un string en punto1 o punto2 o punto3 se analiza
				if(len(coord) == 1):
					coordLatLon = coord[0].split(',')
					# si se tienen 2 coordenadas en el punto se agregan al listado de validacion de punto
					if(len(coordLatLon) == 2):
						datos.insert(2, coordLatLon[1])
						datos.insert(2, coordLatLon[0])
		else:
			mensaje_error = 'El valor de origen y/o destino no es correcto. Por favor verifique los valores.'
			print(mensaje_error)
		
		print('datos')
		print(datos)
	else:
		mensaje_error = 'No se recibio datos de origen y/o destino.'

	if(requestOk):
	    #gml = True
		print('gmll crudo')
		print(gml)
		res = armarRespuestaPuntos(datos,gml)
		return res
	else:
	 	resultado_json["mensaje"] = mensaje_error
	 	resultado_json["error"] = True
	 	return resultado_json
def consultarPuntos_old(request):
    """Funcion que es llamada desde el ruteador con la url calculo_ruta. Filtra y analiza el contenido
    del request para que la llamada a los servidores de ruteo sea consistente.

    Args:
        ``request (array)``:  request que puede contener el verbo POST o GET, que es una coleccion
        de flotantes. Condicion: no puede contener menos de 4 parametros, ni mas de ``MAX_POINTS``.

        ``gml (int)`` : Entero (0,1) que determina si en el json de salida se agrega o no la traza
        calculada entregada por el server de ruteo en formato gml.

    Returns:
            ``json``
    """
    resultado_json = {}

    if (request.POST):
        #incluir el header crsf en la llamada ajax
        datos = request.POST.getlist('data[]')
        gml = request.POST.get('gml')
    else:
        datos = request.GET.getlist('data[]')
        gml = request.GET.get('gml')
    print('datos')
    print(len(datos))
    print(int(len(datos)/2))
    # este filtrado tambien contempla la posibilidad de que no se utilice el nombre de lista data[] en algun parametro
    # esta oriendado a un uso inadecuado por get desde el cgi
    if (len(datos) < 4):
        resultado_json["error"] = 'La llamada necesita al menos 2 coordenadas lat lon. Ej: http://$host/calculo_ruta?data[]=lat1&data[]=lon1&data[]=lat2&data[]=lon2&data[]=lat3&data[]=lon3&data[]=lat4&data[]=lon4&gml=1'
        resul = resultado_json
        return JsonResponse(resul)
    else:
        #mas de 2 coordenadas pero faltando un parametro, lat o lon
        if (len(datos)%2 != 0):
            resultado_json["error"] = 'La llamada no contiene una cantidad adecuada de pares ordenados'
            resul = resultado_json
            return JsonResponse(resul)
        else:
            # este error debe ser filtrado en el frontend especifico de este proyecto, ya que los demas errores
            # de coordenadas no podrian presentarse en el caso de la definicion de puntos por drawtool leaflet
            if (len(datos) / 2 > MAX_POINTS):
                resultado_json["error"] = 'No ingrese mas de 10 puntos'
                resul = resultado_json
                return JsonResponse(resul)
            else:
                #gml = True
                print('gmll crudo')
                print(gml)
                res = armarRespuestaPuntos(datos,gml)
                return res
    #else:
      #  resultado_json["error"] = 'Error en el request'
      #  resul = resultado_json
      #  return JsonResponse(resul)

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
def getCostoViaje(total_distance):
    '''
    Se retorna el costo diurno y nocturno
    debido a que el horario del calculo y del inicio del viaje
    puede diferir
    '''
    costo = 0
    tarifa_diurna_en_centavos = valor_ficha_diurna * 100
    tarifa_nocturna_en_centavos = valor_ficha_nocturna * 100

    costo_diurno_sin_bajada_bandera = ((tarifa_diurna_en_centavos * total_distance) / tarifa_diurna_en_centavos + distancia_por_ficha) / 100
    costo_nocturno_sin_bajada_bandera = ((tarifa_nocturna_en_centavos * total_distance) / tarifa_nocturna_en_centavos + distancia_por_ficha) / 100
    costo_diurno = costo_diurno_sin_bajada_bandera + bajada_bandera_diurna * porcentaje_diurno_ajuste
    costo_nocturno = (costo_nocturno_sin_bajada_bandera + bajada_bandera_diurna) * porcentaje_nocturno_ajuste
    
    if(getBandaHoraria() == 'diurna'):
        costo = costo_diurno
    else:
        costo = costo_nocturno
    return costo