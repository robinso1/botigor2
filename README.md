# Bot Igor 2.0

Бот для распределения заявок между пользователями с учетом категорий и городов.

## Основные функции

- Интеграция с Telegram
- Распределение заявок между пользователями
- Админ-панель для управления
- Демо-режим для тестирования

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/robinso1/botigor2.git
cd botigor2
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python3.11 -m venv venv
source venv/bin/activate  # для Linux/macOS
# или
# venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` с необходимыми переменными окружения:
```env
TELEGRAM_BOT_TOKEN=your_token
ADMIN_IDS=id1,id2
DATABASE_URL=sqlite:///./bot.db
SECRET_KEY=your-secret-key
DEMO_MODE=False
```

## Запуск

1. Запустите приложение:
```bash
python run.py
```

2. Откройте админ-панель в браузере:
```
http://localhost:8000/admin
```

## Структура проекта

- `app/` - основной код приложения
  - `models/` - модели данных
  - `services/` - бизнес-логика
  - `routers/` - эндпоинты FastAPI
  - `templates/` - шаблоны для админ-панели
  - `static/` - статические файлы
- `migrations/` - миграции базы данных
- `tests/` - тесты

## Разработка

1. Создайте новую ветку для своих изменений:
```bash
git checkout -b feature/your-feature-name
```

2. Внесите изменения и создайте коммит:
```bash
git add .
git commit -m "Описание изменений"
```

3. Отправьте изменения в репозиторий:
```bash
git push origin feature/your-feature-name
```

## Лицензия

MIT 