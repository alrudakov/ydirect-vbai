"""
🚀 Финальный запуск кампании:
1. Дата старта = сегодня
2. UTM метки в объявлениях
3. Запуск кампании
"""
import requests
from pathlib import Path
from datetime import datetime

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

CAMPAIGN_ID = 706570098
TODAY = datetime.now().strftime("%Y-%m-%d")  # 2026-01-23

# UTM параметры
UTM = "utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2"

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
        print(f"❌ Ошибка: {err.get('error_string')}")
        print(f"   {err.get('error_detail', '')}")
        return None
    
    return result.get("result", {})

print("=" * 60)
print(f"🚀 ЗАПУСК КАМПАНИИ {CAMPAIGN_ID}")
print("=" * 60)

# 1. Обновляем дату старта
print(f"\n📅 Шаг 1: Дата старта → {TODAY}")

result = call_api("campaigns", "update", {
    "Campaigns": [{
        "Id": CAMPAIGN_ID,
        "StartDate": TODAY
    }]
})

if result:
    print("   ✅ Дата обновлена!")

# 2. Получаем объявления и обновляем UTM
print(f"\n🔗 Шаг 2: Добавляю UTM метки в объявления...")

result = call_api("ads", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Status"],
    "TextAdFieldNames": ["Title", "Href"]
})

if result:
    ads = result.get("Ads", [])
    
    for ad in ads:
        ad_id = ad["Id"]
        status = ad["Status"]
        href = ad.get("TextAd", {}).get("Href", "")
        title = ad.get("TextAd", {}).get("Title", "")
        
        # Пропускаем черновики
        if status == "DRAFT":
            continue
        
        # Если UTM уже есть — пропускаем
        if "utm_source" in href:
            print(f"   [{ad_id}] {title[:25]}... — UTM уже есть ✓")
            continue
        
        # Добавляем UTM
        new_href = f"{href}?{UTM}&utm_content={ad_id}"
        
        update_result = call_api("ads", "update", {
            "Ads": [{
                "Id": ad_id,
                "TextAd": {
                    "Href": new_href
                }
            }]
        })
        
        if update_result:
            print(f"   [{ad_id}] {title[:25]}... — UTM добавлен ✅")

# 3. Проверяем статус кампании
print(f"\n📋 Шаг 3: Проверяю статус...")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "State", "Status", "StartDate"]
})

if result:
    for c in result.get("Campaigns", []):
        print(f"   Название: {c.get('Name')}")
        print(f"   Статус: {c.get('Status')} | Состояние: {c.get('State')}")
        print(f"   Дата старта: {c.get('StartDate')}")

# 4. Запускаем кампанию (resume)
print(f"\n▶️ Шаг 4: Запускаю кампанию...")

result = call_api("campaigns", "resume", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]}
})

if result:
    print("   ✅ Кампания запущена!")

# 5. Финальная проверка
print(f"\n📋 Финальный статус:")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "State", "Status"]
})

if result:
    for c in result.get("Campaigns", []):
        state = c.get('State')
        status = c.get('Status')
        
        if state == "ON":
            print(f"   🟢 {c.get('Name')} — РАБОТАЕТ!")
        else:
            print(f"   🟡 {c.get('Name')} — {status} / {state}")

print("\n" + "=" * 60)
print(f"🔗 https://direct.yandex.ru/dna/grid/campaigns/{CAMPAIGN_ID}")
print("=" * 60)

