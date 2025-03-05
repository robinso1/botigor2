"""
Скрипт для очистки старых демо-заявок
Может запускаться по расписанию через cron или другой планировщик
"""
import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy import and_
from bot.models import get_session, Request

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("cleanup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_old_demo_requests(days=7):
    """
    Удаляет старые демо-заявки, которые старше указанного количества дней
    
    Args:
        days (int): Количество дней, после которых заявка считается устаревшей
    
    Returns:
        int: Количество удаленных заявок
    """
    try:
        session = get_session()
        expiration_time = datetime.utcnow() - timedelta(days=days)
        
        # Находим старые демо-заявки
        old_demos = session.query(Request).filter(
            and_(
                Request.is_demo == True,
                Request.created_at < expiration_time
            )
        ).all()
        
        if not old_demos:
            logger.info("Нет старых демо-заявок для удаления")
            return 0
            
        # Удаляем найденные заявки
        count = len(old_demos)
        for demo in old_demos:
            logger.debug(f"Удаление демо-заявки ID={demo.id}, создана {demo.created_at}")
            session.delete(demo)
        
        session.commit()
        logger.info(f"Удалено {count} старых демо-заявок (старше {days} дней)")
        return count
        
    except Exception as e:
        logger.error(f"Ошибка при очистке старых демо-заявок: {e}")
        if 'session' in locals():
            session.rollback()
        return 0
    finally:
        if 'session' in locals():
            session.close()

def main():
    """Основная функция скрипта"""
    logger.info("=" * 50)
    logger.info(f"Запуск очистки демо-заявок в {datetime.now()}")
    
    # Получаем количество дней из аргументов командной строки или используем значение по умолчанию
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            logger.error(f"Некорректное значение дней: {sys.argv[1]}")
            return 1
    
    # Запускаем очистку
    count = cleanup_old_demo_requests(days)
    
    logger.info(f"Очистка завершена. Удалено {count} заявок.")
    logger.info("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 