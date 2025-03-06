import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from bot.database.setup import get_session
from bot.models import User, Category, City, Request, Distribution
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from bot.utils import encrypt_personal_data, decrypt_personal_data, mask_phone_number
from bot.utils.demo_utils import generate_demo_request
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

# Функция для проверки, является ли пользователь администратором
async def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# Обработчик команды /admin
async def admin_command(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /admin"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("У вас нет доступа к панели администратора.")
        return
    
    await show_admin_menu(message, state)

# Показать главное меню администратора
async def show_admin_menu(message: types.Message, state: FSMContext) -> None:
    """Показывает главное меню администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🔧 Категории")],
            [KeyboardButton(text="🏙️ Города"), KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🤖 Демо-генерация")],
            [KeyboardButton(text="🔙 Выйти из админ-панели")]
        ],
        resize_keyboard=True
    )
    
    await message.answer("Панель администратора. Выберите раздел:", reply_markup=keyboard)
    await state.set_state(AdminStates.MAIN_MENU)

# Обработчик выхода из админ-панели
async def exit_admin_panel(message: types.Message, state: FSMContext) -> None:
    """Выход из админ-панели"""
    await show_main_menu(message, state)

# Обработчик раздела категорий
async def admin_categories(message: types.Message, state: FSMContext) -> None:
    """Показывает список категорий с возможностью управления"""
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

# Обработчик добавления новой категории
async def admin_add_category(message: types.Message, state: FSMContext) -> None:
    """Запрашивает название новой категории"""
    await message.answer(
        "Введите название новой категории услуг:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Отмена")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.ADD_CATEGORY)

# Обработчик сохранения новой категории
async def admin_save_category(message: types.Message, state: FSMContext) -> None:
    """Сохраняет новую категорию в базе данных"""
    if message.text == "🔙 Отмена":
        await admin_categories(message, state)
        return
    
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

# Обработчик переключения статуса категории
async def admin_toggle_category(message: types.Message, state: FSMContext) -> None:
    """Переключает статус активности категории"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
    
    if message.text == "➕ Добавить категорию":
        await admin_add_category(message, state)
        return
    
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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Сгенерировать демо-заявку")],
            [KeyboardButton(text="🔙 Назад в админ-меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "Управление демо-генерацией заявок.\n\n"
        "Вы можете сгенерировать тестовую заявку для проверки работы системы.",
        reply_markup=keyboard
    )
    
    await state.set_state(AdminStates.DEMO_GENERATION)

# Обработчик генерации демо-заявки
async def admin_generate_demo_request(message: types.Message, state: FSMContext) -> None:
    """Генерирует демо-заявку"""
    if message.text == "🔙 Назад в админ-меню":
        await show_admin_menu(message, state)
        return
    
    try:
        request_id = generate_demo_request()
        await message.answer(f"Демо-заявка успешно сгенерирована. ID: {request_id}")
    except Exception as e:
        logger.error(f"Ошибка при генерации демо-заявки: {e}")
        await message.answer(f"Ошибка при генерации демо-заявки: {str(e)}")

# Обработчик раздела статистики
async def admin_stats(message: types.Message, state: FSMContext) -> None:
    """Показывает статистику системы"""
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
        
        await message.answer(stats_text, reply_markup=keyboard)
        await state.set_state(AdminStates.STATS)

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