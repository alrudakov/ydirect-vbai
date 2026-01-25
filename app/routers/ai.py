"""
AI Endpoints для Яндекс.Директ (SSE формат как в ssh-vbai)
Эти endpoints вызываются из aihandler-vbai
"""
import json
import base64
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_user_email_from_token
from app.routers.profiles import get_profile_token
from app.direct_client import DirectAPIClient, DirectAPIError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


# =========== SSE HELPERS ===========

def sse_start():
    """Маркер начала функции"""
    return "data: [FUNCTION_START]\n\n"


def sse_end():
    """Маркер конца функции"""
    return "data: [FUNCTION_END]\n\n"


def sse_output(content: str):
    """SSE чанк с контентом (base64)"""
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    data = json.dumps({"function_result": "output", "content": encoded})
    return f"data: {data}\n\n"


def sse_status(exit_code: int = 0):
    """SSE чанк со статусом"""
    data = json.dumps({"function_result": "status", "exit_code": exit_code})
    return f"data: {data}\n\n"


def sse_error(message: str):
    """SSE чанк с ошибкой"""
    encoded = base64.b64encode(message.encode('utf-8')).decode('utf-8')
    data = json.dumps({"function_result": "error", "content": encoded})
    return f"data: {data}\n\n"


# =========== SCHEMAS ===========

class GetCampaignsRequest(BaseModel):
    """Запрос списка кампаний"""
    alias: str
    states: Optional[List[str]] = None  # ON, OFF, SUSPENDED, ENDED, ARCHIVED


class GetStatsRequest(BaseModel):
    """Запрос статистики"""
    alias: str
    campaign_id: int
    days: Optional[int] = 7
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CreateCampaignRequest(BaseModel):
    """Создание кампании"""
    alias: str
    name: str
    daily_budget_rub: int
    start_date: Optional[str] = None  # YYYY-MM-DD, default = today


class UpdateBudgetRequest(BaseModel):
    """Обновление бюджета"""
    alias: str
    campaign_id: int
    weekly_budget_rub: int
    max_cpc_rub: Optional[int] = None


class ToggleRsyaRequest(BaseModel):
    """Вкл/выкл РСЯ"""
    alias: str
    campaign_id: int
    enable: bool = False


class CreateAdGroupRequest(BaseModel):
    """Создание группы объявлений"""
    alias: str
    campaign_id: int
    name: str
    region_ids: Optional[List[int]] = [225]  # Default: Россия


class AddKeywordsRequest(BaseModel):
    """Добавление ключевых слов"""
    alias: str
    ad_group_id: int
    keywords: List[str]
    bid_rub: Optional[int] = None


class CreateAdRequest(BaseModel):
    """Создание объявления"""
    alias: str
    ad_group_id: int
    title: str
    text: str
    href: str
    title2: Optional[str] = None
    display_url: Optional[str] = None


class ModerateAdsRequest(BaseModel):
    """Отправка на модерацию"""
    alias: str
    ad_ids: List[int]


class GetAdsRequest(BaseModel):
    """Получение объявлений"""
    alias: str
    ad_group_id: int


class GetAdGroupsRequest(BaseModel):
    """Получение групп объявлений"""
    alias: str
    campaign_id: int


# =========== ENDPOINTS ===========

@router.post("/campaigns")
async def get_campaigns(
    request: GetCampaignsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список кампаний Яндекс.Директ
    """
    async def generate():
        yield sse_start()
        
        try:
            # Получаем токен профиля
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            # Запрос кампаний
            campaigns = await client.get_campaigns(states=request.states)
            
            # Форматируем ответ
            output_lines = [f"📊 Найдено кампаний: {len(campaigns)}\n"]
            
            for c in campaigns:
                budget = c.get("DailyBudget", {}).get("Amount", 0) / 1_000_000
                output_lines.append(f"\n[{c['Id']}] {c['Name']}")
                output_lines.append(f"  Статус: {c['Status']} | Состояние: {c['State']}")
                output_lines.append(f"  Тип: {c['Type']}")
                if budget > 0:
                    output_lines.append(f"  Бюджет: {budget:.0f} руб/день")
                
                stats = c.get("Statistics", {})
                if stats:
                    output_lines.append(f"  Клики: {stats.get('Clicks', 0)} | Показы: {stats.get('Impressions', 0)}")
            
            yield sse_output("\n".join(output_lines))
            yield sse_status(0)
            
        except DirectAPIError as e:
            logger.error(f"Direct API error: {e}")
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except HTTPException as e:
            yield sse_error(e.detail)
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/stats")
async def get_stats(
    request: GetStatsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику кампании
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            # Определяем даты
            date_to = request.date_to or datetime.now().strftime("%Y-%m-%d")
            if request.date_from:
                date_from = request.date_from
            else:
                date_from = (datetime.now() - timedelta(days=request.days)).strftime("%Y-%m-%d")
            
            # Получаем статистику
            stats = await client.get_stats(
                campaign_id=request.campaign_id,
                date_from=date_from,
                date_to=date_to
            )
            
            # Форматируем ответ
            output_lines = [
                f"📈 Статистика кампании {request.campaign_id}",
                f"Период: {date_from} — {date_to}\n"
            ]
            
            if stats:
                row = stats[0]
                output_lines.append(f"👁️  Показы: {row.get('Impressions', 0)}")
                output_lines.append(f"🖱️  Клики: {row.get('Clicks', 0)}")
                output_lines.append(f"📊 CTR: {row.get('Ctr', 0)}%")
                output_lines.append(f"💰 Расход: {row.get('Cost', 0)} руб")
                output_lines.append(f"💵 Ср. CPC: {row.get('AvgCpc', 0)} руб")
                if row.get('Conversions'):
                    output_lines.append(f"🎯 Конверсии: {row.get('Conversions')}")
            else:
                output_lines.append("Нет данных за указанный период")
            
            yield sse_output("\n".join(output_lines))
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except HTTPException as e:
            yield sse_error(e.detail)
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/campaigns/create")
async def create_campaign(
    request: CreateCampaignRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Создать новую кампанию
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            start_date = request.start_date or datetime.now().strftime("%Y-%m-%d")
            
            campaign_id = await client.create_campaign(
                name=request.name,
                start_date=start_date,
                daily_budget_rub=request.daily_budget_rub
            )
            
            output = f"""✅ Кампания создана!

ID: {campaign_id}
Название: {request.name}
Бюджет: {request.daily_budget_rub} руб/день
Старт: {start_date}

🔗 https://direct.yandex.ru/dna/grid/campaigns/{campaign_id}"""
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/campaigns/budget")
async def update_budget(
    request: UpdateBudgetRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить бюджет кампании
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            await client.update_campaign_budget(
                campaign_id=request.campaign_id,
                weekly_budget_rub=request.weekly_budget_rub,
                max_cpc_rub=request.max_cpc_rub
            )
            
            daily = request.weekly_budget_rub // 7
            output = f"""✅ Бюджет обновлён!

Кампания: {request.campaign_id}
Недельный бюджет: {request.weekly_budget_rub} руб (~{daily} руб/день)"""
            
            if request.max_cpc_rub:
                output += f"\nМакс. CPC: {request.max_cpc_rub} руб"
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/campaigns/rsya")
async def toggle_rsya(
    request: ToggleRsyaRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Включить/выключить РСЯ (Рекламную сеть Яндекса)
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            await client.toggle_rsya(request.campaign_id, request.enable)
            
            status = "включена" if request.enable else "отключена"
            output = f"✅ РСЯ {status} для кампании {request.campaign_id}"
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/adgroups")
async def get_ad_groups(
    request: GetAdGroupsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить группы объявлений кампании
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            groups = await client.get_ad_groups(request.campaign_id)
            
            output_lines = [f"📁 Группы объявлений кампании {request.campaign_id}\n"]
            output_lines.append(f"Найдено: {len(groups)}\n")
            
            for g in groups:
                output_lines.append(f"[{g['Id']}] {g['Name']}")
                output_lines.append(f"  Статус: {g['Status']}")
            
            yield sse_output("\n".join(output_lines))
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/adgroups/create")
async def create_ad_group(
    request: CreateAdGroupRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Создать группу объявлений
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            group_id = await client.create_ad_group(
                campaign_id=request.campaign_id,
                name=request.name,
                region_ids=request.region_ids
            )
            
            output = f"""✅ Группа объявлений создана!

ID: {group_id}
Название: {request.name}
Кампания: {request.campaign_id}
Регионы: {request.region_ids}"""
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/keywords/add")
async def add_keywords(
    request: AddKeywordsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить ключевые слова в группу
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            keyword_ids = await client.add_keywords(
                ad_group_id=request.ad_group_id,
                keywords=request.keywords,
                bid_rub=request.bid_rub
            )
            
            output = f"""✅ Ключевые слова добавлены!

Группа: {request.ad_group_id}
Добавлено: {len(keyword_ids)} из {len(request.keywords)}
IDs: {keyword_ids}"""
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ads")
async def get_ads(
    request: GetAdsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить объявления группы
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            ads = await client.get_ads(request.ad_group_id)
            
            output_lines = [f"📝 Объявления группы {request.ad_group_id}\n"]
            output_lines.append(f"Найдено: {len(ads)}\n")
            
            for ad in ads:
                output_lines.append(f"[{ad['Id']}] {ad['Type']}")
                output_lines.append(f"  Статус: {ad['Status']} | Состояние: {ad['State']}")
                
                text_ad = ad.get("TextAd", {})
                if text_ad:
                    output_lines.append(f"  Заголовок: {text_ad.get('Title', '')}")
                    if text_ad.get('Title2'):
                        output_lines.append(f"  Заголовок 2: {text_ad.get('Title2')}")
                    output_lines.append(f"  Текст: {text_ad.get('Text', '')}")
            
            yield sse_output("\n".join(output_lines))
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ads/create")
async def create_ad(
    request: CreateAdRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Создать текстовое объявление
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            ad_id = await client.create_text_ad(
                ad_group_id=request.ad_group_id,
                title=request.title,
                text=request.text,
                href=request.href,
                title2=request.title2,
                display_url=request.display_url
            )
            
            output = f"""✅ Объявление создано!

ID: {ad_id}
Заголовок: {request.title}
Текст: {request.text}
Ссылка: {request.href}

⚠️ Не забудь отправить на модерацию!"""
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ads/moderate")
async def moderate_ads(
    request: ModerateAdsRequest,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Отправить объявления на модерацию
    """
    async def generate():
        yield sse_start()
        
        try:
            token = await get_profile_token(user_email, request.alias, db)
            client = DirectAPIClient(token)
            
            await client.moderate_ads(request.ad_ids)
            
            output = f"""✅ Объявления отправлены на модерацию!

IDs: {request.ad_ids}
Количество: {len(request.ad_ids)}

⏳ Модерация обычно занимает несколько часов."""
            
            yield sse_output(output)
            yield sse_status(0)
            
        except DirectAPIError as e:
            yield sse_error(f"Ошибка API: {e.message}")
            yield sse_status(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            yield sse_error(f"Ошибка: {str(e)}")
            yield sse_status(1)
        
        yield sse_end()
    
    return StreamingResponse(generate(), media_type="text/event-stream")

