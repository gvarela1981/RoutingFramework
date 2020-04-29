import sys
import os
import re
sys.path.append("../..")
sys.path.append("..")
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings
from datetime import datetime
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from api_ruteadora.models import Ruteo
cont_registros = 0
excepciones = []
archivo = '../data/cuenca_vial.shp'
ds = DataSource(archivo)
rows = ds[0]

print(rows)
print ('Procesando registros...' + str(datetime.now()))
for row in rows:
	try:
		# stripeo y paso a unicode los campos string
		row_data = map(lambda x: x.value.decode('utf-8').srip() if x.type_name == 'String' else x.value, row)

		cont_registros = cont_registros + 1
		obj = Ruteo()

		obj.nomoficial=row_data[0]
		obj.latitud = row_data[1]
		obj.longitud = row_data[2]

		# obj.normalizar = True
		# obj.geocodifcar = False

		geometry = GEOSGeometry(row.geom.ewkt)
		if geometry and isinstance(geometry, Polygon):
			geometry = MultiPolygon(geometry)
		obj.the_geom = geometry
		# obj.the_geom = unicode(row.geom.ewkt.strip())

		obj.save()
		sys.stdout.write('.')
		sys.stdout.flush()

	except Exception as e:
		excepciones.append((cont_registros, e))
		sys.stdout.write('F')
		sys.stdout.flush()
		break

print('')
print("Registros procesado: %s" % (cont_registros))
if (excepciones != []):
	for e in excepciones:
		print(str(e))