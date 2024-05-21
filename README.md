# Automação em Python e Selenium para Extração de Dados da Gupy

## 1. Introdução
Este projeto implementa uma automação em Python usando Selenium para extrair dados sobre as vagas de emprego para as quais você se candidatou na plataforma Gupy. Ele permite acessar tanto as vagas em andamento quanto as finalizadas. Os dados coletados são armazenados em uma planilha do Google Sheets e, posteriormente, utilizados para criar um dashboard no Looker Studio.

## 2. Funcionalidades
- Acessar a página de login da Gupy: O script automatiza o login na plataforma Gupy.
- Aceitar cookies e avisos de segurança: Lidar com cookies e avisos de segurança na página.
- Efetuar login na Gupy: Realizar o login na plataforma Gupy utilizando as credenciais do usuário.
- Acessar a página de Minhas Candidaturas: Acessar a página "Minhas Candidaturas" na Gupy.
- Extrair dados das candidaturas: Extrair informações sobre a empresa, cargo e status da candidatura para cada aplicação.
- Armazenar dados no Google Sheets: Salvar os dados extraídos em uma planilha do Google Sheets.
- Criar dashboard no Looker Studio: Utilizar os dados do Google Sheets para criar um dashboard visual no Looker Studio (opcional)

## 3. Pré-requisitos
- Python 3.10 ou superior: A automação exige Python 3.10 ou versão superior.
- Bibliotecas Python: As bibliotecas 'selenium', 'gspread', 'oauth2client' e 'bs4' precisam ser instaladas.
- ChromeDriver compatível: Um ChromeDriver compatível com a versão do navegador Chrome instalada é necessário, porém, a partir da versão 4 do Selenium o ChromeDriver já vem instalado automaticamente.
- Credenciais de API do Google: Credenciais de API do Google para acesso ao Google Sheets.
- Conta Google Sheets: Uma conta do Google Sheets para armazenar os dados extraídos.
- Conta Looker Studio (opcional): Uma conta Looker Studio para criar dashboards (opcional).

## 4. Bibliotecas Importadas
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
```
- selenium: Controla o navegador Chrome e interage com a página da Gupy.
- selenium.webdriver.common.by: Fornece métodos para localizar elementos na página.
- selenium.webdriver.support.ui: Permite esperar elementos específicos ficarem disponíveis antes da interação.
- selenium.webdriver.support.expected_conditions: Define condições para verificar elementos na página (ex: estar presente, clicável).
- time: Adiciona pausas estratégicas na execução do script.
- bs4: Biblioteca Beautiful Soup para fazer parsing do HTML da página e extrair dados.
- gspread: Permite acessar e atualizar a planilha do Google Sheets.
- oauth2client.service_account: Autenticação com o Google Sheets API usando credenciais JSON.

## 5. Configuração do ambiente
### 5.1. Configuração do Google Sheets API
- Acesse o Google Cloud Console
- Crie um novo projeto.
- Ative as APIs Google Sheets e  Google Drive.
- Crie credenciais de OAuth 2.0 e baixe o arquivo ‘credentials.json’.

## 6. Código da Automação Vagas em andamento:
### 6.1. Funções Auxiliares:
- accept_cookies(driver): Tenta localizar e clicar no botão "Aceitar cookies", se presente.
- click_ok_entendi(driver): Tenta localizar e clicar no botão "Ok, entendi" do aviso de golpe (se existir).
- click_login_with_email_or_cpf(driver): Tenta localizar e clicar no botão "Entrar com e-mail ou CPF".

```python
# Clique no botão "Aceitar cookies", se estiver presente
def accept_cookies(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button_accept_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        button_accept_cookies.click()
    except Exception as e:
        print("Error: Cookies", e)

# Aviso "Cuidados com Golpe", encontre o botão "Ok, entendi" e clique nele
def click_ok_entendi(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button_ok_entendi = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "safe-check-dialog__confirm-button")))
        button_ok_entendi.click()
    except Exception as e:
        print("Error: Aviso de golpe", e)

# Encontre o botão "Entrar com e-mail ou CPF" e clique nele
def click_login_with_email_or_cpf(driver):
    try:
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Entrar com e-mail ou CPF']")))
        element.click()
    except Exception as e:
        print("Error: Botão e-mail ou CPF não encontrado!", e)
```
### 6.2. Função login(driver, username, password):
- Preenche o formulário de login da Gupy com as credenciais fornecidas (e-mail e senha).
- Utiliza WebDriverWait para esperar elementos específicos ficarem disponíveis antes de interagir com eles (evitando erros).
- Adiciona um tempo de espera final (time.sleep(5)) para garantir o login completo.

```python
# Preencha o formulário de login
def login(driver, username, password):
    try:
        wait = WebDriverWait(driver, 10)
        email_or_cpf_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_or_cpf_field.send_keys(username)
        
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password-input")))
        password_field.send_keys(password)
        
        button_acessar_conta = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.gupy-button span span")))
        button_acessar_conta.click()
        
        time.sleep(5)  # Aguarde a conclusão do login
    except Exception as e:
        print("Error: Login não concluído", e)
```
### 6.3. Função scrape_application_data(driver):
- Realiza um loop para processar até 3 páginas de candidaturas (ajuste o número de páginas se necessário).
- Para cada página:
- Obtém o código HTML da página atual usando driver.page_source.
- Utiliza Beautiful Soup para fazer parsing do HTML e extrair os dados.
- Localiza a seção de candidaturas (applications_section) e itera por cada aplicação (article).
- Extrai o nome da empresa, título da vaga e progresso da candidatura usando tags HTML específicos.
- Armazena os dados extraídos em uma lista.
- Verifica se a última página foi processada e, caso não seja, clica no botão "Próxima Página".

```python
# Extrair as informações das empresas para as quais você se candidatou
def scrape_application_data(driver):
    data_list = []
    # Loop para clicar em cada página individualmente
    for page_number in range(1, 4):
        # Obter o conteúdo HTML da página atual
        html_content = driver.page_source
        # Extrair dados para cada aplicação da página atual
        soup = BeautifulSoup(html_content, 'html.parser')
        applications_section = soup.find('section', class_='sc-3303e2f3-0 gpftOq')
        if applications_section:
            for article in applications_section.find_all('article'):
                company_name_tag = article.find(class_='sc-bBXxYQ eJcDNr sc-1cba52f7-5 kuwnaG')
                job_title_tag = article.find('h3', class_='sc-bZkfAO gYfAYo sc-1cba52f7-4 ldEkeI')
                application_progress_tag = article.find('div', class_='sc-d9e69618-2 SZawu')
                
                company_name = company_name_tag.text.strip() if company_name_tag else "N/A"
                job_title = job_title_tag.text.strip() if job_title_tag else "N/A"
                application_progress = application_progress_tag.text.strip() if application_progress_tag else "N/A"
                
                # Lista para armazenar os dados
                data_list.append([company_name, job_title, application_progress])
            
            # Se esta não for a última página, clique no botão da próxima página
            if page_number != 3:
                # Espere até que o botão da próxima página esteja presente e clicável na página
                next_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="pagination-next-button"]'))
                )
                # Clique no botão da próxima página
                next_button.click()
        else:
            print("Seções não encontradas.")
    return data_list
```
### 6.4. Funções para Atualizar a Planilha:
- update_google_sheet(data_list, worksheet): Adiciona cada linha da lista de dados (data_list) como uma nova linha na planilha (worksheet).
- clear_worksheet(worksheet): Limpa a planilha, removendo todas as linhas exceto a primeira (cabeçalho). Você pode comentar essa linha se quiser manter o cabeçalho existente.

```python
# Adicionar os dados à planilha
def update_google_sheet(data_list, worksheet):
    for data in data_list:
        worksheet.append_row(data)

def clear_worksheet(worksheet):
    # Remove todas as linhas, exceto a primeira (cabeçalho)
    worksheet.clear()
    # Se você quiser manter o cabeçalho, remova o comentário da linha abaixo e ajuste conforme necessário
    worksheet.append_row(['Company Name', 'Job Title', 'Application Progress'])
```
### 6.5. Função main():
- Inicia o navegador Chrome.
- Abre a página de login da Gupy.
- Chama as funções auxiliares para lidar com cookies, avisos e clique no botão de login.
- Adiciona um pequeno tempo de espera para o formulário de login carregar.
- Chama a função login para preencher o formulário e efetuar o login.
- Navega para a página de Minhas Vagas (https://portal.gupy.io/my/applications).
- Carrega as credenciais do Google Sheets a partir do arquivo JSON.
- Abre a planilha do Google Sheets especificada.
- Limpa a planilha (opcional).
- Extrai os dados das candidaturas usando scrape_application_data.
- Adiciona os dados extraídos à planilha usando update_google_sheet.
- Exibe uma mensagem de sucesso ou erro.
- Fecha o navegador Chrome.

### 6.7.Bloco if __name__ == "__main__":
- Garante que o código dentro desse bloco seja executado somente quando o script é executado diretamente (evita execução indesejada ao importar como módulo).
Chama a função main() para iniciar o processo de automação.

```python
# Inicialize o driver do navegador
def main():
    driver = webdriver.Chrome()
    # Abra a página de login da Gupy
    driver.get('https://login.gupy.io/candidates/signin')

    accept_cookies(driver)
    click_ok_entendi(driver)
    click_login_with_email_or_cpf(driver)

# Aguarde um momento para o formulário de login ser carregado completamente
    time.sleep(1)  # Ajustar conforme necessário

    login(driver, "seu email", "sua senha")

    driver.get('https://portal.gupy.io/my/applications')

# Carregar as credenciais do arquivo JSON
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        json_file_path = 'Caminho para credentials.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_path, scope)
        client = gspread.authorize(credentials)
        # Abrir a planilha desejada
        spreadsheet = client.open('nome da planilha')
        worksheet = spreadsheet.sheet1

        clear_worksheet(worksheet)  # Limpar a planilha antes de adicionar novos dados

        data_list = scrape_application_data(driver)
        update_google_sheet(data_list, worksheet)
        print("Dados adicionados com Sucesso!")
    except Exception as e:
        print("Error:Dados não adicionados à planilha", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
```    
## 7. Código da Automação Vagas Finalizadas:
O código mantem a mesma lógica com algumas alterações, visando explorar o framework Selenium, acessar: [gupy_finalizadas](https://github.com/vevedomiciano/automation_gupy/blob/main/gupy_finalizadas.py)
- As funções no código possuem docstrings que descrevem sua finalidade, parâmetros e valor de retorno. Isso auxilia na compreensão do código e sua manutenção.
- Autenticar na Gupy: Realiza login na plataforma Gupy utilizando as credenciais do usuário.
- Filtrar por Candidaturas Finalizadas: Clica no botão "Finalizadas" para visualizar apenas candidaturas finalizadas.
- Extrair Dados das Candidaturas: Extrai informações para cada candidatura finalizada, incluindo nome da empresa, nome da vaga e status da candidatura.
- Armazenar Dados no Google Sheets: Salva os dados extraídos em uma planilha do Google Sheets.

## 8. Opcional: Data Visualization 
 Os dados extraídos podem ser visualizados e analisados no Looker Studio: [Painel de Candidaturas Gupy](https://lookerstudio.google.com/reporting/3e881c00-1c96-4c59-89ae-d0b86d5734a1)

 ## 9. Conclusão
 Este script demonstra uma automação robusta para extrair dados da plataforma Gupy e armazená-los no Google Sheets. Substitua as credenciais de login da Gupy, caminho do arquivo JSON e nome da planilha do Google Sheets antes de executar o script. Siga as etapas cuidadosamente para garantir o funcionamento correto da automação.

 ## 10. Links Úteis:
- Python: https://docs.python.org/3/
- Selenium: https://www.selenium.dev/documentation/en/getting_started/
- Beautiful Soup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- APIs Google Sheets: https://developers.google.com/sheets/api/quickstart/python
- Looker Studio: https://support.google.com/looker-studio?hl=pt-br#topic=6267740