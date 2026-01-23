"""
Яндекс Директ API v5 Client
https://yandex.ru/dev/direct/doc/ru/concepts/overview

Исправлено по официальной документации:
- AdImages.add: https://yandex.ru/dev/direct/doc/ru/adimages/add
- Ads.add (TextAd, TextImageAd): https://yandex.ru/dev/direct/doc/ru/ads/add
- AdVideos.add: https://yandex.ru/dev/direct/doc/ru/advideos/add
- Creatives.add: https://yandex.ru/dev/direct/doc/en/creatives/add
"""
import requests
import json
import base64
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectAPIError(Exception):
    """Ошибка API Яндекс Директа"""
    def __init__(self, code: int, message: str, details: str = ""):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"[{code}] {message}: {details}")


class DirectAPIClient:
    """
    Клиент для Яндекс Директ API v5
    """
    
    BASE_URL = "https://api.direct.yandex.com/json/v5"
    SANDBOX_URL = "https://api-sandbox.direct.yandex.com/json/v5"
    
    def __init__(self, token_path: str = "token.txt", sandbox: bool = False):
        self.token = self._load_token(token_path)
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self.sandbox = sandbox
        
        if sandbox:
            logger.info("🧪 Режим SANDBOX (тестовый)")
        else:
            logger.info("🚀 Режим PRODUCTION")
    
    def _load_token(self, path: str) -> str:
        """Загружает OAuth токен из файла"""
        token_file = Path(path)
        if not token_file.exists():
            raise FileNotFoundError(
                f"Токен не найден: {path}\n"
                "Запусти: python auth.py"
            )
        return token_file.read_text().strip()
    
    def _headers(self) -> Dict[str, str]:
        """Заголовки для запросов"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _call(self, service: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Базовый вызов API
        
        Args:
            service: Сервис API (campaigns, adgroups, ads, keywords, adimages, advideos, creatives)
            method: Метод (add, get, update, delete)
            params: Параметры запроса
        """
        url = f"{self.base_url}/{service}"
        
        body = {
            "method": method,
            "params": params
        }
        
        logger.debug(f"→ {service}.{method}")
        
        response = requests.post(
            url,
            headers=self._headers(),
            json=body,
            timeout=120  # Увеличил для загрузки файлов
        )
        
        result = response.json()
        
        # Проверка на ошибку
        if "error" in result:
            err = result["error"]
            raise DirectAPIError(
                code=err.get("error_code", 0),
                message=err.get("error_string", "Unknown error"),
                details=err.get("error_detail", "")
            )
        
        logger.debug(f"← OK")
        return result.get("result", {})
    
    def _check_add_result(self, result: Dict, entity_name: str = "объект") -> Any:
        """Проверяет результат add-метода и возвращает ID/Hash"""
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first and first["Errors"]:
            err = first["Errors"][0]
            raise DirectAPIError(
                err.get("Code", 0),
                err.get("Message", "Unknown error"),
                err.get("Details", "")
            )
        
        # Warnings логируем но не фейлим
        if "Warnings" in first and first["Warnings"]:
            for w in first["Warnings"]:
                logger.warning(f"⚠️ {w.get('Message', '')}")
        
        return first
    
    # =========== CAMPAIGNS ===========
    
    def get_campaigns(self, 
                      ids: Optional[List[int]] = None,
                      states: Optional[List[str]] = None) -> List[Dict]:
        """
        Получить список кампаний
        
        States: ARCHIVED, CONVERTED, ENDED, OFF, ON, SUSPENDED
        """
        criteria = {}
        if ids:
            criteria["Ids"] = ids
        if states:
            criteria["States"] = states
        
        result = self._call("campaigns", "get", {
            "SelectionCriteria": criteria,
            "FieldNames": [
                "Id", "Name", "State", "Status", "Type",
                "StartDate", "DailyBudget", "Statistics"
            ]
        })
        
        return result.get("Campaigns", [])
    
    def create_campaign(self, 
                        name: str,
                        start_date: str,
                        daily_budget_rub: int,
                        negative_keywords: Optional[List[str]] = None) -> int:
        """
        Создать текстовую кампанию (РСЯ + Поиск)
        
        Args:
            name: Название кампании
            start_date: Дата начала (YYYY-MM-DD)
            daily_budget_rub: Дневной бюджет в рублях
            negative_keywords: Минус-слова
        
        Returns:
            ID созданной кампании
        """
        # Бюджет в микроединицах (1 руб = 1_000_000 микроединиц)
        budget_micros = daily_budget_rub * 1_000_000
        
        # Недельный бюджет = дневной * 7
        weekly_budget_micros = budget_micros * 7
        
        campaign_data = {
            "Name": name,
            "StartDate": start_date,
            "NegativeKeywords": {
                "Items": negative_keywords or []
            },
            "TextCampaign": {
                "BiddingStrategy": {
                    "Search": {
                        "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                        "WbMaximumClicks": {
                            "WeeklySpendLimit": weekly_budget_micros,
                            "BidCeiling": 50000000  # 50 руб макс за клик
                        }
                    },
                    "Network": {
                        "BiddingStrategyType": "NETWORK_DEFAULT"
                    }
                },
                "Settings": [
                    {"Option": "ADD_METRICA_TAG", "Value": "YES"},
                    {"Option": "ADD_TO_FAVORITES", "Value": "NO"},
                    {"Option": "ENABLE_AREA_OF_INTEREST_TARGETING", "Value": "YES"},
                    {"Option": "ENABLE_COMPANY_INFO", "Value": "YES"},
                    {"Option": "ENABLE_SITE_MONITORING", "Value": "NO"},
                ]
            }
        }
        
        logger.info(f"📢 Создаю кампанию: {name}")
        logger.info(f"   Бюджет: {daily_budget_rub} руб/день")
        logger.info(f"   Старт: {start_date}")
        
        result = self._call("campaigns", "add", {
            "Campaigns": [campaign_data]
        })
        
        first = self._check_add_result(result, "кампания")
        campaign_id = first["Id"]
        logger.info(f"✅ Кампания создана! ID: {campaign_id}")
        return campaign_id
    
    # =========== AD GROUPS ===========
    
    def create_ad_group(self,
                        campaign_id: int,
                        name: str,
                        region_ids: List[int]) -> int:
        """
        Создать группу объявлений
        
        Args:
            campaign_id: ID кампании
            name: Название группы
            region_ids: Регионы показа (225 = Россия)
        """
        group_data = {
            "Name": name,
            "CampaignId": campaign_id,
            "RegionIds": region_ids,
        }
        
        logger.info(f"📁 Создаю группу объявлений: {name}")
        
        result = self._call("adgroups", "add", {
            "AdGroups": [group_data]
        })
        
        first = self._check_add_result(result, "группа")
        group_id = first["Id"]
        logger.info(f"✅ Группа создана! ID: {group_id}")
        return group_id
    
    # =========== AD IMAGES ===========
    # Docs: https://yandex.ru/dev/direct/doc/ru/adimages/add
    
    def upload_image(self, image_path: str, name: str = None) -> str:
        """
        Загрузить изображение в библиотеку (AdImages.add)
        
        Args:
            image_path: Путь к файлу (jpg/png/gif)
            name: Название изображения (обязательно, до 255 символов)
        
        Returns:
            AdImageHash для использования в объявлениях
        
        Ограничения:
            - Форматы: JPG, PNG, GIF
            - Для графических объявлений: до 512 КБ
            - Для остальных: до 10 МБ
            - Разрешение: от 450px до 5000px (зависит от соотношения сторон)
        """
        file_path = Path(image_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")
        
        # Проверка размера (10 МБ макс)
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            raise ValueError(f"Файл слишком большой: {file_size / 1024 / 1024:.1f} МБ (макс 10 МБ)")
        
        # Читаем и кодируем в base64
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        image_name = (name or file_path.stem)[:255]
        
        logger.info(f"🖼️ Загружаю изображение: {file_path.name} ({file_size / 1024:.1f} КБ)")
        
        # Официальный формат запроса
        result = self._call("adimages", "add", {
            "AdImages": [{
                "ImageData": image_data,
                "Type": "AUTO",  # Автоопределение типа
                "Name": image_name
            }]
        })
        
        first = self._check_add_result(result, "изображение")
        image_hash = first.get("AdImageHash")
        
        if not image_hash:
            raise DirectAPIError(0, "AdImageHash не получен", str(first))
        
        logger.info(f"✅ Изображение загружено! Hash: {image_hash}")
        return image_hash
    
    def get_images(self) -> List[Dict]:
        """Получить список загруженных изображений"""
        result = self._call("adimages", "get", {
            "FieldNames": ["AdImageHash", "Name", "Type", "Subtype", "OriginalUrl"]
        })
        return result.get("AdImages", [])
    
    # =========== AD VIDEOS ===========
    # Docs: https://yandex.ru/dev/direct/doc/ru/advideos/add
    
    def upload_video_by_url(self, video_url: str) -> str:
        """
        Загрузить видео по URL (AdVideos.add)
        
        Args:
            video_url: Прямая ссылка на видеофайл
        
        Returns:
            VideoId для создания креатива
        
        Ограничения:
            - Форматы: MP4, WebM, MOV, QT, FLV, AVI
            - Размер: до 100 МБ
            - Длительность: 5-60 сек
            - Разрешение: мин 360p, рек 1080p
        """
        logger.info(f"🎬 Загружаю видео по URL: {video_url[:50]}...")
        
        result = self._call("advideos", "add", {
            "AdVideos": [{
                "Url": video_url
            }]
        })
        
        first = self._check_add_result(result, "видео")
        video_id = first.get("Id")
        
        if not video_id:
            raise DirectAPIError(0, "VideoId не получен", str(first))
        
        logger.info(f"✅ Видео загружено! ID: {video_id}")
        return video_id
    
    def upload_video_binary(self, video_path: str, name: str = None) -> str:
        """
        Загрузить видео файлом (AdVideos.add с VideoData)
        
        Args:
            video_path: Путь к видеофайлу
            name: Название видео
        
        Returns:
            VideoId для создания креатива
        
        Ограничение: только 1 видео за вызов в бинарном режиме
        """
        file_path = Path(video_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Видео не найдено: {video_path}")
        
        # Проверка размера (100 МБ макс)
        file_size = file_path.stat().st_size
        if file_size > 100 * 1024 * 1024:
            raise ValueError(f"Видео слишком большое: {file_size / 1024 / 1024:.1f} МБ (макс 100 МБ)")
        
        logger.info(f"🎬 Загружаю видео: {file_path.name} ({file_size / 1024 / 1024:.1f} МБ)")
        logger.info("   (это может занять время...)")
        
        # Читаем и кодируем в base64
        with open(file_path, "rb") as f:
            video_data = base64.b64encode(f.read()).decode("utf-8")
        
        video_name = (name or file_path.stem)[:255]
        
        result = self._call("advideos", "add", {
            "AdVideos": [{
                "VideoData": video_data,
                "Name": video_name
            }]
        })
        
        first = self._check_add_result(result, "видео")
        video_id = first.get("Id")
        
        if not video_id:
            raise DirectAPIError(0, "VideoId не получен", str(first))
        
        logger.info(f"✅ Видео загружено! ID: {video_id}")
        return video_id
    
    # =========== CREATIVES ===========
    # Docs: https://yandex.ru/dev/direct/doc/en/creatives/add
    
    def create_video_extension_creative(self, video_id: str) -> int:
        """
        Создать креатив для видеодополнения (Creatives.add)
        
        Args:
            video_id: ID видео из AdVideos.add
        
        Returns:
            CreativeId для привязки к объявлению
        """
        logger.info(f"🎞️ Создаю креатив для видео ID: {video_id}")
        
        result = self._call("creatives", "add", {
            "Creatives": [{
                "VideoExtensionCreative": {
                    "VideoId": video_id
                }
            }]
        })
        
        first = self._check_add_result(result, "креатив")
        creative_id = first.get("Id")
        
        if not creative_id:
            raise DirectAPIError(0, "CreativeId не получен", str(first))
        
        logger.info(f"✅ Креатив создан! ID: {creative_id}")
        return creative_id
    
    # =========== ADS ===========
    # Docs: https://yandex.ru/dev/direct/doc/ru/ads/add
    
    def create_text_ad(self,
                       ad_group_id: int,
                       title: str,
                       text: str,
                       href: str,
                       title2: Optional[str] = None,
                       display_url: Optional[str] = None,
                       image_hash: Optional[str] = None,
                       video_creative_id: Optional[int] = None) -> int:
        """
        Создать текстово-графическое объявление (TextAd)
        
        Args:
            ad_group_id: ID группы объявлений
            title: Заголовок 1 (обязательный, до 56 символов)
            text: Текст объявления (обязательный, до 81 символа)
            href: Ссылка на сайт
            title2: Заголовок 2 (до 30 символов)
            display_url: Отображаемая ссылка
            image_hash: AdImageHash для картинки (типы REGULAR или WIDE)
            video_creative_id: CreativeId для видеодополнения
        
        Returns:
            ID созданного объявления
        """
        # Обрезаем по лимитам
        title = title[:56]
        text = text[:81]
        if title2:
            title2 = title2[:30]
        
        # Формируем TextAd по официальной структуре
        text_ad = {
            "Title": title,
            "Text": text,
            "Href": href,
            "Mobile": "NO"  # Обязательное поле (устаревшее, но required)
        }
        
        if title2:
            text_ad["Title2"] = title2
        if display_url:
            text_ad["DisplayUrlPath"] = display_url
        if image_hash:
            text_ad["AdImageHash"] = image_hash
        if video_creative_id:
            text_ad["VideoExtension"] = {"CreativeId": video_creative_id}
        
        ad_data = {
            "AdGroupId": ad_group_id,
            "TextAd": text_ad
        }
        
        logger.info(f"📝 Создаю объявление: {title[:30]}...")
        if image_hash:
            logger.info(f"   + картинка: {image_hash[:20]}...")
        if video_creative_id:
            logger.info(f"   + видео: {video_creative_id}")
        
        result = self._call("ads", "add", {
            "Ads": [ad_data]
        })
        
        first = self._check_add_result(result, "объявление")
        ad_id = first["Id"]
        logger.info(f"✅ Объявление создано! ID: {ad_id}")
        return ad_id
    
    def create_text_image_ad(self,
                             ad_group_id: int,
                             image_hash: str,
                             href: str) -> int:
        """
        Создать графическое объявление (TextImageAd)
        
        Это объявление где основа — картинка (баннер).
        Подходят только изображения типа FIXED_IMAGE.
        
        Args:
            ad_group_id: ID группы объявлений
            image_hash: AdImageHash (обязательный, тип FIXED_IMAGE)
            href: Ссылка на сайт
        
        Returns:
            ID созданного объявления
        """
        ad_data = {
            "AdGroupId": ad_group_id,
            "TextImageAd": {
                "AdImageHash": image_hash,
                "Href": href
            }
        }
        
        logger.info(f"📝 Создаю графическое объявление...")
        logger.info(f"   Hash: {image_hash[:20]}...")
        
        result = self._call("ads", "add", {
            "Ads": [ad_data]
        })
        
        first = self._check_add_result(result, "объявление")
        ad_id = first["Id"]
        logger.info(f"✅ Графическое объявление создано! ID: {ad_id}")
        return ad_id
    
    # =========== KEYWORDS ===========
    
    def add_keywords(self,
                     ad_group_id: int,
                     keywords: List[str],
                     bid_rub: Optional[int] = None) -> List[int]:
        """
        Добавить ключевые слова в группу
        
        Args:
            ad_group_id: ID группы объявлений
            keywords: Список ключевых слов
            bid_rub: Ставка в рублях (опционально)
        """
        keywords_data = []
        for kw in keywords:
            kw_item = {
                "AdGroupId": ad_group_id,
                "Keyword": kw
            }
            if bid_rub:
                kw_item["Bid"] = bid_rub * 1_000_000  # микроединицы
            keywords_data.append(kw_item)
        
        logger.info(f"🔑 Добавляю {len(keywords)} ключевых слов")
        
        result = self._call("keywords", "add", {
            "Keywords": keywords_data
        })
        
        keyword_ids = []
        for r in result.get("AddResults", []):
            if "Id" in r:
                keyword_ids.append(r["Id"])
            elif "Errors" in r and r["Errors"]:
                err = r["Errors"][0]
                logger.warning(f"⚠️ Ключ не добавлен: {err.get('Message')}")
        
        logger.info(f"✅ Добавлено ключей: {len(keyword_ids)}")
        return keyword_ids
    
    # =========== MODERATION ===========
    
    def moderate_ads(self, ad_ids: List[int]) -> bool:
        """Отправить объявления на модерацию"""
        logger.info(f"📤 Отправляю на модерацию {len(ad_ids)} объявлений...")
        
        result = self._call("ads", "moderate", {
            "SelectionCriteria": {
                "Ids": ad_ids
            }
        })
        
        logger.info("✅ Отправлено на модерацию")
        return True


# =========== CLI для быстрого теста ===========

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    
    client = DirectAPIClient()
    
    print("\n📊 Текущие кампании:")
    print("-" * 50)
    
    campaigns = client.get_campaigns()
    if not campaigns:
        print("Кампаний нет")
    else:
        for c in campaigns:
            budget = c.get("DailyBudget", {}).get("Amount", 0) / 1_000_000
            print(f"  [{c['Id']}] {c['Name']}")
            print(f"      Статус: {c['Status']} | Состояние: {c['State']}")
            print(f"      Бюджет: {budget:.0f} руб/день")
            print()
    
    print("\n🖼️ Загруженные изображения:")


    # =========== BID MODIFIERS ===========
    
    def disable_mobile_and_tablet(self, campaign_id: int) -> List[int]:
        """
        Отключить мобильные и планшеты для кампании (только десктоп)
        
        BidModifier=0 в API = -100% в интерфейсе = полное отключение
        Диапазон: 0..1300 (0=-100%, 100=0%, 1300=+1200%)
        
        Args:
            campaign_id: ID кампании
        
        Returns:
            Список ID созданных корректировок
        """
        # Два отдельных модификатора: Mobile и Tablet
        modifiers = [
            {
                "CampaignId": campaign_id,
                "MobileAdjustment": {
                    "BidModifier": 0  # 0 = -100% = отключено
                }
            },
            {
                "CampaignId": campaign_id,
                "TabletAdjustment": {
                    "BidModifier": 0  # 0 = -100% = отключено
                }
            }
        ]
        
        logger.info(f"📱 Отключаю мобильные и планшеты для кампании {campaign_id}")
        
        # Используем метод ADD для создания корректировок
        result = self._call("bidmodifiers", "add", {
            "BidModifiers": modifiers
        })
        
        ids = []
        for r in result.get("AddResults", []):
            if "Id" in r:
                ids.append(r["Id"])
                logger.info(f"✅ Корректировка создана: ID {r['Id']}")
            elif "Errors" in r:
                for err in r["Errors"]:
                    logger.warning(f"⚠️ {err.get('Message')}")
        
        return ids
    
    def add_excluded_placements(self, campaign_id: int, placements: List[str]) -> bool:
        """
        Добавить минус-площадки (заблокировать сайты)
        
        Args:
            campaign_id: ID кампании  
            placements: Список площадок для блокировки
        
        Returns:
            True если успешно
        """
        if not placements:
            return True
        
        logger.info(f"🚫 Добавляю {len(placements)} минус-площадок")
        
        # Используем update для кампании
        result = self._call("campaigns", "update", {
            "Campaigns": [{
                "Id": campaign_id,
                "ExcludedSites": {
                    "Items": placements
                }
            }]
        })
        
        for r in result.get("UpdateResults", []):
            if "Errors" not in r:
                logger.info(f"✅ Минус-площадки добавлены")
                return True
        
        return False
    print("-" * 50)
    
    images = client.get_images()
    if not images:
        print("Изображений нет")
    else:
        for img in images[:10]:
            print(f"  [{img.get('AdImageHash', 'N/A')[:15]}...] {img.get('Name')} ({img.get('Type')})")
