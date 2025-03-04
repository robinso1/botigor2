from bot.models import get_session
from bot.models.models import Request, RequestStatus
from bot.services.request_service import RequestService

session = get_session()
request_service = RequestService(session)

# Создаем новую заявку без категории
new_request = Request(
    client_name='Тестовый клиент для проверки 4',
    client_phone='+79991234570',
    description='Тестовая заявка для проверки распределения без категории',
    status=RequestStatus.NEW,
    is_demo=True,
    category_id=None,  # Без категории
    city_id=1          # Город "Москва"
)

session.add(new_request)
session.commit()

print(f'Создана новая заявка с ID={new_request.id}')

# Распределяем заявку
distributions = request_service.distribute_request(new_request.id)
print(f'Заявка распределена между {len(distributions)} пользователями')

for d in distributions:
    print(f'Распределение ID={d.id}, пользователь ID={d.user_id}, статус={d.status}') 