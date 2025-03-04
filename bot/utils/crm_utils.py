import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CRMIntegration:
    """Базовый класс для интеграции с CRM-системами"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def format_data_json(self, data: Dict[str, Any]) -> str:
        """
        Форматирует данные в JSON
        
        Args:
            data (Dict[str, Any]): Данные для форматирования
        
        Returns:
            str: JSON-строка
        """
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def format_data_xml(self, data: Dict[str, Any]) -> str:
        """
        Форматирует данные в XML
        
        Args:
            data (Dict[str, Any]): Данные для форматирования
        
        Returns:
            str: XML-строка
        """
        root = ET.Element("request")
        
        def dict_to_xml(parent: ET.Element, data: Dict[str, Any]):
            for key, value in data.items():
                child = ET.SubElement(parent, key)
                if isinstance(value, dict):
                    dict_to_xml(child, value)
                else:
                    child.text = str(value)
        
        dict_to_xml(root, data)
        return ET.tostring(root, encoding='unicode', method='xml')

class Bitrix24Integration(CRMIntegration):
    """Интеграция с Битрикс24"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует данные заявки для Битрикс24
        
        Args:
            request_data (Dict[str, Any]): Данные заявки
        
        Returns:
            Dict[str, Any]: Отформатированные данные
        """
        return {
            "fields": {
                "TITLE": f"Заявка №{request_data.get('id')}",
                "NAME": request_data.get("client_name", ""),
                "PHONE": [{"VALUE": request_data.get("client_phone", "")}],
                "COMMENTS": request_data.get("description", ""),
                "CATEGORY_ID": request_data.get("category_id"),
                "ADDRESS": request_data.get("address", ""),
                "SOURCE_ID": "TELEGRAM_BOT",
                "STATUS_ID": "NEW",
                "ASSIGNED_BY_ID": request_data.get("assigned_to"),
                "DATE_CREATE": datetime.utcnow().isoformat()
            }
        }

class AmoCRMIntegration(CRMIntegration):
    """Интеграция с AmoCRM"""
    
    def format_lead(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует данные заявки для AmoCRM
        
        Args:
            request_data (Dict[str, Any]): Данные заявки
        
        Returns:
            Dict[str, Any]: Отформатированные данные
        """
        return {
            "name": f"Заявка №{request_data.get('id')}",
            "created_at": int(datetime.utcnow().timestamp()),
            "status_id": 1,  # Новая заявка
            "pipeline_id": 1,  # Основная воронка
            "custom_fields_values": [
                {
                    "field_id": 1,
                    "values": [{"value": request_data.get("client_name", "")}]
                },
                {
                    "field_id": 2,
                    "values": [{"value": request_data.get("client_phone", "")}]
                },
                {
                    "field_id": 3,
                    "values": [{"value": request_data.get("description", "")}]
                }
            ]
        }

def send_to_crm(request_data: Dict[str, Any], crm_type: str = "bitrix24") -> bool:
    """
    Отправляет данные заявки в CRM
    
    Args:
        request_data (Dict[str, Any]): Данные заявки
        crm_type (str): Тип CRM-системы ("bitrix24" или "amocrm")
    
    Returns:
        bool: True если данные успешно отправлены, False в противном случае
    """
    try:
        # В реальном проекте здесь будет реальная отправка данных в CRM
        # через API соответствующей системы
        
        if crm_type == "bitrix24":
            crm = Bitrix24Integration("api_key", "https://your-domain.bitrix24.ru")
            data = crm.format_lead(request_data)
            formatted_data = crm.format_data_json(data)
        else:  # amocrm
            crm = AmoCRMIntegration("api_key", "https://your-domain.amocrm.ru")
            data = crm.format_lead(request_data)
            formatted_data = crm.format_data_xml(data)
        
        logger.info(f"Данные подготовлены для отправки в {crm_type}: {formatted_data}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при отправке данных в CRM {crm_type}: {e}")
        return False 