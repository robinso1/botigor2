import logging
from typing import Dict, Any, List, Optional, Union, Callable
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
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
    try:
        logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
        user = update.effective_user
        session = get_session()
        
        logger.info("Создаем экземпляр UserService")
        user_service = UserService(session)
        
        # Получаем или создаем пользователя
        logger.info(f"Получаем или создаем пользователя с ID {user.id}")
        db_user = user_service.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"Пользователь получен/создан: {db_user.id}")
        
        # Приветственное сообщение
        logger.info("Отправляем приветственное сообщение")
        await update.message.reply_text(
            f"Привет, {user.first_name}! Я бот по распределению заявок.\n\n"
            "Я буду отправлять вам заявки в соответствии с вашими настройками.\n"
            "Используйте меню для настройки профиля и просмотра заявок."
        )
        
        # Показываем главное меню
        logger.info("Переходим к показу главного меню")
        return await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при обработке команды. Пожалуйста, попробуйте еще раз или обратитесь к администратору."
        )
        return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает главное меню"""
    try:
        logger.info(f"Вызвана функция show_main_menu для пользователя {update.effective_user.id}")
        user = update.effective_user
        
        # Создаем клавиатуру с кнопками внизу экрана
        keyboard = [
            ["📋 Мои заявки"],
            ["👤 Профиль", "⚙️ Настройки"]
        ]
        
        # Добавляем кнопку админ-панели для администраторов
        if user.id in ADMIN_IDS:
            logger.info(f"Пользователь {user.id} является администратором, добавляем кнопку админ-панели")
            keyboard.append(["🔐 Админ-панель"])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Определяем, нужно ли отправить новое сообщение или ответить на существующее
        if update.callback_query:
            logger.info("Обрабатываем callback_query")
            update.callback_query.answer()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Главное меню системы распределения заявок:",
                reply_markup=reply_markup
            )
        else:
            logger.info("Отправляем сообщение с главным меню")
            await update.message.reply_text(
                text="Главное меню системы распределения заявок:",
                reply_markup=reply_markup
            )
        
        logger.info("Главное меню успешно отображено")
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Ошибка в функции show_main_menu: {str(e)}", exc_info=True)
        try:
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Произошла ошибка при отображении меню. Пожалуйста, попробуйте еще раз или используйте команду /start."
                )
            else:
                await update.message.reply_text(
                    text="Произошла ошибка при отображении меню. Пожалуйста, попробуйте еще раз или используйте команду /start."
                )
        except Exception:
            logger.error("Не удалось отправить сообщение об ошибке", exc_info=True)
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
    
    # Создаем клавиатуру для inline кнопок
    inline_keyboard = [
        [InlineKeyboardButton("📱 Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # Создаем клавиатуру для reply кнопок
    reply_keyboard = [
        ["📱 Изменить телефон"],
        ["🔙 Вернуться в главное меню"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    if update.callback_query:
        # Проверяем, что callback_query не None перед вызовом answer()
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=profile_text,
            reply_markup=inline_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=profile_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
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
        f"*Категории*: {', '.join([cat.name for cat in db_user.categories]) or 'Не выбраны'}\n"
        f"*Города*: {', '.join([city.name for city in db_user.cities]) or 'Не выбраны'}\n"
        f"*Телефон*: {db_user.phone or 'Не указан'}"
    )
    
    # Создаем клавиатуру для inline кнопок
    inline_keyboard = [
        [InlineKeyboardButton("🏷️ Выбрать категории", callback_data="select_categories")],
        [InlineKeyboardButton("🏙️ Выбрать города", callback_data="select_cities")],
        [InlineKeyboardButton("📱 Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # Создаем клавиатуру для reply кнопок
    reply_keyboard = [
        ["🏷️ Выбрать категории", "🏙️ Выбрать города"],
        ["📱 Изменить телефон"],
        ["🔙 Вернуться в главное меню"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    if update.callback_query:
        # Проверяем, что callback_query не None перед вызовом answer()
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=settings_text,
            reply_markup=inline_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=settings_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
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
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_category_{category.id}")])
    
    # Добавляем кнопку "Готово"
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="back_to_settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Создаем клавиатуру для reply кнопок
    reply_keyboard = [["🔙 Вернуться в главное меню"]]
    reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="Выберите категории заявок, которые хотите получать:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="Выберите категории заявок, которые хотите получать:",
            reply_markup=reply_markup
        )
        # Добавляем кнопку возврата в главное меню
        await update.message.reply_text(
            "Используйте кнопку ниже для возврата в главное меню:",
            reply_markup=reply_markup_keyboard
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
    category_id = int(update.callback_query.data.split("_")[2])
    
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
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_city_{city.id}")])
    
    # Добавляем кнопку "Готово"
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="back_to_settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Создаем клавиатуру для reply кнопок
    reply_keyboard = [["🔙 Вернуться в главное меню"]]
    reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="Выберите города, в которых хотите получать заявки:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="Выберите города, в которых хотите получать заявки:",
            reply_markup=reply_markup
        )
        # Добавляем кнопку возврата в главное меню
        await update.message.reply_text(
            "Используйте кнопку ниже для возврата в главное меню:",
            reply_markup=reply_markup_keyboard
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
    city_id = int(update.callback_query.data.split("_")[2])
    
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
    """Показывает форму редактирования телефона"""
    # Создаем клавиатуру для reply кнопок
    reply_keyboard = [["🔙 Вернуться в главное меню"]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    if update.callback_query:
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="Введите ваш номер телефона в формате +7XXXXXXXXXX:"
        )
        # Отправляем дополнительное сообщение с кнопкой возврата
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Или используйте кнопку ниже для возврата в главное меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="Введите ваш номер телефона в формате +7XXXXXXXXXX:",
            reply_markup=reply_markup
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
    
    # Отправляем сообщение об успешном обновлении
    await update.message.reply_text(f"Номер телефона успешно обновлен!")
    
    # Возвращаемся в меню профиля
    return await profile_menu(update, context)

async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список заявок пользователя"""
    user = update.effective_user
    session = get_session()
    request_service = RequestService(session)
    
    # Получаем распределения пользователя
    distributions = request_service.get_user_distributions(user.id)
    
    if not distributions:
        # Создаем клавиатуру
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение
        if update.callback_query:
            update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text="У вас пока нет заявок.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text="У вас пока нет заявок.",
                reply_markup=ReplyKeyboardMarkup([["🔙 Вернуться в главное меню"]], resize_keyboard=True)
            )
        
        return REQUEST_MENU
    
    # Создаем список заявок
    text = "📋 *Ваши заявки*:\n\n"
    
    # Создаем клавиатуру
    keyboard = []
    
    for dist in distributions:
        request = dist.request
        status_emoji = {
            "отправлено": "📤",
            "просмотрено": "👁️",
            "принято": "✅",
            "отклонено": "❌",
            "завершено": "🏁",
            "отменено": "🚫"
        }.get(dist.status, "❓")
        
        # Добавляем информацию о заявке
        text += f"{status_emoji} *Заявка #{request.id}*\n"
        text += f"Статус: {dist.status}\n"
        if request.client_name:
            text += f"Клиент: {request.client_name}\n"
        if request.category:
            text += f"Категория: {request.category.name}\n"
        if request.city:
            text += f"Город: {request.city.name}\n"
        text += f"Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Добавляем кнопку для просмотра заявки
        keyboard.append([InlineKeyboardButton(
            f"Заявка #{request.id} ({dist.status})",
            callback_data=f"request_{dist.id}"
        )])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение
    if update.callback_query:
        update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Для текстовых кнопок отправляем сначала список заявок с inline кнопками
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        # И добавляем кнопку возврата в главное меню
        await update.message.reply_text(
            "Выберите заявку или вернитесь в главное меню:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Вернуться в главное меню"]], resize_keyboard=True)
        )
    
    return REQUEST_MENU

async def show_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает детали заявки"""
    session = get_session()
    request_service = RequestService(session)
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[1])
    
    # Получаем распределение
    distribution = request_service.get_distribution(distribution_id)
    
    if not distribution:
        update.callback_query.answer("Заявка не найдена")
        return await my_requests(update, context)
    
    # Обновляем статус распределения на "просмотрено", если он "новая"
    if distribution.status == "новая":
        request_service.update_distribution_status(distribution_id, "просмотрено")
        distribution.status = "просмотрено"
    
    # Получаем заявку
    request = distribution.request
    
    # Формируем текст деталей заявки
    request_text = (
        f"📋 *Заявка #{request.id}*\n\n"
        f"*Клиент*: {request.client_name or 'Не указан'}\n"
        f"*Телефон*: {request.client_phone or 'Не указан'}\n"
        f"*Категория*: {request.category.name if request.category else 'Не указана'}\n"
        f"*Город*: {request.city.name if request.city else 'Не указан'}\n"
        f"*Площадь*: {request.area or 'Не указана'} м²\n"
        f"*Адрес*: {request.address or 'Не указан'}\n\n"
        f"*Описание*:\n{request.description or 'Не указано'}\n\n"
        f"*Статус*: {distribution.status}\n"
        f"*Дата создания*: {request.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Создаем клавиатуру
    keyboard = []
    
    # Добавляем кнопки действий в зависимости от статуса
    if distribution.status in ["новая", "просмотрено"]:
        keyboard.append([
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_request_{distribution_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_request_{distribution_id}")
        ])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_requests")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=request_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return REQUEST_MENU

async def accept_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Принимает заявку"""
    session = get_session()
    request_service = RequestService(session)
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[2])
    
    # Обновляем статус распределения на "принято"
    request_service.update_distribution_status(distribution_id, "принято")
    
    await update.callback_query.answer("Заявка принята!")
    
    # Возвращаемся к списку заявок
    return await my_requests(update, context)

async def reject_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отклоняет заявку"""
    session = get_session()
    request_service = RequestService(session)
    
    # Получаем ID распределения из callback_data
    distribution_id = int(update.callback_query.data.split("_")[2])
    
    # Обновляем статус распределения на "отклонено"
    request_service.update_distribution_status(distribution_id, "отклонено")
    
    await update.callback_query.answer("Заявка отклонена!")
    
    # Возвращаемся к списку заявок
    return await my_requests(update, context)

async def show_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает сообщение о необходимости использовать команду /admin"""
    await update.message.reply_text("Используйте команду /admin для доступа к админ-панели")
    return MAIN_MENU

def get_user_conversation_handler() -> ConversationHandler:
    """Возвращает обработчик диалога с пользователем"""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^📋 Мои заявки$'), my_requests),
                MessageHandler(filters.Regex('^👤 Профиль$'), profile_menu),
                MessageHandler(filters.Regex('^⚙️ Настройки$'), settings_menu),
                MessageHandler(filters.Regex('^🔐 Админ-панель$'), show_admin_message),
                CallbackQueryHandler(my_requests, pattern='^my_requests$'),
                CallbackQueryHandler(profile_menu, pattern='^profile$'),
                CallbackQueryHandler(settings_menu, pattern='^settings$'),
                CallbackQueryHandler(lambda u, c: u.callback_query.answer("Используйте команду /admin для доступа к админ-панели"), pattern='^admin$'),
            ],
            PROFILE_MENU: [
                MessageHandler(filters.Regex('^📱 Изменить телефон$'), edit_phone),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
                CallbackQueryHandler(edit_phone, pattern='^edit_phone$'),
                CallbackQueryHandler(show_main_menu, pattern='^back_to_main$'),
            ],
            SETTINGS_MENU: [
                MessageHandler(filters.Regex('^🏷️ Выбрать категории$'), select_categories),
                MessageHandler(filters.Regex('^🏙️ Выбрать города$'), select_cities),
                MessageHandler(filters.Regex('^📱 Изменить телефон$'), edit_phone),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
                CallbackQueryHandler(select_categories, pattern='^select_categories$'),
                CallbackQueryHandler(select_cities, pattern='^select_cities$'),
                CallbackQueryHandler(edit_phone, pattern='^edit_phone$'),
                CallbackQueryHandler(show_main_menu, pattern='^back_to_main$'),
            ],
            CATEGORY_SELECTION: [
                CallbackQueryHandler(toggle_category, pattern='^toggle_category_'),
                CallbackQueryHandler(settings_menu, pattern='^back_to_settings$'),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
            ],
            CITY_SELECTION: [
                CallbackQueryHandler(toggle_city, pattern='^toggle_city_'),
                CallbackQueryHandler(settings_menu, pattern='^back_to_settings$'),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
            ],
            PHONE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^🔙 Вернуться в главное меню$'), save_phone),
                CallbackQueryHandler(settings_menu, pattern='^back_to_settings$'),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
            ],
            REQUEST_MENU: [
                CallbackQueryHandler(show_request, pattern='^request_'),
                CallbackQueryHandler(my_requests, pattern='^back_to_requests$'),
                CallbackQueryHandler(show_main_menu, pattern='^back_to_main$'),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
            ],
            REQUEST_STATUS_SELECTION: [
                CallbackQueryHandler(accept_request, pattern='^accept_request_'),
                CallbackQueryHandler(reject_request, pattern='^reject_request_'),
                CallbackQueryHandler(my_requests, pattern='^back_to_requests$'),
                CallbackQueryHandler(show_main_menu, pattern='^back_to_main$'),
                MessageHandler(filters.Regex('^🔙 Вернуться в главное меню$'), show_main_menu),
            ],
        },
        fallbacks=[CommandHandler('start', start_command)],
        name="user_conversation",
        persistent=False
    )

def user_conversation_handler() -> ConversationHandler:
    """Возвращает обработчик диалога с пользователем (для совместимости)"""
    return get_user_conversation_handler() 