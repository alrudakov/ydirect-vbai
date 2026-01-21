"""
Получение списка рекламных кампаний из Yandex Direct
"""
import requests
import json
from config import DIRECT_API_URL


def load_token() -> str:
    """Загружает токен из файла"""
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Файл token.txt не найден!")
        print("Сначала запусти auth.py для получения токена")
        return None


def get_campaigns(token: str) -> dict:
    """Получает список кампаний"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json",
    }
    
    # Минимальный запрос без фильтров
    body = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "State", "Status"]
        }
    }
    
    url = DIRECT_API_URL + "campaigns"
    response = requests.post(url, headers=headers, json=body)
    return response.json()


def main():
    token = load_token()
    if not token:
        return
    
    print("Запрашиваю кампании из Yandex Direct...")
    print("-" * 60)
    
    result = get_campaigns(token)
    
    if "error" in result:
        print("Ошибка API:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    campaigns = result.get("result", {}).get("Campaigns", [])
    
    if not campaigns:
        print("Кампаний не найдено")
        print("\nСырой ответ API:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    print(f"Найдено кампаний: {len(campaigns)}\n")
    
    for camp in campaigns:
        print("=" * 60)
        print(f"ID: {camp.get('Id')}")
        print(f"Название: {camp.get('Name')}")
        print(f"Тип: {camp.get('Type')}")
        print(f"Статус: {camp.get('Status')}")
        print(f"Состояние: {camp.get('State')}")
        print(f"Статус оплаты: {camp.get('StatusPayment', 'N/A')}")
        print(f"Дата старта: {camp.get('StartDate', 'N/A')}")
        
        budget = camp.get('DailyBudget')
        if budget:
            amount = budget.get('Amount', 0) / 1000000  # микроединицы -> рубли
            print(f"Дневной бюджет: {amount:.2f} руб")
        
        stats = camp.get('Statistics')
        if stats:
            clicks = stats.get('Clicks', 0)
            imps = stats.get('Impressions', 0)
            print(f"Клики: {clicks}, Показы: {imps}")
        
        print()
    
    # Сохранить полный ответ
    with open("campaigns.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("Полный ответ сохранен в campaigns.json")


if __name__ == "__main__":
    main()

