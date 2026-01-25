"""
Яндекс Директ API v5 Client
Адаптировано из POC для использования в микросервисе
"""
import httpx
import json
import base64
import logging
from typing import Optional, List, Dict, Any

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
    Async клиент для Яндекс Директ API v5
    """
    
    BASE_URL = "https://api.direct.yandex.com/json/v5"
    SANDBOX_URL = "https://api-sandbox.direct.yandex.com/json/v5"
    REPORTS_URL = "https://api.direct.yandex.com/json/v5/reports"
    
    def __init__(self, token: str, sandbox: bool = False):
        self.token = token
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self.sandbox = sandbox
    
    def _headers(self) -> Dict[str, str]:
        """Заголовки для запросов"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _reports_headers(self) -> Dict[str, str]:
        """Заголовки для Reports API"""
        headers = self._headers()
        headers.update({
            "processingMode": "auto",
            "returnMoneyInMicros": "false",
            "skipReportHeader": "true",
            "skipReportSummary": "true"
        })
        return headers
    
    async def _call(
        self, 
        service: str, 
        method: str, 
        params: Dict[str, Any],
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Базовый вызов API
        """
        url = f"{self.base_url}/{service}"
        body = {"method": method, "params": params}
        
        logger.debug(f"→ {service}.{method}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json=body,
                timeout=timeout
            )
            
            result = response.json()
            
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
        """Проверяет результат add-метода"""
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
        
        return first
    
    # =========== CAMPAIGNS ===========
    
    async def get_campaigns(
        self,
        ids: Optional[List[int]] = None,
        states: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Получить список кампаний
        States: ARCHIVED, CONVERTED, ENDED, OFF, ON, SUSPENDED
        """
        criteria = {}
        if ids:
            criteria["Ids"] = ids
        if states:
            criteria["States"] = states
        
        result = await self._call("campaigns", "get", {
            "SelectionCriteria": criteria,
            "FieldNames": [
                "Id", "Name", "State", "Status", "Type",
                "StartDate", "DailyBudget", "Statistics"
            ]
        })
        
        return result.get("Campaigns", [])
    
    async def create_campaign(
        self,
        name: str,
        start_date: str,
        daily_budget_rub: int,
        negative_keywords: Optional[List[str]] = None
    ) -> int:
        """Создать текстовую кампанию"""
        budget_micros = daily_budget_rub * 1_000_000
        weekly_budget_micros = budget_micros * 7
        
        campaign_data = {
            "Name": name,
            "StartDate": start_date,
            "NegativeKeywords": {"Items": negative_keywords or []},
            "TextCampaign": {
                "BiddingStrategy": {
                    "Search": {
                        "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                        "WbMaximumClicks": {
                            "WeeklySpendLimit": weekly_budget_micros,
                            "BidCeiling": 50000000
                        }
                    },
                    "Network": {"BiddingStrategyType": "NETWORK_DEFAULT"}
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
        
        result = await self._call("campaigns", "add", {"Campaigns": [campaign_data]})
        first = self._check_add_result(result, "кампания")
        return first["Id"]
    
    async def update_campaign_budget(
        self,
        campaign_id: int,
        weekly_budget_rub: int,
        max_cpc_rub: Optional[int] = None
    ) -> bool:
        """Обновить бюджет кампании"""
        weekly_micros = weekly_budget_rub * 1_000_000
        
        strategy = {
            "Search": {
                "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                "WbMaximumClicks": {
                    "WeeklySpendLimit": weekly_micros
                }
            },
            "Network": {"BiddingStrategyType": "NETWORK_DEFAULT"}
        }
        
        if max_cpc_rub:
            strategy["Search"]["WbMaximumClicks"]["BidCeiling"] = max_cpc_rub * 1_000_000
        
        result = await self._call("campaigns", "update", {
            "Campaigns": [{
                "Id": campaign_id,
                "TextCampaign": {"BiddingStrategy": strategy}
            }]
        })
        
        return True
    
    async def toggle_rsya(self, campaign_id: int, enable: bool = False) -> bool:
        """Включить/выключить РСЯ"""
        network_type = "NETWORK_DEFAULT" if enable else "SERVING_OFF"
        
        # Сначала получаем текущую стратегию поиска
        campaigns = await self.get_campaigns(ids=[campaign_id])
        if not campaigns:
            raise DirectAPIError(0, "Кампания не найдена", str(campaign_id))
        
        result = await self._call("campaigns", "update", {
            "Campaigns": [{
                "Id": campaign_id,
                "TextCampaign": {
                    "BiddingStrategy": {
                        "Network": {"BiddingStrategyType": network_type}
                    }
                }
            }]
        })
        
        return True
    
    # =========== AD GROUPS ===========
    
    async def get_ad_groups(self, campaign_id: int) -> List[Dict]:
        """Получить группы объявлений кампании"""
        result = await self._call("adgroups", "get", {
            "SelectionCriteria": {"CampaignIds": [campaign_id]},
            "FieldNames": ["Id", "Name", "CampaignId", "Status", "RegionIds"]
        })
        return result.get("AdGroups", [])
    
    async def create_ad_group(
        self,
        campaign_id: int,
        name: str,
        region_ids: List[int]
    ) -> int:
        """Создать группу объявлений"""
        result = await self._call("adgroups", "add", {
            "AdGroups": [{
                "Name": name,
                "CampaignId": campaign_id,
                "RegionIds": region_ids
            }]
        })
        first = self._check_add_result(result, "группа")
        return first["Id"]
    
    # =========== ADS ===========
    
    async def get_ads(self, ad_group_id: int) -> List[Dict]:
        """Получить объявления группы"""
        result = await self._call("ads", "get", {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Id", "AdGroupId", "Status", "State", "Type"],
            "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "DisplayUrlPath"]
        })
        return result.get("Ads", [])
    
    async def create_text_ad(
        self,
        ad_group_id: int,
        title: str,
        text: str,
        href: str,
        title2: Optional[str] = None,
        display_url: Optional[str] = None
    ) -> int:
        """Создать текстовое объявление"""
        text_ad = {
            "Title": title[:56],
            "Text": text[:81],
            "Href": href,
            "Mobile": "NO"
        }
        
        if title2:
            text_ad["Title2"] = title2[:30]
        if display_url:
            text_ad["DisplayUrlPath"] = display_url
        
        result = await self._call("ads", "add", {
            "Ads": [{"AdGroupId": ad_group_id, "TextAd": text_ad}]
        })
        first = self._check_add_result(result, "объявление")
        return first["Id"]
    
    async def moderate_ads(self, ad_ids: List[int]) -> bool:
        """Отправить объявления на модерацию"""
        await self._call("ads", "moderate", {
            "SelectionCriteria": {"Ids": ad_ids}
        })
        return True
    
    # =========== KEYWORDS ===========
    
    async def get_keywords(self, ad_group_id: int) -> List[Dict]:
        """Получить ключевые слова группы"""
        result = await self._call("keywords", "get", {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Id", "Keyword", "AdGroupId", "Status", "State"]
        })
        return result.get("Keywords", [])
    
    async def add_keywords(
        self,
        ad_group_id: int,
        keywords: List[str],
        bid_rub: Optional[int] = None
    ) -> List[int]:
        """Добавить ключевые слова"""
        keywords_data = []
        for kw in keywords:
            kw_item = {"AdGroupId": ad_group_id, "Keyword": kw}
            if bid_rub:
                kw_item["Bid"] = bid_rub * 1_000_000
            keywords_data.append(kw_item)
        
        result = await self._call("keywords", "add", {"Keywords": keywords_data})
        
        keyword_ids = []
        for r in result.get("AddResults", []):
            if "Id" in r:
                keyword_ids.append(r["Id"])
        
        return keyword_ids
    
    # =========== STATISTICS ===========
    
    async def get_stats(
        self,
        campaign_id: int,
        date_from: str,
        date_to: str,
        report_type: str = "CAMPAIGN_PERFORMANCE_REPORT",
        fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Получить статистику через Reports API
        """
        if fields is None:
            fields = [
                "Impressions", "Clicks", "Ctr", 
                "AvgCpc", "Cost", "Conversions"
            ]
        
        body = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from,
                    "DateTo": date_to,
                    "Filter": [{
                        "Field": "CampaignId",
                        "Operator": "EQUALS",
                        "Values": [str(campaign_id)]
                    }]
                },
                "FieldNames": fields,
                "ReportName": f"stats_{campaign_id}",
                "ReportType": report_type,
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "NO"
            }
        }
        
        headers = self._reports_headers()
        
        async with httpx.AsyncClient() as client:
            for attempt in range(5):
                response = await client.post(
                    self.REPORTS_URL,
                    headers=headers,
                    json=body,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    lines = response.text.strip().split("\n")
                    if len(lines) >= 2:
                        header = lines[0].split("\t")
                        result = []
                        for line in lines[1:]:
                            data = line.split("\t")
                            result.append(dict(zip(header, data)))
                        return result
                    return []
                
                if response.status_code in (201, 202):
                    # Report is being prepared
                    import asyncio
                    await asyncio.sleep(2)
                    continue
                
                raise DirectAPIError(
                    response.status_code,
                    "Reports API error",
                    response.text[:200]
                )
        
        return []
    
    # =========== BID MODIFIERS ===========
    
    async def disable_mobile_tablet(self, campaign_id: int) -> List[int]:
        """Отключить мобильные и планшеты (только десктоп)"""
        modifiers = [
            {"CampaignId": campaign_id, "MobileAdjustment": {"BidModifier": 0}},
            {"CampaignId": campaign_id, "TabletAdjustment": {"BidModifier": 0}}
        ]
        
        result = await self._call("bidmodifiers", "add", {"BidModifiers": modifiers})
        
        ids = []
        for r in result.get("AddResults", []):
            if "Id" in r:
                ids.append(r["Id"])
        
        return ids

