import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Загрузка переменных окружения из файла .env
load_dotenv()

# Основные настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "robinso1/botigor2"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Преобразование строки с ID администраторов в список
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "[]")
try:
    ADMIN_IDS = json.loads(ADMIN_IDS_STR)
except json.JSONDecodeError:
    ADMIN_IDS = []

# Настройки демо-режима
DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() in ("true", "1", "t")
DEMO_REQUESTS_PER_DAY = (3, 5)  # Минимальное и максимальное количество демо-заявок в день

# Настройки распределения заявок
DEFAULT_DISTRIBUTION_INTERVAL = 3  # Интервал распределения заявок в часах
DEFAULT_USERS_PER_REQUEST = 3  # Количество пользователей, которым отправляется одна заявка
DEFAULT_MAX_DISTRIBUTIONS = 5  # Максимальное количество распределений одной заявки

# Настройки для мониторинга чатов
MONITORED_CHATS: List[int] = []  # ID чатов для мониторинга заявок

# Статусы заявок
REQUEST_STATUSES = [
    "новая",
    "актуальная",
    "неактуальная",
    "в работе",
    "замер",
    "отказ клиента",
    "выполнена"
]

# Префиксы мобильных номеров по городам
CITY_PHONE_PREFIXES: Dict[str, List[str]] = {
    "Москва": ["495", "499", "925", "926", "977", "999"],
    "Санкт-Петербург": ["812", "921", "911", "981"],
    # Добавьте другие города по необходимости
}

# Категории заявок (будут настраиваться через админ-панель)
DEFAULT_CATEGORIES = [
    "Ремонт квартир",
    "Сантехника",
    "Электрика",
    "Отделка",
    "Строительство",
    "Дизайн интерьера"
]

# Города (будут настраиваться через админ-панель)
DEFAULT_CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Екатеринбург",
    "Новосибирск",
    "Казань"
]

# Настройки веб-сервера для админ-панели
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 8000 