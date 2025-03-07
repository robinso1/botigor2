"""
Пакет с обработчиками команд бота
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from aiogram.filters.state import State
from aiogram import types

from bot.handlers.user_handlers import (
    start_command, show_main_menu, profile_menu, settings_menu,
    select_categories, toggle_category, select_cities, toggle_city,
    edit_phone, save_phone, my_requests, show_request,
    accept_request, reject_request, show_admin_message,
    select_subcategories, handle_subcategory_selection,
    UserStates
)
from bot.handlers.admin_handlers_aiogram import (
    admin_command, show_admin_menu, exit_admin_panel,
    admin_categories, admin_add_category, admin_save_category, admin_toggle_category,
    admin_cities, admin_add_city, admin_save_city, admin_toggle_city,
    admin_demo_generation, admin_generate_demo_request, admin_stats, admin_demo_stats,
    create_test_data, AdminStates, is_admin
)
from bot.handlers.help_handlers import help_command
from bot.handlers.error_handlers import register_error_handlers

logger = logging.getLogger(__name__)

def setup_handlers() -> Router:
    """
    Настраивает и возвращает роутер с обработчиками команд
    """
    router = Router()
    
    # Регистрация обработчиков команд (доступны в любом состоянии)
    router.message.register(start_command, CommandStart())
    router.message.register(show_main_menu, Command("menu"))
    router.message.register(help_command, Command("help"))
    router.message.register(admin_command, Command("admin"))
    
    # Обработчики для главного меню
    router.message.register(profile_menu, F.text == "👤 Мой профиль", StateFilter(UserStates.MAIN_MENU))
    router.message.register(my_requests, F.text == "📋 Мои заявки", StateFilter(UserStates.MAIN_MENU))
    router.message.register(settings_menu, F.text == "⚙️ Настройки", StateFilter(UserStates.MAIN_MENU))
    
    # Обработчики для меню профиля
    router.message.register(select_cities, F.text == "🏙️ Выбрать города", StateFilter(UserStates.PROFILE_MENU))
    router.message.register(select_categories, F.text == "🔧 Выбрать категории", StateFilter(UserStates.PROFILE_MENU))
    router.message.register(edit_phone, F.text == "📱 Изменить телефон", StateFilter(UserStates.PROFILE_MENU))
    router.message.register(select_subcategories, F.text == "🔍 Выбрать подкатегории", StateFilter(UserStates.PROFILE_MENU))
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.PROFILE_MENU))
    
    # Обработчики для выбора категорий
    router.message.register(toggle_category, StateFilter(UserStates.SELECTING_CATEGORIES))
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.SELECTING_CATEGORIES))
    
    # Обработчики для выбора городов
    router.message.register(toggle_city, StateFilter(UserStates.SELECTING_CITIES))
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.SELECTING_CITIES))
    
    # Обработчики для выбора подкатегорий
    router.message.register(handle_subcategory_selection, StateFilter(UserStates.SELECTING_SUBCATEGORIES))
    
    # Обработчики для ввода телефона
    router.message.register(save_phone, StateFilter(UserStates.EDIT_PHONE))
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.EDIT_PHONE))
    
    # Обработчики для меню заявок
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.MY_REQUESTS))
    
    # Обработчики для меню настроек
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.SETTINGS_MENU))
    
    # Обработчики для админ-панели
    router.message.register(show_admin_menu, F.text == "🏠 Главное меню", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_categories, F.text == "🔧 Категории", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_cities, F.text == "🏙️ Города", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_demo_generation, F.text == "🤖 Демо-режим", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_stats, F.text == "📊 Статистика", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(create_test_data, F.text == "🧪 Создать тестовые данные", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(exit_admin_panel, F.text == "🚪 Выйти из админ-панели", StateFilter(AdminStates.MAIN_MENU))
    
    # Обработчики для категорий в админ-панели
    router.message.register(admin_add_category, F.text == "➕ Добавить категорию", StateFilter(AdminStates.CATEGORIES))
    router.message.register(admin_toggle_category, F.text.startswith(("✅", "❌")), StateFilter(AdminStates.CATEGORIES))
    router.message.register(show_admin_menu, F.text == "🔙 Назад", StateFilter(AdminStates.CATEGORIES))
    
    # Обработчики для добавления категории в админ-панели
    router.message.register(admin_save_category, StateFilter(AdminStates.ADD_CATEGORY))
    router.message.register(show_admin_menu, F.text == "🔙 Отмена", StateFilter(AdminStates.ADD_CATEGORY))
    
    # Обработчики для городов в админ-панели
    router.message.register(admin_add_city, F.text == "➕ Добавить город", StateFilter(AdminStates.CITIES))
    router.message.register(admin_toggle_city, F.text.startswith(("✅", "❌")), StateFilter(AdminStates.CITIES))
    router.message.register(show_admin_menu, F.text == "🔙 Назад", StateFilter(AdminStates.CITIES))
    
    # Обработчики для добавления города в админ-панели
    router.message.register(admin_save_city, StateFilter(AdminStates.ADD_CITY))
    router.message.register(show_admin_menu, F.text == "🔙 Отмена", StateFilter(AdminStates.ADD_CITY))
    
    # Обработчики для демо-режима в админ-панели
    router.message.register(admin_generate_demo_request, F.text == "🔄 Сгенерировать заявку", StateFilter(AdminStates.DEMO_GENERATION))
    router.message.register(admin_demo_stats, F.text == "📊 Статистика демо-заявок", StateFilter(AdminStates.DEMO_GENERATION))
    router.message.register(show_admin_menu, F.text == "🔙 Назад", StateFilter(AdminStates.DEMO_GENERATION))
    
    # Обработчик для всех текстовых сообщений, если не сработал ни один из предыдущих
    async def handle_unknown_message(message: types.Message):
        """Обработчик для неизвестных сообщений"""
        logger.info(f"Получено неизвестное сообщение: {message.text}")
        await message.answer(
            "Извините, я не понимаю эту команду. Пожалуйста, используйте кнопки меню или команду /start для начала работы."
        )
    
    # Регистрируем обработчик для всех текстовых сообщений с низким приоритетом
    router.message.register(handle_unknown_message, F.text)
    
    # Регистрация обработчиков ошибок
    register_error_handlers(router)
    
    return router