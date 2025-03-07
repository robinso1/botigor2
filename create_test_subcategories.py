"""
Скрипт для создания тестовых подкатегорий
"""
import logging
import sys
from sqlalchemy.exc import SQLAlchemyError

from bot.database.setup import setup_database, get_session
from bot.models import Category, SubCategory
from config import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

def create_test_subcategories():
    """Создание тестовых подкатегорий"""
    try:
        # Настраиваем базу данных
        setup_database()
        
        # Получаем сессию
        with get_session() as session:
            # Получаем все категории
            categories = session.query(Category).all()
            
            if not categories:
                logger.error("Категории не найдены. Сначала создайте категории.")
                return
            
            # Словарь с подкатегориями для каждой категории
            subcategories_by_category = {
                "Ремонт квартир": [
                    {
                        "name": "Тип дома",
                        "description": "Тип дома, в котором выполняется ремонт",
                        "type": "select",
                        "options": ["Панельный", "Кирпичный", "Монолитный", "Деревянный"]
                    },
                    {
                        "name": "Площадь помещения",
                        "description": "Площадь помещения в квадратных метрах",
                        "type": "number",
                        "min_value": 10,
                        "max_value": 500
                    },
                    {
                        "name": "Наличие дизайн-проекта",
                        "description": "Есть ли готовый дизайн-проект",
                        "type": "boolean"
                    },
                    {
                        "name": "Тип ремонта",
                        "description": "Тип выполняемого ремонта",
                        "type": "select",
                        "options": ["Косметический", "Капитальный", "Евроремонт", "Дизайнерский"]
                    }
                ],
                "Сантехнические работы": [
                    {
                        "name": "Тип сантехники",
                        "description": "Тип сантехники для установки/ремонта",
                        "type": "select",
                        "options": ["Ванна", "Душевая кабина", "Унитаз", "Раковина", "Смеситель", "Полотенцесушитель"]
                    },
                    {
                        "name": "Замена труб",
                        "description": "Требуется ли замена труб",
                        "type": "boolean"
                    }
                ],
                "Электромонтажные работы": [
                    {
                        "name": "Тип электромонтажных работ",
                        "description": "Тип выполняемых электромонтажных работ",
                        "type": "select",
                        "options": ["Проводка", "Розетки/выключатели", "Освещение", "Электрощит"]
                    },
                    {
                        "name": "Количество точек",
                        "description": "Количество точек подключения",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 100
                    }
                ],
                "Отделочные работы": [
                    {
                        "name": "Тип отделки",
                        "description": "Тип выполняемых отделочных работ",
                        "type": "select",
                        "options": ["Штукатурка", "Шпаклевка", "Покраска", "Обои", "Плитка", "Ламинат", "Паркет"]
                    },
                    {
                        "name": "Площадь отделки",
                        "description": "Площадь отделки в квадратных метрах",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 500
                    }
                ],
                "Установка дверей": [
                    {
                        "name": "Тип дверей",
                        "description": "Тип устанавливаемых дверей",
                        "type": "select",
                        "options": ["Межкомнатные", "Входные", "Раздвижные", "Складные"]
                    },
                    {
                        "name": "Количество дверей",
                        "description": "Количество устанавливаемых дверей",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 20
                    }
                ],
                "Установка окон": [
                    {
                        "name": "Тип окон",
                        "description": "Тип устанавливаемых окон",
                        "type": "select",
                        "options": ["ПВХ", "Деревянные", "Алюминиевые", "Мансардные"]
                    },
                    {
                        "name": "Количество окон",
                        "description": "Количество устанавливаемых окон",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 20
                    }
                ],
                "Натяжные потолки": [
                    {
                        "name": "Тип потолка",
                        "description": "Тип натяжного потолка",
                        "type": "select",
                        "options": ["Матовый", "Глянцевый", "Сатиновый", "Тканевый", "Многоуровневый"]
                    },
                    {
                        "name": "Площадь потолка",
                        "description": "Площадь потолка в квадратных метрах",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 200
                    }
                ],
                "Укладка плитки": [
                    {
                        "name": "Тип помещения",
                        "description": "Тип помещения для укладки плитки",
                        "type": "select",
                        "options": ["Ванная", "Кухня", "Коридор", "Балкон", "Терраса"]
                    },
                    {
                        "name": "Площадь укладки",
                        "description": "Площадь укладки в квадратных метрах",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 200
                    }
                ],
                "Поклейка обоев": [
                    {
                        "name": "Тип обоев",
                        "description": "Тип обоев для поклейки",
                        "type": "select",
                        "options": ["Бумажные", "Виниловые", "Флизелиновые", "Текстильные", "Жидкие"]
                    },
                    {
                        "name": "Площадь поклейки",
                        "description": "Площадь поклейки в квадратных метрах",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 300
                    }
                ],
                "Монтаж гипсокартона": [
                    {
                        "name": "Тип конструкции",
                        "description": "Тип гипсокартонной конструкции",
                        "type": "select",
                        "options": ["Перегородка", "Потолок", "Короб", "Ниша", "Арка"]
                    },
                    {
                        "name": "Площадь монтажа",
                        "description": "Площадь монтажа в квадратных метрах",
                        "type": "number",
                        "min_value": 1,
                        "max_value": 300
                    }
                ]
            }
            
            # Создаем подкатегории для каждой категории
            for category in categories:
                # Проверяем, есть ли подкатегории для данной категории
                if category.name in subcategories_by_category:
                    subcategories_data = subcategories_by_category[category.name]
                    
                    for subcategory_data in subcategories_data:
                        # Проверяем, существует ли уже такая подкатегория
                        existing_subcategory = session.query(SubCategory).filter(
                            SubCategory.name == subcategory_data["name"],
                            SubCategory.category_id == category.id
                        ).first()
                        
                        if existing_subcategory:
                            logger.info(f"Подкатегория '{subcategory_data['name']}' для категории '{category.name}' уже существует")
                            continue
                        
                        # Создаем новую подкатегорию
                        subcategory = SubCategory(
                            name=subcategory_data["name"],
                            description=subcategory_data["description"],
                            category_id=category.id,
                            type=subcategory_data["type"],
                            min_value=subcategory_data.get("min_value"),
                            max_value=subcategory_data.get("max_value"),
                            is_active=True
                        )
                        
                        session.add(subcategory)
                        logger.info(f"Создана подкатегория '{subcategory_data['name']}' для категории '{category.name}'")
            
            # Сохраняем изменения
            session.commit()
            logger.info("Тестовые подкатегории успешно созданы")
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при создании тестовых подкатегорий: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Запуск скрипта создания тестовых подкатегорий")
    
    if create_test_subcategories():
        logger.info("Скрипт успешно выполнен")
        sys.exit(0)
    else:
        logger.error("Ошибка при выполнении скрипта")
        sys.exit(1) 