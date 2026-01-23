#!/usr/bin/env python3
"""
🚀 Создание кампании Яндекс Директ из JSON конфига

Использование:
    python run_campaign.py config/execai_it_campaign.json

Что делает (пошагово):
    1. Читает JSON конфиг
    2. Создаёт кампанию
    3. Создаёт группу объявлений
    4. Добавляет ключевые слова
    5. Загружает изображения (AdImages.add)
    6. Загружает видео (AdVideos.add → Creatives.add)
    7. Создаёт объявления (TextAd с картинками и видео)
    8. Отправляет на модерацию

Логи сохраняются в ./logs/
"""
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from api_client import DirectAPIClient, DirectAPIError


# =========== LOGGING ===========

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Настройка логирования в файл + консоль"""
    Path(log_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"campaign_{timestamp}.log"
    
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    datefmt = "%H:%M:%S"
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info(f"📄 Лог: {log_file}")
    return logger


# =========== MAIN ===========

class CampaignCreator:
    """Создание кампании из JSON конфига"""
    
    def __init__(self, config_path: str, sandbox: bool = False):
        self.config = self._load_config(config_path)
        self.config_dir = Path(config_path).parent
        self.client = DirectAPIClient(sandbox=sandbox)
        
        # Результаты (для отчёта)
        self.results = {
            "campaign_id": None,
            "ad_group_id": None,
            "ad_ids": [],
            "keyword_ids": [],
            "image_hashes": [],
            "video_id": None,
            "video_creative_id": None,
            "errors": []
        }
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Загрузка и валидация конфига"""
        config_file = Path(path)
        if not config_file.exists():
            raise FileNotFoundError(f"Конфиг не найден: {path}")
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        required = ["campaign", "ad_group", "ads"]
        for key in required:
            if key not in config:
                raise ValueError(f"Отсутствует обязательный раздел: {key}")
        
        logging.info(f"📋 Конфиг загружен: {path}")
        return config
    
    def _resolve_path(self, path: str) -> Path:
        """Резолвит путь относительно директории конфига"""
        p = Path(path)
        if p.is_absolute():
            return p
        # Относительно директории конфига
        resolved = self.config_dir / path
        if resolved.exists():
            return resolved
        # Или относительно cwd
        return Path(path)
    
    def run(self, skip_moderation: bool = False) -> Dict[str, Any]:
        """Полный цикл создания кампании"""
        print("\n" + "=" * 60)
        print("🚀 СОЗДАНИЕ КАМПАНИИ ЯНДЕКС ДИРЕКТ")
        print("=" * 60 + "\n")
        
        try:
            # 1. Кампания
            self._create_campaign()
            
            # 1.5 Отключаем мобильные/планшеты если указано
            self._setup_device_targeting()
            
            # 2. Группа объявлений
            self._create_ad_group()
            
            # 3. Ключевые слова
            self._add_keywords()
            
            # 4. Изображения
            self._upload_images()
            
            # 5. Видео (цепочка: AdVideos → Creatives)
            self._upload_video()
            
            # 6. Объявления
            self._create_ads()
            
            # 7. Модерация
            if not skip_moderation and self.results["ad_ids"]:
                self._send_to_moderation()
            
            self._print_summary()
            
        except DirectAPIError as e:
            logging.error(f"❌ Ошибка API: {e}")
            self.results["errors"].append(str(e))
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")
            self.results["errors"].append(str(e))
            raise
        
        return self.results
    
    def _create_campaign(self):
        """Шаг 1: Создание кампании"""
        print("\n📢 ШАГ 1: Создание кампании")
        print("-" * 40)
        
        cfg = self.config["campaign"]
        
        campaign_id = self.client.create_campaign(
            name=cfg["name"],
            start_date=cfg["start_date"],
            daily_budget_rub=cfg["daily_budget_rub"],
            negative_keywords=cfg.get("negative_keywords", [])
        )
        
        self.results["campaign_id"] = campaign_id
    
    def _setup_device_targeting(self):
        """Шаг 1.5: Настройка таргетинга по устройствам"""
        targeting = self.config.get("targeting", {})
        devices = targeting.get("devices", [])
        
        # Если указан только DESKTOP - отключаем мобильные и планшеты
        if devices == ["DESKTOP"]:
            print("\n📱 ШАГ 1.5: Отключение мобильных и планшетов")
            print("-" * 40)
            
            modifier_ids = self.client.disable_mobile_and_tablet(
                self.results["campaign_id"]
            )
            self.results["bid_modifier_ids"] = modifier_ids
        
        # Минус-площадки
        excluded = targeting.get("excluded_placements", [])
        if excluded:
            print(f"\n🚫 Добавляю {len(excluded)} минус-площадок")
            self.client.add_excluded_placements(
                self.results["campaign_id"],
                excluded
            )
    
    def _create_ad_group(self):
        """Шаг 2: Создание группы объявлений"""
        print("\n📁 ШАГ 2: Создание группы объявлений")
        print("-" * 40)
        
        cfg = self.config["ad_group"]
        
        group_id = self.client.create_ad_group(
            campaign_id=self.results["campaign_id"],
            name=cfg["name"],
            region_ids=cfg.get("regions", [225])
        )
        
        self.results["ad_group_id"] = group_id
    
    def _add_keywords(self):
        """Шаг 3: Добавление ключевых слов"""
        print("\n🔑 ШАГ 3: Добавление ключевых слов")
        print("-" * 40)
        
        cfg = self.config["ad_group"]
        keywords = cfg.get("keywords", [])
        
        if not keywords:
            logging.info("ℹ️ Ключевые слова не указаны, пропускаю")
            return
        
        bid = self.config.get("bidding", {}).get("max_cpc_rub")
        
        keyword_ids = self.client.add_keywords(
            ad_group_id=self.results["ad_group_id"],
            keywords=keywords,
            bid_rub=bid
        )
        
        self.results["keyword_ids"] = keyword_ids
    
    def _upload_images(self):
        """Шаг 4: Загрузка изображений"""
        print("\n🖼️ ШАГ 4: Загрузка изображений")
        print("-" * 40)
        
        creatives = self.config.get("creatives", {})
        images = creatives.get("images", [])
        
        if not images:
            logging.info("ℹ️ Изображения не указаны, пропускаю")
            return
        
        for i, img in enumerate(images, 1):
            path = img.get("path")
            if not path:
                continue
            
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                logging.warning(f"⚠️ [{i}] Файл не найден: {path}")
                continue
            
            print(f"  [{i}/{len(images)}] {img.get('name', resolved_path.name)}")
            
            try:
                image_hash = self.client.upload_image(
                    image_path=str(resolved_path),
                    name=img.get("name")
                )
                self.results["image_hashes"].append(image_hash)
                
            except DirectAPIError as e:
                logging.error(f"  ❌ Ошибка: {e.message}")
                self.results["errors"].append(f"Image #{i}: {e.message}")
    
    def _upload_video(self):
        """Шаг 5: Загрузка видео (AdVideos → Creatives)"""
        print("\n🎬 ШАГ 5: Загрузка видео")
        print("-" * 40)
        
        creatives = self.config.get("creatives", {})
        video = creatives.get("video", {})
        
        if not video or not video.get("path"):
            logging.info("ℹ️ Видео не указано, пропускаю")
            return
        
        path = video.get("path")
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            logging.warning(f"⚠️ Видео не найдено: {path}")
            return
        
        try:
            # Шаг 5.1: Загружаем видео → получаем VideoId
            print(f"  Загружаю: {resolved_path.name}")
            video_id = self.client.upload_video_binary(
                video_path=str(resolved_path),
                name=video.get("name")
            )
            self.results["video_id"] = video_id
            
            # Шаг 5.2: Создаём креатив → получаем CreativeId
            print(f"  Создаю креатив для видеодополнения...")
            creative_id = self.client.create_video_extension_creative(video_id)
            self.results["video_creative_id"] = creative_id
            
        except DirectAPIError as e:
            logging.error(f"  ❌ Ошибка: {e.message}")
            self.results["errors"].append(f"Video: {e.message}")
    
    def _create_ads(self):
        """Шаг 6: Создание объявлений"""
        print("\n📝 ШАГ 6: Создание объявлений")
        print("-" * 40)
        
        ads_config = self.config.get("ads", [])
        
        if not ads_config:
            logging.warning("⚠️ Объявления не указаны в конфиге")
            return
        
        image_hashes = self.results.get("image_hashes", [])
        video_creative_id = self.results.get("video_creative_id")
        
        for i, ad in enumerate(ads_config, 1):
            print(f"\n  [{i}/{len(ads_config)}] {ad['title'][:30]}...")
            
            # Распределяем картинки по объявлениям
            image_hash = None
            if image_hashes and i <= len(image_hashes):
                image_hash = image_hashes[i - 1]
            
            try:
                ad_id = self.client.create_text_ad(
                    ad_group_id=self.results["ad_group_id"],
                    title=ad["title"],
                    text=ad["text"],
                    href=ad["href"],
                    title2=ad.get("title2"),
                    display_url=ad.get("display_url"),
                    image_hash=image_hash,
                    video_creative_id=video_creative_id  # Все объявления с видео
                )
                self.results["ad_ids"].append(ad_id)
                
            except DirectAPIError as e:
                logging.error(f"  ❌ Ошибка: {e.message}")
                self.results["errors"].append(f"Ad #{i}: {e.message}")
    
    def _send_to_moderation(self):
        """Шаг 7: Отправка на модерацию"""
        print("\n📤 ШАГ 7: Отправка на модерацию")
        print("-" * 40)
        
        self.client.moderate_ads(self.results["ad_ids"])
    
    def _print_summary(self):
        """Итоговый отчёт"""
        print("\n" + "=" * 60)
        print("📊 ИТОГ")
        print("=" * 60)
        
        video_status = "✅" if self.results['video_creative_id'] else "—"
        
        print(f"""
✅ Кампания:        ID {self.results['campaign_id']}
✅ Группа:          ID {self.results['ad_group_id']}
✅ Ключей:          {len(self.results['keyword_ids'])}
🖼️ Картинок:        {len(self.results['image_hashes'])}
🎬 Видео:           {video_status} {self.results.get('video_creative_id', '')}
✅ Объявлений:      {len(self.results['ad_ids'])}
❌ Ошибок:          {len(self.results['errors'])}

🔗 Открыть в Директе:
   https://direct.yandex.ru/dna/grid/campaigns/{self.results['campaign_id']}
""")
        
        if self.results["errors"]:
            print("⚠️ Ошибки:")
            for err in self.results["errors"]:
                print(f"   - {err}")


# =========== CLI ===========

def main():
    setup_logging()
    
    if len(sys.argv) < 2:
        config_path = "config/execai_it_campaign.json"
        print(f"ℹ️ Конфиг не указан, использую: {config_path}")
    else:
        config_path = sys.argv[1]
    
    sandbox = "--sandbox" in sys.argv
    skip_mod = "--skip-moderation" in sys.argv or "--no-mod" in sys.argv
    
    if sandbox:
        print("🧪 SANDBOX MODE (тестовый аккаунт)")
    
    creator = CampaignCreator(config_path, sandbox=sandbox)
    results = creator.run(skip_moderation=skip_mod)
    
    result_file = Path("logs") / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результат сохранён: {result_file}")
    
    return 0 if not results["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
