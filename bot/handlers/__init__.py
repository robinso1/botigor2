"""
Пакет с обработчиками команд бота
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from aiogram.filters.state import State
from aiogram import F

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

def setup_handlers() -> Router:
    """
    Настраивает и возвращает роутер с обработчиками команд
    """
    router = Router()
    
    # Регистрация обработчиков команд (доступны в любом состоянии)
    router.message.register(start_command, CommandStart(), StateFilter(default_state))
    router.message.register(show_main_menu, Command("menu"), StateFilter(default_state))
    router.message.register(help_command, Command("help"), StateFilter(default_state))
    router.message.register(admin_command, Command("admin"), StateFilter(default_state))
    
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
    
    # Обработчики для выбора категорий и городов
    router.message.register(toggle_category, StateFilter(UserStates.SELECTING_CATEGORIES))
    router.message.register(toggle_city, StateFilter(UserStates.SELECTING_CITIES))
    
    # Обработчики для изменения телефона
    router.message.register(save_phone, StateFilter(UserStates.EDIT_PHONE))
    
    # Обработчики для меню настроек
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.SETTINGS_MENU))
    
    # Обработчики для списка заявок
    router.message.register(lambda msg, state: my_requests(msg, state, "all"), F.text == "📋 Все заявки", StateFilter(UserStates.MY_REQUESTS))
    router.message.register(lambda msg, state: my_requests(msg, state, "new"), F.text == "🆕 Новые", StateFilter(UserStates.MY_REQUESTS))
    router.message.register(lambda msg, state: my_requests(msg, state, "accepted"), F.text == "✅ Принятые", StateFilter(UserStates.MY_REQUESTS))
    router.message.register(lambda msg, state: my_requests(msg, state, "rejected"), F.text == "❌ Отклоненные", StateFilter(UserStates.MY_REQUESTS))
    router.message.register(show_main_menu, F.text == "🔙 Вернуться в главное меню", StateFilter(UserStates.MY_REQUESTS))
    
    # Обработчики для callback-запросов
    router.callback_query.register(show_request, F.data.startswith("show_request_"))
    router.callback_query.register(accept_request, F.data.startswith("accept_request_"))
    router.callback_query.register(reject_request, F.data.startswith("reject_request_"))
    router.callback_query.register(lambda c, state: my_requests(c.message, state), F.data == "back_to_requests")
    
    # Обработчики для админ-панели
    router.message.register(show_admin_menu, F.text == "🔙 Назад в админ-меню", StateFilter(*AdminStates.states))
    router.message.register(exit_admin_panel, F.text == "🔙 Выйти из админ-панели", StateFilter(*AdminStates.states))
    
    # Обработчик для создания тестовых данных
    router.message.register(create_test_data, F.text == "🔄 Создать тестовые данные", StateFilter(AdminStates.MAIN_MENU))
    
    # Обработчики для управления категориями
    router.message.register(admin_categories, F.text == "🔧 Категории", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_add_category, F.text == "➕ Добавить категорию", StateFilter(AdminStates.CATEGORIES))
    router.message.register(admin_save_category, StateFilter(AdminStates.ADD_CATEGORY))
    router.message.register(admin_toggle_category, StateFilter(AdminStates.CATEGORIES))
    
    # Обработчики для управления городами
    router.message.register(admin_cities, F.text == "🏙️ Города", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_add_city, F.text == "➕ Добавить город", StateFilter(AdminStates.CITIES))
    router.message.register(admin_save_city, StateFilter(AdminStates.ADD_CITY))
    router.message.register(admin_toggle_city, StateFilter(AdminStates.CITIES))
    
    # Обработчики для демо-генерации
    router.message.register(admin_demo_generation, F.text == "🤖 Демо-генерация", StateFilter(AdminStates.MAIN_MENU))
    router.message.register(admin_generate_demo_request, F.text == "🔄 Сгенерировать заявку", StateFilter(AdminStates.DEMO_GENERATION))
    router.message.register(admin_demo_stats, F.text == "📊 Статистика демо-заявок", StateFilter(AdminStates.DEMO_GENERATION))
    
    # Обработчики для статистики
    router.message.register(admin_stats, F.text == "📊 Статистика", StateFilter(AdminStates.MAIN_MENU))
    
    # Обработчики для выбора подкатегорий
    router.message.register(handle_subcategory_selection, StateFilter(UserStates.SELECTING_SUBCATEGORIES))
    
    # Регистрация обработчиков ошибок
    register_error_handlers(router)
    
    return router