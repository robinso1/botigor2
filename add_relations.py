import sqlite3

def main():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    try:
        # Связываем пользователей с категориями и городами
        # Пользователь 3 (ID=3) - Москва, Установка душевой кабины, Монтаж инсталляции
        cursor.execute('INSERT INTO user_category (user_id, category_id) VALUES (3, 1)')
        cursor.execute('INSERT INTO user_category (user_id, category_id) VALUES (3, 2)')
        cursor.execute('INSERT INTO user_city (user_id, city_id) VALUES (3, 1)')
        
        # Пользователь 4 (ID=4) - Москва, Санкт-Петербург, Установка ванны, Монтаж бойлера
        cursor.execute('INSERT INTO user_category (user_id, category_id) VALUES (4, 4)')
        cursor.execute('INSERT INTO user_category (user_id, category_id) VALUES (4, 5)')
        cursor.execute('INSERT INTO user_city (user_id, city_id) VALUES (4, 1)')
        cursor.execute('INSERT INTO user_city (user_id, city_id) VALUES (4, 2)')
        
        # Пользователь 5 (ID=5) - Москва, Екатеринбург, Ремонт квартир под ключ
        cursor.execute('INSERT INTO user_category (user_id, category_id) VALUES (5, 20)')
        cursor.execute('INSERT INTO user_city (user_id, city_id) VALUES (5, 1)')
        cursor.execute('INSERT INTO user_city (user_id, city_id) VALUES (5, 3)')
        
        conn.commit()
        print('Связи добавлены успешно')
        
        # Проверяем связи
        cursor.execute('SELECT COUNT(*) FROM user_category')
        count = cursor.fetchone()[0]
        print(f'Количество связей пользователей с категориями: {count}')
        
        cursor.execute('SELECT COUNT(*) FROM user_city')
        count = cursor.fetchone()[0]
        print(f'Количество связей пользователей с городами: {count}')
        
    except Exception as e:
        print(f'Ошибка: {e}')
    finally:
        conn.close()

if __name__ == "__main__":
    main() 