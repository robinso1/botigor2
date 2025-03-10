# Руководство по отладке бота

Это руководство поможет вам решить проблемы с ботом и убедиться, что все кнопки работают корректно.

## Содержание

1. [Подготовка](#подготовка)
2. [Автоматическое исправление проблем](#автоматическое-исправление-проблем)
3. [Проверка функциональности](#проверка-функциональности)
4. [Отладка конкретных кнопок](#отладка-конкретных-кнопок)
5. [Часто встречающиеся проблемы](#часто-встречающиеся-проблемы)

## Подготовка

Перед началом отладки убедитесь, что у вас установлены все необходимые зависимости:

```bash
pip install -r requirements.txt
```

Также проверьте, что файл `.env` содержит все необходимые переменные окружения:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=[your_telegram_id]
DATABASE_URL=sqlite:///./bot.db
SECRET_KEY=your_secret_key
DEMO_MODE=True
GITHUB_TOKEN=your_github_token
GITHUB_REPO=robinso1/botigor2
```

## Автоматическое исправление проблем

Для автоматического исправления большинства проблем с ботом выполните следующую команду:

```bash
python fix_bot_issues.py
```

Этот скрипт выполнит следующие действия:

1. Проверит наличие базы данных и создаст ее, если она отсутствует
2. Проверит наличие миграций и применит их, если они отсутствуют
3. Проверит наличие тестовых данных и создаст их, если они отсутствуют
4. Проверит наличие необходимых файлов бота и загрузит их, если они отсутствуют
5. Проверит наличие переменных окружения и создаст файл `.env`, если он отсутствует

После выполнения скрипта будет создан отчет `fix_report.md` с информацией о выполненных исправлениях.

## Проверка функциональности

Для проверки функциональности бота выполните следующую команду:

```bash
python test_bot_functionality.py
```

Этот скрипт проверит работу всех основных функций бота и создаст отчет `test_report.md` с результатами тестирования.

## Отладка конкретных кнопок

### Главное меню

Кнопки в главном меню:
- **👤 Мой профиль** - переход в меню профиля
- **📋 Мои заявки** - просмотр заявок пользователя
- **⚙️ Настройки** - переход в меню настроек
- **🔙 Вернуться в главное меню** - возврат в главное меню

Если какая-то из этих кнопок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для соответствующей кнопки в файле `run_bot_railway.py`

### Меню профиля

Кнопки в меню профиля:
- **🔧 Выбрать категории** - выбор категорий работ
- **🏙️ Выбрать города** - выбор городов
- **📱 Изменить телефон** - изменение телефона
- **🔍 Выбрать подкатегории** - выбор подкатегорий
- **🔙 Вернуться в главное меню** - возврат в главное меню

Если какая-то из этих кнопок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для соответствующей кнопки в файле `run_bot_railway.py`
3. Наличие необходимых данных в базе данных (категории, города, подкатегории)

### Выбор категорий

Кнопки в меню выбора категорий:
- **✅ Категория** - отмена выбора категории
- **❌ Категория** - выбор категории
- **✅ Готово** - завершение выбора категорий
- **🔙 Вернуться в главное меню** - возврат в главное меню

Если какая-то из этих кнопок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для соответствующей кнопки в файле `run_bot_railway.py`
3. Наличие категорий в базе данных

### Выбор городов

Кнопки в меню выбора городов:
- **✅ Город** - отмена выбора города
- **❌ Город** - выбор города
- **✅ Готово** - завершение выбора городов
- **🔙 Вернуться в главное меню** - возврат в главное меню

Если какая-то из этих кнопок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для соответствующей кнопки в файле `run_bot_railway.py`
3. Наличие городов в базе данных

### Выбор подкатегорий

Кнопки в меню выбора подкатегорий:
- **📂 Категория** - выбор категории для настройки подкатегорий
- **✅ Подкатегория** - отмена выбора подкатегории
- **❌ Подкатегория** - выбор подкатегории
- **✅ Готово** - завершение выбора подкатегорий
- **🔙 Назад к категориям** - возврат к выбору категорий
- **🔙 Вернуться в профиль** - возврат в меню профиля

Если какая-то из этих кнопок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для соответствующей кнопки в файле `run_bot_railway.py`
3. Наличие подкатегорий в базе данных
4. Наличие выбранных категорий у пользователя

### Изменение телефона

Если функция изменения телефона не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для ввода телефона в файле `run_bot_railway.py`
3. Корректность валидации телефона

### Просмотр заявок

Если функция просмотра заявок не работает, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчика для кнопки "Мои заявки" в файле `run_bot_railway.py`
3. Наличие заявок у пользователя в базе данных

## Часто встречающиеся проблемы

### Бот не запускается

Если бот не запускается, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие всех необходимых файлов
3. Корректность переменных окружения в файле `.env`
4. Наличие базы данных и применение всех миграций

### Кнопки не работают

Если кнопки не работают, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие обработчиков для соответствующих кнопок в файле `run_bot_railway.py`
3. Наличие необходимых данных в базе данных

### Ошибки при работе с базой данных

Если возникают ошибки при работе с базой данных, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие базы данных и применение всех миграций
3. Корректность структуры базы данных

### Ошибки при работе с подкатегориями

Если возникают ошибки при работе с подкатегориями, проверьте следующее:

1. Логи бота в файле `bot.log`
2. Наличие таблицы `subcategories` в базе данных
3. Наличие подкатегорий в базе данных
4. Наличие выбранных категорий у пользователя

## Заключение

Если вы не можете решить проблему самостоятельно, выполните следующие действия:

1. Запустите скрипт автоматического исправления проблем:
   ```bash
   python fix_bot_issues.py
   ```

2. Запустите скрипт проверки функциональности:
   ```bash
   python test_bot_functionality.py
   ```

3. Запустите бота с поддержкой подкатегорий:
   ```bash
   python run_bot_with_subcategories.py
   ```

4. Проверьте логи бота в файле `bot.log` и логи тестирования в файле `test_bot_functionality.log`

5. Если проблема не решена, обратитесь к разработчику с подробным описанием проблемы и приложите логи. 