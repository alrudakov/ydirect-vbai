"""
📋 Проверка объявлений и групп кампании
"""
import requests
from pathlib import Path

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
        err = result["error"]
        print(f"❌ Ошибка: {err.get('error_string')}")
        return None
    
    return result.get("result", {})

print("=" * 60)
print(f"📋 ПРОВЕРКА КАМПАНИИ {CAMPAIGN_ID}")
print("=" * 60)

# 1. Получаем группы
print("\n📁 ГРУППЫ:")
print("-" * 40)

result = call_api("adgroups", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Name", "Status", "RegionIds"]
})

groups = {}
if result:
    for g in result.get("AdGroups", []):
        gid = g["Id"]
        groups[gid] = g
        print(f"   [{gid}] {g['Name']}")
        print(f"       Статус: {g['Status']}")

# 2. Получаем объявления
print("\n📝 ОБЪЯВЛЕНИЯ:")
print("-" * 40)

result = call_api("ads", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "AdGroupId", "Status", "State"],
    "TextAdFieldNames": ["Title", "AdImageHash"]
})

if result:
    ads = result.get("Ads", [])
    if not ads:
        print("   ❌ Объявлений нет!")
    else:
        for ad in ads:
            ad_id = ad["Id"]
            group_id = ad["AdGroupId"]
            title = ad.get("TextAd", {}).get("Title", "N/A")
            status = ad["Status"]
            state = ad["State"]
            has_img = "🖼️" if ad.get("TextAd", {}).get("AdImageHash") else "—"
            
            print(f"   [{ad_id}] {title}")
            print(f"       Группа: {group_id}")
            print(f"       Статус: {status} | Состояние: {state} | Картинка: {has_img}")

# 3. Получаем ключевые слова
print("\n🔑 КЛЮЧЕВЫЕ СЛОВА:")
print("-" * 40)

result = call_api("keywords", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "AdGroupId", "Keyword", "Status"]
})

if result:
    keywords = result.get("Keywords", [])
    if not keywords:
        print("   ❌ Ключевых слов нет!")
    else:
        # Группируем по группам
        by_group = {}
        for kw in keywords:
            gid = kw["AdGroupId"]
            if gid not in by_group:
                by_group[gid] = []
            by_group[gid].append(kw)
        
        for gid, kws in by_group.items():
            print(f"\n   Группа {gid}:")
            for kw in kws[:5]:  # первые 5
                print(f"      - {kw['Keyword']} ({kw['Status']})")
            if len(kws) > 5:
                print(f"      ... и ещё {len(kws) - 5}")

print("\n" + "=" * 60)

