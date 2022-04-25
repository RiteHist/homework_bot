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
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        log_message = f'Сообщение "{message}" успешно отправлено.'
        logger.info(log_message)
    except Exception:
        error_message = f'Не удалось отправить сообщение "{message}"'
        logger.error(error_message, exc_info=1)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        answer = requests.get(ENDPOINT,
                              headers=HEADERS, params=params)
        return answer.json()
    except Exception:
        error_message = 'Не удалось получить ответ от эндпоинта.'
        logger.error(error_message, exc_info=1)
        return error_message


def check_response(response):
    homeworks = []
    if response:
        try:
            homeworks = response.get('homeworks')
        except KeyError:
            error_message = 'В ответе API отсутствует ключ homeworks'
            logger.error(error_message, exc_info=1)
            return error_message
    return homeworks

def parse_status(homework):
    homework_name = homework.get('lesson_name')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES.get(homework_status)
    except KeyError:
        error_message = 'Неизвестный статус домашней работы.'
        logger.error(error_message, exc_info=1)
        return error_message

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    message = 'Отсутствует одна из обязательных переменных окружения.'
    logger.critical(message)
    return False

def check_for_error(response, last_error, bot: telegram.Bot):
    if type(response) == str:
        if last_error != response:
            send_message(bot, response)
        time.sleep(RETRY_TIME)

def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    
    last_error_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        response = get_api_answer(current_timestamp)
        if type(response) == str:
            if last_error_message != response:
                send_message(bot, response)
            time.sleep(RETRY_TIME)
            continue
        homeworks = check_response(response)
        if type(homeworks) == str:
            if last_error_message != homeworks:
                send_message(bot, homeworks)
            time.sleep(RETRY_TIME)
            continue
        if homeworks:
            for work in homeworks:
                message = parse_status(work)
                if message.startswith('Неизвестный'):
                    send_message(bot, message)
                    continue
                send_message(bot, message)
        else:
            debug_message = 'Нет изменений в статусах работ.'
            logger.debug(debug_message)

        current_timestamp = int(time.time())
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
