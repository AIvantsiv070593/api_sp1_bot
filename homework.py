import logging
import os
import os.path
import time
import sys
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s')

logger_bot = logging.getLogger(__name__)
logger_bot.setLevel(logging.DEBUG)
handler_bot = RotatingFileHandler('logger_bot.log', maxBytes=10000000,
                                  backupCount=5, encoding='utf-8')
handler_bot.setFormatter(formatter)
logger_bot.addHandler(handler_bot)

load_dotenv()
try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as er:
    logger_bot.error(f'Ключ {er} не найден')
    sys.exit(f'Ключ {er} не найден')
URL_API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
DICT_STATUSES = {'rejected': 'К сожалению в работе нашлись ошибки.',
                 'approved': ('Ревьюеру всё понравилось, '
                              'можно приступать к следующему уроку.'),
                 'reviewing': 'Работа проверяется.'}
SLEEP_MAIN = 300
SLEEP_EXCEPTION = 150


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
    except KeyError as er:
        logger_bot.error(f'Работа {er} не найдена!')
        return (f'Работа {er} не найдена!\n\nПроверте запрос!')
    try:
        homework_status = homework['status']
    except KeyError as er:
        logger_bot.error(f'Статус {er} не найден!')
        return(f'Статус {er} не найден!\n\nПроверте запрос!')
    try:
        verdict = DICT_STATUSES[homework_status]
    except KeyError as er:
        logger_bot.error(f'Работа или статус работы не найдены: {er}')
        return(f'Получен неизвестный статус {homework_status} !'
               '\n\nПроверте запрос!')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    """Получает статус домашней работы."""
    data = {'from_date': current_timestamp}
    try:
        response = requests.get(URL_API, params=data, headers=HEADERS)
        # response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as er:
        raise requests.exceptions.RequestException(
            f'Ошибка {er} при запросе на {URL_API}')


def send_message(message, bot_сlient):
    """Отправляет сообщение в телеграмм."""
    try:
        logger_bot.info(f'Отправка сообщения | {message}')
        return bot_сlient.send_message(CHAT_ID, message)
    except telegram.error.BadRequest as er:
        logger_bot.error(f'ОШИБКА ОТПРАВКИ | {str(er)}')


def main():
    bot_сlient = telegram.Bot(token=TELEGRAM_TOKEN)
    logger_bot.info('Запуск бота')
    try:
        bot_сlient.getMe()
        send_message('Бот запущен!', bot_сlient)
    except telegram.error.Unauthorized as er:
        logger_bot.error(f'Бот не запущен ОШИБКА АВТОРИЗАЦИИ | {str(er)}')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]), bot_сlient)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(SLEEP_MAIN)
        except telegram.error.BadRequest:
            time.sleep(SLEEP_EXCEPTION)
        except telegram.error.Unauthorized:
            time.sleep(SLEEP_EXCEPTION)
        except Exception as er:
            logger_bot.error(f'Бот столкнулся с ошибкой: {er}')
            send_message(f'Бот столкнулся с ошибкой: {er}', bot_сlient)
            time.sleep(SLEEP_EXCEPTION)


if __name__ == '__main__':
    PATH = os.path.dirname(os.path.abspath(__file__))
    FILENAME = os.path.join(PATH, 'main.log')
    logging.basicConfig(level=logging.DEBUG,
                        handlers=[RotatingFileHandler(FILENAME,
                                                      maxBytes=50000000,
                                                      backupCount=5,
                                                      encoding='utf-8')],
                        format=('%(asctime)s, %(levelname)s,'
                                '%(message)s, %(name)s'))
    main()
