"""
Создание тестовой кампании в Yandex Direct
"""
import requests
import json
from datetime import datetime, timedelta
from config import DIRECT_API_URL


def load_token() -> str:
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Файл token.txt не найден!")
        return None


def create_campaign(token: str) -> dict:
    """Создаёт тестовую кампанию"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json",
    }
    
    # Дата начала - завтра
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    body = {
        "method": "add",
        "params": {
            "Campaigns": [
                {
                    "Name": "API Test Campaign",
                    "StartDate": start_date,
                    "TextCampaign": {
                        "BiddingStrategy": {
                            "Search": {
                                "BiddingStrategyType": "HIGHEST_POSITION"
                            },
                            "Network": {
                                "BiddingStrategyType": "SERVING_OFF"
                            }
                        },
                        "Settings": [
                            {"Option": "ADD_METRICA_TAG", "Value": "NO"},
                            {"Option": "ADD_OPENSTAT_TAG", "Value": "NO"},
                            {"Option": "ADD_TO_FAVORITES", "Value": "NO"},
                            {"Option": "ENABLE_AREA_OF_INTEREST_TARGETING", "Value": "YES"},
                            {"Option": "ENABLE_COMPANY_INFO", "Value": "YES"},
                            {"Option": "ENABLE_SITE_MONITORING", "Value": "NO"},
                            {"Option": "REQUIRE_SERVICING", "Value": "NO"}
                        ]
                    }
                }
            ]
        }
    }
    
    url = DIRECT_API_URL + "campaigns"
    response = requests.post(url, headers=headers, json=body)
    return response.json()


def main():
    token = load_token()
    if not token:
        return
    
    print("Создаю тестовую кампанию...")
    print("-" * 60)
    
    result = create_campaign(token)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if "result" in result:
        add_results = result["result"].get("AddResults", [])
        for r in add_results:
            if "Id" in r:
                print(f"\n✅ Кампания создана! ID: {r['Id']}")
            elif "Errors" in r:
                print(f"\n❌ Ошибка:")
                for err in r["Errors"]:
                    print(f"  {err.get('Code')}: {err.get('Message')}")


if __name__ == "__main__":
    main()

