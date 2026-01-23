"""
🗑️ Удаление черновиковой группы и её объявлений
"""
import requests
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

# Черновик для удаления
DRAFT_GROUP_ID = 5704738196
DRAFT_AD_IDS = [17556256649, 17556256652, 17556256654]

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
print("🗑️ УДАЛЕНИЕ ЧЕРНОВИКА")
print("=" * 60)

# 1. Удаляем объявления
print(f"\n📝 Шаг 1: Удаляю объявления {DRAFT_AD_IDS}...")

result = call_api("ads", "delete", {
    "SelectionCriteria": {
        "Ids": DRAFT_AD_IDS
    }
})

if result:
    for r in result.get("DeleteResults", []):
        if "Id" in r:
            print(f"   ✅ Удалено: {r['Id']}")
        elif "Errors" in r:
            for err in r["Errors"]:
                print(f"   ❌ {err.get('Message')}")

# 2. Удаляем ключевые слова группы
print(f"\n🔑 Шаг 2: Удаляю ключевые слова группы...")

# Сначала получаем ID ключей
result = call_api("keywords", "get", {
    "SelectionCriteria": {"AdGroupIds": [DRAFT_GROUP_ID]},
    "FieldNames": ["Id"]
})

if result:
    keyword_ids = [kw["Id"] for kw in result.get("Keywords", [])]
    
    if keyword_ids:
        result = call_api("keywords", "delete", {
            "SelectionCriteria": {"Ids": keyword_ids}
        })
        
        if result:
            deleted = sum(1 for r in result.get("DeleteResults", []) if "Id" in r)
            print(f"   ✅ Удалено ключей: {deleted}")
    else:
        print("   Ключей нет")

# 3. Удаляем группу
print(f"\n📁 Шаг 3: Удаляю группу {DRAFT_GROUP_ID}...")

result = call_api("adgroups", "delete", {
    "SelectionCriteria": {
        "Ids": [DRAFT_GROUP_ID]
    }
})

if result:
    for r in result.get("DeleteResults", []):
        if "Id" in r:
            print(f"   ✅ Группа удалена: {r['Id']}")
        elif "Errors" in r:
            for err in r["Errors"]:
                print(f"   ❌ {err.get('Message')}")

print("\n" + "=" * 60)
print("✅ Черновик удалён!")
print("=" * 60)

