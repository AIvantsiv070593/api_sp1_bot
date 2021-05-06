import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
url_api = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
bot_сlient = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    """Определяет статус домашней работы."""
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    """Получает статус домашней работы."""
    data = {'from_date': current_timestamp}
    homework_statuses = requests.get(url_api, params=data, headers=headers)
    return homework_statuses.json()


def send_message(message, bot_сlient):
    """Отправляет сообщение в телеграмм."""
    return bot_сlient.send_message(CHAT_ID, message)


def main():
    # проинициализировать бота здесь
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_сlient)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
