"""
💰 Установка бюджета кампании
"""
import requests
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

CAMPAIGN_ID = 706570098
WEEKLY_BUDGET_RUB = 7000  # 7000 руб/неделю = ~1000 руб/день
MAX_CPC_RUB = 15  # Макс цена клика (старая кампания: ~5 руб среднее)

def call_api(service: str, method: str, params: dict):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {"method": method, "params": params}
    url = f"{BASE_URL}/{service}"
    
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    result = resp.json()
    
    if "error" in result:
        err = result["error"]
        print(f"❌ Ошибка [{err.get('error_code')}]: {err.get('error_string')}")
        print(f"   {err.get('error_detail', '')}")
        return None
    
    return result.get("result", {})

print("=" * 60)
print(f"💰 УСТАНОВКА БЮДЖЕТА - Кампания {CAMPAIGN_ID}")
print("=" * 60)

# Бюджет в микроединицах (1 руб = 1_000_000)
weekly_budget_micros = WEEKLY_BUDGET_RUB * 1_000_000
max_cpc_micros = MAX_CPC_RUB * 1_000_000

print(f"\n📊 Устанавливаю:")
print(f"   Недельный бюджет: {WEEKLY_BUDGET_RUB} руб (~{WEEKLY_BUDGET_RUB // 7} руб/день)")
print(f"   Макс CPC: {MAX_CPC_RUB} руб (старая кампания: ~5 руб)")

# Обновляем стратегию с новым бюджетом
result = call_api("campaigns", "update", {
    "Campaigns": [{
        "Id": CAMPAIGN_ID,
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                    "WbMaximumClicks": {
                        "WeeklySpendLimit": weekly_budget_micros,
                        "BidCeiling": max_cpc_micros  # Макс цена клика
                    }
                },
                "Network": {
                    "BiddingStrategyType": "NETWORK_DEFAULT"
                }
            }
        }
    }]
})

if result:
    for r in result.get("UpdateResults", []):
        if "Errors" not in r or not r["Errors"]:
            print(f"\n✅ Бюджет установлен!")
        else:
            for err in r.get("Errors", []):
                print(f"❌ {err.get('Message')}")

# Проверяем
print(f"\n📋 Проверяю настройки кампании...")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "State", "Status"],
    "TextCampaignFieldNames": ["BiddingStrategy"]
})

if result:
    for c in result.get("Campaigns", []):
        print(f"   Название: {c.get('Name')}")
        print(f"   Статус: {c.get('Status')} | Состояние: {c.get('State')}")
        
        strategy = c.get("TextCampaign", {}).get("BiddingStrategy", {})
        search = strategy.get("Search", {})
        
        strategy_type = search.get("BiddingStrategyType")
        print(f"   Стратегия: {strategy_type}")
        
        if "WbMaximumClicks" in search:
            wmc = search["WbMaximumClicks"]
            weekly = wmc.get("WeeklySpendLimit", 0) / 1_000_000
            ceiling = wmc.get("BidCeiling", 0) / 1_000_000
            print(f"   Недельный лимит: {weekly:.0f} руб")
            print(f"   Макс. цена клика: {ceiling:.0f} руб")

print("\n" + "=" * 60)
print("✅ Готово!")
print("=" * 60)

