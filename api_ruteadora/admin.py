from django.contrib import admin

# Register your models here.

from .models import Endpoint

admin.site.register(Endpoint)

