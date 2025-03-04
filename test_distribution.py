from bot.models import get_session
from bot.services.request_service import RequestService

def main():
    session = get_session()
    request_service = RequestService(session)
    
    # Распределяем заявку с ID=5
    distributions = request_service.distribute_request(5)
    
    print(f'Заявка распределена между {len(distributions)} пользователями')
    for dist in distributions:
        print(f'Распределение ID={dist.id}, пользователь ID={dist.user_id}, статус={dist.status}')

if __name__ == "__main__":
    main() 