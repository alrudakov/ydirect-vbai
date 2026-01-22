"""
Яндекс Директ API v5 Client
https://yandex.ru/dev/direct/doc/ru/concepts/overview
"""
import requests
import json
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
    
    Docs: https://yandex.ru/dev/direct/doc/ru/concepts/overview
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
            service: Сервис API (campaigns, adgroups, ads, keywords)
            method: Метод (add, get, update, delete)
            params: Параметры запроса
        """
        url = f"{self.base_url}/{service}"
        
        body = {
            "method": method,
            "params": params
        }
        
        logger.debug(f"→ {service}.{method}")
        logger.debug(f"  Body: {json.dumps(body, ensure_ascii=False)[:500]}")
        
        response = requests.post(
            url,
            headers=self._headers(),
            json=body,
            timeout=60
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
        
        campaign_data = {
            "Name": name,
            "StartDate": start_date,
            "DailyBudget": {
                "Amount": budget_micros,
                "Mode": "STANDARD"  # или DISTRIBUTED
            },
            "NegativeKeywords": {
                "Items": negative_keywords or []
            },
            # Текстовая кампания (классика)
            "TextCampaign": {
                "BiddingStrategy": {
                    "Search": {
                        "BiddingStrategyType": "HIGHEST_POSITION"
                    },
                    "Network": {
                        "BiddingStrategyType": "MAXIMUM_COVERAGE"
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
        
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first:
            err = first["Errors"][0]
            raise DirectAPIError(
                err.get("Code", 0),
                err.get("Message", "Unknown"),
                err.get("Details", "")
            )
        
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
        
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first:
            err = first["Errors"][0]
            raise DirectAPIError(err.get("Code", 0), err.get("Message", ""))
        
        group_id = first["Id"]
        logger.info(f"✅ Группа создана! ID: {group_id}")
        return group_id
    
    # =========== ADS ===========
    
    def create_text_ad(self,
                       ad_group_id: int,
                       title: str,
                       title2: str,
                       text: str,
                       href: str,
                       display_url: Optional[str] = None) -> int:
        """
        Создать текстовое объявление
        
        Args:
            ad_group_id: ID группы объявлений
            title: Заголовок 1 (до 35 символов)
            title2: Заголовок 2 (до 30 символов)
            text: Текст объявления (до 81 символа)
            href: Ссылка на сайт
            display_url: Отображаемая ссылка
        """
        ad_data = {
            "AdGroupId": ad_group_id,
            "TextAd": {
                "Title": title[:35],
                "Title2": title2[:30] if title2 else None,
                "Text": text[:81],
                "Href": href,
                "DisplayUrlPath": display_url,
                "Mobile": "NO"
            }
        }
        
        # Убираем None значения
        ad_data["TextAd"] = {k: v for k, v in ad_data["TextAd"].items() if v is not None}
        
        logger.info(f"📝 Создаю объявление: {title[:30]}...")
        
        result = self._call("ads", "add", {
            "Ads": [ad_data]
        })
        
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first:
            err = first["Errors"][0]
            raise DirectAPIError(err.get("Code", 0), err.get("Message", ""))
        
        ad_id = first["Id"]
        logger.info(f"✅ Объявление создано! ID: {ad_id}")
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
            elif "Errors" in r:
                err = r["Errors"][0]
                logger.warning(f"⚠️ Ключ не добавлен: {err.get('Message')}")
        
        logger.info(f"✅ Добавлено ключей: {len(keyword_ids)}")
        return keyword_ids
    
    # =========== IMAGES ===========
    
    def upload_image(self, image_path: str, name: str = None) -> str:
        """
        Загрузить изображение в библиотеку
        
        Args:
            image_path: Путь к файлу (jpg/png)
            name: Название изображения
        
        Returns:
            ImageHash для использования в объявлениях
        """
        import base64
        
        file_path = Path(image_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")
        
        # Читаем и кодируем в base64
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        image_name = name or file_path.stem
        
        logger.info(f"🖼️ Загружаю изображение: {file_path.name}")
        
        result = self._call("adimages", "add", {
            "AdImages": [{
                "Name": image_name[:255],
                "ImageData": image_data
            }]
        })
        
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first:
            err = first["Errors"][0]
            raise DirectAPIError(err.get("Code", 0), err.get("Message", ""))
        
        image_hash = first.get("AdImageHash")
        logger.info(f"✅ Изображение загружено! Hash: {image_hash}")
        return image_hash
    
    def get_images(self) -> List[Dict]:
        """Получить список загруженных изображений"""
        result = self._call("adimages", "get", {
            "FieldNames": ["AdImageHash", "Name", "Type", "Subtype"]
        })
        return result.get("AdImages", [])
    
    # =========== TEXT AD WITH IMAGE ===========
    
    def create_text_image_ad(self,
                             ad_group_id: int,
                             title: str,
                             title2: str,
                             text: str,
                             href: str,
                             image_hash: str,
                             display_url: Optional[str] = None) -> int:
        """
        Создать текстово-графическое объявление (с картинкой)
        
        Args:
            ad_group_id: ID группы объявлений
            title: Заголовок 1
            title2: Заголовок 2
            text: Текст объявления
            href: Ссылка
            image_hash: Hash изображения из upload_image()
            display_url: Отображаемая ссылка
        """
        ad_data = {
            "AdGroupId": ad_group_id,
            "TextImageAd": {
                "Title": title[:33],
                "Text": text[:75],
                "Href": href,
                "AdImageHash": image_hash,
                "DisplayUrlPath": display_url
            }
        }
        
        # Убираем None
        ad_data["TextImageAd"] = {k: v for k, v in ad_data["TextImageAd"].items() if v is not None}
        
        logger.info(f"📝 Создаю текстово-графическое объявление: {title[:30]}...")
        
        result = self._call("ads", "add", {
            "Ads": [ad_data]
        })
        
        add_results = result.get("AddResults", [])
        if not add_results:
            raise DirectAPIError(0, "Пустой ответ", "AddResults empty")
        
        first = add_results[0]
        if "Errors" in first:
            err = first["Errors"][0]
            raise DirectAPIError(err.get("Code", 0), err.get("Message", ""))
        
        ad_id = first["Id"]
        logger.info(f"✅ Объявление с картинкой создано! ID: {ad_id}")
        return ad_id
    
    # =========== VIDEO EXTENSION ===========
    
    def add_video_extension(self, ad_id: int, video_url: str) -> bool:
        """
        Добавить видеодополнение к объявлению
        
        Note: Видео должно быть предварительно загружено на YouTube 
        или в Видеоконструктор Яндекса
        
        Args:
            ad_id: ID объявления
            video_url: URL видео
        """
        logger.info(f"🎬 Добавляю видеодополнение к объявлению {ad_id}")
        
        # Видеодополнения добавляются через update объявления
        # или через отдельный сервис VideoExtensions
        
        # TODO: Реализовать когда будет понятен точный формат
        logger.warning("⚠️ Видеодополнения через API требуют предзагрузки в Видеоконструктор")
        return False
    
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

