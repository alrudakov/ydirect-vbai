#!/usr/bin/env python3
"""
🚀 Создание кампании Яндекс Директ из JSON конфига

Использование:
    python run_campaign.py config/execai_campaign.json

Что делает (пошагово):
    1. Читает JSON конфиг
    2. Создаёт кампанию
    3. Создаёт группу объявлений
    4. Добавляет ключевые слова
    5. Создаёт объявления
    6. Отправляет на модерацию (опционально)

Логи сохраняются в ./logs/
"""
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from api_client import DirectAPIClient, DirectAPIError


# =========== LOGGING ===========

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Настройка логирования в файл + консоль"""
    Path(log_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"campaign_{timestamp}.log"
    
    # Формат
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    datefmt = "%H:%M:%S"
    
    # Файл
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))
    
    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Root logger
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
        self.client = DirectAPIClient(sandbox=sandbox)
        
        # Результаты (для отчёта)
        self.results = {
            "campaign_id": None,
            "ad_group_id": None,
            "ad_ids": [],
            "keyword_ids": [],
            "image_hashes": [],
            "errors": []
        }
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Загрузка и валидация конфига"""
        config_file = Path(path)
        if not config_file.exists():
            raise FileNotFoundError(f"Конфиг не найден: {path}")
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Базовая валидация
        required = ["campaign", "ad_group", "ads"]
        for key in required:
            if key not in config:
                raise ValueError(f"Отсутствует обязательный раздел: {key}")
        
        logging.info(f"📋 Конфиг загружен: {path}")
        return config
    
    def run(self, skip_moderation: bool = False) -> Dict[str, Any]:
        """
        Полный цикл создания кампании
        
        Args:
            skip_moderation: Не отправлять на модерацию (для тестов)
        """
        print("\n" + "=" * 60)
        print("🚀 СОЗДАНИЕ КАМПАНИИ ЯНДЕКС ДИРЕКТ")
        print("=" * 60 + "\n")
        
        try:
            # 1. Кампания
            self._create_campaign()
            
            # 2. Группа объявлений
            self._create_ad_group()
            
            # 3. Ключевые слова
            self._add_keywords()
            
            # 4. Изображения (если есть)
            self._upload_images()
            
            # 5. Объявления
            self._create_ads()
            
            # 6. Модерация
            if not skip_moderation and self.results["ad_ids"]:
                self._send_to_moderation()
            
            # Итог
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
    
    def _create_ad_group(self):
        """Шаг 2: Создание группы объявлений"""
        print("\n📁 ШАГ 2: Создание группы объявлений")
        print("-" * 40)
        
        cfg = self.config["ad_group"]
        
        group_id = self.client.create_ad_group(
            campaign_id=self.results["campaign_id"],
            name=cfg["name"],
            region_ids=cfg.get("regions", [225])  # 225 = Россия
        )
        
        self.results["ad_group_id"] = group_id
    
    def _add_keywords(self):
        """Шаг 3: Добавление ключевых слов"""
        print("\n🔑 ШАГ 3: Добавление ключевых слов")
        print("-" * 40)
        
        cfg = self.config["ad_group"]
        keywords = cfg.get("keywords", [])
        
        if not keywords:
            logging.warning("⚠️ Ключевые слова не указаны")
            return
        
        # Ставка из bidding секции (если есть)
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
                
            # Проверяем существование файла
            from pathlib import Path
            if not Path(path).exists():
                logging.warning(f"⚠️ [{i}] Файл не найден: {path}")
                continue
            
            print(f"  [{i}/{len(images)}] {img.get('name', path)}...")
            
            try:
                image_hash = self.client.upload_image(
                    image_path=path,
                    name=img.get("name")
                )
                self.results["image_hashes"].append(image_hash)
                
            except DirectAPIError as e:
                logging.error(f"  ❌ Ошибка: {e.message}")
                self.results["errors"].append(f"Image #{i}: {e.message}")
    
    def _create_ads(self):
        """Шаг 5: Создание объявлений"""
        print("\n📝 ШАГ 5: Создание объявлений")
        print("-" * 40)
        
        ads_config = self.config.get("ads", [])
        
        if not ads_config:
            logging.warning("⚠️ Объявления не указаны в конфиге")
            return
        
        # Если есть загруженные картинки — создаём текстово-графические
        has_images = bool(self.results.get("image_hashes"))
        
        for i, ad in enumerate(ads_config, 1):
            print(f"\n  [{i}/{len(ads_config)}] {ad['title'][:30]}...")
            
            try:
                if has_images and i <= len(self.results["image_hashes"]):
                    # Текстово-графическое объявление (с картинкой)
                    ad_id = self.client.create_text_image_ad(
                        ad_group_id=self.results["ad_group_id"],
                        title=ad["title"],
                        title2=ad.get("title2", ""),
                        text=ad["text"],
                        href=ad["href"],
                        image_hash=self.results["image_hashes"][i-1],
                        display_url=ad.get("display_url")
                    )
                else:
                    # Обычное текстовое объявление
                    ad_id = self.client.create_text_ad(
                        ad_group_id=self.results["ad_group_id"],
                        title=ad["title"],
                        title2=ad.get("title2", ""),
                        text=ad["text"],
                        href=ad["href"],
                        display_url=ad.get("display_url")
                    )
                self.results["ad_ids"].append(ad_id)
                
            except DirectAPIError as e:
                logging.error(f"  ❌ Ошибка: {e.message}")
                self.results["errors"].append(f"Ad #{i}: {e.message}")
    
    def _send_to_moderation(self):
        """Шаг 6: Отправка на модерацию"""
        print("\n📤 ШАГ 6: Отправка на модерацию")
        print("-" * 40)
        
        self.client.moderate_ads(self.results["ad_ids"])
    
    def _print_summary(self):
        """Итоговый отчёт"""
        print("\n" + "=" * 60)
        print("📊 ИТОГ")
        print("=" * 60)
        
        print(f"""
✅ Кампания:      ID {self.results['campaign_id']}
✅ Группа:        ID {self.results['ad_group_id']}
✅ Ключей:        {len(self.results['keyword_ids'])}
🖼️ Картинок:      {len(self.results['image_hashes'])}
✅ Объявлений:    {len(self.results['ad_ids'])}
❌ Ошибок:        {len(self.results['errors'])}

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
    
    # Аргументы
    if len(sys.argv) < 2:
        config_path = "config/execai_campaign.json"
        print(f"ℹ️ Конфиг не указан, использую: {config_path}")
    else:
        config_path = sys.argv[1]
    
    # Флаги
    sandbox = "--sandbox" in sys.argv
    skip_mod = "--skip-moderation" in sys.argv or "--no-mod" in sys.argv
    
    if sandbox:
        print("🧪 SANDBOX MODE (тестовый аккаунт)")
    
    # Создание
    creator = CampaignCreator(config_path, sandbox=sandbox)
    results = creator.run(skip_moderation=skip_mod)
    
    # Сохраняем результат
    result_file = Path("logs") / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результат сохранён: {result_file}")
    
    return 0 if not results["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())

