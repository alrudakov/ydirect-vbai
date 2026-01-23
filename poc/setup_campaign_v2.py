"""
🚀 Полная настройка кампании ExecAI IT (706570098)
- Проверка/добавление корректировок устройств
- Создание группы объявлений
- Добавление ключей
- Создание объявлений с картинкой
- Отправка на модерацию
"""
import requests
import json
import base64
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
        print(f"❌ Ошибка [{err.get('error_code')}]: {err.get('error_string')}")
        print(f"   {err.get('error_detail', '')}")
        return None
    
    return result.get("result", {})


print("=" * 60)
print(f"🚀 НАСТРОЙКА КАМПАНИИ EXECAI IT (ID: {CAMPAIGN_ID})")
print("=" * 60)

# ============================================
# 1. Проверяем корректировки устройств
# ============================================
print("\n📱 Шаг 1: Проверка корректировок устройств...")

result = call_api("bidmodifiers", "get", {
    "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
    "FieldNames": ["Id", "CampaignId", "Type"],
    "MobileAdjustmentFieldNames": ["BidModifier"],
    "TabletAdjustmentFieldNames": ["BidModifier"]
})

has_mobile = False
has_tablet = False

if result:
    for mod in result.get("BidModifiers", []):
        mod_type = mod.get("Type")
        if mod_type == "MOBILE_ADJUSTMENT":
            has_mobile = True
            print(f"   ✅ Mobile: BidModifier={mod.get('MobileAdjustment', {}).get('BidModifier')}")
        elif mod_type == "TABLET_ADJUSTMENT":
            has_tablet = True
            print(f"   ✅ Tablet: BidModifier={mod.get('TabletAdjustment', {}).get('BidModifier')}")

# Добавляем если нет
if not has_mobile or not has_tablet:
    print("   Добавляю недостающие корректировки...")
    mods = []
    if not has_mobile:
        mods.append({"CampaignId": CAMPAIGN_ID, "MobileAdjustment": {"BidModifier": 0}})
    if not has_tablet:
        mods.append({"CampaignId": CAMPAIGN_ID, "TabletAdjustment": {"BidModifier": 0}})
    
    result = call_api("bidmodifiers", "add", {"BidModifiers": mods})
    if result:
        for r in result.get("AddResults", []):
            if "Id" in r:
                print(f"   ✅ Добавлено: ID {r['Id']}")

# ============================================
# 2. Создаём группу объявлений
# ============================================
print("\n📁 Шаг 2: Создание группы объявлений...")

result = call_api("adgroups", "add", {
    "AdGroups": [{
        "Name": "DevOps Tools",
        "CampaignId": CAMPAIGN_ID,
        "RegionIds": [225]  # Россия
    }]
})

ad_group_id = None
if result:
    for r in result.get("AddResults", []):
        if "Id" in r:
            ad_group_id = r["Id"]
            print(f"   ✅ Группа создана: ID {ad_group_id}")
        elif "Errors" in r:
            # Возможно уже есть
            for err in r["Errors"]:
                print(f"   ⚠️ {err.get('Message')}")

# Если группа уже существует, получим её
if not ad_group_id:
    result = call_api("adgroups", "get", {
        "SelectionCriteria": {"CampaignIds": [CAMPAIGN_ID]},
        "FieldNames": ["Id", "Name"]
    })
    if result:
        groups = result.get("AdGroups", [])
        if groups:
            ad_group_id = groups[0]["Id"]
            print(f"   📁 Используем существующую группу: ID {ad_group_id}")

if not ad_group_id:
    print("   ❌ Не удалось создать/найти группу!")
    exit(1)

# ============================================
# 3. Добавляем ключевые слова
# ============================================
print("\n🔑 Шаг 3: Добавление ключевых слов...")

keywords = [
    "ai для devops",
    "ai devops",
    "kubectl ai",
    "kubernetes ai помощник",
    "chatgpt devops",
    "gpt для devops",
    "ai терминал",
    "ai ssh",
    "ai linux",
    "ai для сисадмина",
    "нейросеть для разработчика",
    "ai помощник программиста",
    "gpt-5",
    "claude ai"
]

keyword_items = [{"Keyword": kw, "AdGroupId": ad_group_id} for kw in keywords]

result = call_api("keywords", "add", {"Keywords": keyword_items})
if result:
    added = sum(1 for r in result.get("AddResults", []) if "Id" in r)
    print(f"   ✅ Добавлено ключей: {added}")

# ============================================
# 4. Загружаем картинку
# ============================================
print("\n🖼️ Шаг 4: Проверка/загрузка картинки...")

# Проверяем есть ли уже картинка
result = call_api("adimages", "get", {
    "SelectionCriteria": {},
    "FieldNames": ["AdImageHash", "Name"]
})

image_hash = None
if result:
    for img in result.get("AdImages", []):
        if "DevOps" in img.get("Name", ""):
            image_hash = img.get("AdImageHash")
            print(f"   ✅ Используем существующую: {image_hash[:15]}...")
            break

# Если нет — загружаем
if not image_hash:
    img_path = Path("../Creative/IT/DevOps1/2.jpg")
    if img_path.exists():
        with open(img_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        result = call_api("adimages", "add", {
            "AdImages": [{
                "ImageData": img_data,
                "Name": "DevOps Terminal"
            }]
        })
        
        if result:
            for r in result.get("AddResults", []):
                if "AdImageHash" in r:
                    image_hash = r["AdImageHash"]
                    print(f"   ✅ Загружена: {image_hash[:15]}...")

# ============================================
# 5. Создаём объявления
# ============================================
print("\n📝 Шаг 5: Создание объявлений...")

ads = [
    {
        "title": "AI для DevOps",
        "title2": "Kubectl через чат",
        "text": "Делегируй рутину ИИ. SSH, логи, деплой - всё через чат. Попробуй бесплатно.",
        "href": "https://execai.ru/?utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2&utm_content=devops"
    },
    {
        "title": "GPT-5 и Claude для DevOps",
        "title2": "Без VPN, оплата картой РФ",
        "text": "Топовые модели и SSH интеграция. Управляй инфрой через чат.",
        "href": "https://execai.ru/?utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2&utm_content=gpt5"
    },
    {
        "title": "AI видит твой терминал",
        "title2": "Скажи что случилось - найдёт",
        "text": "Подключи SSH, покажи логи. AI сам разберётся и поможет починить.",
        "href": "https://execai.ru/?utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2&utm_content=terminal"
    }
]

ad_ids = []
for ad in ads:
    ad_data = {
        "AdGroupId": ad_group_id,
        "TextAd": {
            "Title": ad["title"],
            "Title2": ad["title2"],
            "Text": ad["text"],
            "Href": ad["href"],
            "Mobile": "NO"
        }
    }
    
    if image_hash:
        ad_data["TextAd"]["AdImageHash"] = image_hash
    
    result = call_api("ads", "add", {"Ads": [ad_data]})
    
    if result:
        for r in result.get("AddResults", []):
            if "Id" in r:
                ad_ids.append(r["Id"])
                print(f"   ✅ {ad['title']}: ID {r['Id']}")
            elif "Errors" in r:
                for err in r["Errors"]:
                    print(f"   ❌ {ad['title']}: {err.get('Message')}")

# ============================================
# 6. Отправляем на модерацию
# ============================================
if ad_ids:
    print("\n📤 Шаг 6: Отправка на модерацию...")
    
    result = call_api("ads", "moderate", {"Ids": ad_ids})
    if result:
        print(f"   ✅ Отправлено: {len(ad_ids)} объявлений")

# ============================================
# Итог
# ============================================
print("\n" + "=" * 60)
print("📊 ИТОГ")
print("=" * 60)
print(f"""
Кампания:    ID {CAMPAIGN_ID}
Группа:      ID {ad_group_id}
Ключей:      {len(keywords)}
Объявлений:  {len(ad_ids)}
Картинка:    {image_hash[:15] + '...' if image_hash else 'нет'}

🔗 https://direct.yandex.ru/dna/grid/campaigns/{CAMPAIGN_ID}
""")

