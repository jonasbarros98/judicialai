from django.urls import path
from django.http import HttpResponseRedirect
from . import views

urlpatterns = [
    path('tela_inicial/', views.tela_inicial, name='tela_inicial'),
    path('documento/<int:documento_id>/exportar_pdf/', views.exportar_documento_pdf, name='exportar_documento_pdf'),
    path('documento/<int:documento_id>/exportar_word/', views.exportar_documento_word, name='exportar_documento_word'),
    path('criar/', views.criar_documento, name='criar_documento'),
    path('sucesso/<int:documento_id>/', views.documento_sucesso, name='documento_sucesso'),
    path('historico/', views.historico, name='historico'),
    path('documento/<int:id>/', views.documento_detalhes, name='documento_detalhes'),
    path('', views.home_view, name='home'),
    
     # Rota para criar contestação
    path('criar_contestacao/', views.criar_contestacao, name='criar_contestacao'),
    # Adiciona uma rota padrão para /documentos/ que redireciona para /documentos/criar/
    path('', lambda request: HttpResponseRedirect('criar/')),
]
