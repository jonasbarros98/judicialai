from django.contrib import admin

# Register your models here.
from .models import DocumentoJuridico, EmentaJuridica

admin.site.register(DocumentoJuridico)
admin.site.register(EmentaJuridica)