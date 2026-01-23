"""
📱 Проверка и добавление корректировок устройств
"""
import requests
import json
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

NEW_CAMPAIGN_ID = 706570098

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
print(f"📱 КОРРЕКТИРОВКИ УСТРОЙСТВ - Кампания {NEW_CAMPAIGN_ID}")
print("=" * 60)

# Получаем корректировки с правильным Levels
print("\n📋 Проверяю существующие корректировки...")

result = call_api("bidmodifiers", "get", {
    "SelectionCriteria": {
        "CampaignIds": [NEW_CAMPAIGN_ID],
        "Levels": ["CAMPAIGN"]  # Обязательный параметр!
    },
    "FieldNames": ["Id", "CampaignId", "Type"],
    "MobileAdjustmentFieldNames": ["BidModifier"],
    "TabletAdjustmentFieldNames": ["BidModifier"]
})

has_mobile = False
has_tablet = False

if result:
    mods = result.get("BidModifiers", [])
    
    if not mods:
        print("   Корректировок нет")
    else:
        for mod in mods:
            mod_type = mod.get("Type")
            
            if mod_type == "MOBILE_ADJUSTMENT":
                has_mobile = True
                bm = mod.get("MobileAdjustment", {}).get("BidModifier", "?")
                status = "🚫 ОТКЛЮЧЕНО" if bm == 0 else f"⚠️ Коэф: {bm}"
                print(f"   Mobile: {status}")
                
            elif mod_type == "TABLET_ADJUSTMENT":
                has_tablet = True
                bm = mod.get("TabletAdjustment", {}).get("BidModifier", "?")
                status = "🚫 ОТКЛЮЧЕНО" if bm == 0 else f"⚠️ Коэф: {bm}"
                print(f"   Tablet: {status}")

# Добавляем недостающие
to_add = []

if not has_mobile:
    print("\n   ➕ Mobile не найден, добавляю...")
    to_add.append({
        "CampaignId": NEW_CAMPAIGN_ID,
        "MobileAdjustment": {"BidModifier": 0}
    })

if not has_tablet:
    print("   ➕ Tablet не найден, добавляю...")
    to_add.append({
        "CampaignId": NEW_CAMPAIGN_ID,
        "TabletAdjustment": {"BidModifier": 0}
    })

if to_add:
    result = call_api("bidmodifiers", "add", {"BidModifiers": to_add})
    
    if result:
        for r in result.get("AddResults", []):
            if "Id" in r:
                print(f"   ✅ Добавлено: ID {r['Id']}")
            elif "Errors" in r:
                for err in r["Errors"]:
                    print(f"   ❌ {err.get('Message')}")

# Финальная проверка
print("\n📋 Финальный статус:")

result = call_api("bidmodifiers", "get", {
    "SelectionCriteria": {
        "CampaignIds": [NEW_CAMPAIGN_ID],
        "Levels": ["CAMPAIGN"]
    },
    "FieldNames": ["Id", "CampaignId", "Type"],
    "MobileAdjustmentFieldNames": ["BidModifier"],
    "TabletAdjustmentFieldNames": ["BidModifier"]
})

if result:
    for mod in result.get("BidModifiers", []):
        mod_type = mod.get("Type")
        
        if mod_type == "MOBILE_ADJUSTMENT":
            bm = mod.get("MobileAdjustment", {}).get("BidModifier", "?")
            status = "🚫 ОТКЛЮЧЕНО (только десктоп)" if bm == 0 else f"Коэф: {bm}"
            print(f"   📱 Mobile: {status}")
            
        elif mod_type == "TABLET_ADJUSTMENT":
            bm = mod.get("TabletAdjustment", {}).get("BidModifier", "?")
            status = "🚫 ОТКЛЮЧЕНО (только десктоп)" if bm == 0 else f"Коэф: {bm}"
            print(f"   📲 Tablet: {status}")

print("\n" + "=" * 60)
print("✅ Готово! Показы только на десктопах.")
print("=" * 60)

