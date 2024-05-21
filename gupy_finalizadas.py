from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
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
    except NoSuchElementException:
        print("Error: Botão Aceitar cookies não encontrado.")

# Aviso "Cuidados com Golpe", encontre o botão "Ok, entendi" e clique nele
def click_ok_entendi(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button_ok_entendi = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "safe-check-dialog__confirm-button")))
        button_ok_entendi.click()
    except NoSuchElementException:
        print("Error: Botão ok entendi, não encontrado.")

# Encontre o botão "Entrar com e-mail ou CPF" e clique nele
def click_login_button(driver):
    try:
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Entrar com e-mail ou CPF']")))
        element.click()
    except NoSuchElementException:
        print("Error: Botão 'Entrar com e-mail ou CPF' não encontrado.")

# Preencha o formulário de login
def fill_login_form(driver, email, password):
    try:
        wait = WebDriverWait(driver, 10)
        email_or_cpf_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_or_cpf_field.send_keys(email)
    except NoSuchElementException:
        print("Error: Field 'username' not found.")

    try:
        wait = WebDriverWait(driver, 10)
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password-input")))
        password_field.send_keys(password)
    except NoSuchElementException:
        print("Error: Field 'password-input' not found.")

# Botão acessar a conta
def click_access_account_button(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button_acessar_conta = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.gupy-button span span")))
        button_acessar_conta.click()
    except NoSuchElementException:
        print("Error: Botão 'Acessar conta' não encontrado.")

# Extrair as informações das empresas para as quais você se candidatou
def extract_application_data(driver):
     # Obter o conteúdo HTML da página atual
    html_content = driver.page_source
    # Extrair dados para cada aplicação da página atual
    soup = BeautifulSoup(html_content, 'html.parser')
    applications_section = soup.find('section', class_='sc-3303e2f3-0 gpftOq')
    # Lista para armazenar os dados
    data_list = []
    for article in applications_section.find_all('article'):
        application_status = article.find(class_='sc-23336bc7-1 ewOMrl').text.strip()
        company_name = article.find('p', class_='sc-bBXxYQ eJcDNr sc-1cba52f7-5 kuwnaG').text.strip()
        job_name = article.find('h3', class_='sc-bZkfAO gYfAYo sc-1cba52f7-4 ldEkeI').text.strip()
        data_list.append([application_status, company_name, job_name])
    return data_list

#Clica no botão finalizadas
def click_finalizadas_button(driver):
    try:
        finalizadas_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@role="button" and descendant::div[contains(text(), "Finalizadas")]]'))
        )
        finalizadas_button.click()
    except NoSuchElementException:
        print("Error: Botão 'Finalizadas' não encontrado.")

#Botão próxima página, se houver
def click_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="pagination-next-button"]'))
        )
        next_button.click()
    except NoSuchElementException:
        print("Error:  Botão próxima página não encontrado.")

def clear_worksheet(worksheet):
    # Remove todas as linhas, exceto a primeira (cabeçalho)
    worksheet.clear()
    # Se você quiser manter o cabeçalho, remova o comentário da linha abaixo e ajuste conforme necessário
    worksheet.append_row(['Application Status', 'Company Name', 'Job Name'])

def main():
    # Inicialize o driver do navegador
    driver = webdriver.Chrome()
    driver.get('https://login.gupy.io/candidates/signin')

    accept_cookies(driver)
    click_ok_entendi(driver)
    click_login_button(driver)

    time.sleep(1)

    fill_login_form(driver, "seu email", "sua senha")
    click_access_account_button(driver)

    time.sleep(5)

    # Abra a página de login da Gupy
    driver.get('https://portal.gupy.io/my/applications')

    click_finalizadas_button(driver)  # Clicar no botão "Finalizadas"

    data_list = []
    # Loop para clicar em cada página individualmente
    for page_number in range(1, 9):
        data_list.extend(extract_application_data(driver))
        if page_number != 8:
            click_next_page(driver)

    driver.quit()

    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

    json_file_path = 'Caminho para credentials.json'

    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_path, scope)
    client = gspread.authorize(credentials)

    spreadsheet = client.open('nome da planilha')
    worksheet = spreadsheet.sheet1
    clear_worksheet(worksheet)  # Limpar a planilha antes de adicionar novos dados

    # Adicionar os dados à planilha
    for data in data_list:
        worksheet.append_row(data)
        time.sleep(1)

    print("Dados adicionados com sucesso!")
if __name__ == "__main__":
    main()       



