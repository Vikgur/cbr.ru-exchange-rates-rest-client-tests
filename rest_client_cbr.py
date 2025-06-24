import logging

import requests

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CBRClient")


class CBRClient:
    BASE_URL = "https://www.cbr-xml-daily.ru/archive"

    def __init__(self):
        """Создание сессии для оптимизации запросов"""
        self.session = requests.Session()
        logger.info(f"REST-клиент подключен к {self.BASE_URL}")

    def get_exchange_rates(self, date: str):
        """
        Получение курсов валют на указанную дату.
        Формат даты: YYYY-MM-DD (например, 2025-03-01)

        :param date: Дата в формате YYYY-MM-DD
        :return: JSON с курсами валют или None в случае ошибки
        """
        # Преобразуем YYYY-MM-DD в YYYY/MM/DD
        formatted_date = date.replace("-", "/")
        url = f"{self.BASE_URL}/{formatted_date}/daily_json.js"
        logger.info(f"Запрос курса валют на {date}: {url}")
        try:
            response = self.session.get(url)
            response.raise_for_status()  # Вызывает исключение, если код ответа не 200-299
            logger.info(f"Ответ от сервера успешный: {response.status_code}")
            try:
                return response.json()
            except ValueError:
                logger.error(
                    f"Ошибка парсинга JSON в ответе API для даты {date}. Ответ сервера: {response.text}"
                )
                return None  # Возвращает None при невалидном JSON
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе курса валют: {e}")
            return None
