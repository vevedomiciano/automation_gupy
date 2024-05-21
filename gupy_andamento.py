from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# Adicionar os dados à planilha
def update_google_sheet(data_list, worksheet):
    for data in data_list:
        worksheet.append_row(data)

def clear_worksheet(worksheet):
    # Remove todas as linhas, exceto a primeira (cabeçalho)
    worksheet.clear()
    # Se você quiser manter o cabeçalho, remova o comentário da linha abaixo e ajuste conforme necessário
    worksheet.append_row(['Company Name', 'Job Title', 'Application Progress'])

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