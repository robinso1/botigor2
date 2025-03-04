from bot.models import get_session
from bot.models.models import Request, RequestStatus, Category
from bot.services.request_service import RequestService

session = get_session()
request_service = RequestService(session)

# Найдем категорию, для которой нет пользователей
# Сначала получим все категории
all_categories = session.query(Category).all()
print("Доступные категории:")
for category in all_categories:
    print(f"ID={category.id}, название={category.name}")

# Создаем новую заявку с категорией ID=3 (предполагаем, что для нее нет пользователей)
new_request = Request(
    client_name='Тестовый клиент для проверки 3',
    client_phone='+79991234569',
    description='Тестовая заявка для проверки распределения по категории без пользователей',
    status=RequestStatus.NEW,
    is_demo=True,
    category_id=3,  # Категория "Электрика" (предполагаем)
    city_id=1       # Город "Москва"
)

session.add(new_request)
session.commit()

print(f'Создана новая заявка с ID={new_request.id}')

# Распределяем заявку
distributions = request_service.distribute_request(new_request.id)
print(f'Заявка распределена между {len(distributions)} пользователями')

for d in distributions:
    print(f'Распределение ID={d.id}, пользователь ID={d.user_id}, статус={d.status}') 