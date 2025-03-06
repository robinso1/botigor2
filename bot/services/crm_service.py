"""
Сервис для интеграции с CRM-системами
"""
import logging
import json
import xml.etree.ElementTree as ET
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from bot.models import Request, User, Category, City
from bot.utils.encryption import decrypt_personal_data
from config import CRM_SETTINGS

logger = logging.getLogger(__name__)

class CRMIntegration:
    """Базовый класс для интеграции с CRM-системами"""
    
    def __init__(self, api_key: str, base_url: str):
        """
        Инициализирует интеграцию с CRM-системой
        
        Args:
            api_key: API-ключ для доступа к CRM
            base_url: Базовый URL для API CRM
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def format_data_json(self, data: Dict[str, Any]) -> str:
        """
        Форматирует данные в JSON
        
        Args:
            data: Данные для форматирования
            
        Returns:
            str: Отформатированные данные в формате JSON
        """
        return json.dumps(data, ensure_ascii=False)
    
    def format_data_xml(self, data: Dict[str, Any]) -> str:
        """
        Форматирует данные в XML
        
        Args:
            data: Данные для форматирования
            
        Returns:
            str: Отформатированные данные в формате XML
        """
        root = ET.Element("request")
        
        def dict_to_xml(parent: ET.Element, data: Dict[str, Any]):
            for key, value in data.items():
                if isinstance(value, dict):
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, value)
                elif isinstance(value, list):
                    for item in value:
                        child = ET.SubElement(parent, key)
                        if isinstance(item, dict):
                            dict_to_xml(child, item)
                        else:
                            child.text = str(item)
                else:
                    child = ET.SubElement(parent, key)
                    child.text = str(value)
        
        dict_to_xml(root, data)
        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    
    async def send_data(self, data: Dict[str, Any], endpoint: str, format_type: str = "json") -> Optional[Dict[str, Any]]:
        """
        Отправляет данные в CRM
        
        Args:
            data: Данные для отправки
            endpoint: Конечная точка API
            format_type: Формат данных (json или xml)
            
        Returns:
            Optional[Dict[str, Any]]: Ответ от CRM или None в случае ошибки
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Форматируем данные
        if format_type == "json":
            formatted_data = self.format_data_json(data)
            headers = self.headers
        elif format_type == "xml":
            formatted_data = self.format_data_xml(data)
            headers = {
                "Content-Type": "application/xml",
                "Authorization": f"Bearer {self.api_key}"
            }
        else:
            logger.error(f"Неподдерживаемый формат данных: {format_type}")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=formatted_data, headers=headers) as response:
                    if response.status == 200:
                        if format_type == "json":
                            return await response.json()
                        else:
                            text = await response.text()
                            # Парсим XML-ответ
                            root = ET.fromstring(text)
                            result = {}
                            for child in root:
                                result[child.tag] = child.text
                            return result
                    else:
                        logger.error(f"Ошибка при отправке данных в CRM: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при отправке данных в CRM: {e}")
            return None

class Bitrix24Integration(CRMIntegration):
    """Интеграция с Битрикс24"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует данные заявки для Битрикс24
        
        Args:
            request_data: Данные заявки
            
        Returns:
            Dict[str, Any]: Отформатированные данные для Битрикс24
        """
        # Расшифровываем персональные данные
        client_name = request_data.get("client_name", "")
        client_phone = request_data.get("client_phone", "")
        
        if not request_data.get("is_demo", False):
            try:
                if client_phone:
                    client_phone = decrypt_personal_data(client_phone)
            except Exception as e:
                logger.error(f"Ошибка при расшифровке телефона: {e}")
        
        # Формируем данные для Битрикс24
        lead_data = {
            "fields": {
                "TITLE": f"Заявка #{request_data.get('id', '')} - {request_data.get('category_name', '')}",
                "NAME": client_name,
                "PHONE": [{"VALUE": client_phone, "VALUE_TYPE": "WORK"}],
                "COMMENTS": request_data.get("description", ""),
                "SOURCE_ID": "BOT",
                "SOURCE_DESCRIPTION": "Telegram Bot",
                "ASSIGNED_BY_ID": 1,  # ID ответственного сотрудника
                "STATUS_ID": "NEW",
                "CURRENCY_ID": "RUB",
                "OPPORTUNITY": request_data.get("estimated_cost", 0),
                "UF_CRM_CITY": request_data.get("city_name", ""),
                "UF_CRM_CATEGORY": request_data.get("category_name", ""),
                "UF_CRM_AREA": request_data.get("area", 0),
                "UF_CRM_ADDRESS": request_data.get("address", ""),
                "UF_CRM_IS_DEMO": request_data.get("is_demo", False)
            },
            "params": {
                "REGISTER_SONET_EVENT": "Y"
            }
        }
        
        return lead_data

class AmoCRMIntegration(CRMIntegration):
    """Интеграция с AmoCRM"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует данные заявки для AmoCRM
        
        Args:
            request_data: Данные заявки
            
        Returns:
            Dict[str, Any]: Отформатированные данные для AmoCRM
        """
        # Расшифровываем персональные данные
        client_name = request_data.get("client_name", "")
        client_phone = request_data.get("client_phone", "")
        
        if not request_data.get("is_demo", False):
            try:
                if client_phone:
                    client_phone = decrypt_personal_data(client_phone)
            except Exception as e:
                logger.error(f"Ошибка при расшифровке телефона: {e}")
        
        # Формируем данные для AmoCRM
        lead_data = {
            "add": [
                {
                    "name": f"Заявка #{request_data.get('id', '')} - {request_data.get('category_name', '')}",
                    "status_id": 1,  # ID статуса "Новая"
                    "price": request_data.get("estimated_cost", 0),
                    "responsible_user_id": 1,  # ID ответственного сотрудника
                    "custom_fields": [
                        {
                            "id": 1,  # ID поля "Телефон"
                            "values": [
                                {
                                    "value": client_phone,
                                    "enum": "WORK"
                                }
                            ]
                        },
                        {
                            "id": 2,  # ID поля "Город"
                            "values": [
                                {
                                    "value": request_data.get("city_name", "")
                                }
                            ]
                        },
                        {
                            "id": 3,  # ID поля "Категория"
                            "values": [
                                {
                                    "value": request_data.get("category_name", "")
                                }
                            ]
                        },
                        {
                            "id": 4,  # ID поля "Площадь"
                            "values": [
                                {
                                    "value": request_data.get("area", 0)
                                }
                            ]
                        },
                        {
                            "id": 5,  # ID поля "Адрес"
                            "values": [
                                {
                                    "value": request_data.get("address", "")
                                }
                            ]
                        },
                        {
                            "id": 6,  # ID поля "Демо-заявка"
                            "values": [
                                {
                                    "value": request_data.get("is_demo", False)
                                }
                            ]
                        }
                    ],
                    "tags": ["bot", "telegram"],
                    "notes": [
                        {
                            "note_type": "COMMON",
                            "text": request_data.get("description", "")
                        }
                    ]
                }
            ]
        }
        
        return lead_data

async def send_to_crm(request_data: Dict[str, Any], crm_type: str = "bitrix24") -> bool:
    """
    Отправляет данные заявки в CRM
    
    Args:
        request_data: Данные заявки
        crm_type: Тип CRM (bitrix24 или amocrm)
        
    Returns:
        bool: True, если данные успешно отправлены, иначе False
    """
    # Проверяем, включена ли интеграция с CRM
    if crm_type == "bitrix24":
        if not CRM_SETTINGS["bitrix24"]["enabled"]:
            logger.debug("Интеграция с Битрикс24 отключена")
            return False
            
        api_key = CRM_SETTINGS["bitrix24"]["api_key"]
        base_url = CRM_SETTINGS["bitrix24"]["base_url"]
        
        if not api_key or not base_url:
            logger.error("Не указаны API-ключ или базовый URL для Битрикс24")
            return False
            
        # Создаем интеграцию с Битрикс24
        crm = Bitrix24Integration(api_key, base_url)
        
        # Форматируем данные
        lead_data = crm.format_lead(request_data)
        
        # Отправляем данные
        result = await crm.send_data(lead_data, "crm.lead.add", "json")
        
        if result and "result" in result:
            logger.info(f"Заявка #{request_data.get('id', '')} успешно отправлена в Битрикс24, ID лида: {result['result']}")
            return True
        else:
            logger.error(f"Ошибка при отправке заявки #{request_data.get('id', '')} в Битрикс24")
            return False
    
    elif crm_type == "amocrm":
        if not CRM_SETTINGS["amocrm"]["enabled"]:
            logger.debug("Интеграция с AmoCRM отключена")
            return False
            
        api_key = CRM_SETTINGS["amocrm"]["api_key"]
        base_url = CRM_SETTINGS["amocrm"]["base_url"]
        
        if not api_key or not base_url:
            logger.error("Не указаны API-ключ или базовый URL для AmoCRM")
            return False
            
        # Создаем интеграцию с AmoCRM
        crm = AmoCRMIntegration(api_key, base_url)
        
        # Форматируем данные
        lead_data = crm.format_lead(request_data)
        
        # Отправляем данные
        result = await crm.send_data(lead_data, "api/v4/leads", "json")
        
        if result and "_embedded" in result and "leads" in result["_embedded"]:
            lead_id = result["_embedded"]["leads"][0]["id"]
            logger.info(f"Заявка #{request_data.get('id', '')} успешно отправлена в AmoCRM, ID лида: {lead_id}")
            return True
        else:
            logger.error(f"Ошибка при отправке заявки #{request_data.get('id', '')} в AmoCRM")
            return False
    
    else:
        logger.error(f"Неподдерживаемый тип CRM: {crm_type}")
        return False

async def send_request_to_crm(request: Request) -> bool:
    """
    Отправляет заявку в CRM
    
    Args:
        request: Заявка
        
    Returns:
        bool: True, если заявка успешно отправлена, иначе False
    """
    # Подготавливаем данные заявки
    request_data = {
        "id": request.id,
        "client_name": request.client_name,
        "client_phone": request.client_phone,
        "description": request.description,
        "status": request.status.value if request.status else None,
        "is_demo": request.is_demo,
        "area": request.area,
        "address": request.address,
        "estimated_cost": request.estimated_cost,
        "created_at": request.created_at.isoformat() if request.created_at else None,
        "category_name": request.category.name if request.category else None,
        "city_name": request.city.name if request.city else None,
        "extra_data": request.extra_data
    }
    
    # Отправляем заявку в Битрикс24
    bitrix_result = await send_to_crm(request_data, "bitrix24")
    
    # Отправляем заявку в AmoCRM
    amo_result = await send_to_crm(request_data, "amocrm")
    
    # Возвращаем True, если заявка успешно отправлена хотя бы в одну CRM
    return bitrix_result or amo_result 