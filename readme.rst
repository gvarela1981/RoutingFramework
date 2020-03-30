Uso de api_manager
=====================================================================


.. note::
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

    - $ git clone http://git-asi.buenosaires.gob.ar/usig/api_manager.git

* Pararse sobre la raiz de api_manage y ejecutar:

    - $ pip install -r requirements.txt

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
        En este caso se pasan 2 pares ordenados lat lon en un request vectorial llamado data
        http://$host/calculo_ruta?data[]=-34.5947&data[]=-58.4858&data[]=-34.6069&data[]=-58.4937&data[]=-34.6038&data[]=-58.5119&data[]=-34.5902&data[]=-58.5288&gml=1
        - Lo que devolvera un json con los calculos de ruta mas un gml si es que lo requerimos en la llamada : {"total_time": 2713, "total_distance": 9377, "return_caba_time": 483, "return_caba_distance": 2248,
    - El uso de un parametro vectorial en el request responde a la idea de hacer un servicio generico que pueda procesar una cantidad indeterminada de paradas, no obstante se determino un limite superior de 10 puntos de calculo.
    - El proyecto tambien consta de un endpoint http://$host/puntosMapa que permite el ingreso de puntos de manera grafica con una script de leaflet, esta script basicamente consume calculo_ruta por intermedio de ajax con el verbo POST, es recomendable por lo tanto tener el servicio corriendo bajo certificacion SSL para evitar bloqueos de CORS.