"""
Пакет с обработчиками команд бота
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import default_state

from bot.handlers.user_handlers import (
    start_command, show_main_menu, profile_menu, settings_menu,
    select_categories, toggle_category, select_cities, toggle_city,
    edit_phone, save_phone, my_requests, show_request,
    accept_request, reject_request, show_admin_message,
    UserStates
)
from bot.handlers.help_handlers import help_command
from bot.handlers.error_handlers import register_error_handlers

def setup_handlers() -> Router:
    """
    Настраивает и возвращает роутер с обработчиками команд
    """
    router = Router()
    
    # Регистрация обработчиков команд
    router.message.register(start_command, CommandStart(), state="*")
    router.message.register(show_main_menu, Command("menu"), state="*")
    router.message.register(help_command, Command("help"), state="*")
    
    # Обработчики для главного меню
    router.message.register(profile_menu, lambda msg: msg.text == "👤 Мой профиль", state=UserStates.MAIN_MENU)
    router.message.register(lambda msg, state: my_requests(msg, state, "all"), 
                           lambda msg: msg.text == "📋 Мои заявки", state=UserStates.MAIN_MENU)
    router.message.register(settings_menu, lambda msg: msg.text == "⚙️ Настройки", state=UserStates.MAIN_MENU)
    
    # Обработчики для меню профиля
    router.message.register(select_cities, lambda msg: msg.text == "🏙️ Выбрать города", state=UserStates.PROFILE_MENU)
    router.message.register(select_categories, lambda msg: msg.text == "🔧 Выбрать категории", state=UserStates.PROFILE_MENU)
    router.message.register(edit_phone, lambda msg: msg.text == "📱 Изменить телефон", state=UserStates.PROFILE_MENU)
    router.message.register(show_main_menu, lambda msg: msg.text == "🔙 Вернуться в главное меню", state=UserStates.PROFILE_MENU)
    
    # Обработчики для выбора категорий
    router.message.register(toggle_category, state=UserStates.SELECTING_CATEGORIES)
    
    # Обработчики для выбора городов
    router.message.register(toggle_city, state=UserStates.SELECTING_CITIES)
    
    # Обработчики для изменения телефона
    router.message.register(save_phone, state=UserStates.EDIT_PHONE)
    
    # Обработчики для меню настроек
    router.message.register(lambda msg, state: msg.answer("Настройки уведомлений в разработке"), 
                           lambda msg: msg.text == "🔔 Уведомления", state=UserStates.SETTINGS_MENU)
    router.message.register(show_main_menu, lambda msg: msg.text == "🔙 Вернуться в главное меню", state=UserStates.SETTINGS_MENU)
    
    # Обработчики для списка заявок
    router.message.register(lambda msg, state: my_requests(msg, state, "all"), 
                           lambda msg: msg.text == "📋 Все заявки", state=UserStates.MY_REQUESTS)
    router.message.register(lambda msg, state: my_requests(msg, state, "new"), 
                           lambda msg: msg.text == "🆕 Новые", state=UserStates.MY_REQUESTS)
    router.message.register(lambda msg, state: my_requests(msg, state, "accepted"), 
                           lambda msg: msg.text == "✅ Принятые", state=UserStates.MY_REQUESTS)
    router.message.register(lambda msg, state: my_requests(msg, state, "rejected"), 
                           lambda msg: msg.text == "❌ Отклоненные", state=UserStates.MY_REQUESTS)
    router.message.register(show_main_menu, lambda msg: msg.text == "🔙 Вернуться в главное меню", state=UserStates.MY_REQUESTS)
    
    # Обработчики для callback-запросов
    router.callback_query.register(show_request, lambda c: c.data.startswith("show_request_"))
    router.callback_query.register(accept_request, lambda c: c.data.startswith("accept_request_"))
    router.callback_query.register(reject_request, lambda c: c.data.startswith("reject_request_"))
    router.callback_query.register(lambda c, state: my_requests(c.message, state), 
                                  lambda c: c.data == "back_to_requests")
    
    # Обработчик для админ-команды
    router.message.register(show_admin_message, Command("admin"))
    
    # Регистрация обработчиков ошибок
    register_error_handlers(router)
    
    return router 