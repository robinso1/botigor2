from bot.models import get_session, Request
from bot.utils import decrypt_personal_data

def main():
    session = get_session()
    
    # Получаем заявку с ID=8 (не демо)
    request = session.query(Request).filter_by(id=8).first()
    
    if request:
        print(f"Заявка ID={request.id}, демо={request.is_demo}")
        print(f"Клиент (зашифровано): {request.client_name}")
        print(f"Телефон (зашифровано): {request.client_phone}")
        
        # Расшифровываем данные
        if not request.is_demo:
            try:
                decrypted_name = decrypt_personal_data(request.client_name)
                decrypted_phone = decrypt_personal_data(request.client_phone)
                print(f"\nРасшифрованные данные:")
                print(f"Клиент: {decrypted_name}")
                print(f"Телефон: {decrypted_phone}")
            except Exception as e:
                print(f"Ошибка при расшифровке: {e}")
        else:
            print("\nДемо-заявка, данные не зашифрованы")
    else:
        print("Заявка не найдена")

if __name__ == "__main__":
    main() 