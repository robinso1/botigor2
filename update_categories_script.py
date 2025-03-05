from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем модели после добавления пути
from bot.models.models import Category, Base

def update_categories():
    try:
        # Создаем подключение к базе данных
        engine = create_engine('sqlite:///bot.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Подключение к базе данных установлено")
        
        # Удаляем существующие категории
        print("Удаление существующих категорий...")
        session.query(Category).delete()
        
        # Добавляем новые категории
        print("Добавление новых категорий...")
        categories = [
            Category(id=1, name="Ремонт квартир", description="Ремонт и отделка квартир", is_active=True, parent_id=None),
            Category(id=2, name="Сантехника", description="Сантехнические работы", is_active=True, parent_id=None),
            Category(id=3, name="Электрика", description="Электромонтажные работы", is_active=True, parent_id=None),
            Category(id=4, name="Клининг", description="Уборка помещений", is_active=True, parent_id=None),
            Category(id=5, name="Грузоперевозки", description="Перевозка грузов", is_active=True, parent_id=None),
            Category(id=6, name="Строительство", description="Строительные работы", is_active=True, parent_id=None),
            Category(id=7, name="Другое", description="Прочие услуги", is_active=True, parent_id=None),
        ]
        
        session.add_all(categories)
        session.commit()
        print(f"Добавлено {len(categories)} категорий")
        
        # Проверяем, что категории добавлены
        count = session.query(Category).count()
        print(f"Всего категорий в базе: {count}")
        
        return True
    except Exception as e:
        print(f"Ошибка при обновлении категорий: {e}")
        return False
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    print("Запуск обновления категорий...")
    success = update_categories()
    if success:
        print("Категории успешно обновлены!")
    else:
        print("Не удалось обновить категории.") 