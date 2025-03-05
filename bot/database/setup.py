"""
Модуль для настройки и инициализации базы данных.
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from bot.database.base import Base
from config import DATABASE_URL, DEBUG_MODE

# Создаем асинхронный движок SQLAlchemy
# В режиме отладки используем echo=True для вывода SQL-запросов
engine = create_async_engine(
    DATABASE_URL, 
    echo=DEBUG_MODE,
    poolclass=NullPool
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def setup_database():
    """
    Настраивает базу данных: создает таблицы, если они не существуют.
    """
    try:
        # Создаем таблицы
        async with engine.begin() as conn:
            # В режиме отладки можно пересоздать таблицы
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        logging.info("База данных настроена успешно")
    except Exception as e:
        logging.error(f"Ошибка при настройке базы данных: {e}")
        raise

async def get_session() -> AsyncSession:
    """
    Возвращает сессию базы данных.
    
    Returns:
        AsyncSession: Асинхронная сессия SQLAlchemy
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 