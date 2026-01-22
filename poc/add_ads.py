#!/usr/bin/env python3
"""
📝 Добавление объявлений к существующей группе

Использование:
    python add_ads.py --group-id 5704219166 --config config/execai_it_campaign.json

Что делает:
    1. Загружает картинки (если указаны и существуют)
    2. Загружает видео (если указано и существует)
    3. Создаёт объявления с привязкой креативов
    
НЕ трогает: кампанию, группу, ключевые слова
"""
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

from api_client import DirectAPIClient, DirectAPIError


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Добавить объявления к группе")
    parser.add_argument("--group-id", type=int, required=True, help="ID группы объявлений")
    parser.add_argument("--config", type=str, default="config/execai_it_campaign.json", help="Путь к конфигу")
    parser.add_argument("--skip-images", action="store_true", help="Пропустить загрузку картинок")
    parser.add_argument("--skip-video", action="store_true", help="Пропустить загрузку видео")
    parser.add_argument("--no-mod", action="store_true", help="Не отправлять на модерацию")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("📝 ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЙ")
    print("=" * 60)
    print(f"Группа ID: {args.group_id}")
    print(f"Конфиг: {args.config}")
    print("=" * 60 + "\n")
    
    # Загружаем конфиг
    config = load_config(args.config)
    client = DirectAPIClient()
    
    results = {
        "group_id": args.group_id,
        "image_hashes": [],
        "video_id": None,
        "video_creative_id": None,
        "ad_ids": [],
        "errors": []
    }
    
    # === ШАГ 1: Загрузка картинок ===
    if not args.skip_images:
        print("🖼️ ШАГ 1: Загрузка изображений")
        print("-" * 40)
        
        images = config.get("creatives", {}).get("images", [])
        
        for i, img in enumerate(images, 1):
            path = img.get("path")
            if not path:
                continue
            
            file_path = Path(path)
            if not file_path.exists():
                print(f"  ⚠️ [{i}] Файл не найден: {path}")
                continue
            
            # Проверка размера
            try:
                from PIL import Image
                with Image.open(file_path) as pil_img:
                    w, h = pil_img.size
                    ratio = w / h
                    
                    # Проверка соотношения сторон
                    valid_ratios = [
                        (0.95, 1.05),   # 1:1 (квадрат)
                        (1.7, 1.8),     # 16:9
                        (1.3, 1.4),     # 4:3
                    ]
                    
                    is_valid = any(low <= ratio <= high for low, high in valid_ratios)
                    
                    if not is_valid:
                        print(f"  ❌ [{i}] Неверное соотношение сторон: {w}×{h} (ratio={ratio:.2f})")
                        print(f"      Нужно: 1:1 (квадрат), 16:9 или 4:3")
                        results["errors"].append(f"Image {i}: wrong aspect ratio {w}×{h}")
                        continue
                    
                    if w < 450 or h < 450:
                        print(f"  ❌ [{i}] Слишком маленькая: {w}×{h} (мин 450×450)")
                        results["errors"].append(f"Image {i}: too small {w}×{h}")
                        continue
                        
            except ImportError:
                print("  ⚠️ PIL не установлен, пропускаю проверку размера")
            except Exception as e:
                print(f"  ⚠️ Ошибка проверки: {e}")
            
            print(f"  [{i}/{len(images)}] {img.get('name', file_path.name)}")
            
            try:
                image_hash = client.upload_image(
                    image_path=str(file_path),
                    name=img.get("name")
                )
                results["image_hashes"].append(image_hash)
            except DirectAPIError as e:
                print(f"  ❌ Ошибка: {e.message}")
                results["errors"].append(f"Image {i}: {e.message}")
    else:
        print("🖼️ ШАГ 1: Пропущен (--skip-images)")
    
    # === ШАГ 2: Загрузка видео ===
    if not args.skip_video:
        print("\n🎬 ШАГ 2: Загрузка видео")
        print("-" * 40)
        
        video = config.get("creatives", {}).get("video", {})
        path = video.get("path")
        
        if path:
            file_path = Path(path)
            if file_path.exists():
                print(f"  Загружаю: {file_path.name}")
                
                try:
                    # Загружаем видео
                    video_id = client.upload_video_binary(
                        video_path=str(file_path),
                        name=video.get("name")
                    )
                    results["video_id"] = video_id
                    
                    # Создаём креатив
                    print(f"  Создаю креатив...")
                    creative_id = client.create_video_extension_creative(video_id)
                    results["video_creative_id"] = creative_id
                    
                except DirectAPIError as e:
                    print(f"  ❌ Ошибка: {e.message}")
                    results["errors"].append(f"Video: {e.message}")
            else:
                print(f"  ⚠️ Файл не найден: {path}")
        else:
            print("  ℹ️ Видео не указано в конфиге")
    else:
        print("\n🎬 ШАГ 2: Пропущен (--skip-video)")
    
    # === ШАГ 3: Создание объявлений ===
    print("\n📝 ШАГ 3: Создание объявлений")
    print("-" * 40)
    
    ads_config = config.get("ads", [])
    
    if not ads_config:
        print("  ⚠️ Объявления не указаны в конфиге")
    else:
        image_hashes = results.get("image_hashes", [])
        video_creative_id = results.get("video_creative_id")
        
        for i, ad in enumerate(ads_config, 1):
            print(f"\n  [{i}/{len(ads_config)}] {ad['title'][:30]}...")
            
            # Берём картинку если есть
            image_hash = None
            if image_hashes:
                image_hash = image_hashes[0]  # Одна картинка на все объявления
            
            try:
                ad_id = client.create_text_ad(
                    ad_group_id=args.group_id,
                    title=ad["title"],
                    text=ad["text"],
                    href=ad["href"],
                    title2=ad.get("title2"),
                    display_url=ad.get("display_url"),
                    image_hash=image_hash,
                    video_creative_id=video_creative_id
                )
                results["ad_ids"].append(ad_id)
                
            except DirectAPIError as e:
                print(f"  ❌ Ошибка: {e.message}")
                results["errors"].append(f"Ad {i}: {e.message}")
    
    # === ШАГ 4: Модерация ===
    if not args.no_mod and results["ad_ids"]:
        print("\n📤 ШАГ 4: Отправка на модерацию")
        print("-" * 40)
        try:
            client.moderate_ads(results["ad_ids"])
        except DirectAPIError as e:
            print(f"  ❌ Ошибка: {e.message}")
            results["errors"].append(f"Moderation: {e.message}")
    
    # === ИТОГ ===
    print("\n" + "=" * 60)
    print("📊 ИТОГ")
    print("=" * 60)
    
    video_status = "✅" if results['video_creative_id'] else "—"
    
    print(f"""
🖼️ Картинок:        {len(results['image_hashes'])}
🎬 Видео:           {video_status} {results.get('video_creative_id', '')}
✅ Объявлений:      {len(results['ad_ids'])}
❌ Ошибок:          {len(results['errors'])}
""")
    
    if results["ad_ids"]:
        print("📝 ID объявлений:")
        for ad_id in results["ad_ids"]:
            print(f"   - {ad_id}")
    
    if results["errors"]:
        print("\n⚠️ Ошибки:")
        for err in results["errors"]:
            print(f"   - {err}")
    
    # Сохраняем результат
    result_file = Path("logs") / f"ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_file.parent.mkdir(exist_ok=True)
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результат: {result_file}")
    
    return 0 if not results["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())

