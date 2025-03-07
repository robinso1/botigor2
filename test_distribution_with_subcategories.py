"""
Скрипт для тестирования распределения заявок с учетом подкатегорий
"""
import logging
import sys
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from bot.database.setup import setup_database, get_session
from bot.models import User, Category, City, Request, Distribution, SubCategory
from bot.services.distribution_service import DistributionService
from config import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

def test_distribution_with_subcategories():
    """Тестирование распределения заявок с учетом подкатегорий"""
    try:
        # Настраиваем базу данных
        setup_database()
        
        # Получаем сессию
        with get_session() as session:
            # Создаем тестовую заявку с подкатегориями
            logger.info("Создание тестовой заявки с подкатегориями...")
            
            # Получаем категорию "Ремонт квартир"
            category = session.query(Category).filter(
                Category.name == "Ремонт квартир",
                Category.is_active == True
            ).first()
            
            if not category:
                logger.error("Категория 'Ремонт квартир' не найдена")
                return False
            
            # Получаем город "Москва"
            city = session.query(City).filter(
                City.name == "Москва",
                City.is_active == True
            ).first()
            
            if not city:
                logger.error("Город 'Москва' не найден")
                return False
            
            # Получаем подкатегории для категории "Ремонт квартир"
            subcategories = session.query(SubCategory).filter(
                SubCategory.category_id == category.id,
                SubCategory.is_active == True
            ).all()
            
            if not subcategories:
                logger.error("Подкатегории для категории 'Ремонт квартир' не найдены")
                return False
            
            # Создаем тестовую заявку
            request = Request(
                title="Тестовая заявка с подкатегориями",
                description="Тестовая заявка для проверки распределения с учетом подкатегорий",
                category_id=category.id,
                city_id=city.id,
                contact_name="Тестовый клиент",
                contact_phone="+79991234567",
                status="новая",
                created_at=datetime.now(),
                area_value=75.5,  # Площадь помещения
                house_type="Кирпичный",  # Тип дома
                has_design_project=True  # Наличие дизайн-проекта
            )
            
            # Добавляем подкатегории к заявке
            for subcategory in subcategories[:2]:  # Добавляем первые две подкатегории
                request.subcategories.append(subcategory)
            
            session.add(request)
            session.commit()
            
            logger.info(f"Создана тестовая заявка #{request.id} с подкатегориями")
            
            # Распределяем заявку
            logger.info("Распределение заявки...")
            distribution_service = DistributionService(session)
            distributions = distribution_service.distribute_request(request)
            
            if not distributions:
                logger.warning("Заявка не была распределена. Возможно, нет подходящих пользователей.")
                return False
            
            # Выводим информацию о распределениях
            logger.info(f"Заявка #{request.id} была распределена {len(distributions)} пользователям:")
            
            for i, distribution in enumerate(distributions, 1):
                user = distribution.user
                logger.info(f"{i}. Пользователь: {user.first_name} {user.last_name} (ID: {user.id})")
                
                # Выводим категории пользователя
                categories = [c.name for c in user.categories]
                logger.info(f"   Категории: {', '.join(categories)}")
                
                # Выводим города пользователя
                cities = [c.name for c in user.cities]
                logger.info(f"   Города: {', '.join(cities)}")
                
                # Выводим подкатегории пользователя
                subcategories = [f"{sc.name} ({sc.category.name})" for sc in user.subcategories]
                logger.info(f"   Подкатегории: {', '.join(subcategories) if subcategories else 'Нет'}")
            
            logger.info("Тестирование распределения заявок с учетом подкатегорий завершено успешно")
            return True
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при тестировании распределения заявок: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск скрипта тестирования распределения заявок с учетом подкатегорий")
    
    if test_distribution_with_subcategories():
        logger.info("Скрипт успешно выполнен")
        sys.exit(0)
    else:
        logger.error("Ошибка при выполнении скрипта")
        sys.exit(1) 