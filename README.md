Uso de api_manager
=====================================================================



    Procedimiento realizado en Ubuntu 18.04.1 LTS

* Tener instalada la ultima version de python, verificarla:

    - $ python3 --version

* Crear un directorio en donde se quiera crear el entorno virtual

    - $ mkdir entorno
    - $ cd entorno

* Tener instalada version de pip, verificar :

    - $ pip3 --version

* Si no se tiene instalar virtualenv:

    - $ virtualenv --version
    - $ sudo pip3 install virtualenv

* Crear entorno virtual

    - $ python3 -m venv mivenv

* Moverse a la carpeta raiz en donde creamos en entorno virtual, escribir la directiva:

    - $ . bin/activate

* Si todo funcionó bien veremos el prefijo (mienv) en la consola

* Verificar git:

    - $ git --version

* Clonar el proyecto:

    - $ git clone https://github.com/gvarela1981/RoutingFramework.git

* Pararse sobre la raiz de api_manage y ejecutar:

    - $ pip install -r requirements.txt
    
* Correr en docker :

    - $ docker-compose build
    - $ docker-compose up
        
* Si estamos trabajando con el IDE Pycharm, se puede arrancar el proyecto virtualizado de la siguiente manera:

    - Abrir el proyecto clonado File-Open...
    - Abrir File - Settings - Project api_manager - Project Interpreter.
    - Ir a la rueda de configuraciones y hacer click en Add.
    - Seleccionar el radio button Existing interpreter y buscar dentro del entorno virtual creado en la carpeta ./bin/ -> el interprete python3.
    - Almacenar los cambios y abrir una terminal dentro de pycharm, si todo esta correcto podremos ver que estamos trabajando en el entorno virtual.
    
* Consideraciones generales de uso:

    - El proyecto puede levantarse con su docker file.
    - Endpoint de calculo de ruta -> $host:\calculo_ruta
    - Ejemplo para el calculo de ruta:
      - En este caso se pasan hasta 3 pares de coordenadas lat lon en un request, si gml no se especifica o es igual a 0 devuelve un json
      http://$host/calculo_ruta?origen=-34.5947,-58.4858&parada1=-34.914821,-57.957681&parada2=-34.594289,-58.379221&parada3=-34.593021,-58.376647&destino=-34.5947,-58.485&cant_equipaje=3&gml=1
      - Lo que devolvera un json con los calculos de ruta mas un gml si es que lo requerimos en la llamada : {"total_tiempo": 7328.7, "total_distancia": 142339, "retorno_caba_tiempo": 0, "retorno_caba_distancia": 0, "ruteo": {"code": "Ok", "routes": [{ ... }]}
      - En este caso se pasan hasta 3 pares de coordenadas lat lon en un request y opcionalmente la cantidad de equipaje poque se tiene en cuenta para el calculo de tarifa, si gml no se especifica o es igual a 0 devuelve un json
      http://$host/calculo_ruta_tarifa?origen=-34.5947,-58.4858&parada1=-34.914821,-57.957681&parada2=-34.594289,-58.379221&parada3=-34.593021,-58.376647&destino=-34.5947,-58.485&gml=1
      - Lo que devolvera un json con los calculos de ruta mas un gml si es que lo requerimos en la llamada : {"total_tiempo": 7328.7, "total_distancia": 142339, "retorno_caba_tiempo": 0, "retorno_caba_distancia": 0, "ruteo": {"code": "Ok", "routes": [{ ... }]}, "total_tarifa": 5219.34, "retorno_caba_tarifa": 0}

    - El uso de un parametro vectorial en el request responde a la idea de hacer un servicio generico que pueda procesar una cantidad indeterminada de paradas, no obstante se determino un limite superior de 10 puntos de calculo.
    - El proyecto tambien consta de un endpoint http://$host/puntosMapa que permite el ingreso de puntos de manera grafica con una script de leaflet, esta script basicamente consume calculo_ruta por intermedio de ajax con el verbo POST, es recomendable por lo tanto tener el servicio corriendo bajo certificacion SSL para evitar bloqueos de CORS.
