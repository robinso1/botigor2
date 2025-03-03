import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from bot.models import User, Category, City, Distribution
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_or_create_user(self, telegram_id: int, username: Optional[str] = None, 
                          first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """
        Получает существующего пользователя или создает нового
        
        Args:
            telegram_id (int): ID пользователя в Telegram
            username (Optional[str]): Имя пользователя в Telegram
            first_name (Optional[str]): Имя пользователя
            last_name (Optional[str]): Фамилия пользователя
        
        Returns:
            User: Пользователь
        """
        user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user:
            # Обновляем данные пользователя, если они изменились
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            
            # Обновляем время последней активности
            user.last_activity = datetime.utcnow()
            
            if updated:
                logger.info(f"Обновлены данные пользователя: ID={user.id}, telegram_id={telegram_id}")
            
            self.session.commit()
            return user
        
        # Создаем нового пользователя
        is_admin = telegram_id in ADMIN_IDS
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.session.add(user)
        self.session.commit()
        
        logger.info(f"Создан новый пользователь: ID={user.id}, telegram_id={telegram_id}, is_admin={is_admin}")
        return user
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получает пользователя по ID в Telegram
        
        Args:
            telegram_id (int): ID пользователя в Telegram
        
        Returns:
            Optional[User]: Пользователь или None, если пользователь не найден
        """
        return self.session.query(User).filter(User.telegram_id == telegram_id).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по ID
        
        Args:
            user_id (int): ID пользователя
        
        Returns:
            Optional[User]: Пользователь или None, если пользователь не найден
        """
        return self.session.query(User).filter(User.id == user_id).first()
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Обновляет данные пользователя
        
        Args:
            user_id (int): ID пользователя
            data (Dict[str, Any]): Новые данные пользователя
        
        Returns:
            Optional[User]: Обновленный пользователь или None, если пользователь не найден
        """
        user = self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Пользователь с ID={user_id} не найден")
            return None
        
        # Обновляем категории, если они указаны
        if "categories" in data:
            category_names = data["categories"]
            categories = self.session.query(Category).filter(Category.name.in_(category_names)).all()
            user.categories = categories
        
        # Обновляем города, если они указаны
        if "cities" in data:
            city_names = data["cities"]
            cities = self.session.query(City).filter(City.name.in_(city_names)).all()
            user.cities = cities
        
        # Обновляем остальные поля
        for key, value in data.items():
            if key not in ["categories", "cities"] and hasattr(user, key):
                setattr(user, key, value)
        
        user.last_activity = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Обновлены данные пользователя: ID={user.id}, telegram_id={user.telegram_id}")
        return user
    
    def get_all_users(self) -> List[User]:
        """
        Получает список всех пользователей
        
        Returns:
            List[User]: Список пользователей
        """
        return self.session.query(User).all()
    
    def get_active_users(self) -> List[User]:
        """
        Получает список активных пользователей
        
        Returns:
            List[User]: Список активных пользователей
        """
        return self.session.query(User).filter(User.is_active == True).all()
    
    def get_admin_users(self) -> List[User]:
        """
        Получает список администраторов
        
        Returns:
            List[User]: Список администраторов
        """
        return self.session.query(User).filter(User.is_admin == True).all()
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Получает статистику по пользователю
        
        Args:
            user_id (int): ID пользователя
        
        Returns:
            Dict[str, Any]: Статистика по пользователю
        """
        user = self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Пользователь с ID={user_id} не найден")
            return {}
        
        # Количество полученных заявок
        total_distributions = self.session.query(func.count(Distribution.id)).filter(
            Distribution.user_id == user_id
        ).scalar()
        
        # Статистика по статусам распределений
        status_stats = {}
        for status in ["отправлено", "просмотрено", "принято", "отклонено"]:
            count = self.session.query(func.count(Distribution.id)).filter(
                Distribution.user_id == user_id,
                Distribution.status == status
            ).scalar()
            status_stats[status] = count
        
        return {
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_activity": user.last_activity.strftime("%Y-%m-%d %H:%M:%S"),
            "total_distributions": total_distributions,
            "status_stats": status_stats,
            "categories": [category.name for category in user.categories],
            "cities": [city.name for city in user.cities]
        } 