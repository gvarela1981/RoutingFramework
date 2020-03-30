
from django.http import JsonResponse
import requests
from django.shortcuts import render

#Server de ruteo
server = 'https://ruteo.usig.buenosaires.gob.ar/auto/viaroute'
#server datos utiles
server_datos_utiles = 'https://ws.usig.buenosaires.gob.ar/datos_utiles/'
#Server autopista
server_no_autopista = 'http://ruteo.eastus2.cloudapp.azure.com/auto/nearest/v1/driving/'
#Server de retorno a caba
server_retorno_caba = 'https://epok.buenosaires.gob.ar/ruteo/buscarInformacionRuteo/'

#Puntos de la busqueda
def ingresarPuntos(request):
    #return JsonResponse({'santi': 'ssssss'})
    return render(request, 'ingresopuntos/ingresopuntos.html', {})
def parseoPuntos():

    punto1 = ['-34.591759'],['-58.372200']

    #Puntos intermedios
    punto2 = ['-34.600952'],['-58.408592']
    punto3 = ['-34.602409'],['-58.442024']
    punto4 = ['-34.605519'],['-58.459969']

    #Punto Final dentro de CABA
    punto5 = ['-34.630768'],['-58.456005']


    #Punto Final Fuera de CABA
    punto6 = ['-34.569041'],['-58.528976']

    puntos = [punto1,punto2,punto3,punto4,punto5,punto6]
    loc = []
    punto=""
    return puntos

def santi(request):
    #return HttpResponse('Hola como andas')
    return JsonResponse({'santi': 'sksksks'})
def taxi(request):
    #url = server_no_autopista + i[1][0] + ',' + i[0][0] + '?exclude=motorway'
    #response = requests.request('GET', url, headers=headers, allow_redirects=False)
    #return JsonResponse({'santi': request})
    if (request):
        punto1Lat = request.GET['punto1Lat']

        punto1Lon = request.GET['punto1Lon']
        punto2Lat = request.GET['punto2Lat']
        punto2Lon = request.GET['punto2Lon']
        punto3Lat = request.GET['punto3Lat']
        punto3Lon = request.GET['punto3Lon']
        punto4Lat = request.GET['punto4Lat']
        punto4Lon = request.GET['punto4Lon']
        punto5Lat = request.GET['punto5Lat']
        punto5Lon = request.GET['punto5Lat']
        punto6Lat = request.GET['punto6Lat']
        punto6Lon = request.GET['punto6Lon']
        punto1 = [punto1Lat], [punto1Lon]

        # Puntos intermedios
        punto2 = [punto2Lat], [punto2Lon]
        punto3 = [punto3Lat], [punto3Lon]
        punto4 = [punto4Lat], [punto4Lon]

        # Punto Final dentro de CABA
        punto5 = [punto5Lat], [punto5Lon]

        # Punto Final Fuera de CABA
        punto6 = [punto6Lat], [punto6Lon]

        puntos = [punto1, punto2, punto3, punto4, punto5, punto6]
        print(puntos)
       # print(s)
    print('entró')
    loc = []
    punto = ""
   # puntos = parseoPuntos()

    print(puntos)
    for i in puntos:
        url = server_no_autopista + i[1][0] + ',' + i[0][0] + '?exclude=motorway'

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request('GET', url, headers=headers, allow_redirects=False)

        resultado_du = response.json()

        punto_chequeado = resultado_du['waypoints'][0]['location']

        punto = [str(punto_chequeado[1]), str(punto_chequeado[0]),
                 str(punto_chequeado[1]) + ',' + str(punto_chequeado[0])]

        loc.append(punto)

    # Composición de la url
    url = server + '?output=json&loc=' + loc[0][2] + '&loc=' + loc[1][2] + '&loc=' + loc[2][2] + '&loc=' + loc[3][
        2] + '&loc=' + loc[5][2]

    headers = {
        'Content-Type': 'application/json'
    }

    # Realizamos la consulta
    response = requests.request('GET', url, headers=headers, allow_redirects=False)
    # print(response.text)

    resultado = response.json()

    total_time = resultado['route_summary']['total_time']
    total_distance = resultado['route_summary']['total_distance']

    # Verificar si esta dentro o fuera de CABA

    # Composición de la url
    # direc = loc[5].split(',')

    url = server_datos_utiles + '?x=' + loc[5][1] + '&y=' + loc[5][0]

    # Realizamos la consulta
    response = requests.request('GET', url, headers=headers, allow_redirects=False)

    resultado_du = response.json()

    comuna = resultado_du['comuna']

    # partido = resultado_du['partido_amba']

    if (comuna == ''):

        # Consultar punto de retorno a CABA

        url_punto_retorno = server_retorno_caba + '?x=' + loc[5][1] + '&y=' + loc[5][0] + '&formato=geojson'

        # Realizamos la consulta de punto de retorno a CABA

        response = requests.request('GET', url_punto_retorno, headers=headers, allow_redirects=False)

        resultado_du = response.json()

        punto_acceso_caba = resultado_du[0]["latitud"] + ',' + resultado_du[0]["longitud"]

        print('debaguear')
        print(punto_acceso_caba)

        # Composición de la url
        url_ruteo_retorno = server + '?output=json&loc=' + loc[5][2] + '&loc=' + punto_acceso_caba

        # Realizamos la consulta
        response = requests.request('GET', url_ruteo_retorno, headers=headers, allow_redirects=False)
        # print(response.text)

        resultado = response.json()

        retorno_caba_distance = resultado['route_summary']['total_distance']
        retorno_caba_time = resultado['route_summary']['total_time']


    else:
        retorno_caba_time = 0
        retorno_caba_distance = 0

    resultado_json = {}

    resultado_json["total_time"] = total_time
    resultado_json["total_distance"] = total_distance
    resultado_json["return_caba_time"] = retorno_caba_time
    resultado_json["return_caba_distance"] = retorno_caba_distance

    resul = resultado_json
    print(resul)
    return JsonResponse(resul)