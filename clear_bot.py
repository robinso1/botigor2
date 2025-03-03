import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

async def clear_bot_settings():
    load_dotenv()
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    # Удаляем все команды бота
    await bot.delete_my_commands()
    
    # Удаляем webhook если он был установлен
    await bot.delete_webhook()
    
    print("Настройки бота успешно очищены")

if __name__ == "__main__":
    asyncio.run(clear_bot_settings()) 