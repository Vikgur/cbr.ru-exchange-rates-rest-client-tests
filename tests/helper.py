import json
import logging

logger = logging.getLogger(__name__)  # Имя логгера — это имя модуля
logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования


def generate_curl_request(url, method="POST", headers=None, body=None):
    """Генерация curl команды для REST API вызовов."""
    headers = headers or {"Content-Type": "application/json"}
    curl_cmd = f"curl -X {method} '{url}'"
    for key, value in headers.items():
        curl_cmd += f" -H '{key}: {value}'"
    if body:
        curl_cmd += f" -d '{json.dumps(body)}'"
    return curl_cmd
