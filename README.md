# Telegram Bot для управления заявками

Бот для автоматизации распределения и управления заявками с интеграцией CRM-систем.

## Основные функции

- Автоматическое распределение заявок между исполнителями
- Управление категориями услуг и пакетами
- Демо-режим для тестирования
- Интеграция с CRM-системами (Битрикс24, AmoCRM)
- Система безопасности и защиты от спама
- Автоматическая синхронизация с GitHub

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/robinso1/botigor2.git
cd botigor2
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env и настройте переменные окружения:
```
TELEGRAM_BOT_TOKEN=your_token
GITHUB_TOKEN=your_github_token
ADMIN_IDS=[id1,id2]
DATABASE_URL=sqlite:///./bot.db
```

5. Инициализируйте базу данных:
```bash
alembic upgrade head
```

## Запуск

```bash
python main.py
```

## Структура проекта

```
bot/
├── handlers/
│   ├── admin_handlers.py
│   └── user_handlers.py
├── models/
│   └── __init__.py
├── services/
│   ├── request_service.py
│   └── user_service.py
├── utils/
│   ├── crm_utils.py
│   ├── security_utils.py
│   └── github_utils.py
├── __init__.py
└── main.py
```

## Администрирование

Для доступа к панели администратора используйте команду `/admin`.
Доступные функции:
- Управление пользователями
- Просмотр статистики
- Ручное распределение заявок
- Настройка параметров системы

## Безопасность

- Шифрование персональных данных
- Защита от спама
- Ролевой доступ
- Журналирование действий

## Демо-режим

Для тестирования системы включите демо-режим в .env:
```
DEMO_MODE=True
```

## Лицензия

MIT 