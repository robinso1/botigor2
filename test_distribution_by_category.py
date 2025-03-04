from bot.models import get_session, User
from bot.services.request_service import RequestService

def main():
    session = get_session()
    request_service = RequestService(session)
    
    # Распределяем заявку с ID=7 (Установка душевой кабины, Москва)
    distributions = request_service.distribute_request(7)
    
    print(f'Заявка распределена между {len(distributions)} пользователями')
    for dist in distributions:
        user = session.query(User).filter_by(id=dist.user_id).first()
        print(f'Распределение ID={dist.id}, пользователь ID={dist.user_id}, имя={user.first_name} {user.last_name}, статус={dist.status}')
        
    # Выводим информацию о пользователях и их категориях/городах
    print("\nИнформация о пользователях:")
    for user_id in [3, 4, 5]:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            print(f"Пользователь ID={user.id}, имя={user.first_name} {user.last_name}:")
            
            # Категории пользователя
            categories = []
            for cat in user.categories:
                categories.append(f"{cat.name} (ID={cat.id})")
            print(f"  Категории: {', '.join(categories) if categories else 'нет'}")
            
            # Города пользователя
            cities = []
            for city in user.cities:
                cities.append(f"{city.name} (ID={city.id})")
            print(f"  Города: {', '.join(cities) if cities else 'нет'}")

if __name__ == "__main__":
    main() 