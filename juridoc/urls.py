from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from documentos.views import tela_inicial, login_view  # Importa a view da tela inicial e a view de login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('documentos/', include('documentos.urls')),  # Inclua as URLs do app documentos
    path('accounts/', include('django.contrib.auth.urls')),  # URLs de autenticação
     path('login/', login_view, name='login'),  # Nova rota de login usando a view personalizada
# Redireciona a URL raiz para a tela inicial após login
    path('tela_inicial/', tela_inicial, name='tela_inicial'),
    path('', lambda request: HttpResponseRedirect('/tela_inicial/')),  # Redirecionar para tela inicial
]
