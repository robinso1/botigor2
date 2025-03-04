import os
import logging
from github import Github
from github.GithubException import GithubException
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_SYNC_INTERVAL
import threading
import time

logger = logging.getLogger(__name__)

def get_github_client():
    """
    Создает и возвращает клиент GitHub API
    """
    try:
        return Github(GITHUB_TOKEN)
    except Exception as e:
        logger.error(f"Ошибка при создании клиента GitHub: {e}")
        return None

def push_changes_to_github(commit_message="Автоматическое обновление"):
    """
    Отправляет изменения в репозиторий GitHub
    
    Args:
        commit_message (str): Сообщение коммита
    
    Returns:
        bool: True, если изменения успешно отправлены, иначе False
    """
    try:
        # Получаем текущую директорию проекта
        current_dir = os.path.abspath(os.getcwd())
        
        # Выполняем команды Git для отправки изменений
        os.system(f'cd "{current_dir}" && git add .')
        os.system(f'cd "{current_dir}" && git commit -m "{commit_message}"')
        os.system(f'cd "{current_dir}" && git push origin main')
        
        logger.info(f"Изменения успешно отправлены в GitHub: {commit_message}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке изменений в GitHub: {e}")
        return False

def get_repo_info():
    """
    Получает информацию о репозитории
    
    Returns:
        dict: Информация о репозитории или None в случае ошибки
    """
    try:
        g = get_github_client()
        if not g:
            return None
        
        repo = g.get_repo(GITHUB_REPO)
        return {
            "name": repo.name,
            "description": repo.description,
            "url": repo.html_url,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "last_update": repo.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    except GithubException as e:
        logger.error(f"Ошибка GitHub API: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении информации о репозитории: {e}")
        return None

def start_github_sync():
    """
    Запускает периодическую синхронизацию с GitHub
    """
    def sync_loop():
        while True:
            try:
                # Отправляем изменения в GitHub
                push_changes_to_github("Автоматическая синхронизация")
                logger.info("Успешная синхронизация с GitHub")
            except Exception as e:
                logger.error(f"Ошибка при синхронизации с GitHub: {e}")
            
            # Ждем следующей синхронизации
            time.sleep(GITHUB_SYNC_INTERVAL * 60)
    
    # Запускаем синхронизацию в отдельном потоке
    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    logger.info("Запущена периодическая синхронизация с GitHub") 