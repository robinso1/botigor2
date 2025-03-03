from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./bot.db')
    
    # Application settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEMO_MODE: bool = os.getenv('DEMO_MODE', 'False').lower() == 'true'
    
    # Request distribution settings
    REQUEST_INTERVAL_HOURS: int = 3
    MAX_USERS_PER_REQUEST: int = 3
    MAX_REQUEST_SENDS: int = 5
    
    # Demo mode settings
    DEMO_REQUESTS_PER_DAY: int = 5
    
    class Config:
        case_sensitive = True

settings = Settings() 