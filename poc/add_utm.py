"""
🔗 Добавление UTM меток ко ВСЕМ объявлениям кампании
"""
import requests
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"
CAMPAIGN_ID = 706570098

# UTM параметры
UTM_BASE = "utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2"

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
        print(f"❌ {result['error'].get('error_string')}")
        return None
    return result.get("result", {})

print("=" * 60)
print("🔗 ДОБАВЛЕНИЕ UTM МЕТОК")
print("=" * 60)

# 1. Получаем все объявления
print("\n📝 Получаю объявления...")

result = call_api("ads", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "Status"],
    "TextAdFieldNames": ["Title", "Href"]
})

if not result:
    print("❌ Не удалось получить объявления")
    exit(1)

ads = result.get("Ads", [])
print(f"   Найдено: {len(ads)} объявлений")

# 2. Обновляем каждое объявление
print("\n🔄 Обновляю UTM метки...")
print("-" * 40)

updated = 0
skipped = 0

for ad in ads:
    ad_id = ad["Id"]
    status = ad["Status"]
    text_ad = ad.get("TextAd", {})
    title = text_ad.get("Title", "N/A")
    href = text_ad.get("Href", "")
    
    # Пропускаем черновики
    if status == "DRAFT":
        print(f"   [{ad_id}] {title[:25]}... — ЧЕРНОВИК, пропуск")
        skipped += 1
        continue
    
    # Проверяем есть ли уже UTM
    if "utm_source" in href:
        print(f"   [{ad_id}] {title[:25]}... — UTM уже есть ✓")
        skipped += 1
        continue
    
    # Формируем новый href с UTM
    # Генерируем utm_content из title (транслит)
    content_id = ad_id
    
    # Добавляем UTM + динамический {keyword}
    separator = "&" if "?" in href else "?"
    new_href = f"{href}{separator}{UTM_BASE}&utm_content=ad{content_id}&utm_term={{keyword}}"
    
    # Обновляем
    update_result = call_api("ads", "update", {
        "Ads": [{
            "Id": ad_id,
            "TextAd": {
                "Href": new_href
            }
        }]
    })
    
    if update_result:
        errors = False
        for r in update_result.get("UpdateResults", []):
            if "Errors" in r and r["Errors"]:
                for err in r["Errors"]:
                    print(f"   [{ad_id}] ❌ {err.get('Message')}")
                errors = True
        
        if not errors:
            print(f"   [{ad_id}] {title[:25]}... — UTM добавлен ✅")
            updated += 1

# 3. Итог
print("\n" + "=" * 60)
print("📊 ИТОГ")
print("=" * 60)
print(f"""
Всего объявлений:  {len(ads)}
Обновлено:         {updated}
Пропущено:         {skipped}

📈 Что увидишь в Метрике:
   • utm_source=yandex — источник
   • utm_medium=cpc — тип трафика
   • utm_campaign=execai_it_v2 — кампания
   • utm_content=ad12345 — ID объявления
   • utm_term={{keyword}} — ключевое слово (динамически)

🔗 Метрика → Отчёты → Источники → UTM-метки
""")

