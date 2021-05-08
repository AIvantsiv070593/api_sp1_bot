import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[RotatingFileHandler('main.log', maxBytes=50000000,
                                  backupCount=5, encoding='utf-8')],
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s')

logger_bot = logging.getLogger(__name__)
logger_bot.setLevel(logging.DEBUG)
handler_bot = RotatingFileHandler('logger_bot.log', maxBytes=10000000,
                                  backupCount=5, encoding='utf-8')
handler_bot.setFormatter(formatter)
logger_bot.addHandler(handler_bot)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
url_api = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}


def parse_homework_status(homework):
    """Определяет статус домашней работы."""
    if homework['homework_name'] and homework['status']:
        homework_name = homework['homework_name']
        verdict = ('Работа не НАЙДЕНА или Статус работы неизвестен, '
                   'проверте правильность запроса!')
        if homework['status'] == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        elif homework['status'] == 'approved':
            verdict = ('Ревьюеру всё понравилось, '
                       'можно приступать к следующему уроку.')
        elif homework['status'] == 'reviewing':
            verdict = 'Работа проверяется.'
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    else:
        return verdict


def get_homework_statuses(current_timestamp):
    """Получает статус домашней работы."""
    data = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url_api, params=data, headers=headers)
        return homework_statuses.json()
    except requests.exceptions.RequestException as er:
        logger_bot.error(f'Ошибка {er} при запросе статуса домашней работы')


def send_message(message, bot_сlient):
    """Отправляет сообщение в телеграмм."""
    logger_bot.info('Отправка сообщения')
    return bot_сlient.send_message(CHAT_ID, message)


def main():
    # проинициализировать бота здесь
    bot_сlient = telegram.Bot(token=TELEGRAM_TOKEN)
    logger_bot.debug('Запуск бота')
    send_message('Бот запущен!', bot_сlient)
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_сlient)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)
        except Exception as e:
            logger_bot.error(f'Бот столкнулся с ошибкой: {e}')
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_сlient)
            time.sleep(150)


if __name__ == '__main__':
    main()
