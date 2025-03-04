from bot.models import get_session
from bot.models.models import Distribution, Request, User, Category
import json

session = get_session()

# Получаем заявку
request_id = 12
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

# Проверяем пользователей с категорией "Электрика"
print('\nПользователи с категорией "Электрика":')
category_id = 3  # ID категории "Электрика"
users_with_category = session.query(User).filter(User.categories.any(id=category_id)).all()
if users_with_category:
    for user in users_with_category:
        print(f'Пользователь ID={user.id}, имя={user.first_name} {user.last_name}, активен={user.is_active}')
else:
    print('Нет пользователей с категорией "Электрика"')

# Проверяем логику распределения в коде
print('\nАнализ логики распределения:')
print('1. Проверяем пользователей, у которых есть эта категория и город:')
users_with_category_and_city = session.query(User).filter(
    User.categories.any(id=category_id),
    User.cities.any(id=request.city_id),
    User.is_active == True
).all()
print(f'Найдено {len(users_with_category_and_city)} пользователей с категорией {category_id} и городом {request.city_id}')

print('\n2. Проверяем пользователей, у которых есть эта категория (любой город):')
users_with_category_any_city = session.query(User).filter(
    User.categories.any(id=category_id),
    User.is_active == True
).all()
print(f'Найдено {len(users_with_category_any_city)} пользователей с категорией {category_id} (любой город)')

print('\n3. Проверяем пользователей, у которых есть этот город (любая категория):')
users_with_city_any_category = session.query(User).filter(
    User.cities.any(id=request.city_id),
    User.is_active == True
).all()
print(f'Найдено {len(users_with_city_any_category)} пользователей с городом {request.city_id} (любая категория)')

print('\n4. Проверяем всех активных пользователей:')
all_active_users = session.query(User).filter(User.is_active == True).all()
print(f'Найдено {len(all_active_users)} активных пользователей')

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