import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from documentos.consumers import DocumentoConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'juridoc.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('gerar_conteudo_juridico/', DocumentoConsumer.as_asgi()),
        ])
    ),
})