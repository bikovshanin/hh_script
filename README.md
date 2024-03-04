# Скрипт для обновления даты публикации резюме на hh.ru
___
### Стек технологий:

[![pre-commit](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3111/)
[![pre-commit](https://img.shields.io/badge/selenium-4.18-43B02A?logo=selenium&logoColor=white)](https://www.selenium.dev/documentation/)
[![pre-commit](https://img.shields.io/badge/sqlalchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.selenium.dev/documentation/)
[![pre-commit](https://img.shields.io/badge/sqlite-db-003B57?logo=sqlite&logoColor=white)](https://docs.sqlalchemy.org/en/20/)
[![pre-commit](https://img.shields.io/badge/python_telegram_bot-13.7-26A5E4?logo=telegram&logoColor=white)](https://docs.python-telegram-bot.org/en/v13.7/)
[![pre-commit](https://img.shields.io/badge/HeadHunter_API-1.0-26A5E4?)](https://api.hh.ru/openapi/redoc)
___
### Описание и возможности:
Скрипт работает через официальный API от hh.ru. При первом запуске получает
токены для авторизации. Автоматически обновляет токены после истечения их срока (14 дней).
Обновляет дату публикации резюме каждые 4 часа. Отправляет сообщения через Telegram-бота 
в случае возникновения ошибок и при обновлении токенов. Для мониторинга работы скрипта используется логирование в файл ``log.txt``
___
### Перед запуском скрипта необходимо:
- Получить доступ к hh api, [сделав запрос в личном кабинете.](https://dev.hh.ru/admin?logout=true)
  Это позволяет получать авторизационные ключи (токены) для
  пользователей hh.ru
- Для первого получения токенов от hh api понадобится логин и пароль учетной записи. Для получения кода авторизации пользователя.
- Так же необходим id резюме. Можно посмотреть в url при переходе на страницу резюме, например: ``https://spb.hh.ru/resume/1234567eff033ee4d60028ed1f32384f6f706f``.
  ``1234567eff033ee4d60028ed1f32384f6f706f`` - эта часть url и есть id резюме.
- Так как при первом запуске используется ``selenium``, то будет не лишним проверить селекторы через инструменты разработчика браузера. Пройдя по ссылке: ``https://hh.ru/oauth/authorize?response_type=code&client_id={CLIENT_ID}``, 
  CLIENT_ID нужно взять в личном кабинете hh api.
```Python
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
```
- Получить токен Telegram-бота, через [BotFather.](https://telegram.me/BotFather) Так же понадобится Telegram ID пользователя, которому будут отправляться сообщения.
- Все переменные разместить в файле .env
```Python
RESUME_ID=id резюме, которое необходимо обновлять
CLIENT_ID=из личного кабинета hh api
CLIENT_SECRET=из личного кабинета hh api
TELEGRAM_TOKEN=от BotFather
TELEGRAM_CHAT_ID=id того, кому отправлять сообщения в Telegram
HH_LOGIN=логин hh.ru
HH_PASSWORD=пароль hh.ru
```
- Будет не лишним, ознакомиться с [документацией HH API](https://api.hh.ru/openapi/redoc#section/Obshaya-informaciya)
___
### Для запуска скрипта на VPS сервере:
- Для корректной работы скрипта необходимо установить на сервер google-chrome и совместимый с ним ChromeDriver. Актуальные версии можно найти на [официальном сайте.](https://sites.google.com/chromium.org/driver/home?authuser=0) Для установки можно воспользоваться [инструкцией.](https://skolo.online/documents/webscrapping/#step-1-download-chrome)
- Перемещаем файлы со скриптом на удалённый сервер удобным способом. Создаём файл .env c необходимыми переменными окружения в директории с исполняемыми файлами.
- Для запуска скрипта воспользуемся [утилитой screen.](https://www.8host.com/blog/ispolzovanie-screen-na-servere-ubuntu/)
- Создаём ``screen`` командой:
```shell
screen -S hh_script
```
- Переходим в директорию с файлами скрипта
- Создаём и активируем виртуальное окружение:
```shell
python3 -m venv venv
source venv/bin/activate
```
- Устанавливаем зависимости:
```shell
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
- Запускаем скрипт:
```shell
python3 main.py
```
- Сворачиваем ``screen`` - ``ctrl a + d``
