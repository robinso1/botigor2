"""
Сервис для работы с подкатегориями
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from bot.models import SubCategory, User, Category

# Настройка логирования
logger = logging.getLogger(__name__)

class SubCategoryService:
    """Сервис для работы с подкатегориями"""
    
    def __init__(self, session: Session):
        """Инициализация сервиса"""
        self.session = session
    
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[SubCategory]:
        """Получение подкатегории по ID"""
        try:
            return self.session.query(SubCategory).filter(
                SubCategory.id == subcategory_id,
                SubCategory.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении подкатегории по ID {subcategory_id}: {e}")
            return None
    
    def get_subcategories_by_category(self, category_id: int) -> List[SubCategory]:
        """Получение подкатегорий по ID категории"""
        try:
            return self.session.query(SubCategory).filter(
                SubCategory.category_id == category_id,
                SubCategory.is_active == True
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении подкатегорий для категории {category_id}: {e}")
            return []
    
    def get_user_subcategories(self, user_id: int) -> List[SubCategory]:
        """Получение подкатегорий пользователя"""
        try:
            user = self.session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
            return user.subcategories
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении подкатегорий пользователя {user_id}: {e}")
            return []
    
    def add_subcategory_to_user(self, user_id: int, subcategory_id: int) -> bool:
        """Добавление подкатегории пользователю"""
        try:
            user = self.session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                logger.error(f"Пользователь с ID {user_id} не найден")
                return False
            
            subcategory = self.get_subcategory_by_id(subcategory_id)
            if not subcategory:
                logger.error(f"Подкатегория с ID {subcategory_id} не найдена")
                return False
            
            if subcategory not in user.subcategories:
                user.subcategories.append(subcategory)
                self.session.commit()
            
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении подкатегории {subcategory_id} пользователю {user_id}: {e}")
            self.session.rollback()
            return False
    
    def remove_subcategory_from_user(self, user_id: int, subcategory_id: int) -> bool:
        """Удаление подкатегории у пользователя"""
        try:
            user = self.session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                logger.error(f"Пользователь с ID {user_id} не найден")
                return False
            
            subcategory = self.get_subcategory_by_id(subcategory_id)
            if not subcategory:
                logger.error(f"Подкатегория с ID {subcategory_id} не найдена")
                return False
            
            if subcategory in user.subcategories:
                user.subcategories.remove(subcategory)
                self.session.commit()
            
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении подкатегории {subcategory_id} у пользователя {user_id}: {e}")
            self.session.rollback()
            return False
    
    def create_subcategory(self, name: str, category_id: int, description: str = None,
                          subcategory_type: str = "boolean", min_value: float = None,
                          max_value: float = None) -> Optional[SubCategory]:
        """Создание новой подкатегории"""
        try:
            # Проверяем существование категории
            category = self.session.query(Category).filter(
                Category.id == category_id,
                Category.is_active == True
            ).first()
            
            if not category:
                logger.error(f"Категория с ID {category_id} не найдена")
                return None
            
            # Создаем новую подкатегорию
            subcategory = SubCategory(
                name=name,
                description=description,
                category_id=category_id,
                type=subcategory_type,
                min_value=min_value,
                max_value=max_value,
                is_active=True
            )
            
            self.session.add(subcategory)
            self.session.commit()
            
            return subcategory
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании подкатегории {name}: {e}")
            self.session.rollback()
            return None
    
    def update_subcategory(self, subcategory_id: int, **kwargs) -> bool:
        """Обновление подкатегории"""
        try:
            subcategory = self.get_subcategory_by_id(subcategory_id)
            if not subcategory:
                logger.error(f"Подкатегория с ID {subcategory_id} не найдена")
                return False
            
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(subcategory, key):
                    setattr(subcategory, key, value)
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении подкатегории {subcategory_id}: {e}")
            self.session.rollback()
            return False
    
    def deactivate_subcategory(self, subcategory_id: int) -> bool:
        """Деактивация подкатегории"""
        return self.update_subcategory(subcategory_id, is_active=False)
    
    def get_subcategories_for_request(self, request_id: int) -> List[Dict[str, Any]]:
        """Получение подкатегорий для заявки"""
        from bot.models import Request
        
        try:
            request = self.session.query(Request).filter(Request.id == request_id).first()
            if not request:
                logger.error(f"Заявка с ID {request_id} не найдена")
                return []
            
            result = []
            for subcategory in request.subcategories:
                result.append({
                    "id": subcategory.id,
                    "name": subcategory.name,
                    "description": subcategory.description,
                    "category_id": subcategory.category_id,
                    "category_name": subcategory.category.name if subcategory.category else "Неизвестно",
                    "type": subcategory.type
                })
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении подкатегорий для заявки {request_id}: {e}")
            return [] 