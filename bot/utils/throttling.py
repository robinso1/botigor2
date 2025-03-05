"""
Модуль для ограничения частоты запросов (throttling)
"""
import asyncio
from typing import Dict, Any, Optional, Union, Callable, Awaitable
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class Throttler:
    """
    Класс для ограничения частоты запросов
    """
    def __init__(self, rate_limit: float = 0.5, key_prefix: str = "throttling"):
        """
        Инициализирует объект Throttler
        
        Args:
            rate_limit: Минимальный интервал между запросами в секундах
            key_prefix: Префикс для ключей в хранилище
        """
        self.rate_limit = rate_limit
        self.prefix = key_prefix
        self.last_call = defaultdict(float)
        self.lock = asyncio.Lock()
        
        logger.debug(f"Инициализирован Throttler с rate_limit={rate_limit}")
    
    async def throttle(self, key: Union[str, int]) -> Optional[float]:
        """
        Проверяет, нужно ли ограничить запрос
        
        Args:
            key: Ключ для идентификации пользователя или чата
            
        Returns:
            Optional[float]: Время ожидания в секундах, если запрос нужно ограничить, иначе None
        """
        async with self.lock:
            throttling_key = f"{self.prefix}_{key}"
            now = time.time()
            
            # Получаем время последнего запроса
            last_time = self.last_call[throttling_key]
            
            # Вычисляем, сколько времени прошло с последнего запроса
            delta = now - last_time
            
            # Если прошло меньше времени, чем rate_limit, то ограничиваем запрос
            if delta < self.rate_limit:
                wait_time = self.rate_limit - delta
                logger.debug(f"Throttling для ключа {key}: ожидание {wait_time:.2f} сек")
                return wait_time
            
            # Обновляем время последнего запроса
            self.last_call[throttling_key] = now
            return None
    
    async def throttle_and_wait(self, key: Union[str, int]) -> None:
        """
        Проверяет и при необходимости ожидает, чтобы соблюсти ограничение частоты
        
        Args:
            key: Ключ для идентификации пользователя или чата
        """
        wait_time = await self.throttle(key)
        if wait_time is not None:
            logger.debug(f"Ожидание {wait_time:.2f} сек для ключа {key}")
            await asyncio.sleep(wait_time)
            # Обновляем время последнего запроса после ожидания
            async with self.lock:
                self.last_call[f"{self.prefix}_{key}"] = time.time()

# Создаем глобальный экземпляр Throttler
default_throttler = Throttler()

async def throttle(key: Union[str, int], rate_limit: Optional[float] = None) -> Optional[float]:
    """
    Глобальная функция для проверки ограничения частоты запросов
    
    Args:
        key: Ключ для идентификации пользователя или чата
        rate_limit: Опциональное переопределение ограничения частоты
        
    Returns:
        Optional[float]: Время ожидания в секундах, если запрос нужно ограничить, иначе None
    """
    if rate_limit is not None and rate_limit != default_throttler.rate_limit:
        throttler = Throttler(rate_limit=rate_limit)
        return await throttler.throttle(key)
    return await default_throttler.throttle(key)

async def throttle_and_wait(key: Union[str, int], rate_limit: Optional[float] = None) -> None:
    """
    Глобальная функция для проверки и ожидания ограничения частоты запросов
    
    Args:
        key: Ключ для идентификации пользователя или чата
        rate_limit: Опциональное переопределение ограничения частоты
    """
    if rate_limit is not None and rate_limit != default_throttler.rate_limit:
        throttler = Throttler(rate_limit=rate_limit)
        await throttler.throttle_and_wait(key)
    else:
        await default_throttler.throttle_and_wait(key) 