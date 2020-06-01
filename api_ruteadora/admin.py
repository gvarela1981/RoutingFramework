#from django.contrib import admin
from django.contrib.gis import admin

# Register your models here.

from .models import Endpoint, Costo, Ruteo
from api_ruteadora.actions import setear_publicable, setear_no_publicable, setear_verificado, setear_no_verificado
from django import forms
from django.conf import settings
from .models import *
from django.contrib import messages
from leaflet.admin import LeafletGeoAdmin

#Panel de Control Ruteo
class RuteoAdmin(LeafletGeoAdmin):
    default_zoom = 1
    modifiable = True
    default_lon = 101780
    default_lat = 101900
    map_srid = settings.SRID

    fieldsets = [
        (u'Informacion básica', {'fields': ['nomoficial','latitud','longitud']}),
        #(u'Ubicación', {'fields': ['calle', 'altura', 'calle2', 'normalizar', 'geocodificar']}),
        (u'Informacion de la Ubicación', {'fields': ['the_geom']}),
        #('Misc', {'fields': ['observaciones_publicables', 'observaciones_privadas', 'timestamp_alta', 'timestamp_modificacion', 'publicable', 'verificado']})
        ]

    list_display = [f.name for f in Ruteo._meta.fields if f.name not in ('the_geom', 'normalizar', 'geocodificar')]
    list_display_links = ['nomoficial']
    readonly_fields = ('id','nomoficial')
    search_fields = ['nomoficial']
    ordering = ['id']
    list_filter = [ 'nomoficial']
    #date_hierarchy = 'id'
    actions = [setear_publicable, setear_no_publicable, setear_verificado, setear_no_verificado]
    
    def get_actions(self, request):
        actions = super(RuteoAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def save_model(self, request, obj, form, change):
        #forzar_normalizacion = 'calle' in form.changed_data or 'altura' in form.changed_data or 'calle2' in form.changed_data
        #resultadoOk, resultado = obj.save(forzar_normalizacion=forzar_normalizacion)
        resultadoOk, resultado = obj.save()
        if resultadoOk:
            self.message_user(request, resultado['texto'])
        else:
            messages.error(request, resultado['texto'])
        super(RuteoAdmin, self).save_model(request, obj, form, change)

class ComunaAdmin(LeafletGeoAdmin):
  default_zoom = 1
  modifiable = True
  default_lon = 101780
  default_lat = 101900
  map_srid = settings.SRID
  readonly_fields=('id', 'timestamp_alta', 'timestamp_modificacion')
  search_fields = ('nombre', 'nombre_original')
  fieldsets = [
      ('Informacion básica', {'fields': ['nombre','nombre_original', 'barrios']}),
      ('Informacion de la Ubicación',   {'fields': ['the_geom']}),
      ('Misc',   {'fields': ['observaciones_publicables', 'observaciones_privadas', 'timestamp_alta','timestamp_modificacion', 'publicable', 'verificado']})]
  list_display = [f.name for f in Comuna._meta.fields if f.name not in ('the_geom')]
  list_display_links = ['id', 'nombre']
  ordering = ["-id"]
  list_filter = ['publicable', 'verificado', ]
  date_hierarchy = 'timestamp_modificacion'
  actions = [setear_publicable, setear_no_publicable, setear_verificado, setear_no_verificado]

class CostoAdmin(admin.GeoModelAdmin):
  #do something
  fields = ('fecha_creacion', 'fecha_modificacion', 'fecha_inicio', 'fecha_fin', 'observacion', 'nombre', 'inicio_servicio_diurno', 'inicio_servicio_nocturno', 'bajada_bandera_diurna', 'bajada_bandera_nocturna', 'valor_ficha_diurna', 'valor_ficha_nocturna', 'porcentaje_diurno_ajuste', 'porcentaje_nocturno_ajuste', 'distancia_por_ficha')
  date_hierarchy = 'fecha_modificacion'
  readonly_fields=('fecha_creacion', 'fecha_modificacion')
  class Meta:
    model = Costo

  def save_model(self, request, obj, form, change):
    # bj.added_by = request.user ### guardar el usuario que modifica
    resultado = obj.save()
    print('El proceso de grabado responde: ', resultado)
    if resultado['resultadoOK']:
      print('respondiendo a usuario')
      print(resultado['texto'])
      try:
        self.message_user(request, resultado['texto'])
      except Exception as e:
        print('Fallo en admin.py CostoAdmin.save_model: ', e)
    else:
      messages.error(request, resultado['texto'])
      super(CostoAdmin, self).save_model(request, obj, form, change)

admin.site.register(Endpoint)
admin.site.register(Costo, CostoAdmin)
admin.site.register(Ruteo, RuteoAdmin)
admin.site.register(Comuna, ComunaAdmin)