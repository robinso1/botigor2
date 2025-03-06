from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table, Text, JSON, create_engine, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, backref
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
import enum

from config import DATABASE_URL, REQUEST_STATUSES

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

# Связующая таблица для отношения многие-ко-многим между заявками и пакетами услуг
request_package = Table(
    'request_package',
    Base.metadata,
    Column('request_id', Integer, ForeignKey('requests.id'), primary_key=True),
    Column('package_id', Integer, ForeignKey('service_packages.id'), primary_key=True)
)

class RequestStatus(enum.Enum):
    """Статусы заявок"""
    NEW = "новая"
    ACTUAL = "актуальная"
    NOT_ACTUAL = "неактуальная"
    IN_PROGRESS = "в работе"
    MEASUREMENT = "замер"
    CLIENT_REJECTED = "отказ клиента"
    COMPLETED = "завершена"
    PENDING = "ожидание подтверждения"
    DISTRIBUTING = "распределение"
    CANCELLED = "отменена"
    EXPIRED = "просрочена"

class DistributionStatus(enum.Enum):
    """Статусы распределений заявок"""
    PENDING = "ожидание"
    ACCEPTED = "принято"
    REJECTED = "отклонено"
    COMPLETED = "завершено"
    EXPIRED = "просрочено"

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
    rating = Column(Float, default=0.0)  # Рейтинг пользователя
    
    # Отношения
    categories = relationship("Category", secondary=user_category, back_populates="users")
    cities = relationship("City", secondary=user_city, back_populates="users")
    distributions = relationship("Distribution", back_populates="user")
    statistics = relationship("UserStatistics", back_populates="user", uselist=False)
    subcategories = relationship("SubCategory", secondary="user_subcategory", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class Category(Base):
    """Модель категории заявок"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    # Отношения
    users = relationship("User", secondary=user_category, back_populates="categories")
    requests = relationship("Request", back_populates="category")
    subcategories = relationship("SubCategory", back_populates="category")
    
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

class ServicePackage(Base):
    """Модель пакета услуг"""
    __tablename__ = 'service_packages'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    services = Column(JSON, nullable=False)  # Список ID категорий услуг в пакете
    
    # Отношения
    requests = relationship("Request", secondary=request_package, back_populates="packages")
    
    def __repr__(self):
        return f"<ServicePackage(id={self.id}, name={self.name})>"

class Request(Base):
    """Модель заявки"""
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    source_chat_id = Column(Integer, nullable=True)  # ID чата, откуда пришла заявка
    source_message_id = Column(Integer, nullable=True)  # ID сообщения в чате
    client_name = Column(String(100), nullable=True)
    client_phone = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)
    area = Column(Float, nullable=True)  # Площадь помещения
    address = Column(String(255), nullable=True)
    is_demo = Column(Boolean, default=False)  # Флаг демо-заявки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estimated_cost = Column(Float, nullable=True)  # Предполагаемая стоимость
    crm_id = Column(String(100), nullable=True)  # ID в CRM-системе
    crm_status = Column(String(50), nullable=True)  # Статус в CRM-системе
    
    # Внешние ключи
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)
    
    # Отношения
    category = relationship("Category", back_populates="requests")
    city = relationship("City", back_populates="requests")
    distributions = relationship("Distribution", back_populates="request")
    packages = relationship("ServicePackage", secondary=request_package, back_populates="requests")
    subcategories = relationship("SubCategory", secondary="request_subcategory")
    
    # Дополнительные данные в формате JSON
    extra_data = Column(JSON, nullable=True)
    
    # Добавляем поля для подкатегорий
    area_value = Column(Float, nullable=True)  # Значение площади
    house_type = Column(String(50), nullable=True)  # Тип дома
    has_design_project = Column(Boolean, default=False)  # Наличие дизайн-проекта
    
    def __repr__(self):
        return f"<Request(id={self.id}, client_name={self.client_name}, status={self.status})>"

class Distribution(Base):
    """Модель распределения заявки пользователю"""
    __tablename__ = 'distributions'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    telegram_message_id = Column(Integer, nullable=True)  # ID сообщения, отправленного пользователю
    status = Column(Enum(DistributionStatus), default=DistributionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    response_time = Column(Integer, nullable=True)  # Время ответа в секундах
    is_converted = Column(Boolean, default=False)  # Флаг успешной конверсии
    expires_at = Column(DateTime, nullable=True)  # Время истечения срока действия распределения
    
    # Отношения
    request = relationship("Request", back_populates="distributions")
    user = relationship("User", back_populates="distributions")
    
    def __repr__(self):
        return f"<Distribution(id={self.id}, request_id={self.request_id}, user_id={self.user_id}, status={self.status})>"

class UserStatistics(Base):
    """Модель статистики пользователя"""
    __tablename__ = 'user_statistics'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    total_requests = Column(Integer, default=0)  # Всего полученных заявок
    processed_requests = Column(Integer, default=0)  # Обработанных заявок
    successful_requests = Column(Integer, default=0)  # Успешно завершенных заявок
    avg_response_time = Column(Float, default=0.0)  # Среднее время ответа в секундах
    conversion_rate = Column(Float, default=0.0)  # Процент успешных конверсий
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="statistics")
    
    def __repr__(self):
        return f"<UserStatistics(user_id={self.user_id}, total_requests={self.total_requests})>"

class Setting(Base):
    """Модель настроек бота"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"

class SubCategory(Base):
    """Модель подкатегории для дополнительных критериев"""
    __tablename__ = 'subcategories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    type = Column(String(50), nullable=False)  # Тип подкатегории: area, house_type, design_project, etc.
    min_value = Column(Float, nullable=True)  # Минимальное значение (для числовых критериев)
    max_value = Column(Float, nullable=True)  # Максимальное значение (для числовых критериев)
    is_active = Column(Boolean, default=True)
    
    # Отношения
    category = relationship("Category", back_populates="subcategories")
    users = relationship("User", secondary="user_subcategory", back_populates="subcategories")
    
    def __repr__(self):
        return f"<SubCategory(id={self.id}, name='{self.name}', type='{self.type}')>"

# Таблица связи пользователей и подкатегорий
user_subcategory = Table(
    'user_subcategory',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('subcategory_id', Integer, ForeignKey('subcategories.id'), primary_key=True)
)

# Таблица связи заявок и подкатегорий
request_subcategory = Table(
    'request_subcategory',
    Base.metadata,
    Column('request_id', Integer, ForeignKey('requests.id'), primary_key=True),
    Column('subcategory_id', Integer, ForeignKey('subcategories.id'), primary_key=True)
)

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