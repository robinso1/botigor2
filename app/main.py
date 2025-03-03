from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.models import Base, get_db
from app.services import TelegramBot, RequestDistributor, DemoService
from app.config import settings
import asyncio
import logging
import sys

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(title="Bot Igor 2.0")

# Создаем таблицы в базе данных
from app.models.base import engine
Base.metadata.create_all(bind=engine)

# Глобальные объекты сервисов
bot: TelegramBot = None
request_distributor: RequestDistributor = None
demo_service: DemoService = None

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья приложения"""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Инициализация сервисов при запуске"""
    global bot, request_distributor, demo_service
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    # Инициализируем сервисы
    bot = TelegramBot(db)
    request_distributor = RequestDistributor(db)
    demo_service = DemoService(db)
    
    # Запускаем бота
    asyncio.create_task(bot.start())
    
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при остановке"""
    global bot
    if bot:
        await bot.stop()
    logger.info("Application shutdown complete")

# Здесь будут эндпоинты для админ-панели 