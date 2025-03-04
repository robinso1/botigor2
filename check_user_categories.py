from bot.models import get_session, User, Category, City

def main():
    session = get_session()
    users = session.query(User).all()
    
    print(f"Всего пользователей: {len(users)}")
    
    for user in users:
        print(f"\nПользователь ID={user.id}, имя={user.first_name} {user.last_name}")
        
        # Проверяем категории
        print(f"Категории ({len(user.categories)}):")
        for category in user.categories:
            print(f"  - ID={category.id}, название={category.name}")
        
        # Проверяем города
        print(f"Города ({len(user.cities)}):")
        for city in user.cities:
            print(f"  - ID={city.id}, название={city.name}")

if __name__ == "__main__":
    main() 