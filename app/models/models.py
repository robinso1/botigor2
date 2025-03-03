from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

# Enum для статусов заявок
class RequestStatus(enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    MEASUREMENT = "measurement"
    CLIENT_REJECTED = "client_rejected"
    COMPLETED = "completed"
    INACTIVE = "inactive"

# Таблица связи между пользователями и категориями
user_categories = Table(
    'user_categories',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

# Таблица связи между пользователями и городами
user_cities = Table(
    'user_cities',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('city_id', Integer, ForeignKey('cities.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    categories = relationship("Category", secondary=user_categories, back_populates="users")
    cities = relationship("City", secondary=user_cities, back_populates="users")
    received_requests = relationship("Request", back_populates="assigned_users")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Связи
    users = relationship("User", secondary=user_categories, back_populates="categories")
    requests = relationship("Request", back_populates="category")

class City(Base):
    __tablename__ = 'cities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone_prefix = Column(String)  # Для демо-режима
    
    # Связи
    users = relationship("User", secondary=user_cities, back_populates="cities")
    requests = relationship("Request", back_populates="city")

class Request(Base):
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True)
    source_chat_id = Column(Integer)  # ID чата, откуда пришла заявка
    client_name = Column(String)
    client_phone = Column(String)
    description = Column(String)
    area = Column(String)  # Площадь помещения
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_demo = Column(Boolean, default=False)
    send_count = Column(Integer, default=0)  # Сколько раз заявка была отправлена
    
    # Внешние ключи
    category_id = Column(Integer, ForeignKey('categories.id'))
    city_id = Column(Integer, ForeignKey('cities.id'))
    
    # Связи
    category = relationship("Category", back_populates="requests")
    city = relationship("City", back_populates="requests")
    assigned_users = relationship("User", secondary="request_assignments", back_populates="received_requests")

# Таблица для отслеживания назначений заявок пользователям
class RequestAssignment(Base):
    __tablename__ = 'request_assignments'
    
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)
    
    # Связи
    request = relationship("Request")
    user = relationship("User") 