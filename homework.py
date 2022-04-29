import logging
from logging import StreamHandler
import os
from http import HTTPStatus
import sys
import time
from dotenv import load_dotenv
import requests
import telegram
import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def init_logger():
    """Инициализация логирования."""
    logger = logging.getLogger('debug_logger')
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def send_message(bot: telegram.Bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        raise exceptions.MessageNotDelivered(message)


def get_api_answer(current_timestamp):
    """Получение информации от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        answer = requests.get(ENDPOINT,
                              headers=HEADERS, params=params)
    except Exception as err:
        raise exceptions.ConnectionError() from err

    if answer.status_code != HTTPStatus.OK:
        raise exceptions.StatusCodeNot200(answer.status_code)
    return answer.json()


def check_response(response):
    """Проверка полученных от API данных."""
    if not isinstance(response, dict):
        raise TypeError('Полученный от API ответ не в виде словаря.')
    homeworks = response.get('homeworks')
    if not homeworks:
        raise exceptions.NoExpectedKeyInAPIResponse('homeworks')
    if type(homeworks) != list:
        raise exceptions.HomeworksNotInList()
    return homeworks


def parse_status(homework):
    """Получение информации о статусах домашних работ."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('В ответе API отсутствует ключ homework_name.')
    homework_status = homework.get('status')
    verdict = VERDICTS.get(homework_status)
    if not verdict:
        raise exceptions.UnknownHomeworkStatus(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия обязательных переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    return False


def main():
    """Основная логика работы бота."""
    logger = init_logger()
    if not check_tokens():
        message = 'Отсутствует одна из обязательных переменных окружения.'
        logger.critical(message)
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_report = {'name': '', 'message': ''}
    while True:
        curr_report = prev_report.copy()
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                work = homeworks[0]
                message = parse_status(work)
                curr_report['name'] = work.get('homework_name')
                curr_report['message'] = message
                if curr_report != prev_report:
                    send_message(bot, message)
                    log_message = f'Сообщение "{message}" успешно отправлено.'
                    logger.info(log_message)
                    prev_report = curr_report.copy()
            else:
                debug_message = 'Нет изменений в статусах работ.'
                logger.debug(debug_message)
            current_timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            curr_report['message'] = message
            if curr_report != prev_report:
                prev_report = curr_report.copy()
                send_message(bot, message)
            logger.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
