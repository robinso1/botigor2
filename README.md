# Telegram Bot для распределения заявок

Бот для автоматического распределения заявок между исполнителями на основе категорий и городов.

## Функциональность

- Регистрация пользователей с выбором категорий и городов
- Автоматическое распределение заявок между исполнителями
- Демо-режим для генерации тестовых заявок
- Административная панель для управления категориями, городами и пользователями
- Статистика по заявкам и пользователям
- Интеграция с CRM-системами (Bitrix24, AmoCRM)
- Периодическая отправка информационных сообщений
- Синхронизация с GitHub

## Требования

- Python 3.9-3.11 (не совместимо с Python 3.12+)
- SQLite (для локальной разработки) или PostgreSQL (для продакшн)
- Telegram Bot API Token

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/robinso1/botigor2.git
cd botigor2
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
# Для локальной разработки рекомендуется Python 3.11
python3.11 -m venv venv_py311
source venv_py311/bin/activate  # для Linux/Mac
# или
venv_py311\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` с необходимыми переменными окружения:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=[your_telegram_id]
DATABASE_URL=sqlite:///./bot.db
SECRET_KEY=your_secret_key
DEMO_MODE=True
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repo
```

4. Примените миграции базы данных:
```bash
python apply_migrations.py
```

## Запуск

Для запуска бота выполните:
```bash
python run_bot.py
```

## Деплой

### Railway

1. Создайте новый проект в Railway
2. Подключите репозиторий GitHub
3. Добавьте переменные окружения в настройках проекта
4. Деплой произойдет автоматически

**Примечание**: Railway использует свою версию Python, которая может отличаться от локальной. Конфигурация в `railway.json` настроена для работы с версией Python, доступной в контейнере Railway.

### Heroku

1. Создайте новое приложение в Heroku
2. Подключите репозиторий GitHub или используйте Heroku CLI
3. Добавьте переменные окружения в настройках приложения
4. Деплой произойдет автоматически

## Структура проекта

- `bot/` - основной код бота
  - `handlers/` - обработчики команд и сообщений
  - `models/` - модели базы данных
  - `services/` - сервисы для работы с данными
  - `utils/` - вспомогательные функции
- `migrations/` - миграции базы данных
- `main.py` - точка входа в приложение
- `config.py` - конфигурация приложения
- `run_bot.py` - скрипт для запуска бота с обработкой ошибок

## Администрирование

Для доступа к административной панели:
1. Добавьте свой Telegram ID в переменную `ADMIN_IDS` в файле `.env`
2. Отправьте команду `/admin` боту

## Демо-режим

Для включения демо-режима установите `DEMO_MODE=True` в файле `.env`. В этом режиме бот будет автоматически генерировать тестовые заявки с заданной периодичностью.

## Лицензия

MIT 