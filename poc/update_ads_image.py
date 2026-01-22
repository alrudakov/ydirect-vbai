"""
Добавление картинки к существующим объявлениям через Ads.update
"""
from api_client import DirectAPIClient

client = DirectAPIClient()

# Наши данные
AD_IDS = [17555015717, 17555016846, 17555016849]
IMAGE_HASH = "cwsd3B7TdANy77zScJKtUw"  # Загруженная картинка 2.jpg

print("🖼️ Добавляю картинку к объявлениям...")
print(f"   Image hash: {IMAGE_HASH}")
print(f"   Объявления: {AD_IDS}")
print("-" * 60)

# Формируем запрос на update
ads_to_update = []
for ad_id in AD_IDS:
    ads_to_update.append({
        "Id": ad_id,
        "TextAd": {
            "AdImageHash": IMAGE_HASH
        }
    })

# Вызываем API
result = client._call("ads", "update", {
    "Ads": ads_to_update
})

print("\n📋 Результат:")
print("-" * 60)

update_results = result.get("UpdateResults", [])
for i, res in enumerate(update_results):
    ad_id = AD_IDS[i]
    if "Errors" in res and res["Errors"]:
        err = res["Errors"][0]
        print(f"❌ Ad {ad_id}: {err.get('Message')}")
    elif "Warnings" in res and res["Warnings"]:
        for w in res["Warnings"]:
            print(f"⚠️ Ad {ad_id}: {w.get('Message')}")
        print(f"✅ Ad {ad_id}: Обновлено (с предупреждением)")
    else:
        print(f"✅ Ad {ad_id}: Картинка добавлена!")

print("\n" + "-" * 60)
print("Готово! Проверь через view_ads.py")

