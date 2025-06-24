import logging
import os
from datetime import datetime

import pytest

from rest_client_cbr import CBRClient

logger = logging.getLogger(__name__)


@pytest.fixture()
def rest_client():
    """Cоздает REST клиент для тестов"""
    return CBRClient()


def pytest_configure(config):
    """Хук для автологирования"""
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(logs_dir, f"get_rates_{now}.log")

    # Создаём новый обработчик логов
    file_handler = logging.FileHandler(log_filename, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Добавляем обработчик к root-логгеру
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

    # Информируем, что настройка завершена
    root_logger.info("=== Логирование тестовой сессии запущено ===")
