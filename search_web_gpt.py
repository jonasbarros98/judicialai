import openai
import requests
from senha_gpt import API_KEY
from bing_key import BING_KEY

# Chave da API do OpenAI (GPT-4) e da Bing Search API
openai.api_key = API_KEY
subscription_key_bing = BING_KEY

# Ponto de extremidade da Bing Search API
bing_search_url = "https://api.bing.microsoft.com/v7.0/search"

# Função para gerar a frase de pesquisa usando GPT-4
def gerar_frase_pesquisa_gpt(caso_juridico):
    try:
        # Construímos a mensagem para o GPT sugerir a melhor frase de pesquisa
        mensagem = (
            f"Você é um advogado altamente experiente especializado em pesquisa de jurisprudencias e fundamentações juridicas.. "
            f"Com base no caso descrito a seguir, sugira uma frase simplificada, pequena e direta para pesquisar jurisprudências: \n\n"
            f"{caso_juridico}\n"
            f"Nao coloque nenhum acento ou "" ou '' dentro da frase."
            f"Caso nenhuma informação do caso juridico tenha sido passada, gere apenas a frase: Sem Dados Suficientes"
        )
        
        # Chamando a API OpenAI para gerar a frase de pesquisa
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "system", "content": "Você é um advogado especializado em direito civil."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.5,
            max_tokens=300,
            stream=False  # Ativando o streaming para receber respostas parciais
        )

        # Processar a resposta corretamente
        conteudo_completo = response.choices[0].message.content
        
        return conteudo_completo

    except Exception as e:
        print("Erro:", e)
        return "Erro: " + str(e)

def buscar_jurisprudencias_bing(caso_juridico):
    # Gerar a frase de pesquisa usando GPT-4
    frase_pesquisa = gerar_frase_pesquisa_gpt(caso_juridico)
    
    # Restrição da busca aos sites desejados
    restricted_query = f'{frase_pesquisa} site:stf.jus.br OR site:stj.jus.br OR site:tst.jus.br OR site:jusbrasil.com.br'
    
    headers = {"Ocp-Apim-Subscription-Key": subscription_key_bing}
    params = {"q": restricted_query, "textDecorations": True, "textFormat": "HTML"}

    # Fazer a requisição à API do Bing
    response = requests.get(bing_search_url, headers=headers, params=params)
    response.raise_for_status()  # Gera erro caso a requisição falhe
    
    return response.json()
