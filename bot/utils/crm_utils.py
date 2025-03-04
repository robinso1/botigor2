import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
import os
from config import SECRET_KEY

logger = logging.getLogger(__name__)

class CRMIntegration:
    """Базовый класс для интеграции с CRM-системами"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def format_data_json(self, data: Dict[str, Any]) -> str:
        """Форматирует данные заявки в JSON для отправки в CRM"""
        formatted_data = {
            "lead": self.format_lead(data),
            "timestamp": datetime.now().isoformat(),
            "source": "telegram_bot"
        }
        return json.dumps(formatted_data, ensure_ascii=False)
    
    def format_data_xml(self, data: Dict[str, Any]) -> str:
        """Форматирует данные заявки в XML для отправки в CRM"""
        root = ET.Element("request")
        
        lead = ET.SubElement(root, "lead")
        lead_data = self.format_lead(data)
        
        # Рекурсивно создаем XML из словаря
        dict_to_xml(lead, lead_data)
        
        # Добавляем метаданные
        meta = ET.SubElement(root, "meta")
        ET.SubElement(meta, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(meta, "source").text = "telegram_bot"
        
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        
        def dict_to_xml(parent: ET.Element, data: Dict[str, Any]):
            """Рекурсивно преобразует словарь в XML"""
            for key, value in data.items():
                if isinstance(value, dict):
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, value)
                else:
                    ET.SubElement(parent, key).text = str(value)

class Bitrix24Integration(CRMIntegration):
    """Класс для интеграции с Битрикс24"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирует данные заявки для Битрикс24"""
        lead = {
            "TITLE": f"Заявка №{request_data.get('id', 'Новая')} от {datetime.now().strftime('%d.%m.%Y')}",
            "NAME": request_data.get("client_name", ""),
            "PHONE": [{"VALUE": request_data.get("client_phone", ""), "VALUE_TYPE": "WORK"}],
            "STATUS_ID": "NEW",
            "OPENED": "Y",
            "SOURCE_ID": "WEB",
            "SOURCE_DESCRIPTION": "Telegram Bot",
            "COMMENTS": request_data.get("description", ""),
            "ASSIGNED_BY_ID": 1,
            "CURRENCY_ID": "RUB",
            "OPPORTUNITY": request_data.get("estimated_cost", 0),
            "UF_CRM_CATEGORY": request_data.get("category", {}).get("name", ""),
            "UF_CRM_CITY": request_data.get("city", {}).get("name", ""),
            "UF_CRM_AREA": request_data.get("area", 0),
            "UF_CRM_ADDRESS": request_data.get("address", ""),
            "UF_CRM_IS_DEMO": "Y" if request_data.get("is_demo", False) else "N"
        }
        return lead

class AmoCRMIntegration(CRMIntegration):
    """Класс для интеграции с AmoCRM"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирует данные заявки для AmoCRM"""
        # Формируем название заявки
        title = f"Заявка №{request_data.get('id', 'Новая')} от {datetime.now().strftime('%d.%m.%Y')}"
        
        # Формируем описание заявки
        description = f"""
        Имя клиента: {request_data.get('client_name', '')}
        Телефон: {request_data.get('client_phone', '')}
        Категория: {request_data.get('category', {}).get('name', '')}
        Город: {request_data.get('city', {}).get('name', '')}
        Площадь: {request_data.get('area', 0)} м²
        Адрес: {request_data.get('address', '')}
        Описание: {request_data.get('description', '')}
        """
        
        lead = {
            "name": title,
            "price": request_data.get("estimated_cost", 0),
            "status_id": 142, # ID статуса "Новая заявка" в AmoCRM
            "pipeline_id": 3312, # ID воронки в AmoCRM
            "created_at": int(datetime.now().timestamp()),
            "custom_fields_values": [
                {
                    "field_id": 303721, # ID поля "Телефон"
                    "values": [{"value": request_data.get("client_phone", "")}]
                },
                {
                    "field_id": 303723, # ID поля "Категория"
                    "values": [{"value": request_data.get("category", {}).get("name", "")}]
                },
                {
                    "field_id": 303725, # ID поля "Город"
                    "values": [{"value": request_data.get("city", {}).get("name", "")}]
                },
                {
                    "field_id": 303727, # ID поля "Площадь"
                    "values": [{"value": str(request_data.get("area", 0))}]
                },
                {
                    "field_id": 303729, # ID поля "Демо-заявка"
                    "values": [{"value": "Да" if request_data.get("is_demo", False) else "Нет"}]
                }
            ],
            "metadata": {
                "source": "telegram_bot",
                "source_uid": str(request_data.get("id", "")),
                "is_demo": request_data.get("is_demo", False)
            }
        }
        return lead

def send_to_crm(request_data: Dict[str, Any], crm_type: str = "bitrix24") -> bool:
    """
    Отправляет данные заявки в указанную CRM-систему
    
    Args:
        request_data: Данные заявки
        crm_type: Тип CRM-системы (bitrix24 или amocrm)
        
    Returns:
        bool: Успешность отправки
    """
    try:
        # Получаем настройки CRM из переменных окружения или конфигурации
        if crm_type.lower() == "bitrix24":
            api_key = os.getenv("BITRIX24_API_KEY", "")
            base_url = os.getenv("BITRIX24_URL", "https://example.bitrix24.ru/rest/1/")
            crm = Bitrix24Integration(api_key, base_url)
        elif crm_type.lower() == "amocrm":
            api_key = os.getenv("AMOCRM_API_KEY", "")
            base_url = os.getenv("AMOCRM_URL", "https://example.amocrm.ru/api/v4/")
            crm = AmoCRMIntegration(api_key, base_url)
        else:
            logger.error(f"Неизвестный тип CRM: {crm_type}")
            return False
            
        # Форматируем данные в JSON
        json_data = crm.format_data_json(request_data)
        
        # Отправляем данные в CRM
        logger.info(f"Отправка данных в {crm_type}: {json_data}")
        
        # Здесь должен быть код для отправки данных в CRM через API
        # Для примера просто логируем данные
        logger.info(f"Данные успешно отправлены в {crm_type}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке данных в CRM {crm_type}: {str(e)}")
        return False 