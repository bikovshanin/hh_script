import logging
import os
import sys
import time
from http import HTTPStatus
from sys import exit

import requests
import telegram
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from database import db_insert_query, db_select_query
from exceptions import DataBaseError, HTTPStatusNot204, TelegramSendMessageError
from utils import convert_seconds

load_dotenv()

logging.basicConfig(
    format=('%(asctime)s - %(levelname)s - '
            '%(name)s - %(funcName)s - %(lineno)d - %(message)s'),
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler('log.txt', encoding='UTF-8')]
)

RETRY_PERIOD = 14400

DRIVER_PATH = '/chromedriver_mac_arm64/chromedriver'
USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/121.0.0.0 Safari/537.36')

RESUME_ID = os.getenv('RESUME_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
HH_LOGIN = os.getenv('HH_LOGIN')
HH_PASSWORD = os.getenv('HH_PASSWORD')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

CODE_URL = (f'https://hh.ru/oauth/authorize?response_type=code&client_id='
            f'{CLIENT_ID}')
TOKEN_URL = 'https://hh.ru/oauth/token'
ENDPOINT = f'https://api.hh.ru/resumes/{RESUME_ID}/publish'
USERNAME_INPUT_SELECTOR = ('#HH-React-Root > div > div > div.HH-MainContent.'
                           'HH-Supernova-MainContent > div.main-content.'
                           'main-content_broad-spacing > div > div > div > '
                           'div > div > div:nth-child(1) > div.account-login-'
                           'tile-content-wrapper > div > form > div:nth-'
                           'child(7) > fieldset > input')
PASSWORD_INPUT_SELECTOR = ('#HH-React-Root > div > div > div.HH-MainContent.'
                           'HH-Supernova-MainContent > div.main-content.'
                           'main-content_broad-spacing > div > div > div > '
                           'div > div > div:nth-child(1) > div.account-login-'
                           'tile-content-wrapper > div > form > div:nth-child'
                           '(8) > fieldset > input')
SUBMIT_BUTTON_SELECTOR = ('/html/body/div[5]/div/div/div[4]/div[1]/div/div/'
                          'div/div/div/div[1]/div[1]/div/form/div[7]/button')


def check_tokens(*args):
    """
    Проверка переменных окружения.
    Остановка скрипта в случае отсутствия хотя бы одной.
    """
    for variable in args:
        if not variable:
            logging.critical(
                'Отсутствует одна или несколько '
                'переменных окружения во время запуска скрипта'
            )
            exit(f'ID резюме: {args[0]}\n'
                 f'ID клиента: {args[1]}\n'
                 f'Секрет клиента: {args[2]}\n'
                 f'hh логин: {args[3]}\n'
                 f'hh пароль: {args[4]}\n'
                 f'Токен телеграм: {args[5]}\n'
                 f'ID телеграм: {args[6]}\n')


def send_message(message):
    """Отправка сообщения об ошибках в Telegram."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'В Telegram отправлено сообщение: {message}')
    except Exception as error:
        logging.exception(
            TelegramSendMessageError(f'Сбой при отправке '
                                     f'сообщения в Telegram: {error}')
        )


def get_user_auth_code():
    """Получение кода авторизации для последующего получения токена."""
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={USER_AGENT}')
    options.add_argument('--headless')
    options.binary_location = DRIVER_PATH
    driver = webdriver.Chrome(options=options)
    driver.get(CODE_URL)
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, USERNAME_INPUT_SELECTOR)))
    username_input.send_keys(HH_LOGIN)
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, PASSWORD_INPUT_SELECTOR)))
    password_input.send_keys(HH_PASSWORD)
    try:
        driver.find_element(By.XPATH, SUBMIT_BUTTON_SELECTOR).click()
        logging.info('Кнопка успешно нажата.')
    except Exception as error:
        logging.error(f'Произошла ошибка при нажатии кнопки: {error}')
    time.sleep(10)
    current_url = driver.current_url
    auth_code = current_url.split('=')[1]
    logging.info('Код авторизации получен.')
    driver.quit()
    return auth_code


NEW_TOKEN_FORM = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': get_user_auth_code(),
    'grant_type': 'authorization_code'
}


def post_to_db(response):
    """Запись в базу полученных токенов."""
    try:
        expires_in = int(time.time()) + response['expires_in']
        db_insert_query(response['access_token'], response['refresh_token'],
                        expires_in)
    except Exception as error:
        logging.exception(
            DataBaseError(f'Ошибка при записи в базу данных: {error}')
        )


def get_api_tokens(form):
    """Получение и обновление токенов от API."""
    try:
        response = requests.post(TOKEN_URL, form)
        return response.json()
    except Exception as error:
        message = f'При запросе токенов произошла ошибка: {error}'
        logging.error(message)
        send_message(message)


def execute_rise_cv_up():
    """Поднятие резюме(обновление даты публикации)."""
    data = db_select_query()
    refresh_token_form = {
        "refresh_token": data.refresh_token,
        "grant_type": "refresh_token"
    }
    if data.expires_in - int(time.time()) > 0:
        headers = {'Authorization': 'Bearer ' + data.access_token}
        api_response = requests.post(ENDPOINT, headers=headers)
        return api_response
    tokens = get_api_tokens(refresh_token_form)
    post_to_db(tokens)
    days, hours, minutes = convert_seconds(tokens['expires_in'])
    message = (f'Токены обновлены, следующее обновление '
               f'через {days} дней, {hours} часов, {minutes} минут.')
    send_message(message)
    return execute_rise_cv_up()


def main():
    """
    Основная функция скрипта с циклическим запросом
    к серверу для обновления даты публикации резюме и другой логикой.
    """
    check_tokens(
        RESUME_ID,
        CLIENT_ID,
        CLIENT_SECRET,
        HH_LOGIN,
        HH_PASSWORD,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    )
    response = get_api_tokens(NEW_TOKEN_FORM)
    post_to_db(response)
    while True:
        try:
            cv_response = execute_rise_cv_up()
            if cv_response.status_code != HTTPStatus.NO_CONTENT:
                raise HTTPStatusNot204(
                    f'Код ошибки: {cv_response}'
                    f'\n{cv_response.text}'
                )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
