"""
Скрипт для проверки демо-заявок в базе данных
"""
import sqlite3
from datetime import datetime

def main():
    """Основная функция скрипта"""
    # Подключаемся к базе данных
    conn = sqlite3.connect('bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Получаем все демо-заявки
    cursor.execute("""
        SELECT r.id, r.client_name, r.client_phone, r.description, 
               r.created_at, r.status, c.name as category_name, 
               city.name as city_name
        FROM requests r
        LEFT JOIN categories c ON r.category_id = c.id
        LEFT JOIN cities city ON r.city_id = city.id
        WHERE r.is_demo = 1
        ORDER BY r.created_at DESC
    """)
    
    requests = cursor.fetchall()
    
    print(f"Всего демо-заявок: {len(requests)}")
    print("\nПоследние 5 демо-заявок:")
    
    for i, req in enumerate(requests[:5]):
        created_at = datetime.fromisoformat(req['created_at']) if req['created_at'] else "Неизвестно"
        print(f"\n{i+1}. ID: {req['id']}")
        print(f"   Клиент: {req['client_name']}, Телефон: {req['client_phone']}")
        print(f"   Категория: {req['category_name']}, Город: {req['city_name']}")
        print(f"   Описание: {req['description']}")
        print(f"   Статус: {req['status']}")
        print(f"   Создана: {created_at}")
    
    # Получаем статистику по категориям
    cursor.execute("""
        SELECT c.name, COUNT(r.id) as count
        FROM requests r
        JOIN categories c ON r.category_id = c.id
        WHERE r.is_demo = 1
        GROUP BY c.name
        ORDER BY count DESC
    """)
    
    categories = cursor.fetchall()
    
    print("\nРаспределение по категориям:")
    for cat in categories:
        print(f"   {cat['name']}: {cat['count']} заявок")
    
    # Получаем статистику по городам
    cursor.execute("""
        SELECT c.name, COUNT(r.id) as count
        FROM requests r
        JOIN cities c ON r.city_id = c.id
        WHERE r.is_demo = 1
        GROUP BY c.name
        ORDER BY count DESC
    """)
    
    cities = cursor.fetchall()
    
    print("\nРаспределение по городам:")
    for city in cities:
        print(f"   {city['name']}: {city['count']} заявок")
    
    # Закрываем соединение
    conn.close()

if __name__ == "__main__":
    main() 