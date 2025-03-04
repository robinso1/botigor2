from bot.models import get_session
from bot.models.models import Distribution, Request, User, Category
import json

session = get_session()

# Получаем заявку
request_id = 13
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

# Проверяем логику распределения в коде
print('\nАнализ логики распределения:')
print('1. Проверяем пользователей с городом ID=1:')
users_with_city = session.query(User).filter(
    User.cities.any(id=request.city_id),
    User.is_active == True
).all()
print(f'Найдено {len(users_with_city)} пользователей с городом {request.city_id}')
for user in users_with_city:
    print(f'  - Пользователь ID={user.id}, имя={user.first_name} {user.last_name}')

print('\n2. Проверяем всех активных пользователей:')
all_active_users = session.query(User).filter(User.is_active == True).all()
print(f'Найдено {len(all_active_users)} активных пользователей')
for user in all_active_users:
    print(f'  - Пользователь ID={user.id}, имя={user.first_name} {user.last_name}')

# Проверяем категории распределенных пользователей
print('\nКатегории пользователей, получивших заявку:')
for d in distributions:
    user = session.query(User).filter(User.id == d.user_id).first()
    if user:
        print(f'Пользователь ID={user.id}, имя={user.first_name} {user.last_name}:')
        if user.categories:
            for cat in user.categories:
                print(f'  - Категория ID={cat.id}, название={cat.name}')
        else:
            print('  - Нет категорий')
    else:
        print(f'Пользователь ID={d.user_id} не найден') 