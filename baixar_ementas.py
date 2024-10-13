import os
import django
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import logging
import sys
from bs4 import BeautifulSoup
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'juridoc.settings')
django.setup()

# Importar o modelo Django
from documentos.models import EmentaJuridica

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Definir os parâmetros de pesquisa
search_params = {
    'contendo_palavras_e': ' "abandono de emprego" "mau comportamento"',
    'sem_conter_palavras_nao': '',
    'palavras_na_ementa_e': '',
    'data_inicio': '',  # Data de início em formato DD-MM-YYYY
    'data_fim': datetime.now().strftime('%d-%m-%Y'),  # Data final (hoje) em formato DD-MM-YYYY
}

# Configurar opções do Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Inicializar o WebDriver (Chrome)
try:
    driver = webdriver.Chrome(options=chrome_options)
    logging.info("WebDriver iniciado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao iniciar o WebDriver: {e}")
    sys.exit(1)

try:
    # Abrir o site
    driver.get('https://jurisprudencia.tst.jus.br/')
    logging.info("Página inicial carregada.")
    time.sleep(3)

    # Fechar o pop-up inicial, se existir
    try:
        btn_fechar_popup = driver.find_element(By.XPATH, '//span[contains(text(), "Fechar")]')
        btn_fechar_popup.click()
        logging.info("Pop-up inicial fechado.")
        time.sleep(1)
    except Exception:
        logging.info("Pop-up inicial não encontrado ou já foi fechado.")
        time.sleep(1)

    # Preencher "Contendo as palavras (e):"
    try:
        input_contendo_e = driver.find_element(By.ID, 'campoTxtOperadorE')
        input_contendo_e.send_keys(search_params['contendo_palavras_e'])
        logging.info('"Contendo as palavras (e)" preenchido.')
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao preencher 'Contendo as palavras (e)': {e}")
        raise

    # Preencher "Sem conter as palavras (não):"
    try:
        input_sem_conter_nao = driver.find_element(By.ID, 'campoTxtOperadorNaoContem')
        input_sem_conter_nao.send_keys(search_params['sem_conter_palavras_nao'])
        logging.info('"Sem conter as palavras (não)" preenchido.')
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao preencher 'Sem conter as palavras (não)': {e}")
        raise

    # Preencher "Palavras na ementa (e):"
    try:
        input_palavras_na_ementa = driver.find_element(By.ID, 'campoTxtEmenta')
        input_palavras_na_ementa.send_keys(search_params['palavras_na_ementa_e'])
        logging.info('"Palavras na ementa (e)" preenchido.')
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao preencher 'Palavras na ementa (e)': {e}")
        raise

    # Desmarcar o checkbox "Todos"
    try:
        checkbox_todos = driver.find_element(By.XPATH, '//input[@type="checkbox" and @value="todos"]')
        if checkbox_todos.is_selected():
            checkbox_todos.click()
            logging.info('Checkbox "Todos" desmarcado.')
            time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao desmarcar o checkbox 'Todos': {e}")
        raise

    # Marcar o checkbox "Acórdãos"
    try:
        checkbox_acordaos = driver.find_element(By.XPATH, '//input[@type="checkbox" and @value="acordaos"]')
        if not checkbox_acordaos.is_selected():
            checkbox_acordaos.click()
            logging.info('Checkbox "Acórdãos" marcado.')
            time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao marcar o checkbox 'Acórdãos': {e}")
        raise

    # Definir Data de Publicação Início
    try:
        input_data_inicio = driver.find_element(By.ID, 'idDataPublicacaoInicio')
        input_data_inicio.clear()
        input_data_inicio.send_keys(search_params['data_inicio'])
        logging.info('Data de Publicação Início definida.')
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao definir a Data de Publicação Início: {e}")
        raise

    # Definir Data de Publicação Fim
    try:
        input_data_fim = driver.find_element(By.ID, 'idDataPublicacaoFim')
        input_data_fim.clear()
        input_data_fim.send_keys(search_params['data_fim'])
        logging.info('Data de Publicação Fim definida.')
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao definir a Data de Publicação Fim: {e}")
        raise

    # Clicar no botão "Pesquisar"
    btn_pesquisar = driver.find_element(By.XPATH, '//span[contains(text(), "Pesquisar")]/..')
    btn_pesquisar.click()

    # Esperar os resultados carregarem
    time.sleep(5)

    # Capturar todas as Ementas para Citação
    try:
        botoes_ementa_para_citacao = driver.find_elements(By.XPATH, '//span[@aria-label="Ementa para citação"]')

        for index in range(len(botoes_ementa_para_citacao)):
            botoes_ementa_para_citacao = driver.find_elements(By.XPATH, '//span[@aria-label="Ementa para citação"]')
            botoes_ementa_para_citacao[index].click()
            logging.info(f'Botão "Ementa para citação" {index + 1} clicado.')
            time.sleep(3)

            # Capturar o conteúdo da ementa
            textarea_ementa = driver.find_element(By.XPATH, '//textarea')
            ementa_texto = textarea_ementa.get_attribute("value")
            logging.info(f'Conteúdo da ementa {index + 1} capturado.')

            # Salvar no banco de dados com apenas o texto da ementa
            EmentaJuridica.objects.create(
                numero_processo='',  # Deixe vazio ou use um valor padrão, caso não esteja disponível
                orgao_julgador='',   # Deixe vazio ou adicione o valor quando disponível
                ministro_relator='', # Deixe vazio ou adicione o valor quando disponível
                data_julgamento=None,  # Se não estiver disponível, deixe como None
                data_publicacao=None,  # Se não estiver disponível, deixe como None
                tipo_documento='Acórdão',  # Assumindo que são acórdãos
                referencias_legais='',  # Pode ficar vazio por enquanto
                ementa=ementa_texto,  # O texto completo da ementa
                palavras_chave='',  # Pode adicionar palavras-chave depois
                fonte='Tribunal Superior do Trabalho - TST'
            )
            logging.info(f'Ementa {index + 1} salva no banco de dados.')

            # Fechar o modal após capturar a ementa
            btn_fechar_modal = driver.find_element(By.XPATH, '//span[text()="Fechar"]/ancestor::button')
            btn_fechar_modal.click()
            logging.info(f'Modal fechado para o resultado {index + 1}.')
            time.sleep(2)

    except Exception as e:
        logging.error(f"Erro ao capturar as ementas para citação: {e}")
        raise

finally:
    time.sleep(10)
    driver.quit()
    logging.info("Navegador fechado.")
