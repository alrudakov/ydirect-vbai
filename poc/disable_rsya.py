"""
Отключение РСЯ (Рекламной сети Яндекса) для кампании.
Оставляет только поиск.

Usage:
  python disable_rsya.py --campaign-id 706570098
"""

import argparse
import json
from pathlib import Path

import requests

TOKEN = Path("token.txt").read_text().strip()
API_URL = "https://api.direct.yandex.com/json/v5/campaigns"


def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }


def get_campaign_settings(campaign_id: str):
    """Получить текущие настройки кампании"""
    body = {
        "method": "get",
        "params": {
            "SelectionCriteria": {"Ids": [int(campaign_id)]},
            "FieldNames": ["Id", "Name", "Status", "State"],
            "TextCampaignFieldNames": [
                "BiddingStrategy",
                "Settings",
                "CounterIds",
            ],
        },
    }

    resp = requests.post(API_URL, headers=get_headers(), json=body)
    data = resp.json()

    if "result" in data and data["result"].get("Campaigns"):
        return data["result"]["Campaigns"][0]
    
    print(f"❌ Ошибка: {json.dumps(data, ensure_ascii=False, indent=2)}")
    return None


def disable_rsya(campaign_id: str):
    """
    Отключить РСЯ для кампании.
    
    В API это делается через BiddingStrategy.Network = NETWORK_OFF
    или через Settings с EXCLUDE_PAUSED_SITES и т.д.
    
    Для TEXT_CAMPAIGN нужно обновить стратегию.
    """
    
    # Сначала получим текущие настройки
    campaign = get_campaign_settings(campaign_id)
    if not campaign:
        return False
    
    print(f"📋 Кампания: {campaign.get('Name')}")
    print(f"   ID: {campaign.get('Id')}")
    print(f"   Status: {campaign.get('Status')}")
    
    text_campaign = campaign.get("TextCampaign", {})
    current_strategy = text_campaign.get("BiddingStrategy", {})
    
    print(f"\n📊 Текущая стратегия:")
    print(json.dumps(current_strategy, ensure_ascii=False, indent=2))
    
    # Для отключения РСЯ нужно в Network стратегии поставить NETWORK_OFF
    # или BiddingStrategyType который не включает сети
    
    # Сразу пробуем SERVING_OFF - это полное отключение сетей
    update_body = {
        "method": "update",
        "params": {
            "Campaigns": [
                {
                    "Id": int(campaign_id),
                    "TextCampaign": {
                        "BiddingStrategy": {
                            "Search": current_strategy.get("Search", {}),
                            "Network": {
                                "BiddingStrategyType": "SERVING_OFF"
                            }
                        }
                    }
                }
            ]
        }
    }
    
    print(f"\n🔄 Отключаю РСЯ (SERVING_OFF)...")
    
    resp = requests.post(API_URL, headers=get_headers(), json=update_body)
    data = resp.json()
    
    if "result" in data:
        print(f"✅ РСЯ отключена! Теперь только поиск.")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return True
    else:
        print(f"❌ Ошибка: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", required=True, help="ID кампании")
    parser.add_argument("--dry-run", action="store_true", help="Только показать текущие настройки")
    args = parser.parse_args()

    if args.dry_run:
        campaign = get_campaign_settings(args.campaign_id)
        if campaign:
            print(json.dumps(campaign, ensure_ascii=False, indent=2))
    else:
        disable_rsya(args.campaign_id)


if __name__ == "__main__":
    main()

