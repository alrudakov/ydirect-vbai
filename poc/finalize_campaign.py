"""
🔧 Финализация кампании ExecAI IT:
1. Получить настройки метрики из старой кампании
2. Применить к новой
3. Отправить на модерацию (правильный формат)
"""
import requests
import json
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

OLD_CAMPAIGN_ID = 706552117  # Старая (ExecAI - DevOps IT)
NEW_CAMPAIGN_ID = 706570098  # Новая (ExecAI IT)

AD_IDS = [17556257661, 17556257662, 17556257664]  # Созданные объявления

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
print("🔧 ФИНАЛИЗАЦИЯ КАМПАНИИ")
print("=" * 60)

# ============================================
# 1. Получаем настройки старой кампании
# ============================================
print("\n📋 Шаг 1: Получаю настройки старой кампании...")

result = call_api("campaigns", "get", {
    "SelectionCriteria": {"Ids": [OLD_CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name"],
    "TextCampaignFieldNames": ["CounterIds", "Settings"]
})

counter_ids = []
if result:
    for c in result.get("Campaigns", []):
        print(f"   Кампания: {c.get('Name')}")
        
        text_camp = c.get("TextCampaign", {})
        counter_ids = text_camp.get("CounterIds", {}).get("Items", [])
        
        print(f"   Счётчики Метрики: {counter_ids}")
        
        settings = text_camp.get("Settings", [])
        for s in settings:
            if "METRICA" in s.get("Option", ""):
                print(f"   {s.get('Option')}: {s.get('Value')}")

# ============================================
# 2. Применяем метрику к новой кампании
# ============================================
if counter_ids:
    print(f"\n📊 Шаг 2: Привязываю метрику {counter_ids} к новой кампании...")
    
    result = call_api("campaigns", "update", {
        "Campaigns": [{
            "Id": NEW_CAMPAIGN_ID,
            "TextCampaign": {
                "CounterIds": {
                    "Items": counter_ids
                }
            }
        }]
    })
    
    if result:
        for r in result.get("UpdateResults", []):
            if "Errors" not in r or not r["Errors"]:
                print(f"   ✅ Метрика привязана!")
            else:
                for err in r.get("Errors", []):
                    print(f"   ❌ {err.get('Message')}")
else:
    print("\n⚠️ Счётчики не найдены в старой кампании")

# ============================================
# 3. Отправляем на модерацию (правильный формат!)
# ============================================
print(f"\n📤 Шаг 3: Отправляю объявления на модерацию...")
print(f"   IDs: {AD_IDS}")

# Правильный формат: SelectionCriteria.Ids
result = call_api("ads", "moderate", {
    "SelectionCriteria": {
        "Ids": AD_IDS
    }
})

if result:
    print(f"   ✅ Отправлено на модерацию!")

# ============================================
# 4. Проверяем статус
# ============================================
print(f"\n📋 Шаг 4: Проверяю статус объявлений...")

result = call_api("ads", "get", {
    "SelectionCriteria": {"Ids": AD_IDS},
    "FieldNames": ["Id", "Status", "State"]
})

if result:
    for ad in result.get("Ads", []):
        print(f"   [{ad['Id']}] Статус: {ad['Status']} | Состояние: {ad['State']}")

# ============================================
# 5. Проверяем корректировки устройств
# ============================================
print(f"\n📱 Шаг 5: Проверяю корректировки устройств...")

result = call_api("bidmodifiers", "get", {
    "SelectionCriteria": {"CampaignIds": [NEW_CAMPAIGN_ID]},
    "FieldNames": ["Id", "CampaignId", "Type"],
    "MobileAdjustmentFieldNames": ["BidModifier"],
    "TabletAdjustmentFieldNames": ["BidModifier"]
})

if result:
    mods = result.get("BidModifiers", [])
    if not mods:
        print("   ⚠️ Корректировок нет! Добавляю...")
        
        result = call_api("bidmodifiers", "add", {
            "BidModifiers": [
                {"CampaignId": NEW_CAMPAIGN_ID, "MobileAdjustment": {"BidModifier": 0}},
                {"CampaignId": NEW_CAMPAIGN_ID, "TabletAdjustment": {"BidModifier": 0}}
            ]
        })
        
        if result:
            for r in result.get("AddResults", []):
                if "Id" in r:
                    print(f"   ✅ Добавлено: ID {r['Id']}")
    else:
        for mod in mods:
            mod_type = mod.get("Type")
            if mod_type == "MOBILE_ADJUSTMENT":
                bm = mod.get("MobileAdjustment", {}).get("BidModifier")
                status = "✅ ОТКЛЮЧЕНО" if bm == 0 else f"⚠️ {bm}%"
                print(f"   Mobile: {status}")
            elif mod_type == "TABLET_ADJUSTMENT":
                bm = mod.get("TabletAdjustment", {}).get("BidModifier")
                status = "✅ ОТКЛЮЧЕНО" if bm == 0 else f"⚠️ {bm}%"
                print(f"   Tablet: {status}")

print("\n" + "=" * 60)
print("✅ ГОТОВО!")
print("=" * 60)
print(f"""
🔗 Новая кампания: https://direct.yandex.ru/dna/grid/campaigns/{NEW_CAMPAIGN_ID}
   
Осталось:
1. Проверить что модерация прошла
2. Запустить кампанию (включить)
""")

