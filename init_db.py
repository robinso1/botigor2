import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.append(str(root_dir))

from app.models import Base, get_db, Category, City
from app.models.base import engine

def init_database():
    """Инициализация базы данных"""
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Получаем сессию
    db = next(get_db())
    
    try:
        # Добавляем базовые категории
        categories = [
            Category(name="Ремонт квартир", description="Полный ремонт квартир под ключ"),
            Category(name="Косметический ремонт", description="Поверхностный ремонт помещений"),
            Category(name="Ремонт ванной", description="Ремонт ванных комнат"),
            Category(name="Электрика", description="Электромонтажные работы"),
            Category(name="Сантехника", description="Сантехнические работы")
        ]
        
        # Добавляем города
        cities = [
            City(name="Москва", phone_prefix="495"),
            City(name="Санкт-Петербург", phone_prefix="812"),
            City(name="Екатеринбург", phone_prefix="343"),
            City(name="Новосибирск", phone_prefix="383"),
            City(name="Казань", phone_prefix="843")
        ]
        
        # Проверяем, существуют ли уже категории
        existing_categories = db.query(Category).all()
        if not existing_categories:
            db.add_all(categories)
        
        # Проверяем, существуют ли уже города
        existing_cities = db.query(City).all()
        if not existing_cities:
            db.add_all(cities)
        
        db.commit()
        print("База данных успешно инициализирована")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 