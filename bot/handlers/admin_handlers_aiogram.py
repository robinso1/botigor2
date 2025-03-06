import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from sqlalchemy import func

from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from bot.database.setup import get_session
from bot.models import User, Category, City, Request, Distribution, RequestStatus
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from bot.utils import encrypt_personal_data, decrypt_personal_data, mask_phone_number
from bot.utils.demo_generator import generate_demo_request, get_demo_info_message
from config import ADMIN_IDS, DEFAULT_CATEGORIES, DEFAULT_CITIES
from bot.handlers.user_handlers import show_main_menu

logger = logging.getLogger(__name__)

# Состояния для FSM
class AdminStates(StatesGroup):
    MAIN_MENU = State()
    USERS = State()
    CATEGORIES = State()
    ADD_CATEGORY = State()
    EDIT_CATEGORY = State()
    CITIES = State()
    ADD_CITY = State()
    EDIT_CITY = State()
    REQUESTS = State()
    VIEW_REQUEST = State()
    DISTRIBUTIONS = State()
    DEMO_GENERATION = State()
    STATS = State()
    
    @classmethod
    @property
    def states(cls):
        """Возвращает список всех состояний"""
        return [
            cls.MAIN_MENU, cls.USERS, cls.CATEGORIES, cls.ADD_CATEGORY, 
            cls.EDIT_CATEGORY, cls.CITIES, cls.ADD_CITY, cls.EDIT_CITY,
            cls.REQUESTS, cls.VIEW_REQUEST, cls.DISTRIBUTIONS, 
            cls.DEMO_GENERATION, cls.STATS
        ]

# Функция для проверки, является ли пользователь администратором
async def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    try:
        # Преобразуем user_id в int, если это строка
        user_id = int(user_id)
        # Проверяем, есть ли пользователь в списке администраторов
        return user_id in ADMIN_IDS
    except (ValueError, TypeError):
        logger.error(f"Ошибка при проверке администратора: неверный формат ID {user_id}")
        return False

# Обработчик команды /admin
async def admin_command(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /admin"""
    try:
        user = message.from_user
        
        # Проверяем, является ли пользователь администратором
        if not await is_admin(user.id):
            await message.answer(
                "У вас нет прав для доступа к административной панели."
            )
            return
        
        # Создаем клавиатуру для админ-панели
        keyboard = [
            ["🔧 Категории", "🏙️ Города"],
            ["🤖 Демо-генерация", "📊 Статистика"],
            ["🔄 Создать тестовые данные"],
            ["🔙 Выйти из админ-панели"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Отправляем приветственное сообщение
        await message.answer(
            "👨‍💼 *Административная панель*\n\n"
            "Добро пожаловать в панель администратора бота!\n\n"
            "Здесь вы можете управлять категориями, городами, "
            "настройками демо-генерации и просматривать статистику.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Устанавливаем состояние
        await state.set_state(AdminStates.MAIN_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в admin_command: {e}")
        await message.answer(
            "Произошла ошибка при открытии административной панели. Пожалуйста, попробуйте позже."
        )

# Показать главное меню администратора
async def show_admin_menu(message: types.Message, state: FSMContext) -> None:
    """Показывает главное меню администратора"""
    try:
        # Создаем клавиатуру для админ-панели
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🔧 Категории")],
                [KeyboardButton(text="🏙️ Города"), KeyboardButton(text="📋 Заявки")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🤖 Демо-генерация")],
                [KeyboardButton(text="🔙 Выйти из админ-панели")]
            ],
            resize_keyboard=True
        )
        
        # Устанавливаем состояние перед отправкой сообщения
        await state.set_state(AdminStates.MAIN_MENU)
        
        # Отправляем сообщение с клавиатурой
        await message.answer("Панель администратора. Выберите раздел:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в show_admin_menu: {e}")
        await message.answer("Произошла ошибка при отображении меню администратора.")

# Обработчик выхода из админ-панели
async def exit_admin_panel(message: types.Message, state: FSMContext) -> None:
    """Выход из админ-панели"""
    try:
        await show_main_menu(message, state)
    except Exception as e:
        logger.error(f"Ошибка в exit_admin_panel: {e}")
        await message.answer("Произошла ошибка при выходе из панели администратора.")

# Обработчик раздела категорий
async def admin_categories(message: types.Message, state: FSMContext) -> None:
    """Показывает список категорий с возможностью управления"""
    try:
        with get_session() as session:
            categories = session.query(Category).all()
            
            keyboard = []
            for category in categories:
                status = "✅" if category.is_active else "❌"
                keyboard.append([KeyboardButton(text=f"{status} {category.name}")])
            
            keyboard.append([KeyboardButton(text="➕ Добавить категорию")])
            keyboard.append([KeyboardButton(text="🔙 Назад в админ-меню")])
            
            reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
            
            await message.answer(
                "Управление категориями услуг:\n"
                "✅ - активна, ❌ - неактивна\n\n"
                "Нажмите на категорию для изменения статуса или добавьте новую.",
                reply_markup=reply_markup
            )
            
            await state.set_state(AdminStates.CATEGORIES)
    except Exception as e:
        logger.error(f"Ошибка в admin_categories: {e}")
        await message.answer("Произошла ошибка при загрузке категорий. Пожалуйста, попробуйте позже.")
        await state.set_state(AdminStates.MAIN_MENU)

# Обработчик добавления новой категории
async def admin_add_category(message: types.Message, state: FSMContext) -> None:
    """Запрашивает название новой категории"""
    try:
        await message.answer(
            "Введите название новой категории услуг:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Назад в админ-меню")]],
                resize_keyboard=True
            )
        )
        await state.set_state(AdminStates.ADD_CATEGORY)
    except Exception as e:
        logger.error(f"Ошибка в admin_add_category: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.set_state(AdminStates.MAIN_MENU)

# Обработчик сохранения новой категории
async def admin_save_category(message: types.Message, state: FSMContext) -> None:
    """Сохраняет новую категорию в базе данных"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
    
    try:
        category_name = message.text.strip()
        
        with get_session() as session:
            # Проверяем, существует ли уже такая категория
            existing_category = session.query(Category).filter(Category.name == category_name).first()
            
            if existing_category:
                await message.answer(f"Категория '{category_name}' уже существует.")
            else:
                # Создаем новую категорию
                new_category = Category(name=category_name, is_active=True)
                session.add(new_category)
                session.commit()
                await message.answer(f"Категория '{category_name}' успешно добавлена.")
            
            # Возвращаемся к списку категорий
            await admin_categories(message, state)
    except Exception as e:
        logger.error(f"Ошибка в admin_save_category: {e}")
        await message.answer("Произошла ошибка при сохранении категории. Пожалуйста, попробуйте позже.")
        await state.set_state(AdminStates.MAIN_MENU)

# Обработчик переключения статуса категории
async def admin_toggle_category(message: types.Message, state: FSMContext) -> None:
    """Переключает статус активности категории"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
    
    if message.text == "➕ Добавить категорию":
        await admin_add_category(message, state)
        return
    
    try:
        # Извлекаем название категории из сообщения (убираем статус)
        category_text = message.text
        if category_text.startswith("✅ ") or category_text.startswith("❌ "):
            category_name = category_text[2:].strip()
            
            with get_session() as session:
                category = session.query(Category).filter(Category.name == category_name).first()
                
                if category:
                    # Переключаем статус
                    category.is_active = not category.is_active
                    session.commit()
                    
                    status = "активирована" if category.is_active else "деактивирована"
                    await message.answer(f"Категория '{category_name}' {status}.")
                else:
                    await message.answer(f"Категория '{category_name}' не найдена.")
            
            # Обновляем список категорий
            await admin_categories(message, state)
    except Exception as e:
        logger.error(f"Ошибка в admin_toggle_category: {e}")
        await message.answer("Произошла ошибка при изменении статуса категории. Пожалуйста, попробуйте позже.")
        await state.set_state(AdminStates.MAIN_MENU)

# Обработчик раздела городов
async def admin_cities(message: types.Message, state: FSMContext) -> None:
    """Показывает список городов с возможностью управления"""
    with get_session() as session:
        cities = session.query(City).all()
        
        keyboard = []
        for city in cities:
            status = "✅" if city.is_active else "❌"
            keyboard.append([KeyboardButton(text=f"{status} {city.name}")])
        
        keyboard.append([KeyboardButton(text="➕ Добавить город")])
        keyboard.append([KeyboardButton(text="🔙 Назад в админ-меню")])
        
        reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        await message.answer(
            "Управление городами:\n"
            "✅ - активен, ❌ - неактивен\n\n"
            "Нажмите на город для изменения статуса или добавьте новый.",
            reply_markup=reply_markup
        )
        
        await state.set_state(AdminStates.CITIES)

# Обработчик добавления нового города
async def admin_add_city(message: types.Message, state: FSMContext) -> None:
    """Запрашивает название нового города"""
    await message.answer(
        "Введите название нового города:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Отмена")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.ADD_CITY)

# Обработчик сохранения нового города
async def admin_save_city(message: types.Message, state: FSMContext) -> None:
    """Сохраняет новый город в базе данных"""
    if message.text == "🔙 Отмена":
        await admin_cities(message, state)
        return
    
    city_name = message.text.strip()
    
    with get_session() as session:
        # Проверяем, существует ли уже такой город
        existing_city = session.query(City).filter(City.name == city_name).first()
        
        if existing_city:
            await message.answer(f"Город '{city_name}' уже существует.")
        else:
            # Создаем новый город
            new_city = City(name=city_name, is_active=True)
            session.add(new_city)
            session.commit()
            await message.answer(f"Город '{city_name}' успешно добавлен.")
        
        # Возвращаемся к списку городов
        await admin_cities(message, state)

# Обработчик переключения статуса города
async def admin_toggle_city(message: types.Message, state: FSMContext) -> None:
    """Переключает статус активности города"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
    
    if message.text == "➕ Добавить город":
        await admin_add_city(message, state)
        return
    
    # Извлекаем название города из сообщения (убираем статус)
    city_text = message.text
    if city_text.startswith("✅ ") or city_text.startswith("❌ "):
        city_name = city_text[2:].strip()
        
        with get_session() as session:
            city = session.query(City).filter(City.name == city_name).first()
            
            if city:
                # Переключаем статус
                city.is_active = not city.is_active
                session.commit()
                
                status = "активирован" if city.is_active else "деактивирован"
                await message.answer(f"Город '{city_name}' {status}.")
            else:
                await message.answer(f"Город '{city_name}' не найден.")
        
        # Обновляем список городов
        await admin_cities(message, state)

# Обработчик демо-генерации
async def admin_demo_generation(message: types.Message, state: FSMContext) -> None:
    """Показывает меню демо-генерации заявок"""
    try:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔄 Сгенерировать заявку")],
                [KeyboardButton(text="📊 Статистика демо-заявок")],
                [KeyboardButton(text="🔙 Назад в админ-меню")]
            ],
            resize_keyboard=True
        )
        
        # Устанавливаем состояние перед отправкой сообщения
        await state.set_state(AdminStates.DEMO_GENERATION)
        
        await message.answer(
            "Управление демо-генерацией заявок.\n\n"
            "Вы можете сгенерировать тестовую заявку для проверки работы системы "
            "или просмотреть статистику по демо-заявкам.",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка в admin_demo_generation: {e}")
        await message.answer("Произошла ошибка при отображении меню демо-генерации.")
        await show_admin_menu(message, state)

# Обработчик генерации демо-заявки
async def admin_generate_demo_request(message: types.Message, state: FSMContext) -> None:
    """Генерирует демо-заявку"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
        
    if message.text == "📊 Статистика демо-заявок":
        await admin_demo_stats(message, state)
        return
    
    try:
        # Генерируем демо-заявку
        request_data = generate_demo_request()
        
        if not request_data:
            await message.answer("Не удалось сгенерировать демо-заявку. Проверьте наличие активных категорий и городов.")
            return
            
        # Создаем заявку в базе данных
        with get_session() as session:
            new_request = Request(
                client_name=request_data["client_name"],
                client_phone=request_data["client_phone"],
                description=request_data["description"],
                status=request_data["status"],
                is_demo=True,
                category_id=request_data["category_id"],
                city_id=request_data["city_id"],
                area=request_data.get("area"),
                address=request_data.get("address"),
                estimated_cost=request_data.get("estimated_cost"),
                extra_data=request_data.get("extra_data", {})
            )
            session.add(new_request)
            session.commit()
            
            # Получаем информацию о категории и городе
            category = session.query(Category).filter_by(id=request_data["category_id"]).first()
            city = session.query(City).filter_by(id=request_data["city_id"]).first()
            
            category_name = category.name if category else "Неизвестная категория"
            city_name = city.name if city else "Неизвестный город"
            
            # Формируем сообщение с информацией о заявке
            info_text = (
                f"✅ Демо-заявка успешно сгенерирована (ID: {new_request.id})\n\n"
                f"👤 Клиент: {request_data['client_name']}\n"
                f"📱 Телефон: {request_data['client_phone']}\n"
                f"🔧 Категория: {category_name}\n"
                f"🏙️ Город: {city_name}\n"
                f"📝 Описание: {request_data['description']}\n"
                f"📏 Площадь: {request_data.get('area', 'Не указана')} м²\n"
                f"🏠 Адрес: {request_data.get('address', 'Не указан')}\n"
                f"💰 Примерная стоимость: {request_data.get('estimated_cost', 'Не указана')} руб.\n\n"
                f"Заявка будет распределена между пользователями согласно настройкам системы."
            )
            
            await message.answer(info_text)
            
            # Отправляем информационное сообщение о демо-режиме
            await message.answer(
                "ℹ️ *Информационное сообщение для пользователей:*\n\n" + 
                get_demo_info_message("after_request"),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при генерации демо-заявки: {e}")
        await message.answer(f"Ошибка при генерации демо-заявки: {str(e)}")

# Обработчик статистики демо-заявок
async def admin_demo_stats(message: types.Message, state: FSMContext) -> None:
    """Показывает статистику по демо-заявкам"""
    try:
        with get_session() as session:
            # Общее количество демо-заявок
            total_demo = session.query(func.count(Request.id)).filter(Request.is_demo == True).scalar()
            
            # Количество демо-заявок по статусам
            status_counts = {}
            for status in RequestStatus:
                count = session.query(func.count(Request.id)).filter(
                    Request.is_demo == True,
                    Request.status == status
                ).scalar()
                if count > 0:
                    status_counts[status.value] = count
            
            # Количество демо-заявок по категориям
            category_counts = {}
            categories = session.query(Category).all()
            for category in categories:
                count = session.query(func.count(Request.id)).filter(
                    Request.is_demo == True,
                    Request.category_id == category.id
                ).scalar()
                if count > 0:
                    category_counts[category.name] = count
            
            # Количество демо-заявок по городам
            city_counts = {}
            cities = session.query(City).all()
            for city in cities:
                count = session.query(func.count(Request.id)).filter(
                    Request.is_demo == True,
                    Request.city_id == city.id
                ).scalar()
                if count > 0:
                    city_counts[city.name] = count
            
            # Формируем сообщение со статистикой
            stats_text = f"📊 *Статистика демо-заявок*\n\n"
            stats_text += f"Всего демо-заявок: {total_demo}\n\n"
            
            if status_counts:
                stats_text += "*По статусам:*\n"
                for status, count in status_counts.items():
                    stats_text += f"- {status}: {count}\n"
                stats_text += "\n"
            
            if category_counts:
                stats_text += "*По категориям:*\n"
                for category, count in category_counts.items():
                    stats_text += f"- {category}: {count}\n"
                stats_text += "\n"
            
            if city_counts:
                stats_text += "*По городам:*\n"
                for city, count in city_counts.items():
                    stats_text += f"- {city}: {count}\n"
            
            await message.answer(
                stats_text,
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🔙 Назад в админ-меню")]
                    ],
                    resize_keyboard=True
                )
            )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики демо-заявок: {e}")
        await message.answer("Произошла ошибка при получении статистики демо-заявок.")
        await show_admin_menu(message, state)

# Обработчик раздела статистики
async def admin_stats(message: types.Message, state: FSMContext) -> None:
    """Показывает статистику системы"""
    try:
        with get_session() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            total_requests = session.query(Request).count()
            total_distributions = session.query(Distribution).count()
            
            stats_text = (
                "📊 *Статистика системы*\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"👤 Активных пользователей: {active_users}\n"
                f"📋 Всего заявок: {total_requests}\n"
                f"📨 Всего распределений: {total_distributions}\n"
            )
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔙 Назад в админ-меню")]
                ],
                resize_keyboard=True
            )
            
            # Устанавливаем состояние перед отправкой сообщения
            await state.set_state(AdminStates.STATS)
            
            await message.answer(stats_text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в admin_stats: {e}")
        await message.answer("Произошла ошибка при получении статистики.")
        await show_admin_menu(message, state)

# Функция для создания тестовых данных
async def create_test_data(update: types.Message, state: FSMContext) -> None:
    """Создает тестовые данные (города и категории)"""
    try:
        user = update.from_user
        
        # Проверяем, является ли пользователь администратором
        if not is_admin(user.id):
            await update.answer(
                "У вас нет прав для доступа к административной панели."
            )
            return
        
        # Создаем тестовые категории
        session = get_session()
        
        # Проверяем, есть ли уже категории
        categories_count = session.query(func.count(Category.id)).scalar()
        
        if categories_count == 0:
            # Создаем категории
            test_categories = [
                {"name": "Сантехника", "description": "Услуги сантехника", "is_active": True},
                {"name": "Электрика", "description": "Услуги электрика", "is_active": True},
                {"name": "Натяжные потолки", "description": "Установка натяжных потолков", "is_active": True},
                {"name": "Ремонт квартир под ключ", "description": "Комплексный ремонт квартир", "is_active": True},
                {"name": "Дизайн интерьера", "description": "Услуги дизайнера интерьера", "is_active": True}
            ]
            
            for cat_data in test_categories:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    is_active=cat_data["is_active"]
                )
                session.add(category)
            
            session.commit()
            logger.info(f"Создано {len(test_categories)} тестовых категорий")
        
        # Проверяем, есть ли уже города
        cities_count = session.query(func.count(City.id)).scalar()
        
        if cities_count == 0:
            # Создаем города
            test_cities = [
                {"name": "Москва", "is_active": True, "phone_prefixes": ["495", "499"]},
                {"name": "Санкт-Петербург", "is_active": True, "phone_prefixes": ["812"]},
                {"name": "Екатеринбург", "is_active": True, "phone_prefixes": ["343"]},
                {"name": "Новосибирск", "is_active": True, "phone_prefixes": ["383"]},
                {"name": "Казань", "is_active": True, "phone_prefixes": ["843"]}
            ]
            
            for city_data in test_cities:
                city = City(
                    name=city_data["name"],
                    is_active=city_data["is_active"]
                )
                
                if "phone_prefixes" in city_data:
                    city.set_phone_prefixes(city_data["phone_prefixes"])
                
                session.add(city)
            
            session.commit()
            logger.info(f"Создано {len(test_cities)} тестовых городов")
        
        # Отправляем сообщение об успешном создании тестовых данных
        await update.answer(
            f"✅ Тестовые данные успешно созданы!\n\n"
            f"Категории: {categories_count == 0 and len(test_categories) or 'уже существуют'}\n"
            f"Города: {cities_count == 0 and len(test_cities) or 'уже существуют'}"
        )
        
        # Возвращаемся в главное меню админ-панели
        await state.set_state(AdminStates.MAIN_MENU)
        
    except Exception as e:
        logger.error(f"Ошибка в create_test_data: {e}")
        await update.answer(
            "Произошла ошибка при создании тестовых данных. Пожалуйста, попробуйте позже."
        )
        await state.set_state(AdminStates.MAIN_MENU)

# Функция для регистрации обработчиков администратора
def register_admin_handlers(router: Router) -> None:
    """Регистрирует обработчики администратора"""
    # Команда /admin
    router.message.register(admin_command, Command("admin"))
    
    # Главное меню админа
    router.message.register(exit_admin_panel, 
                           F.text == "🔙 Выйти из админ-панели", 
                           AdminStates.MAIN_MENU)
    router.message.register(admin_categories, 
                           F.text == "🔧 Категории", 
                           AdminStates.MAIN_MENU)
    router.message.register(admin_cities, 
                           F.text == "🏙️ Города", 
                           AdminStates.MAIN_MENU)
    router.message.register(admin_demo_generation, 
                           F.text == "🤖 Демо-генерация", 
                           AdminStates.MAIN_MENU)
    router.message.register(admin_stats, 
                           F.text == "📊 Статистика", 
                           AdminStates.MAIN_MENU)
    
    # Обработчики категорий
    router.message.register(admin_toggle_category, AdminStates.CATEGORIES)
    router.message.register(admin_save_category, AdminStates.ADD_CATEGORY)
    
    # Обработчики городов
    router.message.register(admin_toggle_city, AdminStates.CITIES)
    router.message.register(admin_save_city, AdminStates.ADD_CITY)
    
    # Обработчики демо-генерации
    router.message.register(admin_generate_demo_request, AdminStates.DEMO_GENERATION)
    
    # Обработчики статистики
    router.message.register(show_admin_menu, 
                           F.text == "🔙 Назад в админ-меню", 
                           AdminStates.STATS) 