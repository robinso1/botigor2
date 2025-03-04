from bot.models import get_session, Request, Category, City

def main():
    session = get_session()
    request = session.query(Request).filter_by(id=7).first()
    
    if request:
        category = session.query(Category).filter_by(id=request.category_id).first()
        city = session.query(City).filter_by(id=request.city_id).first()
        
        print(f'Заявка ID={request.id}')
        print(f'Категория ID={request.category_id} ({category.name if category else "не найдена"})')
        print(f'Город ID={request.city_id} ({city.name if city else "не найден"})')
        print(f'Описание: {request.description}')
        print(f'Демо: {request.is_demo}')
    else:
        print('Заявка с ID=7 не найдена')

if __name__ == "__main__":
    main() 