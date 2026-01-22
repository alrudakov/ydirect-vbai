"""Просмотр объявлений через API"""
import json
from api_client import DirectAPIClient

client = DirectAPIClient()

# Получаем объявления
print("📝 Получаю объявления...")
print("-" * 60)

result = client._call("ads", "get", {
    "SelectionCriteria": {
        "Ids": [17555015717, 17555016846, 17555016849]
    },
    "FieldNames": ["Id", "State", "Status", "Type", "AdGroupId"],
    "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "DisplayUrlPath", "AdImageHash", "SitelinkSetId"]
})

ads = result.get("Ads", [])

if not ads:
    print("Объявлений не найдено")
else:
    for ad in ads:
        print(f"\n📝 ID: {ad.get('Id')}")
        print(f"   Статус: {ad.get('Status')} | Состояние: {ad.get('State')}")
        print(f"   Тип: {ad.get('Type')}")
        
        text_ad = ad.get("TextAd", {})
        if text_ad:
            print(f"   Title: {text_ad.get('Title')}")
            print(f"   Title2: {text_ad.get('Title2')}")
            print(f"   Text: {text_ad.get('Text')}")
            print(f"   Href: {text_ad.get('Href')}")
            
            image_hash = text_ad.get("AdImageHash")
            if image_hash:
                print(f"   🖼️ AdImageHash: {image_hash}")
            else:
                print(f"   🖼️ AdImageHash: ❌ НЕТ КАРТИНКИ")
            
            video_ext = text_ad.get("VideoExtension")
            if video_ext:
                print(f"   🎬 VideoExtension: {video_ext}")
            else:
                print(f"   🎬 VideoExtension: ❌ НЕТ ВИДЕО")

print("\n" + "-" * 60)
print("Полный JSON:")
print(json.dumps(result, indent=2, ensure_ascii=False))

