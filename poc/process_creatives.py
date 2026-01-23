"""
🖼️ Обработка креативов и добавление в кампанию
1. Конвертация в 1080x1080 с чёрным фоном
2. Загрузка в Директ
3. Создание объявлений
"""
from PIL import Image
import os
import base64
import requests
from pathlib import Path

TOKEN = Path("token.txt").read_text().strip()
BASE_URL = "https://api.direct.yandex.com/json/v5"

CAMPAIGN_ID = 706570098
AD_GROUP_ID = 5704738217  # Группа на модерации

ORIG_DIR = Path(r"C:\Users\fatal\Desktop\Projects\ydirect-vbai\Creative\IT\orig")
OUTPUT_DIR = Path(r"C:\Users\fatal\Desktop\Projects\ydirect-vbai\Creative\IT\ready")
OUTPUT_DIR.mkdir(exist_ok=True)

# Креативы с описаниями
CREATIVES = {
    "20serv1chat.jpg": {
        "name": "20 серверов — один чат",
        "title": "20 серверов — один чат",
        "title2": "Профили SSH в ExecAI",
        "text": "Добавь все сервера. Переключайся между prod/stage одним кликом. AI запомнит.",
    },
    "bastion.jpg": {
        "name": "SSH через бастион",
        "title": "SSH через Jump-host",
        "title2": "Бастион? Не проблема",
        "text": "Настрой SSH через бастион один раз. AI будет ходить сам.",
    },
    "monitor.jpg": {
        "name": "Мониторинг 5 серверов",
        "title": "Проверь все сервера сразу",
        "title2": "5 профилей в одном чате",
        "text": "Один запрос — AI проверит load на всех серверах. Покажет кто перегружен.",
    },
    "multi.jpg": {
        "name": "Jira + Git + SSH",
        "title": "Jira + Git + SSH = один чат",
        "title2": "Три инструмента сразу",
        "text": "Возьми задачу, создай ветку, задеплой. Всё в одном диалоге.",
    },
    "nginx502promo.jpg": {
        "name": "Nginx 502 фикс",
        "title": "Nginx 502? AI разберётся",
        "title2": "Скажи что сломалось",
        "text": "AI зайдёт на сервер, найдёт причину, перезапустит сервис. Ты отдыхаешь.",
    },
}

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

def convert_to_square(input_path: Path, output_path: Path, size: int = 1080):
    """Конвертация в квадрат с чёрным фоном"""
    img = Image.open(input_path)
    w, h = img.size
    
    # Создаём квадрат с тёмным фоном (как терминал)
    square = Image.new('RGB', (size, size), (18, 18, 24))
    
    # Масштабируем чтобы вписать
    ratio = min(size / w, size / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Центрируем
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    square.paste(img_resized, (x, y))
    
    square.save(output_path, 'JPEG', quality=95)
    return output_path

print("=" * 60)
print("🖼️ ОБРАБОТКА КРЕАТИВОВ")
print("=" * 60)

# 1. Проверяем размеры и конвертируем
print("\n📐 Шаг 1: Проверка и конвертация")
print("-" * 40)

for filename in CREATIVES.keys():
    orig_path = ORIG_DIR / filename
    if not orig_path.exists():
        print(f"   ⚠️ {filename} — не найден")
        continue
    
    img = Image.open(orig_path)
    print(f"   {filename}: {img.size[0]}x{img.size[1]}")
    
    # Конвертируем
    output_path = OUTPUT_DIR / filename
    convert_to_square(orig_path, output_path)
    print(f"      → {output_path.name} (1080x1080) ✅")

# 2. Загружаем в Директ
print("\n📤 Шаг 2: Загрузка в Яндекс Директ")
print("-" * 40)

image_hashes = {}

for filename, info in CREATIVES.items():
    ready_path = OUTPUT_DIR / filename
    if not ready_path.exists():
        continue
    
    with open(ready_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    result = call_api("adimages", "add", {
        "AdImages": [{
            "ImageData": img_data,
            "Name": info["name"]
        }]
    })
    
    if result:
        for r in result.get("AddResults", []):
            if "AdImageHash" in r:
                h = r["AdImageHash"]
                image_hashes[filename] = h
                print(f"   ✅ {info['name']}: {h[:15]}...")
            elif "Errors" in r:
                for err in r["Errors"]:
                    print(f"   ❌ {info['name']}: {err.get('Message')}")

# 3. Создаём объявления
print("\n📝 Шаг 3: Создание объявлений")
print("-" * 40)

UTM = "utm_source=yandex&utm_medium=cpc&utm_campaign=execai_it_v2"
ad_ids = []

for filename, info in CREATIVES.items():
    if filename not in image_hashes:
        continue
    
    href = f"https://execai.ru/?{UTM}&utm_content={filename.replace('.jpg', '')}"
    
    result = call_api("ads", "add", {
        "Ads": [{
            "AdGroupId": AD_GROUP_ID,
            "TextAd": {
                "Title": info["title"],
                "Title2": info["title2"],
                "Text": info["text"],
                "Href": href,
                "AdImageHash": image_hashes[filename],
                "Mobile": "NO"
            }
        }]
    })
    
    if result:
        for r in result.get("AddResults", []):
            if "Id" in r:
                ad_ids.append(r["Id"])
                print(f"   ✅ {info['title']}: ID {r['Id']}")
            elif "Errors" in r:
                for err in r["Errors"]:
                    print(f"   ❌ {info['title']}: {err.get('Message')}")

# 4. Модерация
if ad_ids:
    print("\n📤 Шаг 4: Отправка на модерацию")
    print("-" * 40)
    
    result = call_api("ads", "moderate", {
        "SelectionCriteria": {"Ids": ad_ids}
    })
    
    if result:
        print(f"   ✅ {len(ad_ids)} объявлений отправлено!")

# Итог
print("\n" + "=" * 60)
print("📊 ИТОГ")
print("=" * 60)
print(f"""
Конвертировано:  {len(image_hashes)} картинок
Загружено:       {len(image_hashes)} изображений
Создано:         {len(ad_ids)} объявлений

🔗 https://direct.yandex.ru/dna/grid/campaigns/{CAMPAIGN_ID}
""")

