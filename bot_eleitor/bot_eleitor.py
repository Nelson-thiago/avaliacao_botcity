
from botcity.web import WebBot, Browser, By
from botcity.maestro import *
from webdriver_manager.chrome import ChromeDriverManager
from botcity.plugins.http import BotHttpPlugin
from PyPDF2 import PdfReader, PdfWriter
from pdf.pdf import merge_pdfs
import requests
from planilha.planilha import ler_excel
from datetime import datetime



def extrair_dados(bot):
    dados = {}

    dados['nro_titulo'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/div[1]/p[1]/b', By.XPATH).text
    dados['situacao'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/div[1]/p[2]/span', By.XPATH).text
    dados['secao'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[2]/div[1]/span[2]', By.XPATH).text
    dados['zona'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[2]/div[3]/span[2]', By.XPATH).text
    dados['local_votacao'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[1]/div[1]/span[2]', By.XPATH).text
    dados['endereco_votacao'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[1]/div[2]/span[2]', By.XPATH).text
    dados['bairro'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[1]/div[4]/span[2]', By.XPATH).text
    dados['municipio_uf'] = bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[1]/app-box-local-votacao/div/div/div[1]/div[3]/span[2]', By.XPATH).text
    dados['pais'] = "Brasil"  # Supondo que o país seja fixo

    return dados

def criar_eleitor(eleitor, dados_extraidos):
    url = 'http://127.0.0.1:5000/eleitor'
    headers = {'Content-Type': 'application/json'}
    
    # Converte a data de nascimento de string para objeto datetime
    data_nascimento = datetime.strptime(eleitor["DATA_NASCIMENTO"], '%d%m%Y').strftime('%d/%m/%Y')

    data = {
        "cpf": eleitor["CPF"],
        "nome": eleitor["NOME"],
        "data_nascimento": data_nascimento,
        "nome_mae": eleitor["NOME_MAE"],
        "cep": eleitor["CEP"],
        "nro_endereco": eleitor["NRO_ENDERECO"],
        # Adicione os dados extraídos
        "nro_titulo": dados_extraidos["nro_titulo"],
        "situacao": dados_extraidos["situacao"],
        "secao": dados_extraidos["secao"],
        "zona": dados_extraidos["zona"],
        "local_votacao": dados_extraidos["local_votacao"],
        "endereco_votacao": dados_extraidos["endereco_votacao"],
        "bairro": dados_extraidos["bairro"],
        "municipio_uf": dados_extraidos["municipio_uf"],
        "pais": dados_extraidos["pais"]
    }

    try:
        resposta = requests.post(url=url, headers=headers, json=data)
        resposta.raise_for_status()  # Verifica se houve algum erro na requisição
        # Retorna a resposta em formato JSON
        retorno = resposta.json()
        return retorno  # Retorna o resultado se necessário
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP: {err}")
    except Exception as e:
        print(f"Erro: {e}")

def imprimir_dados_extraidos(eleitor, mae, nascimento, cpf, dados_extraidos):
    # Formata a data de nascimento para dd/mm/aa
    nascimento_formatado = nascimento[:2] + '/' + nascimento[2:4] + '/' + nascimento[4:]  # (dd/mm/aa)
    
    print("\n=== Dados Extraídos ===")
    print(f"Nome: {eleitor}")
    print(f"Mãe: {mae}")
    print(f"Data de Nascimento: {nascimento_formatado}")
    print(f"CPF: {cpf}")
    print(f"Número do Título: {dados_extraidos['nro_titulo']}")
    print(f"Situação: {dados_extraidos['situacao']}")
    print(f"Seção: {dados_extraidos['secao']}")
    print(f"Zona: {dados_extraidos['zona']}")
    print(f"Local de Votação: {dados_extraidos['local_votacao']}")
    print(f"Endereço de Votação: {dados_extraidos['endereco_votacao']}")
    print(f"Bairro: {dados_extraidos['bairro']}")
    print(f"Município/UF: {dados_extraidos['municipio_uf']}")
    print(f"País: {dados_extraidos['pais']}")
    print("========================\n")


def acessar_site(bot, arq_excel):
    bot.browse("https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral")

    # Espera o site carregar
    while len(bot.find_elements('//*[@id="visual-portal-wrapper"]/nav/div/div/h1/a/img', By.XPATH)) < 1:
        bot.wait(1000)
        print('carregando.')
    bot.wait(1000)
    
    # Fechar o modal de cookies
    bot.find_element('//*[@id="modal-lgpd"]/div/div/div[2]/button', By.XPATH).click()
    
    # Lê os dados da planilha
    df = ler_excel(arq_excel, 'CPF')  # Supondo que essa função retorne um DataFrame

    bot.find_element('//*[@id="menu-lateral-res"]/ul/li[8]/a', By.XPATH).click()
    bot.wait(1000)

    lista_pdf = []  # Define a lista aqui

    for index, row in df.iterrows():
        eleitor = row['NOME']
        mae = row['NOME_MAE']
        nascimento = row['DATA_NASCIMENTO'].strftime('%d%m%Y')  # Formata a data
        cpf = row['CPF']
        
        # Acessa a seção de atendimento ao eleitor
        bot.find_element('//*[@id="content"]/app-root/div/app-atendimento-eleitor/div[1]/app-menu-option[10]/button/div/span[2]', By.XPATH).click()
        bot.wait(1000)

        # Preenche os dados do eleitor
        bot.find_element('//*[@id="modal"]/div/div/div[2]/div[2]/form/div[1]/div[1]/input', By.XPATH).send_keys(eleitor)
        bot.find_element('//*[@id="modal"]/div/div/div[2]/div[2]/form/div[1]/div[3]/div/input', By.XPATH).send_keys(mae)
        bot.find_element('//*[@id="modal"]/div/div/div[2]/div[2]/form/div[1]/div[2]/input', By.XPATH).send_keys(nascimento)
        bot.wait(1000)
        bot.find_element('//*[@id="modal"]/div/div/div[2]/div[2]/form/div[2]/button[2]', By.XPATH).click()
        bot.wait(1000)

        # função - Extrai dados da página
        dados_extraidos = extrair_dados(bot)

        # função - Chama a função para imprimir os dados extraídos
        imprimir_dados_extraidos(eleitor, mae, nascimento, cpf, dados_extraidos)

        # Salva o PDF com o nome completo
        nome_arq_pdf = f'{cpf}_{dados_extraidos["nro_titulo"]}.pdf'  # Adicione a extensão .pdf aqui
        caminho_pdf = fr'C:\Users\matutino\Desktop\avaliacao-botcity\bot_eleitor\pdf\{nome_arq_pdf}'
        bot.print_pdf(caminho_pdf)

        # Aguardar um pouco para garantir que o PDF foi salvo
        bot.wait(2000)

        # Adiciona o caminho completo do PDF à lista
        lista_pdf.append(caminho_pdf)

        # Salva os dados no banco de dados
        # Atualiza a variável eleitor com os dados necessários
        eleitor_dados = {
            "CPF": cpf,
            "NOME": eleitor,
            "DATA_NASCIMENTO": nascimento,
            "NOME_MAE": mae,
            "CEP": row['CEP'],
            "NRO_ENDERECO": row['NRO_ENDERECO']
        }

        # Salva no banco de dados
        criar_eleitor(eleitor_dados, dados_extraidos)

        # Voltar à tela anterior
        bot.find_element('//*[@id="content"]/app-root/div/app-consultar-numero-titulo-eleitor/div[2]/button', By.XPATH).click()  # Botão de voltar
        bot.wait(1000)
        bot.refresh()
        bot.wait(1000)

    # Chama a função de mesclagem após processar todos os eleitores
    if lista_pdf:
        caminho_saida = r'C:\Users\matutino\Desktop\avaliacao-botcity\bot_eleitor\pdf\merged_output.pdf'
        merge_pdfs(lista_pdf, caminho_saida)
        print(f"PDFs mesclados em: {caminho_saida}")

    print('Todos os eleitores foram processados.')


def main():
    bot = WebBot()
    bot.headless = False
    bot.browser = Browser.CHROME
    bot.driver_path = ChromeDriverManager().install()
    
    print('Inicio do processamento...')
    bot.start_browser()
    bot.maximize_window()
    arq_excel = r'C:\Users\matutino\Desktop\avaliacao-botcity\bot_eleitor\planilha\RelacaoEleitor.xlsx'
    acessar_site(bot, arq_excel)

    print('Fim do processamento...')
    bot.stop_browser()


def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()