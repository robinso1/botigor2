from bot.models import get_session, Request
from bot.services.request_service import RequestService
from bot.utils import decrypt_personal_data

def main():
    session = get_session()
    request_service = RequestService(session)
    
    # Создаем реальную заявку
    request_data = {
        'client_name': 'Иван Петров',
        'client_phone': '+79991234567',
        'description': 'Реальная заявка для проверки шифрования',
        'is_demo': False,  # Реальная заявка
        'category_id': 7,  # Установка душевой кабины
        'city_id': 1,      # Москва
    }
    
    # Используем метод create_request из RequestService для правильного шифрования
    request = request_service.create_request(request_data)
    
    print(f"Создана реальная заявка: ID={request.id}")
    print(f"Клиент (зашифровано): {request.client_name}")
    print(f"Телефон (зашифровано): {request.client_phone}")
    
    # Расшифровываем данные
    try:
        decrypted_name = decrypt_personal_data(request.client_name)
        decrypted_phone = decrypt_personal_data(request.client_phone)
        print(f"\nРасшифрованные данные:")
        print(f"Клиент: {decrypted_name}")
        print(f"Телефон: {decrypted_phone}")
    except Exception as e:
        print(f"Ошибка при расшифровке: {e}")

if __name__ == "__main__":
    main() 