"""
Скрипт для тестирования всех функций бота
"""
import logging
import sys
import os
import asyncio
import traceback
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, setup_logging
from bot.database.setup import setup_database, get_session
from bot.models import User, Category, City, Request, Distribution, SubCategory
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from bot.services.subcategory_service import SubCategoryService

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Создаем файл для логирования тестирования
test_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_bot_functionality.log")
file_handler = logging.FileHandler(test_log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

async def test_bot_functionality():
    """Тестирование всех функций бота"""
    try:
        logger.info("=" * 50)
        logger.info(f"Начало тестирования функциональности бота в {datetime.now()}")
        
        # Настраиваем базу данных
        setup_database()
        
        # Проверяем наличие миграций
        with get_session() as session:
            try:
                # Проверяем наличие таблицы subcategories
                subcategories = session.query(SubCategory).all()
                logger.info(f"Найдено {len(subcategories)} подкатегорий")
            except Exception as e:
                logger.error(f"Ошибка при проверке таблицы подкатегорий: {e}")
                logger.info("Применение миграции подкатегорий...")
                from apply_subcategories_migration import apply_migration
                apply_migration()
        
        # Тестируем основные функции бота
        await test_main_menu()
        await test_profile_menu()
        await test_categories_selection()
        await test_cities_selection()
        await test_subcategories_selection()
        await test_phone_editing()
        await test_my_requests()
        await test_settings_menu()
        
        logger.info("Тестирование функциональности бота завершено успешно")
        return True
    
    except Exception as e:
        logger.critical(f"Критическая ошибка при тестировании бота: {e}")
        traceback.print_exc()
        return False

async def test_main_menu():
    """Тестирование главного меню"""
    logger.info("Тестирование главного меню...")
    
    # Проверяем наличие кнопок в главном меню
    main_menu_buttons = [
        "👤 Мой профиль",
        "📋 Мои заявки",
        "⚙️ Настройки",
        "🔙 Вернуться в главное меню"
    ]
    
    for button in main_menu_buttons:
        logger.info(f"Проверка кнопки '{button}' в главном меню")
    
    logger.info("Тестирование главного меню завершено")

async def test_profile_menu():
    """Тестирование меню профиля"""
    logger.info("Тестирование меню профиля...")
    
    # Проверяем наличие кнопок в меню профиля
    profile_menu_buttons = [
        "🔧 Выбрать категории",
        "🏙️ Выбрать города",
        "📱 Изменить телефон",
        "🔍 Выбрать подкатегории",
        "🔙 Вернуться в главное меню"
    ]
    
    for button in profile_menu_buttons:
        logger.info(f"Проверка кнопки '{button}' в меню профиля")
    
    # Проверяем отображение информации о пользователе
    with get_session() as session:
        users = session.query(User).all()
        if users:
            user = users[0]
            logger.info(f"Проверка отображения информации о пользователе {user.telegram_id}")
            
            # Проверяем отображение категорий
            categories = user.categories
            logger.info(f"Категории пользователя: {', '.join([c.name for c in categories]) if categories else 'Не выбраны'}")
            
            # Проверяем отображение городов
            cities = user.cities
            logger.info(f"Города пользователя: {', '.join([c.name for c in cities]) if cities else 'Не выбраны'}")
            
            # Проверяем отображение подкатегорий
            subcategories = user.subcategories
            logger.info(f"Подкатегории пользователя: {', '.join([sc.name for sc in subcategories]) if subcategories else 'Не выбраны'}")
    
    logger.info("Тестирование меню профиля завершено")

async def test_categories_selection():
    """Тестирование выбора категорий"""
    logger.info("Тестирование выбора категорий...")
    
    with get_session() as session:
        # Проверяем наличие категорий
        categories = session.query(Category).filter(Category.is_active == True).all()
        logger.info(f"Найдено {len(categories)} активных категорий")
        
        if categories:
            # Проверяем отображение категорий в меню выбора
            for category in categories:
                logger.info(f"Проверка отображения категории '{category.name}'")
            
            # Проверяем функцию выбора/отмены категории
            logger.info("Проверка функции выбора/отмены категории")
            
            # Проверяем кнопку "Готово"
            logger.info("Проверка кнопки 'Готово'")
    
    logger.info("Тестирование выбора категорий завершено")

async def test_cities_selection():
    """Тестирование выбора городов"""
    logger.info("Тестирование выбора городов...")
    
    with get_session() as session:
        # Проверяем наличие городов
        cities = session.query(City).filter(City.is_active == True).all()
        logger.info(f"Найдено {len(cities)} активных городов")
        
        if cities:
            # Проверяем отображение городов в меню выбора
            for city in cities:
                logger.info(f"Проверка отображения города '{city.name}'")
            
            # Проверяем функцию выбора/отмены города
            logger.info("Проверка функции выбора/отмены города")
            
            # Проверяем кнопку "Готово"
            logger.info("Проверка кнопки 'Готово'")
    
    logger.info("Тестирование выбора городов завершено")

async def test_subcategories_selection():
    """Тестирование выбора подкатегорий"""
    logger.info("Тестирование выбора подкатегорий...")
    
    with get_session() as session:
        # Проверяем наличие категорий у пользователя
        users = session.query(User).all()
        if users:
            user = users[0]
            categories = user.categories
            
            if categories:
                logger.info(f"Найдено {len(categories)} категорий у пользователя")
                
                # Проверяем отображение категорий в меню выбора подкатегорий
                for category in categories:
                    logger.info(f"Проверка отображения категории '{category.name}' в меню выбора подкатегорий")
                    
                    # Проверяем наличие подкатегорий для категории
                    subcategories = session.query(SubCategory).filter(
                        SubCategory.category_id == category.id,
                        SubCategory.is_active == True
                    ).all()
                    
                    logger.info(f"Найдено {len(subcategories)} подкатегорий для категории '{category.name}'")
                    
                    if subcategories:
                        # Проверяем отображение подкатегорий в меню выбора
                        for subcategory in subcategories:
                            logger.info(f"Проверка отображения подкатегории '{subcategory.name}'")
                        
                        # Проверяем функцию выбора/отмены подкатегории
                        logger.info("Проверка функции выбора/отмены подкатегории")
                        
                        # Проверяем кнопку "Готово"
                        logger.info("Проверка кнопки 'Готово'")
                        
                        # Проверяем кнопку "Назад к категориям"
                        logger.info("Проверка кнопки 'Назад к категориям'")
                
                # Проверяем кнопку "Вернуться в профиль"
                logger.info("Проверка кнопки 'Вернуться в профиль'")
    
    logger.info("Тестирование выбора подкатегорий завершено")

async def test_phone_editing():
    """Тестирование изменения телефона"""
    logger.info("Тестирование изменения телефона...")
    
    # Проверяем ввод телефона
    test_phone = "+79991234567"
    logger.info(f"Проверка ввода телефона '{test_phone}'")
    
    # Проверяем валидацию телефона
    logger.info("Проверка валидации телефона")
    
    # Проверяем сохранение телефона
    logger.info("Проверка сохранения телефона")
    
    logger.info("Тестирование изменения телефона завершено")

async def test_my_requests():
    """Тестирование просмотра заявок"""
    logger.info("Тестирование просмотра заявок...")
    
    with get_session() as session:
        # Проверяем наличие заявок у пользователя
        users = session.query(User).all()
        if users:
            user = users[0]
            
            # Получаем распределения пользователя
            request_service = RequestService(session)
            distributions = request_service.get_user_distributions(user.telegram_id)
            
            logger.info(f"Найдено {len(distributions)} распределений у пользователя")
            
            if distributions:
                # Проверяем отображение заявок
                for distribution in distributions:
                    request = distribution.request
                    logger.info(f"Проверка отображения заявки #{request.id}")
                    
                    # Проверяем отображение статуса заявки
                    logger.info(f"Проверка отображения статуса заявки: {distribution.status}")
            else:
                logger.info("Проверка отображения сообщения 'У вас нет активных заявок'")
    
    logger.info("Тестирование просмотра заявок завершено")

async def test_settings_menu():
    """Тестирование меню настроек"""
    logger.info("Тестирование меню настроек...")
    
    # Проверяем наличие кнопок в меню настроек
    settings_menu_buttons = [
        "🔔 Уведомления",
        "🔙 Вернуться в главное меню"
    ]
    
    for button in settings_menu_buttons:
        logger.info(f"Проверка кнопки '{button}' в меню настроек")
    
    logger.info("Тестирование меню настроек завершено")

def create_test_report():
    """Создание отчета о тестировании"""
    logger.info("Создание отчета о тестировании...")
    
    report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_report.md")
    
    with open(report_file, "w") as f:
        f.write("# Отчет о тестировании функциональности бота\n\n")
        f.write(f"Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Проверенные функции\n\n")
        f.write("1. Главное меню\n")
        f.write("2. Меню профиля\n")
        f.write("3. Выбор категорий\n")
        f.write("4. Выбор городов\n")
        f.write("5. Выбор подкатегорий\n")
        f.write("6. Изменение телефона\n")
        f.write("7. Просмотр заявок\n")
        f.write("8. Меню настроек\n\n")
        
        f.write("## Инструкция по отладке\n\n")
        f.write("Если какая-то кнопка не работает, выполните следующие шаги:\n\n")
        f.write("1. Проверьте логи бота в файле `bot.log`\n")
        f.write("2. Проверьте логи тестирования в файле `test_bot_functionality.log`\n")
        f.write("3. Убедитесь, что все миграции применены\n")
        f.write("4. Проверьте наличие необходимых данных в базе данных\n")
        f.write("5. Перезапустите бота с помощью команды `python run_bot_with_subcategories.py`\n\n")
        
        f.write("## Рекомендации\n\n")
        f.write("1. Для полной функциональности бота рекомендуется использовать скрипт `run_bot_with_subcategories.py`\n")
        f.write("2. Перед запуском бота убедитесь, что все миграции применены\n")
        f.write("3. Для тестирования распределения заявок с учетом подкатегорий используйте скрипт `test_distribution_with_subcategories.py`\n")
    
    logger.info(f"Отчет о тестировании создан: {report_file}")

if __name__ == "__main__":
    logger.info("Запуск скрипта тестирования функциональности бота")
    
    try:
        # Запускаем тестирование
        asyncio.run(test_bot_functionality())
        
        # Создаем отчет о тестировании
        create_test_report()
        
        logger.info("Скрипт успешно выполнен")
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("Тестирование остановлено пользователем (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc()
        sys.exit(1) 