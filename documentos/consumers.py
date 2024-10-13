import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .services.documento_service import gerar_conteudo_juridico

class DocumentoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        dados = json.loads(text_data)
        tipo_documento = dados.get('tipo_documento')
        dados_preenchimento = dados.get('dados_preenchimento')

        async for conteudo_parcial in gerar_conteudo_juridico(tipo_documento, dados_preenchimento):
            await self.send(text_data=json.dumps({
                'conteudo_parcial': conteudo_parcial
            }))
