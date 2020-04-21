from django.contrib import admin

# Register your models here.

from .models import Endpoint, Costo

admin.site.register(Endpoint)
admin.site.register(Costo)

