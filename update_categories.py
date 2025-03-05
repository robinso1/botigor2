#!/usr/bin/env python
"""
Скрипт для обновления категорий в базе данных в соответствии с новой структурой.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Category
from config import DATABASE_URL, DEFAULT_CATEGORIES

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_categories():
    """Обновляет категории в базе данных в соответствии с новой структурой"""
    # Создаем подключение к базе данных
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Получаем все существующие категории
        existing_categories = session.query(Category).all()
        logger.info(f"Найдено {len(existing_categories)} существующих категорий")
        
        # Деактивируем все существующие категории
        for category in existing_categories:
            category.is_active = False
            logger.info(f"Деактивирована категория: {category.name}")
        
        # Добавляем или активируем категории из DEFAULT_CATEGORIES
        for category_name in DEFAULT_CATEGORIES:
            # Проверяем, существует ли уже такая категория
            category = session.query(Category).filter(Category.name == category_name).first()
            
            if category:
                # Если категория существует, активируем ее
                category.is_active = True
                logger.info(f"Активирована существующая категория: {category.name}")
            else:
                # Если категории нет, создаем новую
                new_category = Category(name=category_name, is_active=True)
                session.add(new_category)
                logger.info(f"Добавлена новая категория: {category_name}")
        
        # Сохраняем изменения
        session.commit()
        logger.info("Категории успешно обновлены")
        
        # Выводим обновленный список категорий
        updated_categories = session.query(Category).all()
        logger.info(f"Обновленный список категорий ({len(updated_categories)}):")
        for category in updated_categories:
            status = "активна" if category.is_active else "неактивна"
            logger.info(f"- {category.name} (ID: {category.id}, {status})")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении категорий: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_categories() 