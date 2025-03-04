from bot.models import get_session, Distribution, Request, User

def main():
    session = get_session()
    
    # Проверяем распределения для заявки с ID=7
    distributions = session.query(Distribution).filter_by(request_id=7).all()
    
    print(f"Распределения для заявки с ID=7: {len(distributions)}")
    
    for dist in distributions:
        user = session.query(User).filter_by(id=dist.user_id).first()
        print(f"  - ID={dist.id}, пользователь={user.first_name} {user.last_name}, статус={dist.status}, создано={dist.created_at}")
    
    # Проверяем все распределения
    all_distributions = session.query(Distribution).all()
    print(f"\nВсе распределения: {len(all_distributions)}")
    
    for dist in all_distributions:
        request = session.query(Request).filter_by(id=dist.request_id).first()
        user = session.query(User).filter_by(id=dist.user_id).first()
        print(f"  - ID={dist.id}, заявка={dist.request_id}, пользователь={user.first_name} {user.last_name}, статус={dist.status}, создано={dist.created_at}")

if __name__ == "__main__":
    main() 