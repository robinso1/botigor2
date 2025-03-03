from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import settings
from app.models import User, Request, Category, City, RequestStatus
from sqlalchemy.orm import Session
from datetime import datetime
import re
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db: Session):
        self.db = db
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Обработчик для новых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Проверяем, существует ли пользователь в базе
        db_user = self.db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            # Создаем нового пользователя
            is_admin = user.id in settings.ADMIN_IDS
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                is_admin=is_admin
            )
            self.db.add(db_user)
            self.db.commit()
        
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я бот для распределения заявок. "
        )
        
        if db_user.is_admin:
            welcome_text += "\nУ вас есть права администратора."
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/status - Показать ваш статус\n"
        )
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        user = self.db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Вы не зарегистрированы. Используйте /start для регистрации.")
            return
        
        status_text = (
            f"Ваш статус:\n"
            f"{'Администратор' if user.is_admin else 'Пользователь'}\n"
            f"Активен: {'Да' if user.is_active else 'Нет'}\n"
            f"Категории: {', '.join(c.name for c in user.categories)}\n"
            f"Города: {', '.join(c.name for c in user.cities)}"
        )
        await update.message.reply_text(status_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик входящих сообщений"""
        # Здесь будет логика обработки заявок из чатов
        pass
    
    async def start(self):
        """Запуск бота"""
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
    
    async def stop(self):
        """Остановка бота"""
        await self.application.stop()
        await self.application.shutdown() 