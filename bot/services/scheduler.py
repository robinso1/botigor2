"""
Модуль для планировщика задач.
"""
import logging
import asyncio
from datetime import datetime, timedelta

from bot.services.demo_service import generate_demo_requests
from bot.services.distribution_service import process_distributions
from bot.services.cleanup_service import cleanup_old_requests, cleanup_old_distributions
from config import DEMO_MODE, DEBUG_MODE

# Словарь для хранения задач
tasks = {}

async def start_scheduler():
    """
    Запускает планировщик задач.
    """
    logging.info("Запуск планировщика задач...")
    
    # Запускаем задачи
    if DEMO_MODE:
        tasks["demo_generator"] = asyncio.create_task(
            schedule_task(
                generate_demo_requests,
                interval=300 if DEBUG_MODE else 3600,  # 5 минут в режиме отладки, 1 час в обычном режиме
                name="Генератор демо-заявок"
            )
        )
    
    tasks["distribution_processor"] = asyncio.create_task(
        schedule_task(
            process_distributions,
            interval=60 if DEBUG_MODE else 300,  # 1 минута в режиме отладки, 5 минут в обычном режиме
            name="Обработчик распределений"
        )
    )
    
    tasks["cleanup_old_requests"] = asyncio.create_task(
        schedule_task(
            cleanup_old_requests,
            interval=3600 if DEBUG_MODE else 86400,  # 1 час в режиме отладки, 1 день в обычном режиме
            name="Очистка старых заявок"
        )
    )
    
    tasks["cleanup_old_distributions"] = asyncio.create_task(
        schedule_task(
            cleanup_old_distributions,
            interval=3600 if DEBUG_MODE else 86400,  # 1 час в режиме отладки, 1 день в обычном режиме
            name="Очистка старых распределений"
        )
    )
    
    logging.info(f"Запущено {len(tasks)} задач")

async def schedule_task(task_func, interval, name="Задача"):
    """
    Планирует выполнение задачи с заданным интервалом.
    
    Args:
        task_func: Функция задачи
        interval: Интервал выполнения в секундах
        name: Название задачи
    """
    logging.info(f"Запуск задачи '{name}' с интервалом {interval} секунд")
    
    while True:
        start_time = datetime.now()
        try:
            logging.debug(f"Выполнение задачи '{name}'")
            await task_func()
            logging.debug(f"Задача '{name}' выполнена успешно")
        except Exception as e:
            logging.error(f"Ошибка при выполнении задачи '{name}': {e}")
        
        # Вычисляем время до следующего запуска
        execution_time = (datetime.now() - start_time).total_seconds()
        sleep_time = max(0, interval - execution_time)
        
        if sleep_time > 0:
            logging.debug(f"Задача '{name}' будет выполнена снова через {sleep_time:.1f} секунд")
            await asyncio.sleep(sleep_time)
        else:
            logging.warning(f"Задача '{name}' выполнялась дольше интервала ({execution_time:.1f} > {interval} секунд)")
            await asyncio.sleep(1)  # Небольшая пауза, чтобы избежать перегрузки CPU

async def stop_scheduler():
    """
    Останавливает планировщик задач.
    """
    logging.info("Остановка планировщика задач...")
    
    for name, task in tasks.items():
        if not task.done():
            task.cancel()
            logging.info(f"Задача '{name}' остановлена")
    
    tasks.clear()
    logging.info("Планировщик задач остановлен") 