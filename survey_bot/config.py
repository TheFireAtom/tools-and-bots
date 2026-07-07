import os
from typing import cast
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

_bot_token = os.getenv("BOT_TOKEN")

if not _bot_token:
    raise ValueError(
        "BOT_TOKEN не найден! Создай файл .env и добавь туда BOT_TOKEN=твой_токен"
    )

# cast() явно говорит Pylance/mypy: "доверься мне, дальше это точно str".
BOT_TOKEN = cast(str, _bot_token)