# -*- coding: utf-8 -*-
import csv
from django.http import HttpResponse
#from shapes.views import ShpResponder
from datetime import datetime

def export_as_csv_action(file_name='', description="Exportar selección a CSV", fields=None, exclude=None, header=True, headers=None, encoding="utf-8"):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    http://djangosnippets.org/snippets/2369/
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/1697/
        """
        opts = modeladmin.model._meta
        field_names = [field.name for field in opts.fields]

        fields_finales = []
        if fields:
            for val in fields:
                if val=='*': 
                    fields_finales=fields_finales + field_names # sumo los originales
                if val in field_names or hasattr(modeladmin.model, val.replace('()','')):
                    fields_finales.append(val)
        else:
            fields_finales = field_names
        if exclude:
            fields_finales = [val for val in fields_finales if val not in exclude]
        
        response = HttpResponse(mimetype='text/csv')
        if file_name == '':
            csv_file_name = '%s.%s' % (str(opts), datetime.today().strftime("%Y%m%d"))
        else:
            csv_file_name = file_name
            
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % csv_file_name #unicode(opts).replace('.', '_')

        writer = csv.writer(response)
        if header:
            if headers and len(headers) == len(fields_finales):
                writer.writerow(list(headers))
            else:
                writer.writerow(list(fields_finales))

        for obj in queryset:
            writer.writerow([str(eval('obj.'+field)).encode(encoding,"replace") for field in fields_finales])

        return response
    export_as_csv.short_description = description
    return export_as_csv

def export_as_shape_action(file_name='', description="Exportar selección a Shape", geo_field=None):
    """
    Action para exportar un modelo a shape.
    Ej: en el admin del modelo poner:
        actions = [export_as_shape_action(description="Exportar Dir. laboral a shape", geo_field='dirlab_the_geom')]
    """
    def export_as_shape(modeladmin, request, queryset):
        try:
            if file_name == '':
                classname = modeladmin.model._meta
                shp_file_name = '%s.%s' % (classname, datetime.today().strftime("%Y%m%d"))
            else:
                shp_file_name = file_name
            shp_response = ShpResponder(queryset)
            shp_response.file_name = shp_file_name
            shp_response.geo_field = geo_field
#            modeladmin.message_user(request, u'La exportación a Shape se realizó con éxito.')
            return shp_response()
        except Exception as e:
            modeladmin.message_user(request, 'Se produjo un error en la exportación a Shape (%s).' % e)
    export_as_shape.short_description = description
    return export_as_shape

"""
Action para borrar objetos llamando a cada delete.
Ej: en el admin del modelo poner:
    actions = [really_delete_selected]
    y en el encabezado del archivo:
    from commons.actions import really_delete_selected
OJO: esta acción no tiene la pantalla intermedia de confirmación que tiene el delete por default
"""
def really_delete_selected(modeladmin, request, queryset):
        for obj in queryset:
            obj.delete()
        if queryset.count() == 1:
            message_bit = "1 objeto fue borrado con éxito"
        else:
            message_bit = "%s objetos fueron borrados con éxito" % queryset.count()
        modeladmin.message_user(request, message_bit)
really_delete_selected.short_description = "Borrar objetos seleccionados"


# función llamable desde los admins para factorizar los mensajes al usuario 
def armar_texto_resultante_de_accion(cant, str_accion, str_clase_singular='objeto', str_clase_plural='objetos'):
    if cant == 1:
        return '1 %s seteado como "%s"'%(str(str_clase_singular),str(str_accion))
    else:
        return '%s %s seteados como "%s"' % (str(cant), str(str_clase_plural), str(str_accion))

def setear_publicable(modeladmin, request, queryset):
    modeladmin.message_user(request, armar_texto_resultante_de_accion(queryset.update(publicable=True), 'Publicable'))
setear_publicable.short_description = 'Setear "Publicable"'

def setear_no_publicable(modeladmin, request, queryset):
    modeladmin.message_user(request, armar_texto_resultante_de_accion(queryset.update(publicable=False), 'No Publicable'))
setear_no_publicable.short_description = 'Setear "No Publicable"'

def setear_verificado(modeladmin, request, queryset):
    modeladmin.message_user(request, armar_texto_resultante_de_accion(queryset.update(verificado=True), 'Verificado'))
setear_verificado.short_description = 'Setear "Verificado"'

def setear_no_verificado(modeladmin, request, queryset):
    modeladmin.message_user(request, armar_texto_resultante_de_accion(queryset.update(verificado=False), 'No verificado'))
setear_no_verificado.short_description = 'Setear "No Verificado"'
