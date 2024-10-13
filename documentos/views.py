from django.shortcuts import render, redirect, get_object_or_404
from .models import DocumentoJuridico
from .services.documento_service import gerar_conteudo_juridico,gerar_conteudo_contestacao  # Importa a função de gerar conteúdo
from .services.documento_service import render_pdf_view  # Importa a função de exportação para PDF
from .services.documento_service import gerar_word_view
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
import logging
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login
from django.contrib import messages

def home_view(request):
    return render(request, 'documentos/home.html')

@login_required
def historico(request):
    # Captura o usuário logado
    usuario = request.user
    
    # Filtra os documentos jurídicos do usuário logado
    documentos = DocumentoJuridico.objects.filter(user=usuario)
    
    # Se não houver documentos, passamos uma mensagem
    if not documentos.exists():
        mensagem = "Você ainda não gerou nenhum documento."
    else:
        mensagem = None
    
    # Renderiza a página de histórico com os documentos do usuário
    return render(request, 'documentos/historico.html', {
        'documentos': documentos,
        'mensagem': mensagem
    })

def documento_detalhes(request, id):
    documento = get_object_or_404(DocumentoJuridico, id=id)
    return render(request, 'documentos/detalhes.html', {'documento': documento})


logger = logging.getLogger(__name__)

def exportar_documento_word(request, documento_id):
    try:
        # Recupera o documento do banco de dados
        documento = get_object_or_404(DocumentoJuridico, pk=documento_id)
        
        # Verifica se o documento tem conteúdo
        if not documento.conteudo:
            logger.error(f"Documento {documento_id} não contém conteúdo.")
            return HttpResponse("O documento não possui conteúdo.", status=400)

        # Chama a função para gerar o arquivo Word a partir do conteúdo do documento
        return gerar_word_view(request, documento)

    except Exception as e:
        # Registra o erro no log
        logger.error(f"Erro ao gerar arquivo Word para o documento {documento_id}: {e}")
        return HttpResponse("Erro ao gerar o arquivo Word.", status=500)
# Função para criar o documento


@login_required(login_url='/index/')
def criar_documento(request):
    if request.method == 'POST':
        try:
            # Captura os dados do formulário
            tipo = request.POST.get('tipo')
            tipo_acao = request.POST.get('tipo_acao')
            valor_causa = request.POST.get('valor_causa')
            juizo_competente = request.POST.get('juizo_competente')
            descricao_fatos = request.POST.get('descricao_fatos')
            dados_requerente = request.POST.get('dados_requerente')
            dados_requerido = request.POST.get('dados_requerido')
            justica_gratis = 'justica_gratis' in request.POST

            # Converte o valor_causa em Decimal
            try:
                valor_causa = Decimal(valor_causa)
            except (InvalidOperation, ValueError, TypeError):
                return render(request, 'documentos/criar_documento.html', {
                    'error_message': 'O valor da causa deve ser um número válido.',
                    'tipo': tipo,
                    'tipo_acao': tipo_acao,
                    'juizo_competente': juizo_competente,
                    'descricao_fatos': descricao_fatos,
                    'dados_requerente': dados_requerente,
                    'dados_requerido': dados_requerido,
                    'justica_gratis': justica_gratis
                })

            # Gera o conteúdo jurídico baseado nas informações fornecidas
            dados_preenchimento = {
                'tipo_acao': tipo_acao,
                'valor_causa': valor_causa,
                'juizo_competente': juizo_competente,
                'descricao_fatos': descricao_fatos,
                'dados_requerente': dados_requerente,
                'dados_requerido': dados_requerido,
                'justica_gratis': justica_gratis
            }

            # Gera o conteúdo jurídico
            conteudo_gerado = gerar_conteudo_juridico(
                tipo_documento=tipo,
                dados_preenchimento=dados_preenchimento
            )

            # Cria o documento no banco de dados com o usuário logado
            documento = DocumentoJuridico.objects.create(
                tipo=tipo,
                titulo=f"{tipo_acao}",
                conteudo=conteudo_gerado,
                valor_causa=valor_causa,
                juizo_competente=juizo_competente,
                descricao_fatos=descricao_fatos,
                dados_requerente=dados_requerente if dados_requerente else '',  # Evita valor None
                dados_requerido=dados_requerido if dados_requerido else '',  # Evita valor None   
                justica_gratis=justica_gratis,  
                user=request.user  # Associa o documento ao usuário logado
            )

            # Redireciona para a página de sucesso com o ID do documento
            return redirect('documento_sucesso', documento_id=documento.id)

        except Exception as e:
            print(f"Erro ao criar o documento: {str(e)}")
            return render(request, 'documentos/criar_documento.html', {
                'error_message': f'Ocorreu um erro ao criar o documento: {str(e)}',
                'tipo': tipo,
                'tipo_acao': tipo_acao,
                'valor_causa': valor_causa,
                'juizo_competente': juizo_competente,
                'descricao_fatos': descricao_fatos,
                'dados_requerente': dados_requerente,
                'dados_requerido': dados_requerido,
                'justica_gratis': justica_gratis
            })

    # Renderiza o formulário se a requisição for GET
    return render(request, 'documentos/criar_documento.html')



# Função para exportar o documento como PDF
def exportar_documento_pdf(request, documento_id):
    # Busca o documento pelo ID, ou retorna 404 se não for encontrado
    documento = get_object_or_404(DocumentoJuridico, id=documento_id)
    
    # Chama a função de renderização de PDF
    return render_pdf_view(request, documento)


def documento_sucesso(request, documento_id):
    documento = get_object_or_404(DocumentoJuridico, id=documento_id)
    return render(request, 'documentos/documento_sucesso.html', {'documento': documento})

@login_required  # Certifica que o usuário esteja logado para acessar a tela inicial
def tela_inicial(request):
    return render(request, 'documentos/tela_inicial.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('tela_inicial')
        else:
            messages.error(request, 'Credenciais inválidas. Por favor, tente novamente.')
            return render(request, 'registration/index.html')
    return render(request, 'registration/index.html')



@login_required(login_url='/index/')
def criar_contestacao(request):
    if request.method == 'POST':
        try:
            # Captura os dados do formulário
            tipo = 'contestacao'  # Define como "contestacao" diretamente
            tipo_acao = request.POST.get('tipo_acao')
            valor_causa = request.POST.get('valor_causa')
            juizo_competente = request.POST.get('juizo_competente')
            descricao_fatos = request.POST.get('descricao_fatos')
            dados_requerente = request.POST.get('dados_requerente')
            dados_requerido = request.POST.get('dados_requerido')
            fundamentacao_fatos = request.POST.get('fundamentacao_fatos')
            fundamentacao_direito = request.POST.get('fundamentacao_direito')
            provas = request.POST.get('provas')
            processo_numero = request.POST.get('processo_numero')

            # Lidar com o arquivo anexado (um PDF)
            arquivo_anexado = request.FILES.get('anexar_documento')

            if arquivo_anexado:
                # Verifica se o arquivo é um PDF
                if not arquivo_anexado.name.endswith('.pdf'):
                    return render(request, 'documentos/criar_contestacao.html', {
                        'error_message': 'Somente arquivos PDF são permitidos.',
                        'tipo_acao': tipo_acao,
                        'valor_causa': valor_causa,
                        'juizo_competente': juizo_competente,
                        'descricao_fatos': descricao_fatos,
                        'dados_requerente': dados_requerente,
                        'dados_requerido': dados_requerido,
                        'fundamentacao_fatos':fundamentacao_fatos,
                        'fundamentacao_direito':fundamentacao_direito,
                        'provas': provas,
                        
                        'processo_numero': processo_numero
                    })

                # Salvar o arquivo PDF
                fs = FileSystemStorage()
                nome_arquivo = fs.save(arquivo_anexado.name, arquivo_anexado)
                caminho_arquivo = fs.url(nome_arquivo)  # Caminho para acessar o arquivo depois

            # Converte o valor_causa em Decimal
            try:
                valor_causa = Decimal(valor_causa)
            except (InvalidOperation, ValueError, TypeError):
                return render(request, 'documentos/criar_contestacao.html', {
                    'error_message': 'O valor da causa deve ser um número válido.',
                    'tipo_acao': tipo_acao,
                    'juizo_competente': juizo_competente,
                    'descricao_fatos': descricao_fatos,
                    'dados_requerente': dados_requerente,
                    'dados_requerido': dados_requerido,
                    'fundamentacao_fatos':fundamentacao_fatos,
                    'fundamentacao_direito':fundamentacao_direito,
                    'processo_numero': processo_numero
                })

            # Gera o conteúdo jurídico baseado nas informações fornecidas
            dados_preenchimento = {
                'tipo_acao': tipo_acao,
                'valor_causa': valor_causa,
                'juizo_competente': juizo_competente,
                'descricao_fatos': descricao_fatos,
                'dados_requerente': dados_requerente,
                'dados_requerido': dados_requerido,
                'provas': provas,
                'fundamentacao_fatos':fundamentacao_fatos,
                'fundamentacao_direito':fundamentacao_direito,
                'processo_numero': processo_numero
            }

            # Gera o conteúdo jurídico
            conteudo_gerado = gerar_conteudo_contestacao('contestacao', dados_preenchimento)

            # Cria o documento no banco de dados com o usuário logado
            documento = DocumentoJuridico.objects.create(
                tipo='contestacao',
                titulo=f'Contestação - {processo_numero}',
                conteudo=conteudo_gerado,
                valor_causa=valor_causa,
                juizo_competente=juizo_competente,
                descricao_fatos=descricao_fatos if descricao_fatos else '',  # Evita valor None
                dados_requerente=dados_requerente if dados_requerente else '',  # Evita valor None
                dados_requerido=dados_requerido if dados_requerido else '',  # Evita valor None
                provas=provas,
                anexo=caminho_arquivo if arquivo_anexado else None,  # Salva o caminho do arquivo PDF
                processo_numero=processo_numero if processo_numero else '',  # Evita valor None 
                fundamentacao_fatos=fundamentacao_fatos,
                fundamentacao_direito=fundamentacao_direito if fundamentacao_direito else '',  # Evita valor None
                user=request.user  # Associa o documento ao usuário logado
            )

            # Redireciona para a página de sucesso com o ID do documento
            return redirect('documento_sucesso', documento_id=documento.id)

        except Exception as e:
            print(f"Erro ao criar o documento: {str(e)}")
            return render(request, 'documentos/criar_contestacao.html', {
                'error_message': f'Ocorreu um erro ao criar o documento: {str(e)}',
                'tipo_acao': tipo_acao,
                'valor_causa': valor_causa,
                'juizo_competente': juizo_competente,
                'descricao_fatos': descricao_fatos,
                'dados_requerente': dados_requerente,
                'dados_requerido': dados_requerido,
                'processo_numero': processo_numero,
                'fundamentacao_fatos':fundamentacao_fatos,
                'fundamentacao_direito':fundamentacao_direito,
            })

    # Renderiza o formulário se a requisição for GET
    return render(request, 'documentos/criar_contestacao.html')

