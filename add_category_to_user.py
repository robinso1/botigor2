from bot.models import get_session, User, Category

def main():
    session = get_session()
    
    # Получаем пользователя
    user = session.query(User).filter_by(id=3).first()
    if not user:
        print("Пользователь не найден")
        return
    
    # Получаем категорию "Установка душевой кабины"
    category = session.query(Category).filter_by(id=7).first()
    if not category:
        print("Категория не найдена")
        return
    
    # Добавляем категорию пользователю
    user.categories.append(category)
    session.commit()
    
    print(f"Категория '{category.name}' успешно добавлена пользователю {user.first_name} {user.last_name}")
    
    # Проверяем категории пользователя
    print(f"Категории пользователя ({len(user.categories)}):")
    for cat in user.categories:
        print(f"  - ID={cat.id}, название={cat.name}")

if __name__ == "__main__":
    main() 