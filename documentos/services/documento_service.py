import openai
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO
from senha_gpt import API_KEY
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.shortcuts import get_object_or_404, redirect
from documentos.models import DocumentoJuridico
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
from bs4 import BeautifulSoup  # Usaremos para processar o HTML
from docx.shared import Pt, Inches
from search_web_gpt import buscar_jurisprudencias_bing,gerar_frase_pesquisa_gpt
from django import template
from django.http import StreamingHttpResponse
import time

openai.api_key = API_KEY
print("keyGPT: " + API_KEY)


def render_pdf_view(request, documento):
    try:
        # Carrega o template HTML
        template = get_template('documentos/documento_pdf_template.html')

        # Passa os dados do documento para o template
        html = template.render({'documento': documento})

        # Configura a resposta HTTP para um arquivo PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="documento_{documento.id}.pdf"'

        # Gera o PDF a partir do conteúdo HTML
        pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)

        # Verifica erros no processo de criação do PDF
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF', status=500)

        return response

    except Exception as e:
        # Captura exceções e retorna erro
        return HttpResponse(f'Ocorreu um erro: {str(e)}', status=500)


def gerar_word_view_old(request, documento):


    # Cria um novo documento Word
    doc = Document()

    # Ajusta a formatação para Times New Roman e tamanho 12
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Processa o conteúdo HTML para extração do texto formatado
    soup = BeautifulSoup(documento.conteudo, "html.parser")

    # Itera sobre os elementos processados pelo BeautifulSoup
    for elemento in soup.children:
        if isinstance(elemento, str):
            # Adiciona texto puro (fora de tags)
            p = doc.add_paragraph(elemento.strip())
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Inches(0.5)
        else:
            # Tratamento para negrito e itálico
            if elemento.name == 'p':
                p = doc.add_paragraph()
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Inches(0.5)  # Adiciona indentação na primeira linha
                for sub_elemento in elemento.children:
                    run = p.add_run(sub_elemento.text)

                    if sub_elemento.name == 'b':
                        run.bold = True
                    if sub_elemento.name == 'i':
                        run.italic = True
            elif elemento.name == 'h3':  # Trata títulos como negrito
                p = doc.add_paragraph(elemento.text.strip())
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.runs[0]
                run.bold = True
                run.font.size = Pt(14)  # Um pouco maior para títulos
                p.paragraph_format.first_line_indent = Inches(0)
            elif elemento.name == 'h4':  # Trata subtítulos como negrito
                p = doc.add_paragraph(elemento.text.strip())
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.runs[0]
                run.bold = True
                run.font.size = Pt(14)
                p.paragraph_format.first_line_indent = Inches(0)

    # Define o nome do arquivo e o tipo de conteúdo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=documento_{documento.id}.docx'

    # Salva o arquivo Word no response
    doc.save(response)

    return response


def gerar_word_view(request, documento):
    # Cria um novo documento Word
    print("Conteúdo do documento recebido (início):")
    print(documento.conteudo)  # Exibe o conteúdo completo do documento

    doc = Document()

    # Ajusta a formatação para Times New Roman e tamanho 12
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    print("Configuração de estilo aplicada (Times New Roman, tamanho 12)")

    # Processa o conteúdo HTML para extração do texto formatado
    print("Iniciando o processamento do conteúdo HTML com BeautifulSoup...")
    soup = BeautifulSoup(documento.conteudo, "html.parser")

    # Ignora a tag 'html' e vai diretamente para o conteúdo dentro de <body>
    body = soup.find('body')
    if not body:
        print("Nenhum corpo <body> encontrado no conteúdo.")
        return HttpResponse("Erro: Nenhum conteúdo no corpo do documento.", status=400)

    for elemento in body.children:
        if elemento.name == 'p':  # Processa parágrafos
            p = doc.add_paragraph()
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Inches(0.5)
            for sub_elemento in elemento.children:
                run = p.add_run(sub_elemento.get_text(strip=True))
                if sub_elemento.name == 'i':
                    run.italic = True
                if sub_elemento.name == 'b':
                    run.bold = True
            print(f"Adicionando parágrafo: {elemento.get_text(strip=True)}")
            
        elif elemento.name == 'h2':  # Processa títulos H2
            print(f"Adicionando título H2: {elemento.get_text(strip=True)}")
            p = doc.add_paragraph(elemento.get_text(strip=True))
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.bold = True
            run.font.size = Pt(16)
            
        elif elemento.name == 'h3':  # Processa subtítulos H3
            print(f"Adicionando subtítulo H3: {elemento.get_text(strip=True)}")
            p = doc.add_paragraph(elemento.get_text(strip=True))
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.bold = True
            run.font.size = Pt(14)
            
        elif elemento.name == 'ol':  # Processa listas ordenadas
            print("Adicionando lista ordenada...")
            for li in elemento.find_all('li'):
                print(f"Adicionando item de lista: {li.get_text(strip=True)}")
                p = doc.add_paragraph(f"{li.get_text(strip=True)}", style='List Number')
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Inches(0.5)

    # Define o nome do arquivo e o tipo de conteúdo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=documento_{documento.id}.docx'

    # Salva o arquivo Word no response
    print("Salvando o documento Word...")
    doc.save(response)

    print("Documento Word gerado com sucesso.")
    return response


def gerar_conteudo_juridico(tipo_documento, dados_preenchimento):
    try:
        # Extração dos dados do caso para a pesquisa de jurisprudência
        tipo_acao = dados_preenchimento.get('tipo_acao')
        valor_causa = dados_preenchimento.get('valor_causa')
        juizo_competente = dados_preenchimento.get('juizo_competente')
        descricao_fatos = dados_preenchimento.get('descricao_fatos')
        dados_requerente = dados_preenchimento.get('dados_requerente') or '[Nome do Requerente]'
        dados_requerido = dados_preenchimento.get('dados_requerido') or '[Nome do Requerido]'
        justica_gratis = dados_preenchimento.get('justica_gratis') or 'Não Solicite Justiça Gratuita'
        pecaValida = True
        
        # Parte 1: Buscar jurisprudências relevantes
        #Trecho comentado pois não uso mais o Bing para buscar jurisprudências.
       
        #query = gerar_frase_pesquisa_gpt(descricao_fatos)
        #jurisprudencias = buscar_jurisprudencias_bing(query)
          

        # Exibir as jurisprudências encontradas (para fins de teste)
        # print(f"Jurisprudências encontradas: {jurisprudencias}")
        # Construímos a mensagem para enviar ao modelo, agora incluindo as jurisprudências reais

        mensagem = (
            f"Você é um advogado altamente especializado em direito civil, com mais de 20 anos de experiência, e precisa redigir uma Petição Inicial para uma ação do tipo: {tipo_acao} \n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}. \n"
            f"Os fatos principais do caso são os seguintes: {descricao_fatos}. "
            f"Os dados conhecidos do requerente são: {dados_requerente}.\n"
            f"os dados conhecidos do requerido são: {dados_requerido}.\n"
            f"- Quando não forem fornecidos os dados do cliente, empresa ou envolvidos no caso, não invente dados de endereço ou afins, coloque-os entre colchetes aguardando inclusão. Ex: [nome], [endereço]."
            f"\n\nInstruções adicionais:\n"
            f"- Inclua a(s) jurisprudência(s) relevante(s) da pesquisa e cite-as corretamente no formato de peça jurídica em HTML.\n"
            f"- Inclua fundamentação legal apropriada, mencionando artigos do Código Civil, Código de Processo Civil, ou outras legislações pertinentes.\n"
            f"- Caso seja citada a jurisprudencia, utilize formatação em HTML, destaque os trechos de legislação ou jurisprudência em <i>itálico</i> , entre aspas e com espaçamento diferenciado. Exemplo: <i>Art. 373. O ônus da prova incumbe ao autor...</i>."
            f"- Não inclua o link da pesquisa de jurisprudência no documento final. Ao inves disso você deve formatá-la igual uma citação profissional na peça juridica.\n"
            f"- Mantenha a argumentação objetiva e focada no necessário para a defesa ou acusação, evitando argumentos vagos ou irrelevantes.\n"
            f"- Todo o documento deve ser em HTML. Não insira marcadores do tipo ```html no inicio ou qualquer outra forma de marcação de código. Traga apenas a estrutura HTML pura.\n"
            f"- A estrutura deve começar com as tags <html>, <head> e <body>. NÃO gere a tag <tittle>\n"
            f"- Utilize as tags <b>negrito</b> para destacar informações importantes, como títulos de seções, palavras-chave ou valores significativos.\n"
            f"- Evite espaços desnecessários ao gerar o documento.\n"
            f"- A estrutura deve conter seções como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, e <h3>DO PEDIDO</h3>, etc., numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Os titulos do inicio devem ser em <h2>, durante o texto pode utilizar <h3> ou <h4>. Nunca use h1 neste documento."
            f"- Finalize com espaço para nome do advogado, OAB e data.\n"
            f"- O documento deve ter clareza e fluidez, com parágrafos bem organizados e fundamentação robusta. Use a formatação HTML para manter o documento corretamente estruturado.\n"
            f"- O documento completo deve conter pelo menos 2000 palavras. Reforço: Não use ```html no retorno de forma alguma"
            f"- O campo a seguir define se o cliente solicita justiça gratuita ou nao: {justica_gratis}.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na pesquisa na web são as seguintes abaixo (mas use apenas as que você considerar pertinentes):\n"
            f"- Incluir apenas jurisprudências reais, verificáveis e acessíveis nos sistemas públicos de consulta dos tribunais. "
            f"Em hipótese alguma, utilize jurisprudências fictícias ou criadas para o documento. Caso não haja jurisprudência aplicável ao contexto, não invente; apenas omita. \n"
            f"A consulta de jurisprudência deve ser realizada nos sistemas públicos. Utilize apenas números de processos reais e completos, verificáveis nos sites dos tribunais. Nunca insira placeholders ou abreviações."
            f"Eu irei consultar na internet todas as jurisprudências que você colocar na peça, portanto as cite de forma válida, verdadeira e verificável."
              
        )

        # Parte 2: Incluir as jurisprudências reais na mensagem para o GPT-4
        # for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
        #    mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
        #   mensagem += f"   URL: {jurisprudencia['url']}\n"
        #    mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nUse essas informações para compor a melhor citação possível. \n"
            "Formate a citação em HTML e siga as instruções."
        )

        print("Comando real passado ao chatGPT: " + mensagem)

        # Chamamos a API OpenAI usando streaming
        
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                #{"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiencia."},
                {"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiência. Inclua apenas jurisprudências reais e verificáveis. Em hipótese alguma use placeholders ou dados fictícios. Caso não haja jurisprudências verificáveis, omita essa seção completamente."},
                {"role": "user", "content": mensagem}],
            temperature=0.2,
            max_tokens=3640,
            #stream=False
            stream = True
        )

        
        conteudo_completo = ""
        # Processar a resposta por partes
       
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
            if delta_content:  # Verifica se o conteúdo não é None
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)

        # Checagem de placeholders na resposta
        if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
            print("Placeholder detectado! Por favor, revise a resposta.")
            pecaValida = False

        if "1234" in conteudo_completo or "XXX" in conteudo_completo:
           print("Citações falsas detectadas! Por favor, revise a resposta.")    
           pecaValida = False

        while not pecaValida:

            mensagem = "Identifiquei que você usou Placeholders ou Citações falsas na peça! Isso não deve acontecer de forma alguma, jamais!\n"
            mensagem += "Reenvie apenas com jurisprudências reais e verificáveis ou omita totalmente a seção de jurisprudência, pois esta resposta será usada em um sistema jurídico profissional que exige precisão absoluta \n"
            mensagem += "Refaça a peça novamente e desta vez utilize somente jurispridências reais e verificáveis. Me responda somente com o HTML da peça sem apresentar mais nenhuma mensagem além disso \n"
            mensagem += "Não insira marcadores do tipo ```html no inicio ou qualquer outra forma de marcação de código. Traga apenas a estrutura HTML pura.\n"
            mensagem += "Segue abaixo o HTML da peça que você gerou e precisa refazer as citações. Me retorne ele completo e com as citações corrigidas\n\n"
            mensagem += conteudo_completo
            response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                #{"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiencia."},
                {"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiência. Inclua apenas jurisprudências reais e verificáveis. Em hipótese alguma use placeholders ou dados fictícios. Caso não haja jurisprudências verificáveis, omita essa seção completamente."},
                {"role": "user", "content": mensagem}],
            temperature=0.2,
            max_tokens=3640,
            #stream=False
            stream = True
            )

            conteudo_completo = ""
            # Processar a resposta por partes
       
            for parte in response:
                delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
                if delta_content:  # Verifica se o conteúdo não é None
                    print(str(delta_content), end="")
                    conteudo_completo += str(delta_content)
            
            pecaValida = True

            # Checagem de placeholders na resposta
            if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
                print("Placeholder detectado! Por favor, revise a resposta.")
                pecaValida = False

            if "1234" in conteudo_completo or "XXX" in conteudo_completo:
                print("Citações falsas detectadas! Por favor, revise a resposta.")    
                pecaValida = False

                            






        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)





def gerar_conteudo_juridico_mostrando_na_tela(tipo_documento, dados_preenchimento, documento_id=None):
    def event_stream():
        try:
            # Extração dos dados do caso para a pesquisa de jurisprudência
            tipo_acao = dados_preenchimento.get('tipo_acao')
            valor_causa = dados_preenchimento.get('valor_causa')
            juizo_competente = dados_preenchimento.get('juizo_competente')
            descricao_fatos = dados_preenchimento.get('descricao_fatos')
            dados_requerente = dados_preenchimento.get('dados_requerente') or '[Nome do Requerente]'
            dados_requerido = dados_preenchimento.get('dados_requerido') or '[Nome do Requerido]'
            justica_gratis = dados_preenchimento.get('justica_gratis') or 'Não Solicite Justiça Gratuita'
            # Parte 1: Buscar jurisprudências relevantes
            #yield f"data: Iniciando a geração do conteúdo jurídico...\n\n"
            query = gerar_frase_pesquisa_gpt(dados_preenchimento.get('descricao_fatos'))
            #yield f"data: Gerando frase de GPT: '{query}'...\n\n"
            jurisprudencias = buscar_jurisprudencias_bing(query)
            #yield f"data: Jurisprudências encontradas: {jurisprudencias}\n\n"

            # Construir a mensagem para GPT com as jurisprudências reais
            mensagem = (
            f"Você é um advogado altamente especializado em direito civil, com mais de 20 anos de experiência, e precisa redigir uma Petição Inicial para uma ação do tipo: {tipo_acao} \n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}. \n"
            f"Os fatos principais do caso são os seguintes: {descricao_fatos}. "
            f"Os dados conhecidos do requerente são: {dados_requerente}.\n"
            f"os dados conhecidos do requerido são: {dados_requerido}.\n"
            f"- Quando não forem fornecidos os dados do cliente, empresa ou envolvidos no caso, não invente dados de endereço ou afins, coloque-os entre colchetes aguardando inclusão. Ex: [nome], [endereço]."
            f"\n\nInstruções adicionais:\n"
            f"- Inclua a(s) jurisprudência(s) relevante(s) da pesquisa e cite-as corretamente no formato de peça jurídica em HTML.\n"
            f"- Inclua fundamentação legal apropriada, mencionando artigos do Código Civil, Código de Processo Civil, ou outras legislações pertinentes.\n"
            f"- Caso seja citada a jurisprudencia, utilize formatação em HTML, destaque os trechos de legislação ou jurisprudência em <i>itálico</i> , entre aspas e com espaçamento diferenciado. Exemplo: <i>Art. 373. O ônus da prova incumbe ao autor...</i>."
            f"- Não inclua o link da pesquisa de jurisprudência no documento final. Ao inves disso você deve formatá-la igual uma citação profissional na peça juridica.\n"
            f"- Mantenha a argumentação objetiva e focada no necessário para a defesa ou acusação, evitando argumentos vagos ou irrelevantes.\n"
            f"- Todo o documento deve ser em HTML. Não insira marcadores do tipo ```html no inicio ou qualquer outra forma de marcação de código. Traga apenas a estrutura HTML pura.\n"
            f"- A estrutura deve começar com as tags <html>, <head> e <body>. NÃO gere a tag <tittle>\n"
            f"- Utilize as tags <b>negrito</b> para destacar informações importantes, como títulos de seções, palavras-chave ou valores significativos.\n"
            f"- Evite espaços desnecessários ao gerar o documento.\n"
            f"- A estrutura deve conter seções como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, e <h3>DO PEDIDO</h3>, etc., numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Os titulos do inicio devem ser em <h2>, durante o texto pode utilizar <h3> ou <h4>. Nunca use h1 neste documento."
            f"- Finalize com espaço para nome do advogado, OAB e data.\n"
            f"- O documento deve ter clareza e fluidez, com parágrafos bem organizados e fundamentação robusta. Use a formatação HTML para manter o documento corretamente estruturado.\n"
            f"- O documento completo deve conter pelo menos 2000 palavras."
            f"- O campo a seguir define se o cliente solicita justiça gratuita ou nao: {justica_gratis}.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na pesquisa na web são as seguintes abaixo (mas use apenas as que você considerar pertinentes):\n"
              
        )

            #yield "data: Enviando conteúdo para o GPT...\n\n"
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiência."},
                          {"role": "user", "content": mensagem}],
                temperature=0.5,
                max_tokens=3640,
                stream=True
            )

            conteudo_completo = ""
            for parte in response:
                delta_content = parte.choices[0].delta.content
                if delta_content:
                    yield delta_content  # Envia o conteúdo para o navegador
                    conteudo_completo += delta_content

            # Salva o conteúdo gerado no documento
            documento = DocumentoJuridico.objects.get(id=documento_id)
            documento.conteudo = conteudo_completo
            documento.save()

            # Indica que o conteúdo foi completamente gerado
            yield "event: done\ndata: STREAMING_COMPLETADO\n\n"

        except Exception as e:
            error_message = f"Erro: {str(e)}"
            yield f"data: {error_message}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


def gerar_conteudo_contestacao(tipo_documento, dados_preenchimento):
    try:
        # Extração dos dados do caso para a contestação
        tipo_acao = dados_preenchimento.get('tipo_acao') or '[Tipo de Ação]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente')
        fundamentacao_fatos = dados_preenchimento.get('fundamentacao_fatos')
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito')
        dados_requerente = dados_preenchimento.get('dados_requerente') or '[Nome do Requerente]'
        dados_requerido = dados_preenchimento.get('dados_requerido') or '[Nome do Requerido]'
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        
        # Parte 1: Buscar jurisprudências relevantes
        query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        jurisprudencias = buscar_jurisprudencias_bing(query)
        
        print(f"Gerando frase de pesquisa para o caso: '{query}'..")
        print("testeeeeeee", tipo_acao, valor_causa, juizo_competente, fundamentacao_fatos, fundamentacao_direito, dados_requerente, dados_requerido, processo_numero)
        # Exibir as jurisprudências encontradas
        #print(f"Jurisprudências encontradas: {jurisprudencias}")

        # Construção da mensagem para o modelo, incluindo jurisprudências reais
        mensagem = (
            f"Você é um advogado altamente especializado em direito civil, com mais de 20 anos de experiência \n"
            f"Voce precisa redigir uma Contestação. para uma ação do tipo: {tipo_acao}.\n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}.\n"
            f"A fundamentação dos fatos são o seguinte: {fundamentacao_fatos}.\n"
            f"Os dados conhecidos do requerente são: {dados_requerente}.\n"
            f"Os dados conhecidos do requerido são: {dados_requerido}.\n"
            f"O número do processo é: {processo_numero}.\n"
            f"As provas apresentadas são: {fundamentacao_direito}.\n"
            f"- Quando não forem fornecidos os dados das partes envolvidas, provas, processo, valores, não invente dados, utilize colchetes aguardando inclusão. Ex: [nome], [endereço].\n"
            f"\n\nInstruções adicionais:\n"
            f"- Inclua as jurisprudências relevantes da pesquisa e cite-as corretamente no formato de contestação jurídica em HTML.\n"
            f"- Inclua fundamentação legal apropriada, mencionando artigos do Código Civil, Código de Processo Civil ou outras legislações pertinentes.\n"
            f"- Caso seja citada a jurisprudência, utilize formatação em HTML, destacando trechos de legislação ou jurisprudência em <i>itálico</i>. numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Não inclua o link da pesquisa de jurisprudência no documento final. Formate as jurisprudências como citação profissional jurídica.\n"
            f"- O documento deve ser claro e objetivo, mantendo foco na defesa contra os fatos apresentados, evitando argumentos vagos ou irrelevantes.\n"
            f"- Todo o documento deve ser em HTML, sem usar ```html ou qualquer outra forma de marcação de código. Somente HTML puro.\n"
            f"- A estrutura deve conter seções como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, <h3>DO PEDIDO</h3>.\n"
            f"- Use títulos como <h2> no início e <h3> ou <h4> ao longo do texto. Nunca use <h1>.\n"
            f"- Finalize com espaço para o nome do advogado, OAB e data.\n"
            f"- O documento deve ter clareza, fluidez e fundamentação robusta, mantendo a estrutura em HTML.\n"
            f"- O documento completo deve conter pelo menos 2000 palavras.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na web são as seguintes (use apenas as pertinentes):\n"
        )

        # Parte 2: Incluir as jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nUse essas informações para compor a melhor contestação possível. "
            "Formate a citação em HTML e siga as instruções."
        )

        # Chamamos a API OpenAI usando streaming
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito civil."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )
        
        conteudo_completo = ""
        # Processar a resposta por partes
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
            if delta_content:  # Verifica se o conteúdo não é None
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)

        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)
    


def gerar_conteudo_apelacao(tipo_documento, dados_preenchimento):
    try:
        # Extração dos dados do caso para a apelação
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        decisao_que_recorrida = dados_preenchimento.get('decisao_que_recorrida') or '[Decisão Recorrida]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        pedido_reforma = dados_preenchimento.get('pedido_reforma') or '[Pedido de Reforma]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente') or '[Juízo Competente]'
        provas = dados_preenchimento.get('provas') or '[Provas]'
        pecaValida = True

        # Parte 1: Buscar jurisprudências relevantes com base na fundamentação do direito
        
        #query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        #jurisprudencias = buscar_jurisprudencias_bing(query)
        
        #print(f"Gerando frase de pesquisa para o caso: '{query}'..")
        #print("Dados da apelação:", processo_numero, decisao_que_recorrida, fundamentacao_direito, pedido_reforma, valor_causa, juizo_competente, provas)

        # Construção da mensagem para o modelo, incluindo jurisprudências reais
        mensagem = (
            f"Você é um advogado altamente especializado em direito civil, com mais de 20 anos de experiência.\n"
            f"Você precisa redigir uma Apelação. A decisão recorrida é a seguinte: {decisao_que_recorrida}.\n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}.\n"
            f"A fundamentação jurídica para o recurso é a seguinte: {fundamentacao_direito}.\n"
            f"O pedido de reforma é: {pedido_reforma}.\n"
            f"O número do processo é: {processo_numero}.\n"
            f"As provas apresentadas são: {provas}.\n"
            f"- Quando não forem fornecidos os dados de provas, processo ou valores, não invente dados, utilize colchetes aguardando inclusão. Ex: [nome], [valor], [provas].\n"
            f"\n\nInstruções adicionais:\n"
            f"- Inclua as jurisprudências relevantes da pesquisa e cite-as corretamente no formato de apelação jurídica em HTML.\n"
            f"- Inclua fundamentação legal apropriada, mencionando artigos do Código Civil, Código de Processo Civil ou outras legislações pertinentes.\n"
            f"- Caso seja citada a jurisprudência, utilize formatação em HTML, destacando trechos de legislação ou jurisprudência em <i>itálico</i>. numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Não inclua o link da pesquisa de jurisprudência no documento final. Formate as jurisprudências como citação profissional jurídica.\n"
            f"- O documento deve ser claro e objetivo, mantendo foco na reforma da sentença, evitando argumentos vagos ou irrelevantes.\n"
            f"- Todo o documento deve ser em HTML, sem usar ```html ou qualquer outra forma de marcação de código. Somente HTML puro.\n"
            f"- A estrutura deve conter seções como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, <h3>DO PEDIDO</h3>.\n"
            f"- Use títulos como <h2> no início e <h3> ou <h4> ao longo do texto. Nunca use <h1>.\n"
            f"- Finalize com espaço para o nome do advogado, OAB e data.\n"
            f"- O documento deve ter clareza, fluidez e fundamentação robusta, mantendo a estrutura em HTML.\n"
            f"- O documento completo deve conter pelo menos 2000 palavras.\n"
            f"- Inclua apenas os trechos essenciais de dispositivos legais e referências, evitando transcrições completas ou longas, para manter as citações objetivas e focadas no ponto relevante.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na web são as seguintes (use apenas as pertinentes):\n"
        )


        mensagem += (
            "\nUse essas informações para compor a melhor apelação possível. "
            "Formate a citação em HTML e siga as instruções."
        )


        # Chamamos a API OpenAI usando streaming
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito civil."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.2,
            max_tokens=3640,
            stream=True
        )
        
        conteudo_completo = ""
        # Processar a resposta por partes
        for parte in response:
            if not parte.choices[0].delta == {}:
                print(str(parte.choices[0].delta.content), end="")
                conteudo_completo += str(parte.choices[0].delta.content)


        # Checagem de placeholders na resposta
        if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
            print("Placeholder detectado! Por favor, revise a resposta.")
            pecaValida = False

        if "1234" in conteudo_completo or "XXX" in conteudo_completo:
           print("Citações falsas detectadas! Por favor, revise a resposta.")    
           pecaValida = False    


        while not pecaValida:

            mensagem = "Identifiquei que você usou Placeholders ou Citações falsas na peça! Isso não deve acontecer de forma alguma, jamais!\n"
            mensagem += "Reenvie apenas com jurisprudências reais e verificáveis ou omita totalmente a seção de jurisprudência, pois esta resposta será usada em um sistema jurídico profissional que exige precisão absoluta \n"
            mensagem += "Refaça a peça novamente e desta vez utilize somente jurispridências reais e verificáveis. Me responda somente com o HTML da peça sem apresentar mais nenhuma mensagem além disso \n"
            mensagem += "Não insira marcadores do tipo ```html no inicio ou qualquer outra forma de marcação de código. Traga apenas a estrutura HTML pura.\n"
            mensagem += "Segue abaixo o HTML da peça que você gerou e precisa refazer as citações. Me retorne ele completo e com as citações corrigidas\n\n"
            mensagem += conteudo_completo
            response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                #{"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiencia."},
                {"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiência. Inclua apenas jurisprudências reais e verificáveis. Em hipótese alguma use placeholders ou dados fictícios. Caso não haja jurisprudências verificáveis, omita essa seção completamente."},
                {"role": "user", "content": mensagem}],
            temperature=0.2,
            max_tokens=3640,
            #stream=False
            stream = True
            )

            conteudo_completo = ""
            # Processar a resposta por partes
       
            for parte in response:
                delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
                if delta_content:  # Verifica se o conteúdo não é None
                    print(str(delta_content), end="")
                    conteudo_completo += str(delta_content)
            
            pecaValida = True

            # Checagem de placeholders na resposta
            if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
                print("\n\n\nPlaceholder detectado! Por favor, revise a resposta.\n\n\n")
                pecaValida = False

            if "1234" in conteudo_completo or "XXX" in conteudo_completo:
                print("\n\n\nCitações falsas detectadas! Por favor, revise a resposta.\n\n\n")    
                pecaValida = False
       

        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)
    


def gerar_conteudo_embargo(tipo_documento, dados_preenchimento):
    try:
        # Extração dos dados do caso para os embargos
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        fundamentacao_fatos = dados_preenchimento.get('fundamentacao_fatos') or '[Fundamentação Fática]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente') or '[Juízo Competente]'
        provas = dados_preenchimento.get('provas') or '[Provas]'

        # Parte 1: Buscar jurisprudências relevantes com base na fundamentação do direito
        query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        jurisprudencias = buscar_jurisprudencias_bing(query)
        
        print(f"Gerando frase de pesquisa para o caso: '{query}'..")
        print("Dados dos embargos:", processo_numero, fundamentacao_fatos, fundamentacao_direito, valor_causa, juizo_competente, provas)

        # Construção da mensagem para o modelo, incluindo jurisprudências reais
        mensagem = (
            f"Você é um advogado altamente especializado em direito civil, com mais de 20 anos de experiência.\n"
            f"Você precisa redigir uma peça de Embargos de Terceiro. O número do processo é: {processo_numero}.\n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}.\n"
            f"A fundamentação fática é a seguinte: {fundamentacao_fatos}.\n"
            f"A fundamentação jurídica para o recurso é a seguinte: {fundamentacao_direito}.\n"
            f"As provas apresentadas são: {provas}.\n"
            f"- Quando não forem fornecidos os dados de provas, processo ou valores, não invente dados, utilize colchetes aguardando inclusão. Ex: [nome], [valor], [provas].\n"
            f"\n\nInstruções adicionais:\n"
            f"- Inclua as jurisprudências relevantes da pesquisa e cite-as corretamente no formato de embargos jurídicos em HTML.\n"
            f"- Inclua fundamentação legal apropriada, mencionando artigos do Código Civil, Código de Processo Civil ou outras legislações pertinentes.\n"
            f"- Caso seja citada a jurisprudência, utilize formatação em HTML, destacando trechos de legislação ou jurisprudência em <i>itálico</i>. numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Não inclua o link da pesquisa de jurisprudência no documento final. Formate as jurisprudências como citação profissional jurídica.\n"
            f"- O documento deve ser claro e objetivo, mantendo foco nos embargos, evitando argumentos vagos ou irrelevantes.\n"
            f"- Todo o documento deve ser em HTML, sem usar ```html ou qualquer outra forma de marcação de código. Somente HTML puro.\n"
            f"- A estrutura deve conter seções como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, <h3>DO PEDIDO</h3>.\n"
            f"- Use títulos como <h2> no início e <h3> ou <h4> ao longo do texto. Nunca use <h1>.\n"
            f"- Finalize com espaço para o nome do advogado, OAB e data.\n"
            f"- O documento deve ter clareza, fluidez e fundamentação robusta, mantendo a estrutura em HTML.\n"
            f"- O documento completo deve conter pelo menos 2000 palavras.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na web são as seguintes (use apenas as pertinentes):\n"
        )

        # Parte 2: Incluir as jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nUse essas informações para compor os melhores embargos possíveis. "
            "Formate a citação em HTML e siga as instruções."
        )

        # Chamamos a API OpenAI usando streaming
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito civil."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )
        
        conteudo_completo = ""
        # Processar a resposta por partes
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
            if delta_content:  # Verifica se o conteúdo não é None
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)

        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)
    


def gerar_conteudo_recurso_extraordinario(dados_preenchimento):
    try:
        # Extração dos dados do recurso extraordinário
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        decisao_recorrida = dados_preenchimento.get('decisao_recorrida') or '[Decisão Recorrida]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        pedido_reforma = dados_preenchimento.get('pedido_reforma') or '[Pedido de Reforma]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente') or '[Juízo Competente]'
        provas = dados_preenchimento.get('provas') or '[Provas]'

        # Parte 1: Buscar jurisprudências relevantes
        query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        jurisprudencias = buscar_jurisprudencias_bing(query)

        print(f"Gerando frase de pesquisa para o caso: '{query}'..")
        # Exibir as jurisprudências encontradas
        # print(f"Jurisprudências encontradas: {jurisprudencias}")

        # Parte 2: Construção da mensagem para o modelo, incluindo jurisprudências reais
        mensagem = (
            f"Você é um advogado altamente especializado em direito constitucional, com mais de 20 anos de experiência.\n"
            f"Você precisa redigir um Recurso Extraordinário referente ao processo {processo_numero}.\n"
            f"A decisão recorrida é a seguinte: {decisao_recorrida}.\n"
            f"A fundamentação jurídica do recurso é: {fundamentacao_direito}.\n"
            f"O pedido de reforma é: {pedido_reforma}.\n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}.\n"
            f"As provas anexadas que sustentam o recurso são: {provas}.\n"
            f"- Quando não forem fornecidos dados sobre as partes envolvidas, provas, processo ou valores, utilize colchetes aguardando inclusão. Ex: [nome], [endereço].\n"
            f"\n\nInstruções adicionais:\n"
            f"- Estruture o documento completo em HTML, incluindo títulos e subtítulos apropriados. Use <h2> para o título principal e <h3> ou <h4> para seções subsequentes. Não utilize <h1>.\n"
            f"- Inclua seções como: <h3>DA DECISÃO RECORRIDA</h3>, <h3>DA FUNDAMENTAÇÃO JURÍDICA</h3>, <h3>DO PEDIDO DE REFORMA</h3>, entre outras que forem necessárias. numerando subtítulos em algarismos romanos (I, II, III).\n"
            f"- Utilize jurisprudências relevantes da pesquisa, citando-as corretamente e formatando-as em HTML, com trechos de legislação ou jurisprudência destacados em <i>itálico</i>.\n"
            f"- Não inclua links de pesquisa de jurisprudência no documento final. Apenas formate as jurisprudências como citação jurídica formal.\n"
            f"- Inclua a fundamentação legal apropriada, mencionando artigos da Constituição Federal, Código de Processo Civil, ou outras legislações pertinentes ao recurso extraordinário.\n"
            f"- Mantenha o foco na constitucionalidade da matéria e na repercussão geral, sem incluir argumentos vagos ou irrelevantes.\n"
            f"- Finalize o documento com espaço para o nome do advogado, OAB e data de forma apropriada.\n"
            f"- O documento deve ser claro e objetivo, com robustez jurídica, fluidez e, no mínimo, 2000 palavras.\n"
            f"- O conteúdo deve ser todo em HTML puro, sem usar ```html ou outra marcação de código. Refoço, não use ```html e nem nada semelhante à isso.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica."
            f"- As jurisprudências reais encontradas na web são as seguintes (use apenas as pertinentes):\n"
        )

        # Parte 3: Incluir as jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nUse essas informações para compor o melhor recurso extraordinário possível. "
            "Formate a citação em HTML e siga as instruções."
        )

        # Parte 4: Chamando a API OpenAI para gerar o conteúdo do documento
        print("Mensagem GPT: " + mensagem)
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito constitucional."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )

        conteudo_completo = ""
        # Processar a resposta por partes
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
            if delta_content:  # Verifica se o conteúdo não é None
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)

        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)



def gerar_conteudo_mandado_seguranca(dados_preenchimento):
    try:
        # Extração dos dados do Mandado de Segurança
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        autoridade_coatora = dados_preenchimento.get('autoridade_coatora') or '[Autoridade Coatora]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        pedido_liminar = dados_preenchimento.get('pedido_liminar') or '[Pedido Liminar]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente') or '[Juízo Competente]'
        provas = dados_preenchimento.get('provas') or '[Provas]'

        # Parte 1: Buscar jurisprudências relevantes
        query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        jurisprudencias = buscar_jurisprudencias_bing(query)

        print(f"Gerando frase de pesquisa para o caso: '{query}'..")
        
        # Parte 2: Construção da mensagem para o modelo, incluindo jurisprudências reais
        mensagem = (
            f"Você é um advogado altamente especializado em direito constitucional e administrativo, com mais de 20 anos de experiência.\n"
            f"Você precisa redigir um Mandado de Segurança referente ao processo {processo_numero}.\n"
            f"A autoridade coatora é a seguinte: {autoridade_coatora}.\n"
            f"A fundamentação jurídica do pedido é: {fundamentacao_direito}.\n"
            f"O pedido liminar, caso aplicável, é: {pedido_liminar}.\n"
            f"O valor da causa é de R$ {valor_causa}, e o juízo competente é {juizo_competente}.\n"
            f"As provas anexadas que sustentam o pedido são: {provas}.\n"
            f"- Quando não forem fornecidos dados sobre as partes envolvidas, provas, processo ou valores, utilize colchetes aguardando inclusão. Ex: [nome], [endereço].\n"
            f"\n\nInstruções adicionais:\n"
            f"- Estruture o documento completo em HTML, incluindo títulos e subtítulos apropriados. Use <h2> para o título principal e <h3> ou <h4> para seções subsequentes. Não utilize <h1>.\n"
            f"- Inclua seções como: <h3>DA AUTORIDADE COATORA</h3>, <h3>DA FUNDAMENTAÇÃO JURÍDICA</h3>, <h3>DO PEDIDO LIMINAR</h3>, entre outras que forem necessárias. numerando subtítulos em algarismos romanos (I, II, III).\n\n"
            f"- Utilize jurisprudências relevantes da pesquisa, citando-as corretamente e formatando-as em HTML, com trechos de legislação ou jurisprudência destacados em <i>itálico</i>.\n"
            f"- Não inclua links de pesquisa de jurisprudência no documento final. Apenas formate as jurisprudências como citação jurídica formal.\n"
            f"- Inclua a fundamentação legal apropriada, mencionando artigos da Constituição Federal, legislação específica, Código de Processo Civil, ou outras legislações pertinentes ao Mandado de Segurança.\n"
            f"- Mantenha o foco na ilegalidade do ato coator e no direito líquido e certo, sem incluir argumentos vagos ou irrelevantes.\n"
            f"- Finalize o documento com espaço para o nome do advogado, OAB e data de forma apropriada.\n"
            f"- O documento deve ser claro e objetivo, com robustez jurídica, fluidez e, no mínimo, 2000 palavras.\n"
            f"- O conteúdo deve ser todo em HTML puro, sem usar ```html ou outra marcação de código.\n"
            f"- As jurisprudências devem ser reais e verificáveis. Em hipótese alguma crie ou invente jurisprudências. Use apenas jurisprudências reais, citando-as de maneira completa e exata, incluindo o número do processo, tribunal, data do julgamento, e outras informações relevantes da decisão. Certifique-se de que as jurisprudências sejam formatadas conforme o padrão jurídico e estejam adequadamente inseridas na peça jurídica.\n"
            f"- As jurisprudências reais encontradas na web são as seguintes (use apenas as pertinentes):\n"
        )

        # Parte 3: Incluir as jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nUse essas informações para compor o melhor Mandado de Segurança possível. "
            "Formate a citação em HTML e siga as instruções."
            "**Não se esqueça de colocar as citações em itálico**"
        )

        # Parte 4: Chamando a API OpenAI para gerar o conteúdo do documento
        print("Mensagem GPT: " + mensagem)
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito constitucional e administrativo."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )

        conteudo_completo = ""
        # Processar a resposta por partes
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
            if delta_content:  # Verifica se o conteúdo não é None
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)

        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)



def gerar_conteudo_habeas_corpus(dados_preenchimento):
    try:
        # Extração dos dados do Habeas Corpus
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        paciente = dados_preenchimento.get('paciente') or '[Paciente]'
        autoridade_coatora = dados_preenchimento.get('autoridade_coatora') or '[Autoridade Coatora]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        pedido_liminar = dados_preenchimento.get('pedido_liminar') or '[Pedido Liminar]'
        provas = dados_preenchimento.get('provas') or '[Provas]'
        pecaValida = True


        # Construção do prompt detalhado para o GPT
        mensagem = (
        f"Você é um advogado altamente especializado em direito constitucional e penal, com mais de 20 anos de experiência, "
        f"e precisa redigir uma peça de Habeas Corpus referente ao processo {processo_numero}.\n"
        f"O paciente é {paciente}, e a autoridade coatora é {autoridade_coatora}.\n"
        f"A fundamentação jurídica do pedido é a seguinte: {fundamentacao_direito}.\n"
        f"Pedido de liminar: {pedido_liminar}.\n"
        f"As provas anexadas que sustentam o Habeas Corpus são: {provas}.\n"
        f"- Quando não forem fornecidos os dados completos sobre o processo, paciente, autoridade coatora, fundamentos ou provas, utilize colchetes indicando inclusão futura. Ex: [nome], [fundamento].\n\n"

        f"Instruções adicionais:\n"
        f"- Todo o conteúdo deve estar em HTML puro, **sem utilizar ```html** ou qualquer outra marcação de código para indicar que é HTML.\n"
        f"- Não utilize `pre`, `code` ou qualquer outra tag que se assemelhe a um bloco de código no HTML.\n"
        f"- A estrutura HTML deve começar com as tags <html>, <head>, e <body>, e não deve incluir qualquer formatação de bloco de código.\n"
        f"- Use títulos como <h2> para seções principais e <h3> ou <h4> para subseções. Nunca utilize a tag <h1>.\n"
        f"- O documento deve conter seções organizadas e numeradas como: <h3>DOS FATOS</h3>, <h3>DO DIREITO</h3>, "
        f"<h3>DO PEDIDO DE LIMINAR</h3>, <h3>DO MÉRITO</h3>, e <h3>DOS PEDIDOS FINAIS</h3>, entre outras que forem necessárias.\n"
        f"- Utilize <b>negrito</b> para destacar informações importantes, como termos técnicos, nomes das seções e outras palavras-chave.\n"
        f"- Use uma linguagem objetiva, clara e precisa, mantendo o foco na argumentação jurídica fundamental e evitando divagações ou informações irrelevantes.\n"
        f"- Inclua as jurisprudências reais e verificáveis encontradas na pesquisa e cite-as corretamente em HTML, com trechos de legislação ou jurisprudência destacados em <i>itálico</i>, em aspas e com espaçamento diferenciado. Exemplo: <i>Art. 5º, inciso LXVIII da Constituição Federal...</i>.\n"
        f"- As jurisprudências reais devem ser formatadas conforme o padrão jurídico e adequadamente inseridas no corpo do documento, sem incluir links diretos.\n"
        f"- Inclua fundamentação legal apropriada, mencionando artigos da Constituição Federal, Código de Processo Penal, ou outras legislações pertinentes ao Habeas Corpus.\n"
        f"- Estruture o documento de maneira que ele esteja completo, claro, e juridicamente robusto, contendo uma argumentação sólida com pelo menos 2000 palavras.\n"
        f"- Finalize com espaço para assinatura do advogado, número da OAB e data.\n"
        f"\n\nAs jurisprudências reais encontradas na pesquisa são as seguintes (use apenas as que considerar relevantes):\n"
        )

       

        mensagem += (
            "\nComponha o Habeas Corpus com base nas informações fornecidas e encontre jurisprudências relevantes, "
            "seguindo as instruções rigorosamente para garantir a melhor argumentação jurídica e formatação correta em HTML. "
            "**Não utilize ```html ou qualquer outra marcação de bloco de código** em nenhuma parte da resposta."
            "**Não se esqueça de colocar as citações em itálico**"
        )

        # Ajuste para chamada da API OpenAI
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[{"role": "system", "content": "Você é um advogado especializado em direito penal."},
                      {"role": "user", "content": mensagem}],
            temperature=0.2,
            max_tokens=3640,
            stream=True
        )


        conteudo_completo = ""
        for parte in response:
            delta_content = parte.choices[0].delta.content  # Captura o conteúdo corretamente
            if delta_content:
                print(str(delta_content), end="")
                conteudo_completo += str(delta_content)


         # Checagem de placeholders na resposta
        if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
            print("Placeholder detectado! Por favor, revise a resposta.")
            pecaValida = False

        if "1234" in conteudo_completo or "XXX" in conteudo_completo:
           print("Citações falsas detectadas! Por favor, revise a resposta.")    
           pecaValida = False

        while not pecaValida:

            mensagem = "Identifiquei que você usou Placeholders ou Citações falsas na peça! Isso não deve acontecer de forma alguma, jamais!\n"
            mensagem += "Reenvie apenas com jurisprudências reais e verificáveis ou omita totalmente a seção de jurisprudência, pois esta resposta será usada em um sistema jurídico profissional que exige precisão absoluta \n"
            mensagem += "Refaça a peça novamente e desta vez utilize somente jurispridências reais e verificáveis. Me responda somente com o HTML da peça sem apresentar mais nenhuma mensagem além disso \n"
            mensagem += "Não insira marcadores do tipo ```html no inicio ou qualquer outra forma de marcação de código. Traga apenas a estrutura HTML pura.\n"
            mensagem += "Segue abaixo o HTML da peça que você gerou e precisa refazer as citações. Me retorne ele completo e com as citações corrigidas\n\n"
            mensagem += conteudo_completo
            response = openai.chat.completions.create(
            model="chatgpt-4o-latest",  # Verifique se o modelo está correto
            messages=[
                #{"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiencia."},
                {"role": "system", "content": "Você é um advogado especializado em direito civil com 20 anos de experiência. Inclua apenas jurisprudências reais e verificáveis. Em hipótese alguma use placeholders ou dados fictícios. Caso não haja jurisprudências verificáveis, omita essa seção completamente."},
                {"role": "user", "content": mensagem}],
            temperature=0.2,
            max_tokens=3640,
            #stream=False
            stream = True
            )

            conteudo_completo = ""
            # Processar a resposta por partes
       
            for parte in response:
                delta_content = parte.choices[0].delta.content  # Captura o conteúdo da parte
                if delta_content:  # Verifica se o conteúdo não é None
                    print(str(delta_content), end="")
                    conteudo_completo += str(delta_content)
            
            pecaValida = True

            # Checagem de placeholders na resposta
            if "[número do processo real]" in conteudo_completo or "[Nome do Relator]" in conteudo_completo:
                print("Placeholder detectado! Por favor, revise a resposta.")
                pecaValida = False

            if "1234" in conteudo_completo or "XXX" in conteudo_completo:
                print("Citações falsas detectadas! Por favor, revise a resposta.")    
                pecaValida = False

        #Retorna o conteúdo após tudo corrigido
        return conteudo_completo

    except Exception as e:
        print("Erro ao gerar conteúdo:", e)
        return f"Erro: {str(e)}"
    


def gerar_conteudo_acao_rescisoria(dados_preenchimento):
    try:
        # Extração dos dados da ação rescisória
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        fundamento_rescisorio = dados_preenchimento.get('fundamento_rescisorio') or '[Fundamento Rescisório]'
        pedido = dados_preenchimento.get('pedido') or '[Pedido]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        provas = dados_preenchimento.get('provas') or '[Provas]'

        # Pesquisa jurisprudencial
        query = gerar_frase_pesquisa_gpt(fundamento_rescisorio)
        jurisprudencias = buscar_jurisprudencias_bing(query)

        # Construção da mensagem para o modelo
        mensagem = (
            f"Você é um advogado altamente especializado em direito processual civil e tem mais de 20 anos de experiência em ações rescisórias.\n"
            f"Precisa redigir uma Ação Rescisória referente ao processo {processo_numero}.\n"
            f"O fundamento rescisório da ação é: {fundamento_rescisorio}.\n"
            f"O pedido principal é: {pedido}.\n"
            f"O valor da causa é de R$ {valor_causa}.\n"
            f"As provas anexadas que justificam o pedido de rescisão são: {provas}.\n"
            f"- Quando não forem fornecidos dados sobre partes, provas, ou valores, insira placeholders entre colchetes para indicar a necessidade de preenchimento posterior. Ex: [Nome do autor], [Nome do réu], [valor].\n\n"
            
            f"Instruções detalhadas para a estrutura do documento:\n"
            f"- O documento deve ser estruturado integralmente em HTML puro, sem qualquer uso de marcação de código, como ```html ou similar. Apenas retorne o conteúdo em HTML puro e organizado.\n"
            f"- A estrutura deve começar com as tags <html>, <head> e <body>. NÃO inclua a tag <title>.\n"
            f"- Organize o conteúdo com cabeçalhos apropriados: use <h2> para o título principal e <h3> ou <h4> para as seções subsequentes. Em hipótese alguma utilize <h1>.\n"
            f"- Estruture o documento com seções como: <h3>DO FUNDAMENTO RESCISÓRIO</h3>, <h3>DO PEDIDO</h3>, e outras necessárias para clareza e organização.\n"
            f"- Utilize as tags <b>negrito</b> para destacar informações importantes, como títulos de seções e conceitos jurídicos relevantes.\n"
            f"- As jurisprudências relevantes devem ser formatadas corretamente em HTML, com os trechos legais ou jurisprudenciais em <i>itálico</i> para destaque. Não inclua links para as jurisprudências; cite-as no formato jurídico correto, incluindo número de processo, tribunal, e data do julgamento.\n"
            f"- Inclua fundamentação legal apropriada, citando artigos do Código de Processo Civil, Código Civil ou outras legislações pertinentes à Ação Rescisória.\n"
            f"- Certifique-se de que a argumentação seja robusta, clara e focada nos fundamentos legais e doutrinários para a rescisão, evitando argumentos vagos ou irrelevantes.\n"
            f"- Finalize o documento com espaço para nome do advogado, número da OAB e data de forma apropriada e formatada.\n"
            f"- Todo o conteúdo deve ter fluidez e precisão jurídica, e o documento deve conter no mínimo 2000 palavras.\n"
            f"- Certifique-se de que as jurisprudências incluídas sejam reais e verificáveis. Não crie ou invente jurisprudências. Use apenas jurisprudências verdadeiras, citando-as completa e exatamente, com o tribunal, número do processo, e data correta.\n"
            f"- As jurisprudências reais encontradas na pesquisa online são as seguintes (use apenas as que forem pertinentes):\n"
        )

        # Inclusão das jurisprudências reais no prompt
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nComponha a Ação Rescisória com base nas informações fornecidas e nas jurisprudências relevantes, "
            "seguindo as instruções rigorosamente para garantir a melhor argumentação jurídica e formatação correta em HTML. "
            "**Não utilize ```html, ```javascript, ```css, ou qualquer outra marcação de bloco de código** em nenhuma parte da resposta."
            "**Não se esqueça de colocar as citações em itálico**"
        )

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito processual civil."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )

        conteudo_completo = ""
        for parte in response:
            delta_content = parte.choices[0].delta.content
            if delta_content:
                conteudo_completo += delta_content

        return conteudo_completo

    except Exception as e:
        return f"Erro: {str(e)}"



def gerar_conteudo_agravo_instrumento(dados_preenchimento):
    try:
        # Extração dos dados do agravo de instrumento
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        fundamentacao_direito = dados_preenchimento.get('fundamentacao_direito') or '[Fundamentação Jurídica]'
        pedido = dados_preenchimento.get('pedido') or '[Pedido]'
        valor_causa = dados_preenchimento.get('valor_causa') or '[Valor da Causa]'
        juizo_competente = dados_preenchimento.get('juizo_competente') or '[Juízo Competente]'
        provas = dados_preenchimento.get('provas') or '[Provas]'

        # Pesquisa jurisprudencial
        query = gerar_frase_pesquisa_gpt(fundamentacao_direito)
        jurisprudencias = buscar_jurisprudencias_bing(query)

        # Construção do prompt robusto
        mensagem = (
            f"Você é um advogado com mais de 20 anos de experiência em agravos de instrumento.\n"
            f"Precisa redigir um Agravo de Instrumento para o processo {processo_numero}.\n"
            f"A fundamentação jurídica é: {fundamentacao_direito}.\n"
            f"O pedido é: {pedido}.\n"
            f"O valor da causa é de R$ {valor_causa}.\n"
            f"O juízo competente é: {juizo_competente}.\n"
            f"As provas anexadas são: {provas}.\n\n"
            
            f"Instruções detalhadas para a estrutura do documento:\n"
            f"- Estruture todo o conteúdo em HTML puro. Não use ```html ou qualquer marcação de código.\n"
            f"- Organize as seções em <h2>, <h3> e <h4> conforme apropriado.\n"
            f"- Inclua seções como <h3>DA FUNDAMENTAÇÃO JURÍDICA</h3>, <h3>DO PEDIDO</h3>, e outras necessárias.\n"
            f"- Utilize <b>negrito</b> para títulos e conceitos jurídicos importantes.\n"
            f"- As jurisprudências relevantes devem ser reais e formatadas em HTML, sem links.\n"
            f"- Insira a fundamentação legal apropriada, como o Código de Processo Civil e outras legislações.\n"
            f"- O documento deve conter ao menos 2000 palavras.\n\n"
            f"- Não se esqueça de incluir ao final do documento o campo para assinatuta e OAB do advogado.\n\n"
        )

        # Inclusão de jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nComponha o Agravo de Instrumento com base nas informações fornecidas e nas jurisprudências relevantes. "
            "**Não utilize ```html ou qualquer outra marcação de bloco de código** em nenhuma parte da resposta."
            "**Não se esqueça de colocar as citações em itálico**"
        )

        # Chamada à API para geração do conteúdo
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Você é um advogado especializado em direito processual civil."},
                      {"role": "user", "content": mensagem}],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )

        conteudo_completo = ""
        for parte in response:
            delta_content = parte.choices[0].delta.content
            if delta_content:
                conteudo_completo += delta_content

        return conteudo_completo

    except Exception as e:
        return f"Erro: {str(e)}"
    


def gerar_conteudo_execucao_fiscal(dados_preenchimento):
    try:
        # Extração dos dados de execução fiscal
        processo_numero = dados_preenchimento.get('processo_numero') or '[Número do Processo]'
        valor_executado = dados_preenchimento.get('valor_executado') or '[Valor Executado]'
        fundamento_legal = dados_preenchimento.get('fundamento_legal') or '[Fundamento Legal]'
        provas = dados_preenchimento.get('provas') or '[Provas]'
        ente_fiscal = dados_preenchimento.get('ente_fiscal') or '[Ente Fiscal]'

        # Pesquisa jurisprudencial relevante
        query = gerar_frase_pesquisa_gpt(fundamento_legal)
        jurisprudencias = buscar_jurisprudencias_bing(query)

        # Construção do prompt com robustez para a Execução Fiscal
        mensagem = (
            f"Você é um advogado altamente especializado em direito tributário e execução fiscal, com mais de 20 anos de experiência.\n"
            f"Precisa redigir uma Execução Fiscal referente ao processo {processo_numero}.\n"
            f"O valor executado é de R$ {valor_executado}, e o ente fiscal envolvido é {ente_fiscal}.\n"
            f"O fundamento legal para a execução é: {fundamento_legal}.\n"
            f"As provas que sustentam a execução são: {provas}.\n"
            f"- Quando não forem fornecidos dados sobre partes ou valores, insira placeholders em colchetes. Ex: [Nome do autor], [Nome do réu], [Valor da execução].\n\n"
            
            f"Instruções detalhadas para a estrutura do documento:\n"
            f"- Estruture o documento em HTML puro, sem marcações de código como ```html. Apenas retorne o conteúdo em HTML bem formatado.\n"
            f"- Comece o documento com as tags <html>, <head>, e <body> (não inclua a tag <title>).\n"
            f"- Utilize cabeçalhos para organizar o conteúdo: <h2> para o título principal e <h3> para as seções.\n"
            f"- As seções devem incluir cabeçalhos como <h3>DO FUNDAMENTO LEGAL</h3>, <h3>DO VALOR EXECUTADO</h3>, e outras relevantes.\n"
            f"- Utilize <b>negrito</b> para destacar pontos-chave, como valores e fundamentos importantes.\n"
            f"- As jurisprudências relevantes devem ser formatadas corretamente em HTML, com os trechos de legislação ou jurisprudência destacados em <i>itálico</i>. Não inclua links; cite-as no formato jurídico adequado.\n"
            f"- Inclua fundamentação legal apropriada, citando artigos do Código Tributário Nacional, leis fiscais, ou outras legislações pertinentes à Execução Fiscal.\n"
            f"- A argumentação deve ser clara e objetiva, com foco em fundamentos legais sólidos, evitando argumentos vagos ou irrelevantes.\n"
            f"- Finalize com espaço para o nome do advogado, número da OAB e a data.\n"
            f"- As jurisprudências reais devem ser verificáveis e verdadeiras. Não invente ou crie jurisprudências. Cite-as corretamente, incluindo o tribunal, número do processo e data.\n"
            f"- As jurisprudências encontradas na pesquisa online são:\n"
        )

        # Inclusão das jurisprudências reais
        for idx, jurisprudencia in enumerate(jurisprudencias["webPages"]["value"][:3]):
            mensagem += f"{idx + 1}. Título: {jurisprudencia['name']}\n"
            mensagem += f"   URL: {jurisprudencia['url']}\n"
            mensagem += f"   Trecho: {jurisprudencia['snippet']}\n\n"

        mensagem += (
            "\nComponha a Execução Fiscal com base nas informações fornecidas e nas jurisprudências relevantes, "
            "seguindo as instruções rigorosamente para garantir a melhor argumentação jurídica e formatação correta em HTML. "
            "**Não utilize ```html ou qualquer outra marcação de bloco de código** em nenhuma parte da resposta."
            "**Não se esqueça de colocar as citações em itálico**"
        )

        # Chamada à API OpenAI para geração do conteúdo
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito tributário e execução fiscal."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=3640,
            stream=True
        )

        conteudo_completo = ""
        for parte in response:
            delta_content = parte.choices[0].delta.content
            if delta_content:
                conteudo_completo += delta_content

        return conteudo_completo

    except Exception as e:
        return f"Erro: {str(e)}"    