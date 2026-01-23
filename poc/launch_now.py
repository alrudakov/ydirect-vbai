"""
🚀 Запуск кампании СЕЙЧАС
"""
import requests
from pathlib import Path
from datetime import datetime

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"
CAMPAIGN_ID = 706570098

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
        print(f"❌ {result['error'].get('error_string')}: {result['error'].get('error_detail', '')}")
        return None
    return result.get("result", {})

print("🚀 ЗАПУСК КАМПАНИИ ExecAI IT")
print("=" * 50)

# 1. Ставим дату на сегодня
today = datetime.now().strftime("%Y-%m-%d")
print(f"\n📅 Дата старта → {today}")

result = call_api("campaigns", "update", {
    "Campaigns": [{"Id": CAMPAIGN_ID, "StartDate": today}]
})
if result:
    print("   ✅ Дата обновлена")

# 2. Запускаем
print(f"\n▶️ Запускаю кампанию...")

result = call_api("campaigns", "resume", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]}
})
if result:
    print("   ✅ Команда отправлена")

# 3. Проверяем статус
print(f"\n📋 Статус:")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "State", "Status", "StartDate"]
})

if result:
    for c in result.get("Campaigns", []):
        state = c.get('State')
        status = c.get('Status')
        emoji = "🟢" if state == "ON" else "🟡"
        print(f"   {emoji} {c.get('Name')}")
        print(f"      Статус: {status} | Состояние: {state}")
        print(f"      Дата старта: {c.get('StartDate')}")

# 4. Проверяем объявления
print(f"\n📝 Объявления:")

result = call_api("ads", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Status", "State"],
    "TextAdFieldNames": ["Title"]
})

if result:
    ads = result.get("Ads", [])
    on_mod = sum(1 for a in ads if a["Status"] == "MODERATION")
    accepted = sum(1 for a in ads if a["Status"] == "ACCEPTED")
    draft = sum(1 for a in ads if a["Status"] == "DRAFT")
    
    print(f"   Всего: {len(ads)}")
    print(f"   ✅ Принято: {accepted}")
    print(f"   ⏳ На модерации: {on_mod}")
    print(f"   📝 Черновиков: {draft}")

print("\n" + "=" * 50)
print(f"🔗 https://direct.yandex.ru/dna/grid/campaigns/{CAMPAIGN_ID}")

