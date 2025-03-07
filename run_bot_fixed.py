"""
Исправленная версия скрипта запуска бота
"""
import os
import sys
import logging
import asyncio
import traceback
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart

from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, setup_logging
from bot.database.setup import setup_database, get_session
from bot.models import User, Category, City, Request, Distribution
from bot.services.user_service import UserService
from bot.services.request_service import RequestService

# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    try:
        logger.info("=" * 50)
        logger.info(f"Запуск исправленного бота в {datetime.now()}")
        
        # Настраиваем базу данных
        setup_database()
        
        # Создаем экземпляр бота и диспетчера
        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Обработчик команды /start
        @dp.message(CommandStart())
        async def start_command(message: types.Message):
            """Обработчик команды /start"""
            logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            # Создаем или получаем пользователя
            with get_session() as session:
                user_service = UserService(session)
                db_user = user_service.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            
            # Приветственное сообщение
            welcome_text = (
                f"👋 Здравствуйте, {user.first_name}!\n\n"
                "Я бот для распределения заявок. Чтобы начать получать заявки, "
                "вам нужно настроить свой профиль:\n\n"
                "1️⃣ Выберите категории работ\n"
                "2️⃣ Укажите города, в которых работаете\n"
                "3️⃣ Добавьте контактный телефон\n\n"
                "После настройки вы начнете получать заявки автоматически."
            )
            
            # Создаем клавиатуру
            keyboard = [
                [types.KeyboardButton(text="👤 Мой профиль")],
                [types.KeyboardButton(text="📋 Мои заявки")],
                [types.KeyboardButton(text="⚙️ Настройки")],
                [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                welcome_text,
                reply_markup=reply_markup
            )
        
        # Обработчик для кнопки "Мой профиль"
        @dp.message(F.text == "👤 Мой профиль")
        async def profile_menu(message: types.Message):
            """Обработчик для кнопки 'Мой профиль'"""
            logger.info(f"Получена команда 'Мой профиль' от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            # Получаем информацию о пользователе
            with get_session() as session:
                user_service = UserService(session)
                db_user = user_service.get_user_by_telegram_id(user.id)
                
                if not db_user:
                    await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
                    return
                
                # Формируем информацию о профиле
                profile_text = f"👤 *Профиль пользователя*\n\n"
                
                # Используем first_name и last_name
                full_name = f"{db_user.first_name or ''} {db_user.last_name or ''}".strip()
                if not full_name:
                    full_name = db_user.username or "Не указано"
                    
                profile_text += f"*Имя*: {full_name}\n"
                
                # Телефон
                phone = "Не указан"
                if db_user.phone:
                    try:
                        from bot.utils import decrypt_personal_data, mask_phone_number
                        decrypted_phone = decrypt_personal_data(db_user.phone)
                        phone = mask_phone_number(decrypted_phone)
                    except Exception as e:
                        logger.error(f"Ошибка при расшифровке телефона: {e}")
                        phone = "Ошибка расшифровки"
                
                profile_text += f"*Телефон*: {phone}\n\n"
                
                # Категории
                categories = db_user.categories
                if categories:
                    profile_text += "*Выбранные категории*:\n"
                    for category in categories:
                        profile_text += f"- {category.name}\n"
                else:
                    profile_text += "*Выбранные категории*: Не выбраны\n"
                
                # Города
                cities = db_user.cities
                if cities:
                    profile_text += "\n*Выбранные города*:\n"
                    for city in cities:
                        profile_text += f"- {city.name}\n"
                else:
                    profile_text += "\n*Выбранные города*: Не выбраны\n"
                
                # Подкатегории
                subcategories = db_user.subcategories
                if subcategories:
                    profile_text += "\n*Выбранные подкатегории*:\n"
                    for subcategory in subcategories:
                        profile_text += f"- {subcategory.name} ({subcategory.category.name})\n"
                else:
                    profile_text += "\n*Выбранные подкатегории*: Не выбраны\n"
            
            # Создаем клавиатуру
            keyboard = [
                [types.KeyboardButton(text="🔧 Выбрать категории"), types.KeyboardButton(text="🏙️ Выбрать города")],
                [types.KeyboardButton(text="📱 Изменить телефон"), types.KeyboardButton(text="🔍 Выбрать подкатегории")],
                [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                profile_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Обработчик для кнопки "Выбрать категории"
        @dp.message(F.text == "🔧 Выбрать категории")
        async def select_categories(message: types.Message):
            """Обработчик для кнопки 'Выбрать категории'"""
            logger.info(f"Получена команда 'Выбрать категории' от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            # Получаем категории
            with get_session() as session:
                user_service = UserService(session)
                db_user = user_service.get_user_by_telegram_id(user.id)
                
                if not db_user:
                    await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
                    return
                
                # Получаем все категории
                categories = session.query(Category).filter(Category.is_active == True).all()
                
                # Получаем категории пользователя
                user_categories = db_user.categories
                user_category_ids = [c.id for c in user_categories]
                
                # Создаем клавиатуру с категориями
                keyboard = []
                for category in categories:
                    # Добавляем маркер выбранной категории
                    status = "✅" if category.id in user_category_ids else "❌"
                    keyboard.append([f"{status} {category.name}"])
                
                # Добавляем кнопку "Готово"
                keyboard.append(["✅ Готово"])
                keyboard.append(["🔙 Вернуться в главное меню"])
                
                reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
                
                # Текст с инструкцией
                message_text = (
                    "Выберите категории работ, которые вы выполняете:\n\n"
                    "❌ - категория не выбрана\n"
                    "✅ - категория выбрана\n\n"
                    "Нажимайте на категории для выбора/отмены.\n"
                    "После завершения выбора нажмите кнопку '✅ Готово'."
                )
                
                await message.answer(
                    message_text,
                    reply_markup=reply_markup
                )
        
        # Обработчик для выбора категорий
        @dp.message(lambda msg: msg.text and (msg.text.startswith("✅ ") or msg.text.startswith("❌ ")))
        async def toggle_category(message: types.Message):
            """Обработчик для выбора категорий"""
            logger.info(f"Получена команда '{message.text}' от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            # Получаем имя категории из текста сообщения
            category_name = message.text[2:].strip()
            
            with get_session() as session:
                user_service = UserService(session)
                db_user = user_service.get_user_by_telegram_id(user.id)
                
                if not db_user:
                    await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
                    return
                
                # Получаем категорию по имени
                category = session.query(Category).filter(Category.name == category_name).first()
                
                if not category:
                    await message.answer(f"Категория '{category_name}' не найдена.")
                    return
                
                # Проверяем, выбрана ли категория
                is_selected = message.text.startswith("✅ ")
                
                # Обновляем выбор категории
                if is_selected:
                    # Удаляем категорию
                    if category in db_user.categories:
                        db_user.categories.remove(category)
                        session.commit()
                else:
                    # Добавляем категорию
                    if category not in db_user.categories:
                        db_user.categories.append(category)
                        session.commit()
                
                # Получаем обновленный список категорий
                categories = session.query(Category).filter(Category.is_active == True).all()
                user_categories = db_user.categories
                user_category_ids = [c.id for c in user_categories]
                
                # Создаем клавиатуру с категориями
                keyboard = []
                for cat in categories:
                    # Добавляем маркер выбранной категории
                    status = "✅" if cat.id in user_category_ids else "❌"
                    keyboard.append([f"{status} {cat.name}"])
                
                # Добавляем кнопку "Готово"
                keyboard.append(["✅ Готово"])
                keyboard.append(["🔙 Вернуться в главное меню"])
                
                reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
                
                await message.answer(
                    f"Категория '{category_name}' {'удалена' if is_selected else 'добавлена'}.",
                    reply_markup=reply_markup
                )
        
        # Обработчик для кнопки "Выбрать города"
        @dp.message(F.text == "🏙️ Выбрать города")
        async def select_cities(message: types.Message):
            """Обработчик для кнопки 'Выбрать города'"""
            logger.info(f"Получена команда 'Выбрать города' от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            # Получаем города
            with get_session() as session:
                user_service = UserService(session)
                db_user = user_service.get_user_by_telegram_id(user.id)
                
                if not db_user:
                    await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
                    return
                
                # Получаем все города
                cities = session.query(City).filter(City.is_active == True).all()
                
                # Получаем города пользователя
                user_cities = db_user.cities
                user_city_ids = [c.id for c in user_cities]
                
                # Создаем клавиатуру с городами
                keyboard = []
                for city in cities:
                    # Добавляем маркер выбранного города
                    status = "✅" if city.id in user_city_ids else "❌"
                    keyboard.append([f"{status} {city.name}"])
                
                # Добавляем кнопку "Готово"
                keyboard.append(["✅ Готово"])
                keyboard.append(["🔙 Вернуться в главное меню"])
                
                reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
                
                # Текст с инструкцией
                message_text = (
                    "Выберите города, в которых вы работаете:\n\n"
                    "❌ - город не выбран\n"
                    "✅ - город выбран\n\n"
                    "Нажимайте на города для выбора/отмены.\n"
                    "После завершения выбора нажмите кнопку '✅ Готово'."
                )
                
                await message.answer(
                    message_text,
                    reply_markup=reply_markup
                )
        
        # Обработчик для кнопки "Изменить телефон"
        @dp.message(F.text == "📱 Изменить телефон")
        async def edit_phone(message: types.Message):
            """Обработчик для кнопки 'Изменить телефон'"""
            logger.info(f"Получена команда 'Изменить телефон' от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру с кнопкой "Отмена"
            keyboard = [
                [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "Введите ваш номер телефона в формате +7XXXXXXXXXX",
                reply_markup=reply_markup
            )
        
        # Обработчик для кнопки "Выбрать подкатегории"
        @dp.message(F.text == "🔍 Выбрать подкатегории")
        async def select_subcategories(message: types.Message):
            """Обработчик для кнопки 'Выбрать подкатегории'"""
            logger.info(f"Получена команда 'Выбрать подкатегории' от пользователя {message.from_user.id}")
            
            await message.answer(
                "Функция выбора подкатегорий находится в разработке. Пожалуйста, попробуйте позже."
            )
        
        # Обработчик для кнопки "Мои заявки"
        @dp.message(F.text == "📋 Мои заявки")
        async def my_requests(message: types.Message):
            """Обработчик для кнопки 'Мои заявки'"""
            logger.info(f"Получена команда 'Мои заявки' от пользователя {message.from_user.id}")
            
            user = message.from_user
            
            try:
                # Получаем заявки пользователя
                with get_session() as session:
                    request_service = RequestService(session)
                    
                    # Получаем распределения пользователя
                    distributions = await request_service.get_user_distributions(user.id)
                    
                    if not distributions:
                        await message.answer("У вас нет активных заявок.")
                        return
                    
                    # Создаем сообщение со списком заявок
                    requests_text = "📋 *Ваши заявки*:\n\n"
                    
                    for i, distribution in enumerate(distributions, 1):
                        request = distribution.request
                        status_emoji = {
                            "отправлено": "📤",
                            "принято": "✅",
                            "отклонено": "❌",
                            "завершено": "🏁",
                            "просрочено": "⏰"
                        }.get(distribution.status, "❓")
                        
                        # Формируем информацию о заявке
                        requests_text += f"{i}. {status_emoji} *Заявка #{request.id}*\n"
                        requests_text += f"   📅 Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                        requests_text += f"   🏙️ Город: {request.city.name if request.city else 'Не указан'}\n"
                        requests_text += f"   🔧 Категория: {request.category.name if request.category else 'Не указана'}\n"
                        requests_text += f"   📝 Статус: {distribution.status}\n\n"
                    
                    await message.answer(
                        requests_text,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении заявок: {e}")
                await message.answer("Произошла ошибка при загрузке заявок. Пожалуйста, попробуйте позже.")
        
        # Обработчик для кнопки "Настройки"
        @dp.message(F.text == "⚙️ Настройки")
        async def settings_menu(message: types.Message):
            """Обработчик для кнопки 'Настройки'"""
            logger.info(f"Получена команда 'Настройки' от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру
            keyboard = [
                [types.KeyboardButton(text="🔔 Уведомления")],
                [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "⚙️ *Настройки*\n\nВыберите раздел настроек:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Обработчик для кнопки "Вернуться в главное меню"
        @dp.message(F.text == "🔙 Вернуться в главное меню")
        async def back_to_main_menu(message: types.Message):
            """Обработчик для кнопки 'Вернуться в главное меню'"""
            logger.info(f"Получена команда 'Вернуться в главное меню' от пользователя {message.from_user.id}")
            
            # Создаем клавиатуру
            keyboard = [
                [types.KeyboardButton(text="👤 Мой профиль")],
                [types.KeyboardButton(text="📋 Мои заявки")],
                [types.KeyboardButton(text="⚙️ Настройки")],
                [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
            ]
            reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "🏠 Главное меню\n\nВыберите нужный раздел:",
                reply_markup=reply_markup
            )
        
        # Обработчик для кнопки "Готово"
        @dp.message(F.text == "✅ Готово")
        async def done_button(message: types.Message):
            """Обработчик для кнопки 'Готово'"""
            logger.info(f"Получена команда 'Готово' от пользователя {message.from_user.id}")
            
            # Возвращаемся в меню профиля
            await profile_menu(message)
        
        # Обработчик для всех остальных сообщений
        @dp.message()
        async def handle_all_messages(message: types.Message):
            """Обработчик для всех остальных сообщений"""
            logger.info(f"Получено сообщение '{message.text}' от пользователя {message.from_user.id}")
            
            # Проверяем, является ли сообщение телефонным номером
            if message.text and (message.text.startswith('+') or message.text.isdigit()):
                # Обрабатываем как ввод телефона
                user = message.from_user
                phone = message.text.strip()
                
                # Проверяем формат телефона
                import re
                if not re.match(r'^\+?[0-9]{10,15}$', phone):
                    await message.answer(
                        "Неверный формат телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX"
                    )
                    return
                
                # Сохраняем телефон
                with get_session() as session:
                    user_service = UserService(session)
                    db_user = user_service.get_user_by_telegram_id(user.id)
                    
                    if not db_user:
                        await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
                        return
                    
                    # Шифруем и сохраняем телефон
                    from bot.utils import encrypt_personal_data
                    encrypted_phone = encrypt_personal_data(phone)
                    
                    # Обновляем пользователя
                    db_user.phone = encrypted_phone
                    session.commit()
                
                # Возвращаемся в меню профиля
                await profile_menu(message)
            else:
                # Для всех остальных сообщений
                await message.answer(
                    "Извините, я не понимаю эту команду. Пожалуйста, используйте кнопки меню или команду /start для начала работы."
                )
        
        # Отправляем сообщение администраторам о запуске бота
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🤖 Исправленный бот запущен!\n\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                logger.info(f"Отправлено уведомление о запуске администратору {admin_id}")
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
        
        # Запускаем поллинг
        logger.info("Запускаем поллинг бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        traceback.print_exc() 