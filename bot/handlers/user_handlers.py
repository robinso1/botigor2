import logging
from typing import Dict, Any, List, Optional, Union, Callable
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from bot.models import get_session
from bot.services.user_service import UserService
from bot.services.request_service import RequestService
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    MAIN_MENU,
    PROFILE_MENU,
    SETTINGS_MENU,
    CATEGORY_SELECTION,
    CITY_SELECTION,
    PHONE_INPUT,
    REQUEST_MENU,
    REQUEST_STATUS_SELECTION,
) = range(8)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    session = get_session()
    user_service = UserService(session)
    
    # Получаем или создаем пользователя
    db_user = user_service.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Приветственное сообщение
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот Игорь для распределения заявок.\n\n"
        "Я буду отправлять вам заявки в соответствии с вашими настройками.\n"
        "Используйте меню для настройки профиля и просмотра заявок."
    )
    
    # Показываем главное меню
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает главное меню"""
    user = update.effective_user
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("📋 Мои заявки", callback_data="my_requests")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    
    # Добавляем кнопку админ-панели для администраторов
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔐 Админ-панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Определяем, нужно ли отправить новое сообщение или отредактировать существующее
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="Главное меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="Главное меню:",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает меню профиля"""
    user = update.effective_user
    session = get_session()
    user_service = UserService(session)
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем статистику пользователя
    stats = user_service.get_user_statistics(db_user.id)
    
    # Формируем текст профиля
    profile_text = (
        f"👤 *Профиль пользователя*\n\n"
        f"*Имя*: {db_user.first_name or 'Не указано'}\n"
        f"*Фамилия*: {db_user.last_name or 'Не указана'}\n"
        f"*Телефон*: {db_user.phone or 'Не указан'}\n\n"
        f"*Категории*: {', '.join([cat.name for cat in db_user.categories]) or 'Не выбраны'}\n"
        f"*Города*: {', '.join([city.name for city in db_user.cities]) or 'Не выбраны'}\n\n"
        f"*Статистика*:\n"
        f"Всего получено заявок: {stats['total_distributions']}\n"
        f"Просмотрено: {stats['status_stats'].get('просмотрено', 0)}\n"
        f"Принято: {stats['status_stats'].get('принято', 0)}\n"
        f"Отклонено: {stats['status_stats'].get('отклонено', 0)}"
    )
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("📱 Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=profile_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return PROFILE_MENU

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает меню настроек"""
    user = update.effective_user
    session = get_session()
    user_service = UserService(session)
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Формируем текст настроек
    settings_text = (
        f"⚙️ *Настройки*\n\n"
        f"Здесь вы можете настроить параметры получения заявок.\n\n"
        f"*Категории*: {', '.join([cat.name for cat in db_user.categories]) or 'Не выбраны'}\n"
        f"*Города*: {', '.join([city.name for city in db_user.cities]) or 'Не выбраны'}"
    )
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🏷️ Выбрать категории", callback_data="select_categories")],
        [InlineKeyboardButton("🏙️ Выбрать города", callback_data="select_cities")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=settings_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SETTINGS_MENU

async def select_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает меню выбора категорий"""
    session = get_session()
    user_service = UserService(session)
    user = update.effective_user
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем все категории
    from bot.models import Category
    categories = session.query(Category).filter(Category.is_active == True).all()
    
    # Создаем клавиатуру с категориями
    keyboard = []
    for category in categories:
        # Проверяем, выбрана ли категория пользователем
        is_selected = category in db_user.categories
        button_text = f"{'✅' if is_selected else '❌'} {category.name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"category_{category.id}")])
    
    # Добавляем кнопку "Готово"
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="categories_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите категории заявок, которые хотите получать:",
        reply_markup=reply_markup
    )
    
    return CATEGORY_SELECTION

async def toggle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор категории"""
    session = get_session()
    user_service = UserService(session)
    user = update.effective_user
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем ID категории из callback_data
    category_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем категорию
    from bot.models import Category
    category = session.query(Category).filter(Category.id == category_id).first()
    
    if category:
        # Проверяем, выбрана ли категория пользователем
        if category in db_user.categories:
            # Удаляем категорию из выбранных
            db_user.categories.remove(category)
        else:
            # Добавляем категорию в выбранные
            db_user.categories.append(category)
        
        session.commit()
    
    # Показываем обновленное меню выбора категорий
    return await select_categories(update, context)

async def select_cities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает меню выбора городов"""
    session = get_session()
    user_service = UserService(session)
    user = update.effective_user
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем все города
    from bot.models import City
    cities = session.query(City).filter(City.is_active == True).all()
    
    # Создаем клавиатуру с городами
    keyboard = []
    for city in cities:
        # Проверяем, выбран ли город пользователем
        is_selected = city in db_user.cities
        button_text = f"{'✅' if is_selected else '❌'} {city.name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"city_{city.id}")])
    
    # Добавляем кнопку "Готово"
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="cities_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберите города, по которым хотите получать заявки:",
        reply_markup=reply_markup
    )
    
    return CITY_SELECTION

async def toggle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор города"""
    session = get_session()
    user_service = UserService(session)
    user = update.effective_user
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем ID города из callback_data
    city_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем город
    from bot.models import City
    city = session.query(City).filter(City.id == city_id).first()
    
    if city:
        # Проверяем, выбран ли город пользователем
        if city in db_user.cities:
            # Удаляем город из выбранных
            db_user.cities.remove(city)
        else:
            # Добавляем город в выбранные
            db_user.cities.append(city)
        
        session.commit()
    
    # Показываем обновленное меню выбора городов
    return await select_cities(update, context)

async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает новый номер телефона"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Пожалуйста, отправьте ваш номер телефона в формате +7XXXXXXXXXX или нажмите на кнопку ниже:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Отмена", callback_data="back_to_profile")]
        ])
    )
    
    return PHONE_INPUT

async def save_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет новый номер телефона"""
    user = update.effective_user
    session = get_session()
    user_service = UserService(session)
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем номер телефона из сообщения
    phone = update.message.text.strip()
    
    # Обновляем номер телефона
    user_service.update_user(db_user.id, {"phone": phone})
    
    await update.message.reply_text("Номер телефона успешно обновлен!")
    
    # Возвращаемся в меню профиля
    return await profile_menu(update, context)

async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список заявок пользователя"""
    user = update.effective_user
    session = get_session()
    user_service = UserService(session)
    
    # Получаем пользователя из базы данных
    db_user = user_service.get_user_by_telegram_id(user.id)
    
    # Получаем распределения пользователя
    from bot.models import Distribution
    distributions = session.query(Distribution).filter(
        Distribution.user_id == db_user.id
    ).order_by(Distribution.created_at.desc()).limit(10).all()
    
    if not distributions:
        # Если у пользователя нет заявок
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="У вас пока нет заявок.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ])
        )
        return MAIN_MENU
    
    # Создаем клавиатуру с заявками
    keyboard = []
    for dist in distributions:
        request = dist.request
        status_emoji = {
            "отправлено": "📩",
            "просмотрено": "👁️",
            "принято": "✅",
            "отклонено": "❌"
        }.get(dist.status, "📩")
        
        button_text = f"{status_emoji} {request.client_name or 'Без имени'} - {request.status}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"request_{dist.id}")])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Ваши заявки (последние 10):",
        reply_markup=reply_markup
    )
    
    return REQUEST_MENU

async def show_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает детали заявки"""
    session = get_session()
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем распределение
    from bot.models import Distribution
    distribution = session.query(Distribution).filter(Distribution.id == distribution_id).first()
    
    if not distribution:
        await update.callback_query.answer("Заявка не найдена")
        return await my_requests(update, context)
    
    # Обновляем статус распределения на "просмотрено", если он был "отправлено"
    if distribution.status == "отправлено":
        distribution.status = "просмотрено"
        session.commit()
    
    # Получаем заявку
    request = distribution.request
    
    # Формируем текст заявки
    request_text = (
        f"📋 *Заявка #{request.id}*\n\n"
        f"*Клиент*: {request.client_name or 'Не указано'}\n"
        f"*Телефон*: {request.client_phone or 'Не указано'}\n"
        f"*Категория*: {request.category.name if request.category else 'Не указано'}\n"
        f"*Город*: {request.city.name if request.city else 'Не указано'}\n"
        f"*Адрес*: {request.address or 'Не указано'}\n"
        f"*Площадь*: {request.area or 'Не указано'} м²\n"
        f"*Статус*: {request.status}\n\n"
        f"*Описание*:\n{request.description or 'Нет описания'}\n\n"
        f"*Дата создания*: {request.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Создаем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{distribution_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{distribution_id}")
        ],
        [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_requests")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=request_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return REQUEST_MENU

async def accept_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Принимает заявку"""
    session = get_session()
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем распределение
    from bot.models import Distribution
    distribution = session.query(Distribution).filter(Distribution.id == distribution_id).first()
    
    if not distribution:
        await update.callback_query.answer("Заявка не найдена")
        return await my_requests(update, context)
    
    # Обновляем статус распределения на "принято"
    distribution.status = "принято"
    
    # Обновляем статус заявки на "в работе"
    distribution.request.status = "в работе"
    
    session.commit()
    
    await update.callback_query.answer("Заявка принята!")
    
    # Возвращаемся к списку заявок
    return await my_requests(update, context)

async def reject_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отклоняет заявку"""
    session = get_session()
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем распределение
    from bot.models import Distribution
    distribution = session.query(Distribution).filter(Distribution.id == distribution_id).first()
    
    if not distribution:
        await update.callback_query.answer("Заявка не найдена")
        return await my_requests(update, context)
    
    # Обновляем статус распределения на "отклонено"
    distribution.status = "отклонено"
    session.commit()
    
    await update.callback_query.answer("Заявка отклонена")
    
    # Возвращаемся к списку заявок
    return await my_requests(update, context)

def get_user_conversation_handler() -> ConversationHandler:
    """Возвращает ConversationHandler для пользовательских команд"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(profile_menu, pattern="^profile$"),
                CallbackQueryHandler(settings_menu, pattern="^settings$"),
                CallbackQueryHandler(my_requests, pattern="^my_requests$"),
                # Обработчик для админ-панели будет добавлен позже
            ],
            PROFILE_MENU: [
                CallbackQueryHandler(edit_phone, pattern="^edit_phone$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            SETTINGS_MENU: [
                CallbackQueryHandler(select_categories, pattern="^select_categories$"),
                CallbackQueryHandler(select_cities, pattern="^select_cities$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
            CATEGORY_SELECTION: [
                CallbackQueryHandler(toggle_category, pattern="^category_\d+$"),
                CallbackQueryHandler(settings_menu, pattern="^categories_done$"),
            ],
            CITY_SELECTION: [
                CallbackQueryHandler(toggle_city, pattern="^city_\d+$"),
                CallbackQueryHandler(settings_menu, pattern="^cities_done$"),
            ],
            PHONE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_phone),
                CallbackQueryHandler(profile_menu, pattern="^back_to_profile$"),
            ],
            REQUEST_MENU: [
                CallbackQueryHandler(show_request, pattern="^request_\d+$"),
                CallbackQueryHandler(accept_request, pattern="^accept_\d+$"),
                CallbackQueryHandler(reject_request, pattern="^reject_\d+$"),
                CallbackQueryHandler(my_requests, pattern="^back_to_requests$"),
                CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    ) 