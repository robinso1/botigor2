"""
Модуль для настройки и инициализации базы данных.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

from bot.database.base import Base
from config import DATABASE_URL, DEBUG_MODE

# Создаем синхронный движок SQLAlchemy
# В режиме отладки используем echo=True для вывода SQL-запросов
engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG_MODE,
    poolclass=NullPool
)

# Создаем фабрику сессий
Session = sessionmaker(
    bind=engine, 
    expire_on_commit=False
)
session_factory = scoped_session(Session)

def setup_database():
    """
    Настраивает базу данных: создает таблицы, если они не существуют.
    """
    try:
        # Создаем таблицы
        Base.metadata.create_all(engine)
        
        logging.info("База данных настроена успешно")
    except Exception as e:
        logging.error(f"Ошибка при настройке базы данных: {e}")
        raise

def get_session():
    """
    Возвращает сессию базы данных.
    
    Returns:
        Session: Сессия SQLAlchemy
    """
    session = session_factory()
    try:
        return session
    finally:
        session.close() 