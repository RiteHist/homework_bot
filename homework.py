import logging
from logging import StreamHandler
import os
import sys
import time
from dotenv import load_dotenv
import requests
import telegram


load_dotenv()
logger = logging.getLogger('debug_logger')
logger.setLevel(logging.DEBUG)
handler = StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: telegram.Bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        answer = requests.get(ENDPOINT,
                              headers=HEADERS, params=params)
        return answer.json()
    except Exception:
        return {}


def check_response(response):
    homeworks = []
    if response:
        homeworks = response.get('homeworks')
        return homeworks
    return homeworks


def parse_status(homework):
    homework_name = homework.get('lesson_name')
    homework_status = homework.get('status')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False

def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = ''
    
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                for work in homeworks:
                    message = parse_status(work)
                    send_message(bot, message)

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
