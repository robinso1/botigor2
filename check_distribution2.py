from bot.models import get_session
from bot.models.models import Distribution, Request, User, Category

session = get_session()

# Получаем заявку
request_id = 11
request = session.query(Request).filter(Request.id == request_id).first()
print(f'Заявка ID={request.id}:')
print(f'Имя клиента: {request.client_name}')
print(f'Телефон: {request.client_phone}')
print(f'Описание: {request.description}')
print(f'Статус: {request.status}')

# Получаем категорию
category = session.query(Category).filter(Category.id == request.category_id).first()
category_name = category.name if category else "Неизвестная категория"
print(f'Категория ID: {request.category_id} ({category_name})')

# Получаем город
print(f'Город ID: {request.city_id}')
print(f'Демо: {request.is_demo}')

# Получаем распределения
print('\nРаспределения:')
distributions = session.query(Distribution).filter(Distribution.request_id == request_id).all()
for d in distributions:
    user = session.query(User).filter(User.id == d.user_id).first()
    user_name = f"{user.first_name} {user.last_name}" if user else "Неизвестный пользователь"
    print(f'ID={d.id}, пользователь ID={d.user_id} ({user_name}), статус={d.status}, создано={d.created_at}')

# Проверяем всех пользователей с категорией "Сантехника"
print('\nВсе пользователи с категорией "Сантехника":')
category_id = 2  # ID категории "Сантехника"
users_with_category = session.query(User).filter(User.categories.any(id=category_id)).all()
for user in users_with_category:
    print(f'Пользователь ID={user.id}, имя={user.first_name} {user.last_name}, активен={user.is_active}') 