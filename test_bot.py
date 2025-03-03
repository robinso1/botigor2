import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен бота из config.py
from config import TELEGRAM_BOT_TOKEN

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    update.message.reply_text("Привет! Я тестовый бот.")

def main() -> None:
    """Основная функция приложения"""
    try:
        # Создаем Updater и передаем ему токен бота
        updater = Updater(TELEGRAM_BOT_TOKEN)
        
        # Получаем диспетчер для регистрации обработчиков
        dispatcher = updater.dispatcher
        
        # Добавляем обработчик команды /start
        dispatcher.add_handler(CommandHandler("start", start))
        
        # Запускаем бота
        logger.info("Запуск тестового бота...")
        updater.start_polling()
        
        # Останавливаем бота при нажатии Ctrl+C
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main() 