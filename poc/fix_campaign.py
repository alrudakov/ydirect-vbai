"""
🔧 Исправление кампании: отключение мобильных, добавление минус-площадок
"""
import requests
import json
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

CAMPAIGN_ID = 706570098  # Новая кампания ExecAI IT

def call_api(service: str, method: str, params: dict):
    """Вызов API"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    
    body = {"method": method, "params": params}
    url = f"{BASE_URL}/{service}"
    
    resp = requests.post(url, headers=headers, json=body)
    result = resp.json()
    
    if "error" in result:
        print(f"❌ Ошибка: {result['error']}")
        return None
    
    return result.get("result", {})


print("=" * 60)
print(f"🔧 ИСПРАВЛЕНИЕ КАМПАНИИ {CAMPAIGN_ID}")
print("=" * 60)

# 1. Отключаем мобильные и планшеты (BidModifier=0 = -100%)
print("\n📱 Шаг 1: Отключаю мобильные и планшеты...")

result = call_api("bidmodifiers", "add", {
    "BidModifiers": [
        {
            "CampaignId": CAMPAIGN_ID,
            "MobileAdjustment": {
                "BidModifier": 0
            }
        },
        {
            "CampaignId": CAMPAIGN_ID,
            "TabletAdjustment": {
                "BidModifier": 0
            }
        }
    ]
})

if result:
    for r in result.get("AddResults", []):
        if "Id" in r:
            print(f"   ✅ Корректировка создана: ID {r['Id']}")
        elif "Errors" in r:
            for err in r["Errors"]:
                print(f"   ⚠️ {err.get('Message')}")

# 2. Добавляем минус-площадки
print("\n🚫 Шаг 2: Добавляю минус-площадки...")

excluded = [
    "dsp-minimob-ww.yandex.ru",
    "dsp-opera-exchange.yandex.ru",
    "dsp-webeye.yandex.ru",
    "dsp-yeahmobi.yandex.ru",
    "dsp-inneractive.yandex.ru",
    "video.like"
]

result = call_api("campaigns", "update", {
    "Campaigns": [{
        "Id": CAMPAIGN_ID,
        "ExcludedSites": {
            "Items": excluded
        }
    }]
})

if result:
    print(f"   ✅ Минус-площадки добавлены: {len(excluded)} шт")

# 3. Проверяем кампанию
print("\n📋 Шаг 3: Проверяю кампанию...")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "State", "Status", "ExcludedSites"]
})

if result:
    for c in result.get("Campaigns", []):
        print(f"   Название: {c.get('Name')}")
        print(f"   Статус: {c.get('Status')} | Состояние: {c.get('State')}")
        
        excluded_sites = c.get("ExcludedSites", {}).get("Items", [])
        print(f"   Минус-площадки: {len(excluded_sites)} шт")

print("\n" + "=" * 60)
print("✅ Готово!")
print("=" * 60)

