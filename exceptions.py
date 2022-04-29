class StatusCodeNot200(Exception):
    """Исключение при получении от API кода, отличного от 200."""

    def __init__(self, code):
        self.code = code
        super().__init__()

    def __str__(self):
        return f'От API получен код {self.code}. Ожидается 200.'


class NoExpectedKeyInAPIResponse(Exception):
    """Иключение для ситуации, когда в ответе API нет ожидаемого ключа."""

    def __init__(self, key):
        self.key = key
        super().__init__()

    def __str__(self):
        return f'В ответе API нет ключа {self.key}'


class UnknownHomeworkStatus(Exception):
    """Исключение для ситуации, когда у домашней работы неизвестный статус."""

    def __init__(self, status):
        self.status = status
        super().__init__()

    def __str__(self):
        return f'Неизвестный статус домашней работы: {self.status}'


class HomeworksNotInList(Exception):
    """
    Иключение для ситуации, когда домашние работы
    в ответе API не в виде списка.
    """

    def __str__(self):
        return 'Домашние работы в ответе API не в виде списка'


class MessageNotDelivered(Exception):
    """
    Исключение при неудачной отправке сообщения.
    """

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return f'Не удалось отправить сообщение "{self.message}"'


class ConnectionError(Exception):
    """Исключение при ошибке соединения с эндпоинтом."""

    def __str__(self):
        return 'Ошибка соединения с эндпоинтом.'
