from bot.models import get_session, Request, User, Distribution
from bot.services.request_service import RequestService
from bot.utils import decrypt_personal_data

def main():
    session = get_session()
    request_service = RequestService(session)
    
    # Распределяем реальную заявку с ID=9
    distributions = request_service.distribute_request(9)
    
    print(f"Заявка распределена между {len(distributions)} пользователями")
    
    for dist in distributions:
        user = session.query(User).filter_by(id=dist.user_id).first()
        print(f"  - ID={dist.id}, пользователь={user.first_name} {user.last_name}, статус={dist.status}")
    
    # Проверяем информацию о распределении
    print("\nИнформация о распределении:")
    for dist in distributions:
        user = session.query(User).filter_by(id=dist.user_id).first()
        request = session.query(Request).filter_by(id=dist.request_id).first()
        
        # Расшифровываем данные клиента
        client_name = decrypt_personal_data(request.client_name)
        client_phone = decrypt_personal_data(request.client_phone)
        
        print(f"Распределение ID={dist.id}:")
        print(f"  Пользователь: {user.first_name} {user.last_name}")
        print(f"  Заявка ID={request.id}")
        print(f"  Клиент: {client_name}")
        print(f"  Телефон: {client_phone}")
        print(f"  Описание: {request.description}")
        print(f"  Статус распределения: {dist.status}")
        print(f"  Создано: {dist.created_at}")

if __name__ == "__main__":
    main() 