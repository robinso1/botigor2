import logging
from typing import Dict, Any, List, Optional, Union, Callable
from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
# from telegram.ext import ConversationHandler
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import User, Category, City, Request, Distribution, RequestStatus, DistributionStatus
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from bot.utils import encrypt_personal_data, decrypt_personal_data, mask_phone_number
from config import ADMIN_IDS
from bot.database.setup import get_session

logger = logging.getLogger(__name__)

# Состояния для FSM
class UserStates(StatesGroup):
    MAIN_MENU = State()
    PROFILE_MENU = State()
    SETTINGS_MENU = State()
    CATEGORY_SELECTION = State()
    CITY_SELECTION = State()
    PHONE_INPUT = State()
    REQUEST_MENU = State()
    REQUEST_STATUS_SELECTION = State()
    SELECTING_CATEGORIES = State()
    SELECTING_CITIES = State()
    EDIT_PHONE = State()
    MY_REQUESTS = State()
    REQUEST_DETAILS = State()

async def start_command(update: types.Message, state: FSMContext) -> None:
    """Обработчик команды /start"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        # Создаем или получаем пользователя
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
            "После настройки вы начнете получать заявки автоматически.\n\n"
            "❗️ Используйте кнопку 'Вернуться в главное меню' внизу экрана для навигации."
        )
        
        # Создаем клавиатуру
        keyboard = [
            [KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🔙 Вернуться в главное меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        await update.reply(
            welcome_text,
            reply_markup=reply_markup
        )
        
        await state.set_state(UserStates.MAIN_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        await update.reply(
            "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        await state.clear()

async def show_main_menu(update: types.Message, state: FSMContext) -> None:
    """Показывает главное меню"""
    try:
        # Создаем клавиатуру
        keyboard = [
            [KeyboardButton("👤 Мой профиль")],
            [KeyboardButton("📋 Мои заявки")],
            [KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("🔙 Вернуться в главное меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Текст с подсказкой
        menu_text = (
            "🏠 Главное меню\n\n"
            "Выберите нужный раздел:\n"
            "👤 Мой профиль - настройка категорий и городов\n"
            "📋 Мои заявки - просмотр полученных заявок\n"
            "⚙️ Настройки - дополнительные настройки\n\n"
            "❗️ Используйте кнопку 'Вернуться в главное меню' для возврата в это меню"
        )
        
        await update.answer(
            menu_text,
            reply_markup=reply_markup
        )
        
        await state.set_state(UserStates.MAIN_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в show_main_menu: {e}")
        await update.answer(
            "Произошла ошибка при отображении меню. Пожалуйста, попробуйте позже."
        )
        await state.clear()

async def profile_menu(update: types.Message, state: FSMContext) -> None:
    """Показывает меню профиля пользователя"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        db_user = user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Формируем информацию о профиле
        profile_text = f"👤 *Профиль пользователя*\n\n"
        profile_text += f"*Имя*: {db_user.name}\n"
        
        # Расшифровываем и маскируем телефон для отображения
        phone = "Не указан"
        if db_user.phone:
            try:
                decrypted_phone = decrypt_personal_data(db_user.phone)
                phone = mask_phone_number(decrypted_phone)
            except Exception as e:
                logger.error(f"Ошибка при расшифровке телефона: {e}")
                phone = "Ошибка расшифровки"
        
        profile_text += f"*Телефон*: {phone}\n\n"
        
        # Получаем выбранные категории
        categories = user_service.get_user_categories(db_user.id)
        if categories:
            profile_text += "*Выбранные категории*:\n"
            for category in categories:
                profile_text += f"- {category.name}\n"
        else:
            profile_text += "*Выбранные категории*: Не выбраны\n"
        
        # Получаем выбранные города
        cities = user_service.get_user_cities(db_user.id)
        if cities:
            profile_text += "\n*Выбранные города*:\n"
            for city in cities:
                profile_text += f"- {city.name}\n"
        else:
            profile_text += "\n*Выбранные города*: Не выбраны\n"
        
        # Создаем клавиатуру
        keyboard = [
            [KeyboardButton(text="🔧 Выбрать категории"), KeyboardButton(text="🏙️ Выбрать города")],
            [KeyboardButton(text="📱 Изменить телефон")],
            [KeyboardButton(text="🔙 Вернуться в главное меню")]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.answer(
            profile_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await state.set_state(UserStates.PROFILE_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в profile_menu: {e}")
        await update.answer(
            "Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def settings_menu(update: types.Message, state: FSMContext) -> None:
    """Показывает меню настроек"""
    try:
        # Создаем клавиатуру
        keyboard = [
            ["🔔 Уведомления"],
            ["🔙 Вернуться в главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Текст с описанием настроек
        settings_text = (
            "⚙️ *Настройки*\n\n"
            "Здесь вы можете настроить параметры работы бота:\n\n"
            "🔔 *Уведомления* - настройка уведомлений о новых заявках\n"
        )
        
        await update.answer(
            settings_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await state.set_state(UserStates.SETTINGS_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в settings_menu: {e}")
        await update.answer(
            "Произошла ошибка при загрузке настроек. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def select_categories(update: types.Message, state: FSMContext) -> None:
    """Показывает список категорий для выбора"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        # Получаем пользователя из БД
        db_user = user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            await state.set_state(UserStates.MAIN_MENU)
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
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Текст с инструкцией
        message_text = (
            "Выберите категории работ, которые вы выполняете:\n\n"
            "❌ - категория не выбрана\n"
            "✅ - категория выбрана\n\n"
            "Нажимайте на категории для выбора/отмены.\n"
            "После завершения выбора нажмите кнопку '✅ Готово'."
        )
        
        await update.answer(
            message_text,
            reply_markup=reply_markup
        )
        
        await state.set_state(UserStates.SELECTING_CATEGORIES)
        
    except Exception as e:
        logger.error(f"Ошибка в select_categories: {e}")
        await update.answer(
            "Произошла ошибка при загрузке категорий. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def toggle_category(update: types.Message, state: FSMContext) -> None:
    """Обрабатывает выбор категории"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        # Получаем пользователя из БД
        db_user = user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Получаем текст сообщения
        message_text = update.text
        
        # Проверяем, нажата ли кнопка "Готово"
        if message_text == "✅ Готово":
            await update.answer(
                "Категории сохранены! Теперь вы будете получать заявки по выбранным категориям."
            )
            await state.set_state(UserStates.PROFILE_MENU)
            return
        
        # Проверяем, нажата ли кнопка возврата в главное меню
        if message_text == "🔙 Вернуться в главное меню":
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Обрабатываем выбор категории
        if message_text.startswith("✅ ") or message_text.startswith("❌ "):
            # Извлекаем название категории
            category_name = message_text[2:]  # Убираем маркер
            
            # Находим категорию в БД
            category = session.query(Category).filter(
                and_(
                    Category.name == category_name,
                    Category.is_active == True
                )
            ).first()
            
            if not category:
                await update.answer(f"Категория '{category_name}' не найдена.")
                await state.set_state(UserStates.SELECTING_CATEGORIES)
                return
            
            # Проверяем, выбрана ли уже эта категория
            is_selected = category in db_user.categories
            
            # Переключаем выбор категории
            if is_selected:
                db_user.categories.remove(category)
                logger.info(f"Пользователь {user.id} удалил категорию {category.name}")
            else:
                db_user.categories.append(category)
                logger.info(f"Пользователь {user.id} добавил категорию {category.name}")
            
            session.commit()
            
            # Обновляем клавиатуру
            await state.set_state(UserStates.SELECTING_CATEGORIES)
            return
        
        # Если сообщение не соответствует ни одному из ожидаемых форматов
        await update.answer(
            "Пожалуйста, выберите категорию из списка или нажмите 'Готово'."
        )
        await state.set_state(UserStates.SELECTING_CATEGORIES)
        
    except Exception as e:
        logger.error(f"Ошибка в toggle_category: {e}")
        await update.answer(
            "Произошла ошибка при обработке выбора категории. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def select_cities(update: types.Message, state: FSMContext) -> None:
    """Показывает список городов для выбора"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        # Получаем пользователя из БД
        db_user = user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            await state.set_state(UserStates.MAIN_MENU)
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
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Текст с инструкцией
        message_text = (
            "Выберите города, в которых вы работаете:\n\n"
            "❌ - город не выбран\n"
            "✅ - город выбран\n\n"
            "Нажимайте на города для выбора/отмены.\n"
            "После завершения выбора нажмите кнопку '✅ Готово'."
        )
        
        await update.answer(
            message_text,
            reply_markup=reply_markup
        )
        
        await state.set_state(UserStates.SELECTING_CITIES)
        
    except Exception as e:
        logger.error(f"Ошибка в select_cities: {e}")
        await update.answer(
            "Произошла ошибка при загрузке городов. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def toggle_city(update: types.Message, state: FSMContext) -> None:
    """Обрабатывает выбор города"""
    try:
        user = update.from_user
        session = get_session()
        user_service = UserService(session)
        
        # Получаем пользователя из БД
        db_user = user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Получаем текст сообщения
        message_text = update.text
        
        # Проверяем, нажата ли кнопка "Готово"
        if message_text == "✅ Готово":
            await update.answer(
                "Города сохранены! Теперь вы будете получать заявки из выбранных городов."
            )
            await state.set_state(UserStates.PROFILE_MENU)
            return
        
        # Проверяем, нажата ли кнопка возврата в главное меню
        if message_text == "🔙 Вернуться в главное меню":
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Обрабатываем выбор города
        if message_text.startswith("✅ ") or message_text.startswith("❌ "):
            # Извлекаем название города
            city_name = message_text[2:]  # Убираем маркер
            
            # Находим город в БД
            city = session.query(City).filter(
                and_(
                    City.name == city_name,
                    City.is_active == True
                )
            ).first()
            
            if not city:
                await update.answer(f"Город '{city_name}' не найден.")
                await state.set_state(UserStates.SELECTING_CITIES)
                return
            
            # Проверяем, выбран ли уже этот город
            is_selected = city in db_user.cities
            
            # Переключаем выбор города
            if is_selected:
                db_user.cities.remove(city)
                logger.info(f"Пользователь {user.id} удалил город {city.name}")
            else:
                db_user.cities.append(city)
                logger.info(f"Пользователь {user.id} добавил город {city.name}")
            
            session.commit()
            
            # Обновляем клавиатуру
            await state.set_state(UserStates.SELECTING_CITIES)
            return
        
        # Если сообщение не соответствует ни одному из ожидаемых форматов
        await update.answer(
            "Пожалуйста, выберите город из списка или нажмите 'Готово'."
        )
        await state.set_state(UserStates.SELECTING_CITIES)
        
    except Exception as e:
        logger.error(f"Ошибка в toggle_city: {e}")
        await update.answer(
            "Произошла ошибка при обработке выбора города. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def edit_phone(update: types.Message, state: FSMContext) -> None:
    """Запрашивает новый телефон пользователя"""
    try:
        # Создаем клавиатуру для отмены
        keyboard = [
            ["🔙 Вернуться в главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Текст с инструкцией
        message_text = (
            "📱 *Изменение телефона*\n\n"
            "Пожалуйста, введите ваш номер телефона в формате:\n"
            "+7XXXXXXXXXX\n\n"
            "Например: +79991234567\n\n"
            "Или нажмите кнопку 'Вернуться в главное меню' для отмены."
        )
        
        await update.answer(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await state.set_state(UserStates.EDIT_PHONE)
        
    except Exception as e:
        logger.error(f"Ошибка в edit_phone: {e}")
        await update.answer(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def save_phone(update: types.Message, state: FSMContext) -> None:
    """Сохраняет новый телефон пользователя"""
    try:
        user = update.from_user
        phone = update.text.strip()
        
        # Проверяем, нажата ли кнопка возврата в главное меню
        if phone == "🔙 Вернуться в главное меню":
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Проверяем формат телефона
        if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 10:
            await update.answer(
                "❌ Неверный формат телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX."
            )
            await state.set_state(UserStates.EDIT_PHONE)
            return
        
        session = get_session()
        user_service = UserService(session)
        
        # Шифруем телефон перед сохранением
        encrypted_phone = encrypt_personal_data(phone)
        
        # Обновляем телефон пользователя
        db_user = user_service.update_user_phone(user.id, encrypted_phone)
        
        if not db_user:
            await update.answer(
                "❌ Не удалось обновить телефон. Пожалуйста, попробуйте позже."
            )
            await state.set_state(UserStates.MAIN_MENU)
            return
        
        # Отправляем сообщение об успешном обновлении
        await update.answer(
            f"✅ Телефон успешно обновлен: {mask_phone_number(phone)}"
        )
        
        # Возвращаемся в меню профиля
        await state.set_state(UserStates.PROFILE_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в save_phone: {e}")
        await update.answer(
            "Произошла ошибка при сохранении телефона. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def my_requests(update: types.Message, state: FSMContext, filter_type: str = "all") -> None:
    """Показывает список заявок пользователя"""
    try:
        user = update.from_user
        session = get_session()
        request_service = RequestService(session)
        
        # Получаем распределения пользователя
        distributions = request_service.get_user_distributions(user.id)
        
        if not distributions:
            # Создаем клавиатуру для возврата
            keyboard = [
                ["🔙 Вернуться в главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.answer(
                "У вас пока нет заявок. Они появятся здесь, когда будут распределены вам.",
                reply_markup=reply_markup
            )
            await state.set_state(UserStates.MY_REQUESTS)
            return
        
        # Фильтруем распределения по статусу
        filtered_distributions = []
        if filter_type == "new":
            filtered_distributions = [d for d in distributions if d.status == "отправлено"]
        elif filter_type == "accepted":
            filtered_distributions = [d for d in distributions if d.status == "принято"]
        elif filter_type == "rejected":
            filtered_distributions = [d for d in distributions if d.status == "отклонено"]
        else:  # all
            filtered_distributions = distributions
        
        if not filtered_distributions:
            # Создаем клавиатуру для фильтрации и возврата
            keyboard = [
                ["📋 Все заявки", "🆕 Новые"],
                ["✅ Принятые", "❌ Отклоненные"],
                ["🔙 Вернуться в главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.answer(
                f"У вас нет заявок с выбранным статусом ({filter_type}).",
                reply_markup=reply_markup
            )
            await state.set_state(UserStates.MY_REQUESTS)
            return
        
        # Создаем клавиатуру для фильтрации и возврата
        keyboard = [
            ["📋 Все заявки", "🆕 Новые"],
            ["✅ Принятые", "❌ Отклоненные"],
            ["🔙 Вернуться в главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Создаем инлайн-клавиатуру для просмотра заявок
        inline_keyboard = []
        for dist in filtered_distributions[:10]:  # Ограничиваем 10 заявками
            request = dist.request
            status_emoji = "🆕" if dist.status == "отправлено" else "✅" if dist.status == "принято" else "❌"
            category_name = request.category.name if request.category else "Без категории"
            button_text = f"{status_emoji} {category_name} - {request.client_name}"
            inline_keyboard.append([InlineKeyboardButton(button_text, callback_data=f"show_request_{dist.id}")])
        
        inline_markup = InlineKeyboardMarkup(inline_keyboard)
        
        # Определяем заголовок в зависимости от фильтра
        title = "Все заявки"
        if filter_type == "new":
            title = "Новые заявки"
        elif filter_type == "accepted":
            title = "Принятые заявки"
        elif filter_type == "rejected":
            title = "Отклоненные заявки"
        
        await update.answer(
            f"{title} ({len(filtered_distributions)}):\n"
            "Нажмите на заявку для просмотра деталей.",
            reply_markup=reply_markup
        )
        
        await update.answer(
            "Выберите заявку:",
            reply_markup=inline_markup
        )
        
        await state.set_state(UserStates.MY_REQUESTS)
        
    except Exception as e:
        logger.error(f"Ошибка в my_requests: {e}")
        await update.answer(
            "Произошла ошибка при загрузке заявок. Пожалуйста, попробуйте позже."
        )
        await state.set_state(UserStates.MAIN_MENU)

async def show_request(update: types.CallbackQuery, state: FSMContext) -> None:
    """Показывает детали заявки"""
    try:
        # Получаем ID распределения из callback_data
        callback_query = update.query
        callback_query.answer()
        
        distribution_id = int(callback_query.data.split("_")[-1])
        
        session = get_session()
        request_service = RequestService(session)
        
        # Получаем распределение
        distribution = request_service.get_distribution(distribution_id)
        if not distribution:
            await callback_query.message.answer(
                "Заявка не найдена или была удалена."
            )
            await state.set_state(UserStates.MY_REQUESTS)
            return
        
        # Получаем заявку
        request = distribution.request
        
        # Расшифровываем и маскируем телефон для отображения
        phone = "Не указан"
        if request.phone:
            try:
                decrypted_phone = decrypt_personal_data(request.phone)
                phone = mask_phone_number(decrypted_phone)
            except Exception as e:
                logger.error(f"Ошибка при расшифровке телефона: {e}")
                phone = "Ошибка расшифровки"
        
        # Формируем текст с деталями заявки
        text = f"📋 *Заявка #{request.id}*\n\n"
        text += f"🔧 *Категория:* {request.category.name}\n"
        text += f"🏙️ *Город:* {request.city.name}\n"
        text += f"👤 *Клиент:* {request.name}\n"
        text += f"📱 *Телефон:* {phone}\n"
        text += f"📝 *Описание:*\n{request.description}\n\n"
        text += f"📊 *Статус распределения:* {distribution.status}\n"
        text += f"📅 *Дата создания:* {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        # Создаем клавиатуру с кнопками действий
        keyboard = []
        
        # Добавляем кнопки в зависимости от статуса
        if distribution.status == DistributionStatus.NEW.value:
            keyboard.append([
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_request_{distribution_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_request_{distribution_id}")
            ])
        
        # Добавляем кнопку возврата к списку заявок
        keyboard.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_requests")])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Если статус "принято", показываем полный телефон
        if distribution.status == DistributionStatus.ACCEPTED.value:
            try:
                full_phone = decrypt_personal_data(request.phone)
                text += f"\n*Контактный телефон*: {full_phone}"
            except Exception as e:
                logger.error(f"Ошибка при расшифровке телефона: {e}")
                text += "\n*Контактный телефон*: Ошибка расшифровки"
        
        await callback_query.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await state.set_state(UserStates.REQUEST_DETAILS)
        
    except Exception as e:
        logger.error(f"Ошибка в show_request: {e}")
        if update.query:
            await update.query.message.answer(
                "Произошла ошибка при загрузке заявки. Пожалуйста, попробуйте позже."
            )
        await state.set_state(UserStates.MY_REQUESTS)

async def accept_request(update: types.CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает принятие заявки"""
    try:
        # Получаем ID распределения из callback_data
        callback_query = update.query
        callback_query.answer()
        
        distribution_id = int(callback_query.data.split("_")[2])
        
        session = get_session()
        request_service = RequestService(session)
        
        # Обновляем статус распределения
        distribution = request_service.update_distribution_status(distribution_id, "принято")
        if not distribution:
            await callback_query.message.answer(
                "Заявка не найдена или была удалена."
            )
            await state.set_state(UserStates.MY_REQUESTS)
            return
        
        # Отправляем сообщение об успешном принятии заявки
        await callback_query.message.answer(
            "✅ Вы приняли заявку! Свяжитесь с клиентом по указанному телефону."
        )
        
        # Возвращаемся к списку заявок
        await my_requests(update, state)
        
    except Exception as e:
        logger.error(f"Ошибка в accept_request: {e}")
        if update.query:
            await update.query.message.answer(
                "Произошла ошибка при принятии заявки. Пожалуйста, попробуйте позже."
            )
        await state.set_state(UserStates.MY_REQUESTS)

async def reject_request(update: types.CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает отклонение заявки"""
    try:
        # Получаем ID распределения из callback_data
        callback_query = update.query
        callback_query.answer()
        
        distribution_id = int(callback_query.data.split("_")[2])
        
        session = get_session()
        request_service = RequestService(session)
        
        # Обновляем статус распределения
        distribution = request_service.update_distribution_status(distribution_id, "отклонено")
        if not distribution:
            await callback_query.message.answer(
                "Заявка не найдена или была удалена."
            )
            await state.set_state(UserStates.MY_REQUESTS)
            return
        
        # Отправляем сообщение об успешном отклонении заявки
        await callback_query.message.answer(
            "❌ Вы отклонили заявку. Она больше не будет отображаться в списке новых заявок."
        )
        
        # Возвращаемся к списку заявок
        await my_requests(update, state)
        
    except Exception as e:
        logger.error(f"Ошибка в reject_request: {e}")
        if update.query:
            await update.query.message.answer(
                "Произошла ошибка при отклонении заявки. Пожалуйста, попробуйте позже."
            )
        await state.set_state(UserStates.MY_REQUESTS)

async def show_admin_message(update: types.Message, state: FSMContext) -> None:
    """Показывает сообщение о необходимости использовать команду /admin"""
    await update.answer("Используйте команду /admin для доступа к админ-панели")
    await state.set_state(UserStates.MAIN_MENU)

# Закомментированные функции, которые использовали python-telegram-bot
# def get_user_conversation_handler() -> ConversationHandler:
#     """Возвращает обработчик диалогов для пользователя"""
#     return ConversationHandler(
#         entry_points=[
#             CommandHandler("start", start_command),
#             MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#         ],
#         states={
#             UserStates.MAIN_MENU: [
#                 MessageHandler(filters.Regex(r"^👤 Мой профиль$"), profile_menu),
#                 MessageHandler(filters.Regex(r"^📋 Мои заявки$"), my_requests),
#                 MessageHandler(filters.Regex(r"^⚙️ Настройки$"), settings_menu),
#                 MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#             ],
#             UserStates.PROFILE_MENU: [
#                 MessageHandler(filters.Regex(r"^🏙️ Выбрать города$"), select_cities),
#                 MessageHandler(filters.Regex(r"^🔧 Выбрать категории$"), select_categories),
#                 MessageHandler(filters.Regex(r"^📱 Изменить телефон$"), edit_phone),
#                 MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#             ],
#             UserStates.SELECTING_CATEGORIES: [
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, toggle_category),
#             ],
#             UserStates.SELECTING_CITIES: [
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, toggle_city),
#             ],
#             UserStates.EDIT_PHONE: [
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, save_phone),
#             ],
#             UserStates.SETTINGS_MENU: [
#                 MessageHandler(filters.Regex(r"^🔔 Уведомления$"), lambda u, c: u.message.answer("Настройки уведомлений в разработке")),
#                 MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#             ],
#             UserStates.MY_REQUESTS: [
#                 MessageHandler(filters.Regex(r"^📋 Все заявки$"), lambda u, c: my_requests(u, c, filter_type="all")),
#                 MessageHandler(filters.Regex(r"^🆕 Новые$"), lambda u, c: my_requests(u, c, filter_type="new")),
#                 MessageHandler(filters.Regex(r"^✅ Принятые$"), lambda u, c: my_requests(u, c, filter_type="accepted")),
#                 MessageHandler(filters.Regex(r"^❌ Отклоненные$"), lambda u, c: my_requests(u, c, filter_type="rejected")),
#                 MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#                 CallbackQueryHandler(show_request, pattern=r"^show_request_\d+$"),
#             ],
#             UserStates.REQUEST_DETAILS: [
#                 CallbackQueryHandler(accept_request, pattern=r"^accept_request_\d+$"),
#                 CallbackQueryHandler(reject_request, pattern=r"^reject_request_\d+$"),
#                 CallbackQueryHandler(lambda u, c: my_requests(u, c), pattern=r"^back_to_requests$"),
#             ],
#         },
#         fallbacks=[
#             CommandHandler("start", start_command),
#             MessageHandler(filters.Regex(r"^🔙 Вернуться в главное меню$"), show_main_menu),
#         ],
#         name="user_conversation",
#         persistent=False,
#     )

# def user_conversation_handler() -> ConversationHandler:
#     """Возвращает обработчик диалога с пользователем (для совместимости)"""
#     return get_user_conversation_handler() 