from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

from config import DATABASE_URL

# Создание базового класса для моделей
Base = declarative_base()

# Связующая таблица для отношения многие-ко-многим между пользователями и категориями
user_category = Table(
    'user_category',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

# Связующая таблица для отношения многие-ко-многим между пользователями и городами
user_city = Table(
    'user_city',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('city_id', Integer, ForeignKey('cities.id'), primary_key=True)
)

class User(Base):
    """Модель пользователя бота"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    categories = relationship("Category", secondary=user_category, back_populates="users")
    cities = relationship("City", secondary=user_city, back_populates="users")
    distributions = relationship("Distribution", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class Category(Base):
    """Модель категории заявок"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Отношения
    users = relationship("User", secondary=user_category, back_populates="categories")
    requests = relationship("Request", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"

class City(Base):
    """Модель города"""
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    phone_prefixes = Column(String(255), nullable=True)  # Хранится как JSON-строка
    is_active = Column(Boolean, default=True)
    
    # Отношения
    users = relationship("User", secondary=user_city, back_populates="cities")
    requests = relationship("Request", back_populates="city")
    
    def get_phone_prefixes(self) -> List[str]:
        """Получить список префиксов телефонов для города"""
        if not self.phone_prefixes:
            return []
        try:
            return json.loads(self.phone_prefixes)
        except json.JSONDecodeError:
            return []
    
    def set_phone_prefixes(self, prefixes: List[str]) -> None:
        """Установить список префиксов телефонов для города"""
        self.phone_prefixes = json.dumps(prefixes)
    
    def __repr__(self):
        return f"<City(id={self.id}, name={self.name})>"

class Request(Base):
    """Модель заявки"""
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    source_chat_id = Column(Integer, nullable=True)  # ID чата, откуда пришла заявка
    source_message_id = Column(Integer, nullable=True)  # ID сообщения в чате
    client_name = Column(String(100), nullable=True)
    client_phone = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="новая")
    area = Column(Float, nullable=True)  # Площадь помещения
    address = Column(String(255), nullable=True)
    is_demo = Column(Boolean, default=False)  # Флаг демо-заявки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)
    
    # Отношения
    category = relationship("Category", back_populates="requests")
    city = relationship("City", back_populates="requests")
    distributions = relationship("Distribution", back_populates="request")
    
    # Дополнительные данные в формате JSON
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Request(id={self.id}, client_name={self.client_name}, status={self.status})>"

class Distribution(Base):
    """Модель распределения заявки пользователю"""
    __tablename__ = 'distributions'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    telegram_message_id = Column(Integer, nullable=True)  # ID сообщения, отправленного пользователю
    status = Column(String(50), default="отправлено")  # отправлено, просмотрено, принято, отклонено
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    request = relationship("Request", back_populates="distributions")
    user = relationship("User", back_populates="distributions")
    
    def __repr__(self):
        return f"<Distribution(id={self.id}, request_id={self.request_id}, user_id={self.user_id}, status={self.status})>"

class Setting(Base):
    """Модель настроек бота"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"

# Функция для создания и инициализации базы данных
def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

# Функция для создания сессии базы данных
def get_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session() 