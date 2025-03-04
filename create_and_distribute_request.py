from bot.models import get_session, Request, Category, City, User, Distribution
from bot.services.request_service import RequestService

def main():
    session = get_session()
    request_service = RequestService(session)
    
    # Создаем новую заявку
    request_data = {
        'client_name': 'Тестовый клиент 2',
        'client_phone': '+79991234567',
        'description': 'Тестовая заявка для проверки распределения',
        'is_demo': True,
        'category_id': 7,  # Установка душевой кабины
        'city_id': 1,      # Москва
    }
    
    request = Request(**request_data)
    session.add(request)
    session.commit()
    
    print(f"Создана новая заявка: ID={request.id}")
    
    # Распределяем заявку
    distributions = request_service.distribute_request(request.id)
    
    print(f"Заявка распределена между {len(distributions)} пользователями")
    
    for dist in distributions:
        user = session.query(User).filter_by(id=dist.user_id).first()
        print(f"  - ID={dist.id}, пользователь={user.first_name} {user.last_name}, статус={dist.status}")
    
    # Проверяем пользователей, которые должны были получить заявку
    print("\nПользователи с категорией 'Установка душевой кабины' и городом 'Москва':")
    users = session.query(User).join(User.categories).join(User.cities).filter(
        Category.id == 7,
        City.id == 1
    ).all()
    
    for user in users:
        print(f"  - ID={user.id}, имя={user.first_name} {user.last_name}")

if __name__ == "__main__":
    main() 