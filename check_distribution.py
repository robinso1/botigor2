from bot.models import get_session
from bot.models.models import Distribution, Request, User

session = get_session()

# Получаем заявку
request_id = 10
request = session.query(Request).filter(Request.id == request_id).first()
print(f'Заявка ID={request.id}:')
print(f'Имя клиента: {request.client_name}')
print(f'Телефон: {request.client_phone}')
print(f'Описание: {request.description}')
print(f'Статус: {request.status}')
print(f'Категория ID: {request.category_id}')
print(f'Город ID: {request.city_id}')
print(f'Демо: {request.is_demo}')

# Получаем распределения
print('\nРаспределения:')
distributions = session.query(Distribution).filter(Distribution.request_id == request_id).all()
for d in distributions:
    user = session.query(User).filter(User.id == d.user_id).first()
    user_name = f"{user.first_name} {user.last_name}" if user else "Неизвестный пользователь"
    print(f'ID={d.id}, пользователь ID={d.user_id} ({user_name}), статус={d.status}, создано={d.created_at}')

# Проверяем категории пользователя
if distributions:
    user_id = distributions[0].user_id
    print(f'\nКатегории пользователя ID={user_id}:')
    user = session.query(User).filter(User.id == user_id).first()
    if user and user.categories:
        for category in user.categories:
            print(f'Категория ID={category.id}, название={category.name}')
    else:
        print('У пользователя нет категорий') 