"""totem_taxi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
#from taxi import views
from api_ruteadora import views

urlpatterns = [
  path('api_ruteadora/', include('api_ruteadora.urls')),
  path('admin/', admin.site.urls),
  path('calculo_ruta', views.consultarCalculoRuta), #api de consulta GET o POST, recibe variables origen y destino como string con coordenadas x,y en srid=4326, opcionalmente parada1, parada2 y parada3
  path('calculo_ruta_tarifa', views.consultarCalculoRutaTarifa), #api de consulta GET o POST, recibe variables origen y destino como string con coordenadas x,y en srid=4326 junto con cant_equipaje y cant_pasajero, opcionalmente parada1, parada2 y parada3
  #path('puntos',views.ingresarPuntos),
  ]
