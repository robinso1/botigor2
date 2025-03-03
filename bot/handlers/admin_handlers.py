import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import TelegramError

from bot.models import get_session, User, Category, City, Request, Distribution
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from bot.utils.demo_utils import generate_demo_request
from config import ADMIN_IDS, DEFAULT_CATEGORIES, DEFAULT_CITIES
from bot.handlers.user_handlers import show_main_menu

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    ADMIN_MAIN,
    ADMIN_STATS,
    ADMIN_USERS,
    ADMIN_CATEGORIES,
    ADMIN_CITIES,
    ADMIN_REQUESTS,
    ADMIN_ADD_CATEGORY,
    ADMIN_ADD_CITY,
    ADMIN_ADD_REQUEST,
    ADMIN_REQUEST_DETAILS,
    ADMIN_EDIT_REQUEST,
    ADMIN_EDIT_REQUEST_STATUS,
    ADMIN_EDIT_REQUEST_CATEGORY,
    ADMIN_EDIT_REQUEST_CITY,
    ADMIN_EDIT_REQUEST_CLIENT_NAME,
    ADMIN_EDIT_REQUEST_CLIENT_PHONE,
    ADMIN_EDIT_REQUEST_DESCRIPTION,
    ADMIN_EDIT_REQUEST_AREA,
    ADMIN_EDIT_REQUEST_ADDRESS,
) = range(19)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает админ-панель"""
    user = update.effective_user
    
    # Проверяем, является ли пользователь администратором
    if user.id not in ADMIN_IDS:
        if update.callback_query:
            await update.callback_query.answer("У вас нет доступа к админ-панели")
        else:
            await update.message.reply_text("У вас нет доступа к админ-панели")
        
        # Возвращаемся в главное меню
        return await show_main_menu(update, context)
    
    # Создаем клавиатуру с кнопками внизу экрана
    keyboard = [
        ["📊 Статистика", "👥 Пользователи"],
        ["🏷️ Категории", "🏙️ Города"],
        ["📋 Заявки", "➕ Добавить заявку"],
        ["🎲 Создать демо-заявку"],
        ["🔙 Вернуться в главное меню"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Панель администратора системы распределения заявок:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="Панель администратора системы распределения заявок:",
            reply_markup=reply_markup
        )
    
    return ADMIN_MAIN

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает статистику"""
    session = get_session()
    request_service = RequestService(session)
    
    # Получаем статистику
    stats = request_service.get_request_statistics()
    
    # Формируем текст статистики
    stats_text = (
        f"📊 *Статистика*\n\n"
        f"Всего заявок: {stats['total_requests']}\n"
        f"Новых заявок: {stats['new_requests']}\n"
        f"В работе: {stats['in_progress_requests']}\n"
        f"Завершенных: {stats['completed_requests']}\n"
        f"Отмененных: {stats['cancelled_requests']}\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Активных пользователей: {stats['active_users']}\n"
        f"Администраторов: {stats['admin_users']}\n\n"
        f"Заявок за сегодня: {stats['today_requests']}\n"
        f"Заявок за неделю: {stats['week_requests']}\n"
        f"Заявок за месяц: {stats['month_requests']}"
    )
    
    # Создаем клавиатуру для возврата в админ-панель
    keyboard = [["🔙 Вернуться в админ-панель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Отправляем сообщение
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ADMIN_STATS

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список пользователей"""
    session = get_session()
    user_service = UserService(session)
    
    # Получаем всех пользователей
    users = user_service.get_all_users()
    
    # Формируем текст списка пользователей
    users_text = f"👥 *Пользователи* ({len(users)})\n\n"
    
    for user in users[:10]:  # Показываем только первые 10 пользователей
        admin_mark = "👑 " if user.is_admin else ""
        active_mark = "✅ " if user.is_active else "❌ "
        users_text += f"{admin_mark}{active_mark}*{user.first_name or ''} {user.last_name or ''}* (@{user.username or 'нет'})\n"
    
    if len(users) > 10:
        users_text += f"\n... и еще {len(users) - 10} пользователей"
    
    # Создаем клавиатуру для возврата в админ-панель
    keyboard = [["🔙 Вернуться в админ-панель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=users_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=users_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ADMIN_USERS

async def admin_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список категорий"""
    session = get_session()
    
    # Получаем все категории
    categories = session.query(Category).all()
    
    # Формируем текст списка категорий
    categories_text = f"🏷️ *Категории* ({len(categories)})\n\n"
    
    for category in categories:
        active_mark = "✅ " if category.is_active else "❌ "
        categories_text += f"{active_mark}*{category.name}*\n"
    
    # Создаем клавиатуру
    keyboard = [
        ["➕ Добавить категорию"],
        ["🔙 Вернуться в админ-панель"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=categories_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=categories_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ADMIN_CATEGORIES

async def admin_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает название новой категории"""
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Пожалуйста, введите название новой категории:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            text="Пожалуйста, введите название новой категории:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    
    return ADMIN_ADD_CATEGORY

async def admin_save_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет новую категорию"""
    session = get_session()
    
    # Получаем название категории из сообщения
    category_name = update.message.text.strip()
    
    # Проверяем, существует ли уже такая категория
    existing_category = session.query(Category).filter(Category.name == category_name).first()
    
    if existing_category:
        await update.message.reply_text(f"Категория '{category_name}' уже существует!")
    else:
        # Создаем новую категорию
        category = Category(name=category_name, is_active=True)
        session.add(category)
        session.commit()
        
        await update.message.reply_text(f"Категория '{category_name}' успешно добавлена!")
    
    # Возвращаемся к списку категорий
    return await admin_categories(update, context)

async def admin_cities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список городов"""
    session = get_session()
    
    # Получаем все города
    cities = session.query(City).all()
    
    # Формируем текст списка городов
    cities_text = f"🏙️ *Города* ({len(cities)})\n\n"
    
    for city in cities:
        active_mark = "✅ " if city.is_active else "❌ "
        cities_text += f"{active_mark}*{city.name}*\n"
    
    # Создаем клавиатуру
    keyboard = [
        ["➕ Добавить город"],
        ["🔙 Вернуться в админ-панель"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=cities_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=cities_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ADMIN_CITIES

async def admin_add_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает название нового города"""
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Пожалуйста, введите название нового города:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            text="Пожалуйста, введите название нового города:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    
    return ADMIN_ADD_CITY

async def admin_save_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет новый город"""
    session = get_session()
    
    # Получаем название города из сообщения
    city_name = update.message.text.strip()
    
    # Проверяем, существует ли уже такой город
    existing_city = session.query(City).filter(City.name == city_name).first()
    
    if existing_city:
        await update.message.reply_text(f"Город '{city_name}' уже существует!")
    else:
        # Создаем новый город
        city = City(name=city_name, is_active=True)
        session.add(city)
        session.commit()
        
        await update.message.reply_text(f"Город '{city_name}' успешно добавлен!")
    
    # Возвращаемся к списку городов
    return await admin_cities(update, context)

async def admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список заявок"""
    session = get_session()
    
    # Получаем все заявки
    requests = session.query(Request).order_by(Request.created_at.desc()).limit(10).all()
    
    # Формируем текст списка заявок
    requests_text = f"📋 *Заявки* (последние 10)\n\n"
    
    for request in requests:
        status_emoji = {
            "новая": "🆕",
            "актуальная": "✅",
            "неактуальная": "❌",
            "в работе": "🔄",
            "замер": "📏",
            "отказ клиента": "🚫",
            "выполнена": "✨"
        }.get(request.status, "🆕")
        
        demo_mark = "🎲 " if request.is_demo else ""
        requests_text += f"{demo_mark}{status_emoji} *#{request.id}* - {request.client_name or 'Без имени'} ({request.created_at.strftime('%d.%m.%Y')})\n"
    
    # Создаем клавиатуру
    keyboard = [
        ["➕ Добавить заявку"],
        ["🎲 Создать демо-заявку"],
        ["🔙 Вернуться в админ-панель"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=requests_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=requests_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ADMIN_REQUESTS

async def admin_create_demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Создает демо-заявку"""
    session = get_session()
    request_service = RequestService(session)
    
    # Генерируем демо-заявку
    demo_data = generate_demo_request()
    demo_data['is_demo'] = True
    
    # Создаем заявку
    request = request_service.create_request(demo_data)
    
    # Распределяем заявку
    distributions = request_service.distribute_request(request.id)
    
    # Формируем сообщение об успехе
    success_text = f"✅ Демо-заявка успешно создана и распределена!\n\n"
    success_text += f"ID: {request.id}\n"
    success_text += f"Клиент: {request.client_name}\n"
    success_text += f"Телефон: {request.client_phone}\n"
    success_text += f"Категория: {request.category.name if request.category else 'Не указана'}\n"
    success_text += f"Город: {request.city.name if request.city else 'Не указан'}\n"
    success_text += f"Распределена: {len(distributions)} пользователям"
    
    # Отправляем сообщение
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=success_text,
            reply_markup=ReplyKeyboardMarkup([["🔙 Вернуться в админ-панель"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            text=success_text,
            reply_markup=ReplyKeyboardMarkup([["🔙 Вернуться в админ-панель"]], resize_keyboard=True)
        )
    
    return ADMIN_MAIN

async def admin_add_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает данные для новой заявки"""
    session = get_session()
    
    # Получаем все категории и города для выбора
    categories = session.query(Category).filter(Category.is_active == True).all()
    cities = session.query(City).filter(City.is_active == True).all()
    
    # Сохраняем их в контексте
    context.user_data['categories'] = categories
    context.user_data['cities'] = cities
    context.user_data['new_request'] = {}
    
    # Запрашиваем имя клиента
    if update.callback_query:
        update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Пожалуйста, введите имя клиента:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            text="Пожалуйста, введите имя клиента:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        )
    
    return ADMIN_ADD_REQUEST

def get_admin_conversation_handler() -> ConversationHandler:
    """Возвращает обработчик диалога с администратором"""
    return ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            ADMIN_MAIN: [
                MessageHandler(filters.Regex('^📊 Статистика$'), admin_stats),
                MessageHandler(filters.Regex('^👥 Пользователи$'), admin_users),
                MessageHandler(filters.Regex('^🏷️ Категории$'), admin_categories),
                MessageHandler(filters.Regex('^🏙️ Города$'), admin_cities),
                MessageHandler(filters.Regex('^📋 Заявки$'), admin_requests),
                MessageHandler(filters.Regex('^➕ Добавить заявку$'), admin_add_request),
                MessageHandler(filters.Regex('^🎲 Создать демо-заявку$'), admin_create_demo),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), lambda u, c: show_main_menu(u, c)),
                # Оставляем обработчики для callback_query для обратной совместимости
                CallbackQueryHandler(admin_stats, pattern='^admin_stats$'),
                CallbackQueryHandler(admin_users, pattern='^admin_users$'),
                CallbackQueryHandler(admin_categories, pattern='^admin_categories$'),
                CallbackQueryHandler(admin_cities, pattern='^admin_cities$'),
                CallbackQueryHandler(admin_requests, pattern='^admin_requests$'),
                CallbackQueryHandler(admin_add_request, pattern='^admin_add_request$'),
                CallbackQueryHandler(admin_create_demo, pattern='^admin_create_demo$'),
                CallbackQueryHandler(lambda u, c: show_main_menu(u, c), pattern='^back_to_main$'),
            ],
            ADMIN_STATS: [
                MessageHandler(filters.Regex('^🔙 Вернуться в админ-панель$'), admin_panel),
                CallbackQueryHandler(admin_panel, pattern="^back_to_admin$"),
            ],
            ADMIN_USERS: [
                MessageHandler(filters.Regex('^🔙 Вернуться в админ-панель$'), admin_panel),
                CallbackQueryHandler(admin_panel, pattern="^back_to_admin$"),
            ],
            ADMIN_CATEGORIES: [
                MessageHandler(filters.Regex('^➕ Добавить категорию$'), admin_add_category),
                MessageHandler(filters.Regex('^🔙 Вернуться в админ-панель$'), admin_panel),
                CallbackQueryHandler(admin_add_category, pattern="^admin_add_category$"),
                CallbackQueryHandler(admin_panel, pattern="^back_to_admin$"),
            ],
            ADMIN_ADD_CATEGORY: [
                MessageHandler(filters.Regex('^🔙 Отмена$'), admin_categories),
                MessageHandler(filters.text & ~filters.command, admin_save_category),
                CallbackQueryHandler(admin_categories, pattern="^back_to_categories$"),
            ],
            ADMIN_CITIES: [
                MessageHandler(filters.Regex('^➕ Добавить город$'), admin_add_city),
                MessageHandler(filters.Regex('^🔙 Вернуться в админ-панель$'), admin_panel),
                CallbackQueryHandler(admin_add_city, pattern="^admin_add_city$"),
                CallbackQueryHandler(admin_panel, pattern="^back_to_admin$"),
            ],
            ADMIN_ADD_CITY: [
                MessageHandler(filters.Regex('^🔙 Отмена$'), admin_cities),
                MessageHandler(filters.text & ~filters.command, admin_save_city),
                CallbackQueryHandler(admin_cities, pattern="^back_to_cities$"),
            ],
            ADMIN_REQUESTS: [
                MessageHandler(filters.Regex('^➕ Добавить заявку$'), admin_add_request),
                MessageHandler(filters.Regex('^🎲 Создать демо-заявку$'), admin_create_demo),
                MessageHandler(filters.Regex('^🔙 Вернуться в админ-панель$'), admin_panel),
                CallbackQueryHandler(admin_add_request, pattern="^admin_add_request$"),
                CallbackQueryHandler(admin_create_demo, pattern="^admin_create_demo$"),
                CallbackQueryHandler(admin_panel, pattern="^back_to_admin$"),
            ],
            ADMIN_ADD_REQUEST: [
                MessageHandler(filters.Regex('^🔙 Отмена$'), admin_requests),
                MessageHandler(filters.text & ~filters.command, lambda u, c: admin_save_city(u, c)),  # Заглушка, нужно реализовать
                CallbackQueryHandler(admin_requests, pattern="^back_to_requests$"),
            ],
        },
        fallbacks=[CommandHandler('admin', admin_panel), CommandHandler('start', lambda u, c: show_main_menu(u, c))],
        name="admin_conversation",
        persistent=False
    )

def admin_conversation_handler() -> ConversationHandler:
    """Возвращает обработчик диалога с администратором (для совместимости)"""
    return get_admin_conversation_handler()
