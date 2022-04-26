import logging
from logging import StreamHandler
import os
import sys
import time
from dotenv import load_dotenv
import requests
import telegram
import exceptions

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
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        log_message = f'Сообщение "{message}" успешно отправлено.'
        logger.info(log_message)
    except Exception:
        error_message = f'Не удалось отправить сообщение "{message}"'
        logger.error(error_message, exc_info=1)


def get_api_answer(current_timestamp):
    """Получение информации от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    answer = requests.get(ENDPOINT,
                          headers=HEADERS, params=params)
    if answer.status_code != 200:
        raise exceptions.StatusCodeNot200(answer.status_code)
    return answer.json()


def check_response(response):
    """Проверка полученных от API данных."""
    if type(response) != dict:
        raise TypeError
    homeworks = response.get('homeworks')
    if not homeworks:
        raise exceptions.NoExpectedKeyInAPIResponse('homeworks')
    if type(homeworks) != list:
        raise exceptions.HomeworksNotInList
    return homeworks


def parse_status(homework):
    """Получение информации о статусах домашних работ."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        raise exceptions.UnknownHomeworkStatus(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия обязательных переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    message = 'Отсутствует одна из обязательных переменных окружения.'
    logger.critical(message)
    return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()

    last_error_message = ''
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
            else:
                debug_message = 'Нет изменений в статусах работ.'
                logger.debug(debug_message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_error_message != str(error):
                last_error_message = str(error)
                send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
