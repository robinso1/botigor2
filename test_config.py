import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import secrets

# Загрузка переменных окружения из файла .env
load_dotenv()

# Основные настройки
TELEGRAM_BOT_TOKEN = "YOUR_TEST_TOKEN_HERE"  # Замените на тестовый токен
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "robinso1/botigor2")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_bot.db")

# Генерация безопасного ключа, если он не указан в переменных окружения
# SECRET_KEY используется для шифрования персональных данных и должен быть надежно защищен
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Генерируем случайный ключ длиной 32 байта (256 бит)
    SECRET_KEY = secrets.token_hex(32)
    print("WARNING: SECRET_KEY не найден в переменных окружения. Сгенерирован временный ключ.")
    print("Для продакшн-среды рекомендуется установить постоянный SECRET_KEY в .env файле.")

# Преобразование строки с ID администраторов в список
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "[]")
try:
    ADMIN_IDS = json.loads(ADMIN_IDS_STR)
except json.JSONDecodeError:
    ADMIN_IDS = []

# Настройки демо-режима
DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() in ("true", "1", "t")
DEMO_REQUESTS_PER_DAY = (3, 5)  # Минимальное и максимальное количество демо-заявок в день
DEMO_PHONE_MASK_PERCENT = 60  # Процент скрытия номера телефона
DEMO_GENERATION_INTERVALS = {
    "min": 3 * 3600,  # 3 часа в секундах
    "max": 6 * 3600   # 6 часов в секундах
}  # Интервал генерации демо-заявок в часах

# Настройки распределения заявок
DEFAULT_DISTRIBUTION_INTERVAL = 3  # Интервал распределения заявок в часах
DEFAULT_USERS_PER_REQUEST = 3  # Основной поток: до 3 пользователей
RESERVE_USERS_PER_REQUEST = 2  # Резервный поток: до 2 дополнительных
DEFAULT_MAX_DISTRIBUTIONS = 5  # Максимальное количество распределений одной заявки

# Режим отладки
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")

# Настройки логирования
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "test_bot.log"

# Настройки безопасности
MAX_REQUESTS_PER_MINUTE = 30  # Максимальное количество запросов от одного пользователя в минуту
SPAM_BLOCK_DURATION = 60  # Длительность блокировки при обнаружении спама (в секундах)

# Настройки уведомлений
NOTIFICATION_DELAY = 60  # Задержка между уведомлениями в секундах

# Вывод информации о конфигурации при запуске
if DEBUG_MODE:
    print(f"Запуск в режиме отладки. Уровень логирования: {LOG_LEVEL}")
    print(f"Демо-режим: {'Включен' if DEMO_MODE else 'Выключен'}")
    print(f"Администраторы: {ADMIN_IDS}")
    print(f"База данных: {DATABASE_URL}")
    print(f"GitHub репозиторий: {GITHUB_REPO}")
    print(f"Настройки распределения: {DEFAULT_USERS_PER_REQUEST} основных + {RESERVE_USERS_PER_REQUEST} резервных пользователей")

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
    "завершена",
    "ожидание подтверждения"
]

# Префиксы мобильных номеров по городам
CITY_PHONE_PREFIXES = {
    "Москва": ["495", "499", "496"],
    "Санкт-Петербург": ["812", "921", "911"],
    "Екатеринбург": ["343", "922", "912"],
    "Новосибирск": ["383", "923", "913"],
    "Казань": ["843", "917", "919"]
}

# Категории услуг
DEFAULT_CATEGORIES = [
    # Основные категории
    "Сантехника",
    "Электрика",
    "Натяжные потолки",
    "Дизайн интерьера",
    "Кухни на заказ",
    "Ремонт квартир под ключ",
    "Строительство домов: каркасные",
    "Строительство домов: блочные",
    "Остекление балконов и лоджий"
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

# Настройки GitHub
GITHUB_SYNC_INTERVAL = 15  # Интервал синхронизации с GitHub в минутах 

# Security Settings
MAX_WARNINGS = 3
BLOCK_DURATION_HOURS = 24

# Service Packages
SERVICE_PACKAGES = [
    {
        'name': 'Ремонт ванной комнаты',
        'services': ['Сантехника', 'Электрика', 'Натяжные потолки']
    },
    {
        'name': 'Комплексный ремонт квартиры',
        'services': ['Ремонт квартир под ключ', 'Дизайн интерьера', 'Кухни на заказ']
    },
    {
        'name': 'Строительство и отделка дома',
        'services': ['Строительство домов: каркасные', 'Электрика', 'Сантехника']
    },
    {
        'name': 'Отделка балкона',
        'services': ['Остекление балконов и лоджий', 'Электрика']
    }
] 