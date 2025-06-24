import json
import logging

import allure
import pytest
import requests

from tests.helper import generate_curl_request

logger = logging.getLogger(__name__)


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
@pytest.mark.parametrize(
    "test_date, expected_status",
    [
        ("2025-03-01", True),  # Ожидаем успешный ответ
        ("2025-13-01", False),  # Некорректный месяц
        ("abcd-ef-gh", False),  # Полностью некорректная дата
        ("2030-01-01", False),  # Будущая дата, которой нет в архиве
        ("1900-01-01", False),  # Старая дата, архив недоступен
    ],
    ids=["valid_date", "invalid_month", "invalid_format", "future_date", "old_date"],
)
def test_get_exchange_rates_various_dates(rest_client, test_date, expected_status):
    """Проверяем, что REST API ЦБ РФ корректно обрабатывает разные даты"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Формирование запроса"):
        request_body = {"date": test_date}
        allure.attach(
            json.dumps(request_body, ensure_ascii=False, indent=2),
            name="Тело запроса",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step("Формирование curl команды"):
        curl_cmd = generate_curl_request(
            url="http://testserver/api/v1/cbr/rates", method="POST", body=request_body
        )
        allure.attach(
            curl_cmd, name="curl команда", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Отправка запроса"):
        logger.info(
            f"Отправляем запрос на {test_date}, ожидаем статус: {expected_status}"
        )
        rates = rest_client.get_exchange_rates(test_date)

    with allure.step("Проверка ответа сервера"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Тело ответа",
            attachment_type=allure.attachment_type.JSON,
        )

        if expected_status:
            logger.info(f"Проверяем, что ответ от API не пуст для даты {test_date}")
            assert rates, f"Ошибка: REST API не вернул данные для даты {test_date}"

            logger.info(f"Проверяем структуру ответа для даты {test_date}")
            for key in ["Date", "PreviousDate", "Valute"]:
                logger.info(f"Ищем ключ {key} в ответе...")
                assert key in rates, f"Ошибка: В ответе API отсутствует ключ {key}"

            logger.info(
                f"Проверяем наличие ключевых валют (USD, EUR) в ответе для {test_date}"
            )
            for currency in ["USD", "EUR"]:
                assert (
                    currency in rates["Valute"]
                ), f"Ошибка: В данных отсутствует {currency}"

                value = rates["Valute"][currency]["Value"]
                logger.info(f"Проверяем, что курс {currency} ({value}) – число и > 0")
                assert isinstance(
                    value, (int, float)
                ), f"Ошибка: Курс {currency} должен быть числом, а не {type(value)}"
                assert (
                    value > 0
                ), f"Ошибка: Курс {currency} должен быть положительным, но получено {value}"

            logger.info(f"Тест пройден для даты {test_date}: курсы валют корректны.")
        else:
            logger.info(
                f"Проверяем, что ответ от API не приходит для некорректной даты {test_date}"
            )
            assert (
                rates is None
            ), f"Ошибка: Ожидали, что API не вернет данные для даты {test_date}, но они пришли!"
            logger.info(
                f"Тест пройден: API корректно обработал некорректную дату {test_date}."
            )


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
def test_session_reuse(rest_client):
    """Проверяем, что REST клиент использует одну и ту же сессию между вызовами"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Проверяем повторное использование сессии"):
        session_id_1 = id(rest_client.session)
        session_id_2 = id(rest_client.session)

        logger.info(
            f"Сравниваем идентификаторы сессий: {session_id_1} и {session_id_2}"
        )
        assert (
            session_id_1 == session_id_2
        ), "Ошибка: Объект сессии изменился между вызовами, что не оптимально"
        logger.info("Тест пройден: Сессия повторно используется.")


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
def test_get_exchange_rates_server_errors(rest_client, monkeypatch):
    """Проверяем, что API корректно обрабатывает ошибки сервера (500)"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Формирование запроса"):
        request_params = {"date": "2025-03-01"}
        allure.attach(
            json.dumps(request_params, ensure_ascii=False, indent=2),
            name="Параметры запроса",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step("Формирование curl команды"):
        # Так как метод get_exchange_rates() обычно делает GET,
        # сформируем «условный» curl для наглядности (даже если реальный вызов замокан).
        curl_cmd = f"curl -X GET 'http://testserver/api/v1/cbr/rates?date={request_params['date']}'"
        allure.attach(
            curl_cmd, name="curl команда", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Подмена метода get на mock"):

        class MockResponse:
            status_code = 500

            def raise_for_status(self):
                raise requests.exceptions.HTTPError("500 Internal Server Error")

        def mock_get(*args, **kwargs):
            return MockResponse()

        monkeypatch.setattr(rest_client.session, "get", mock_get)
        logger.info(
            "Метод rest_client.session.get успешно заменён на mock, возвращающий 500."
        )

    with allure.step("Отправка запроса"):
        logger.info("Отправляем запрос, ожидаем None из-за 500 ошибки сервера.")
        rates = rest_client.get_exchange_rates("2025-03-01")

    with allure.step("Проверка ответа сервера"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Тело ответа (mocked)",
            attachment_type=allure.attachment_type.JSON,
        )
        assert (
            rates is None
        ), "Ошибка: Ожидали, что API вернет None при ошибке сервера 500"
        logger.info("Тест пройден: API корректно обработал ошибку 500.")


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
def test_get_exchange_rates_404_error(rest_client, monkeypatch):
    """Проверяем, что API корректно обрабатывает ошибку 404 Not Found"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Формирование запроса"):
        request_params = {"date": "2025-03-01"}
        allure.attach(
            json.dumps(request_params, ensure_ascii=False, indent=2),
            name="Параметры запроса",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step("Формирование curl команды"):
        curl_cmd = f"curl -X GET 'http://testserver/api/v1/cbr/rates?date={request_params['date']}'"
        allure.attach(
            curl_cmd, name="curl команда", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Подмена метода get на mock"):

        class MockResponse:
            status_code = 404

            def raise_for_status(self):
                raise requests.exceptions.HTTPError("404 Not Found")

        def mock_get(*args, **kwargs):
            return MockResponse()

        monkeypatch.setattr(rest_client.session, "get", mock_get)
        logger.info(
            "Метод rest_client.session.get успешно заменён на mock, возвращающий 404."
        )

    with allure.step("Отправка запроса"):
        logger.info("Отправляем запрос, ожидаем None из-за 404 ошибки сервера.")
        rates = rest_client.get_exchange_rates("2025-03-01")

    with allure.step("Проверка ответа сервера"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Тело ответа (mocked)",
            attachment_type=allure.attachment_type.JSON,
        )
        assert rates is None, "Ошибка: Ожидали, что API вернет None при 404 Not Found"
        logger.info("Тест пройден: API корректно обработал ошибку 404.")


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
def test_get_exchange_rates_invalid_json(rest_client, monkeypatch):
    """Проверяем, что API корректно обрабатывает случай, когда сервер возвращает невалидный JSON"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Формирование запроса"):
        request_params = {"date": "2025-03-01"}
        allure.attach(
            json.dumps(request_params, ensure_ascii=False, indent=2),
            name="Параметры запроса",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step("Формирование curl команды"):
        curl_cmd = f"curl -X GET 'http://testserver/api/v1/cbr/rates?date={request_params['date']}'"
        allure.attach(
            curl_cmd, name="curl команда", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Подмена метода get на mock для невалидного JSON"):

        class MockResponse:
            status_code = 200
            text = "INVALID JSON RESPONSE"  # Добавлено для логирования

            def raise_for_status(self):
                pass

            def json(self):
                raise ValueError("Invalid JSON")  # Симулируем ошибку JSON

        def mock_get(*args, **kwargs):
            return MockResponse()

        monkeypatch.setattr(rest_client.session, "get", mock_get)
        logger.info("Метод get подменен на mock, возвращающий невалидный JSON.")

    with allure.step("Отправка запроса"):
        rates = rest_client.get_exchange_rates("2025-03-01")
        logger.info("Запрос отправлен, обработка невалидного JSON.")

    with allure.step("Проверка ответа сервера"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Тело ответа (mocked)",
            attachment_type=allure.attachment_type.JSON,
        )
        assert rates is None, "Ошибка: Ожидали, что API вернет None при невалидном JSON"
        logger.info("Тест пройден: API корректно обработал невалидный JSON.")


@allure.feature("REST: Ходим на cbr.ru и берем курсы валют")
@allure.label("owner", "Viktor Gurko")
def test_get_exchange_rates_network_errors(rest_client, monkeypatch):
    """Проверяем, что API корректно обрабатывает сетевые ошибки и тайм-ауты"""
    logging.info("Тест запущен: проверка получения курсов валют с сайта ЦБР")

    with allure.step("Формирование запроса"):
        request_params = {"date": "2025-03-01"}
        allure.attach(
            json.dumps(request_params, ensure_ascii=False, indent=2),
            name="Параметры запроса",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step("Формирование curl команды"):
        curl_cmd = f"curl -X GET 'http://testserver/api/v1/cbr/rates?date={request_params['date']}'"
        allure.attach(
            curl_cmd, name="curl команда", attachment_type=allure.attachment_type.TEXT
        )

    # Сценарий 1: ConnectionError
    with allure.step("Подмена метода get на mock для ConnectionError"):

        def mock_get(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Connection lost")

        monkeypatch.setattr(rest_client.session, "get", mock_get)
        logger.info("Подмена метода get: ConnectionError.")

    with allure.step("Отправка запроса для ConnectionError"):
        rates = rest_client.get_exchange_rates("2025-03-01")

    with allure.step("Проверка ответа для ConnectionError"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Ответ при ConnectionError",
            attachment_type=allure.attachment_type.JSON,
        )
        assert rates is None, "Ошибка: Ожидали, что API вернет None при ConnectionError"

    # Сценарий 2: Timeout
    with allure.step("Подмена метода get на mock для Timeout"):

        def mock_get_timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("Request timed out")

        monkeypatch.setattr(rest_client.session, "get", mock_get_timeout)
        logger.info("Подмена метода get: Timeout.")

    with allure.step("Отправка запроса для Timeout"):
        rates = rest_client.get_exchange_rates("2025-03-01")

    with allure.step("Проверка ответа для Timeout"):
        allure.attach(
            json.dumps(rates, ensure_ascii=False, indent=2) if rates else "No data",
            name="Ответ при Timeout",
            attachment_type=allure.attachment_type.JSON,
        )
        assert rates is None, "Ошибка: Ожидали, что API вернет None при Timeout"

    logger.info("Тест пройден: API корректно обработал ConnectionError и Timeout.")
