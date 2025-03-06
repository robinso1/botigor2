"""
Сервис для отправки информационных сообщений
"""
import logging
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from aiogram import Bot
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.setup import async_session
from bot.models import User, Distribution, Request
from bot.utils.demo_generator import get_demo_info_message, schedule_demo_info_message
from config import DEMO_MODE

logger = logging.getLogger(__name__)

async def send_info_messages(bot: Bot) -> None:
    """
    Отправляет информационные сообщения пользователям
    
    Args:
        bot: Экземпляр бота
    """
    if not DEMO_MODE:
        logger.debug("Демо-режим отключен, информационные сообщения не отправляются")
        return
        
    try:
        logger.info("Запуск отправки информационных сообщений")
        
        async with async_session() as session:
            # Получаем пользователей, которые взаимодействовали с ботом
            result = await session.execute(
                select(User)
                .where(User.is_active == True)
                .order_by(func.random())
                .limit(5)  # Ограничиваем количество пользователей для одной рассылки
            )
            users = result.scalars().all()
            
            if not users:
                logger.info("Нет активных пользователей для отправки информационных сообщений")
                return
                
            logger.info(f"Найдено {len(users)} пользователей для отправки информационных сообщений")
            
            # Получаем случайное информационное сообщение
            info_message = schedule_demo_info_message()
            
            # Отправляем сообщение каждому пользователю
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=info_message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Отправлено информационное сообщение пользователю {user.telegram_id}")
                    
                    # Делаем паузу между отправками, чтобы не превысить лимиты Telegram
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Ошибка при отправке информационного сообщения пользователю {user.telegram_id}: {e}")
                    
        logger.info("Отправка информационных сообщений завершена")
    except Exception as e:
        logger.error(f"Ошибка при отправке информационных сообщений: {e}")

async def schedule_info_messages(bot: Bot) -> None:
    """
    Планирует периодическую отправку информационных сообщений
    
    Args:
        bot: Экземпляр бота
    """
    if not DEMO_MODE:
        logger.debug("Демо-режим отключен, планирование информационных сообщений не выполняется")
        return
        
    try:
        logger.info("Запуск планировщика информационных сообщений")
        
        while True:
            # Отправляем информационные сообщения
            await send_info_messages(bot)
            
            # Ждем случайное время (от 6 до 12 часов)
            interval_seconds = random.randint(6 * 3600, 12 * 3600)
            logger.info(f"Следующая отправка информационных сообщений через {interval_seconds // 3600} часов")
            
            await asyncio.sleep(interval_seconds)
    except Exception as e:
        logger.error(f"Ошибка в планировщике информационных сообщений: {e}")

async def start_info_service(bot: Bot) -> None:
    """
    Запускает сервис отправки информационных сообщений
    
    Args:
        bot: Экземпляр бота
    """
    if not DEMO_MODE:
        logger.debug("Демо-режим отключен, сервис информационных сообщений не запускается")
        return
        
    try:
        # Запускаем планировщик в отдельной задаче
        asyncio.create_task(schedule_info_messages(bot))
        logger.info("Сервис информационных сообщений запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске сервиса информационных сообщений: {e}") 