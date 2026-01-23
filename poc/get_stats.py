"""
📊 Полная статистика кампании Яндекс Директ (Reports API v5)
https://yandex.ru/dev/direct/doc/ru/reports

Usage:
  python get_stats.py --campaign-id 706570098 --days 7
  python get_stats.py --campaign-id 706552117 --date-from 2026-01-22 --date-to 2026-01-23
"""

import argparse
import csv
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

TOKEN = Path("token.txt").read_text().strip()
REPORT_URL = "https://api.direct.yandex.com/json/v5/reports"

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipReportSummary": "true"
    }

def fetch_report(
    campaign_id: str,
    date_from: str,
    date_to: str,
    report_type: str,
    field_names: list,
    report_name: str,
    order_by: str | None = None,
    retries: int = 12,
    retry_sleep_s: float = 2.0,
    timeout_s: float = 20.0,
) -> list:
    """Получает отчёт из Reports API"""
    
    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": date_from,
                "DateTo": date_to,
                "Filter": [
                    {"Field": "CampaignId", "Operator": "EQUALS", "Values": [campaign_id]}
                ]
            },
            "FieldNames": field_names,
            "ReportName": f"{report_name}_{datetime.now().strftime('%H%M%S')}",
            "ReportType": report_type,
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO"
        }
    }
    
    if order_by:
        body["params"]["OrderBy"] = [{"Field": order_by, "SortOrder": "DESCENDING"}]
    
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                REPORT_URL,
                headers=get_headers(),
                json=body,
                timeout=timeout_s,
            )
        except requests.exceptions.RequestException as e:
            if attempt == 1:
                print(f"   ⚠️ Ошибка сети: {e} (retry...)")
            time.sleep(retry_sleep_s)
            continue

        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            if len(lines) >= 2:
                headers = lines[0].split("\t")
                result = []
                for line in lines[1:]:
                    data = line.split("\t")
                    result.append(dict(zip(headers, data)))
                return result
            return []

        if resp.status_code in (201, 202):
            # Reports service просит повторить тот же запрос позже
            retry_in = resp.headers.get("retryIn")
            sleep_s = float(retry_in) if retry_in and retry_in.isdigit() else retry_sleep_s
            if attempt == 1:
                print(f"   ⏳ Отчёт готовится... (status {resp.status_code}), retryIn={retry_in or 'n/a'}")
            time.sleep(sleep_s)
            continue

        print(f"   ❌ Ошибка {resp.status_code}: {resp.text[:300]}")
        return []

    print("   ❌ Таймаут ожидания отчёта (слишком долго готовится)")
    return []


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print('='*60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", required=True, help="ID кампании")
    parser.add_argument("--date-from", default=None, help="YYYY-MM-DD")
    parser.add_argument("--date-to", default=None, help="YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=2, help="Период в днях назад (если date-from/date-to не заданы)")
    args = parser.parse_args()

    campaign_id = str(args.campaign_id).strip()

    date_to = args.date_to or datetime.now().strftime("%Y-%m-%d")
    if args.date_from:
        date_from = args.date_from
    else:
        date_from = (datetime.now() - timedelta(days=max(1, args.days))).strftime("%Y-%m-%d")

    print("╔════════════════════════════════════════════════════════════╗")
    print("║              📈 СТАТИСТИКА КАМПАНИИ Я.ДИРЕКТ               ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Campaign ID: {campaign_id:<42}║")
    print(f"║  Период: {date_from} — {date_to:<30}║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    all_data = {}
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. ОБЩАЯ СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════════
    print_section("ОБЩАЯ СТАТИСТИКА")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CAMPAIGN_PERFORMANCE_REPORT",
            ["Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
            "Total",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        row = data[0]
        impressions = int(row.get("Impressions", 0))
        clicks = int(row.get("Clicks", 0))
        ctr = row.get("Ctr", "0")
        avg_cpc = row.get("AvgCpc", "0")
        cost = row.get("Cost", "0")
        
        print(f"""
   👁️  Показы:         {impressions:,}
   🖱️  Клики:          {clicks:,}
   📈 CTR:            {ctr}%
   💰 Расход:         {cost} руб
   💵 Ср. цена клика: {avg_cpc} руб
""")
        all_data["total"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. ПО ДНЯМ
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПО ДНЯМ")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CAMPAIGN_PERFORMANCE_REPORT",
            ["Date", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
            "Daily",
            "Date",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        # Сортируем по дате
        data.sort(key=lambda x: x.get("Date", ""))
        
        print(f"   {'Дата':<12} {'Показы':>8} {'Клики':>7} {'CTR':>7} {'CPC':>8} {'Расход':>10}")
        print("   " + "-"*54)
        
        for row in data:
            date = row.get("Date", "")
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            ctr = row.get("Ctr", "0")
            cpc = row.get("AvgCpc", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {date:<12} {impressions:>8} {clicks:>7} {ctr:>6}% {cpc:>7}р {cost:>9}р")
        
        all_data["daily"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. ПО УСТРОЙСТВАМ
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПО УСТРОЙСТВАМ")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CAMPAIGN_PERFORMANCE_REPORT",
            ["Device", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
            "Device",
            "Cost",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        device_names = {
            "DESKTOP": "🖥️  Десктоп",
            "MOBILE": "📱 Мобайл",
            "TABLET": "📲 Планшет"
        }
        
        for row in data:
            device = device_names.get(row.get("Device", ""), row.get("Device", ""))
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            ctr = row.get("Ctr", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {device:<15} {impressions:>7} показов | {clicks:>5} кликов | CTR {ctr}% | {cost} руб")
        
        all_data["device"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. ПО КЛЮЧЕВЫМ СЛОВАМ
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПО КЛЮЧЕВЫМ СЛОВАМ (TOP-15)")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CRITERIA_PERFORMANCE_REPORT",
            ["Criterion", "CriteriaType", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
            "Keywords",
            "Cost",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        # Только ключевики, топ-15 по расходу
        keywords = [d for d in data if d.get("CriteriaType") == "KEYWORD"][:15]
        
        for i, row in enumerate(keywords, 1):
            keyword = row.get("Criterion", "")[:40]
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            ctr = row.get("Ctr", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {i:>2}. {keyword:<40}")
            print(f"       {impressions} показов | {clicks} кликов | CTR {ctr}% | {cost} руб")
        
        all_data["keywords"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. ПО РЕГИОНАМ
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПО РЕГИОНАМ (TOP-10)")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CAMPAIGN_PERFORMANCE_REPORT",
            ["LocationOfPresenceName", "Impressions", "Clicks", "Ctr", "Cost"],
            "Regions",
            "Cost",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        for i, row in enumerate(data[:10], 1):
            region = row.get("LocationOfPresenceName", "")[:30]
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {i:>2}. {region:<30} {impressions:>6} показов | {clicks:>4} кликов | {cost} руб")
        
        all_data["regions"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. ПО ПЛОЩАДКАМ РСЯ (TOP-15)
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПО ПЛОЩАДКАМ РСЯ (TOP-15)")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "CAMPAIGN_PERFORMANCE_REPORT",
            ["AdNetworkType", "Placement", "Impressions", "Clicks", "Ctr", "Cost"],
            "Placements",
            "Cost",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        # Только РСЯ (AD_NETWORK)
        rsya = [d for d in data if d.get("AdNetworkType") == "AD_NETWORK"][:15]
        
        for i, row in enumerate(rsya, 1):
            placement = row.get("Placement", "")[:45]
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            ctr = row.get("Ctr", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {i:>2}. {placement:<45}")
            print(f"       {impressions} показов | {clicks} кликов | CTR {ctr}% | {cost} руб")
        
        all_data["placements"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. ПОИСКОВЫЕ ЗАПРОСЫ (что реально вводили)
    # ═══════════════════════════════════════════════════════════════════
    print_section("ПОИСКОВЫЕ ЗАПРОСЫ (TOP-15)")
    
    try:
        data = fetch_report(
            campaign_id,
            date_from,
            date_to,
            "SEARCH_QUERY_PERFORMANCE_REPORT",
            ["Query", "Impressions", "Clicks", "Ctr", "Cost"],
            "SearchQueries",
            "Cost",
        )
    except KeyboardInterrupt:
        print("\n   ⚠️ Прервано пользователем")
        return
    
    if data:
        for i, row in enumerate(data[:15], 1):
            query = row.get("Query", "")[:50]
            impressions = row.get("Impressions", "0")
            clicks = row.get("Clicks", "0")
            ctr = row.get("Ctr", "0")
            cost = row.get("Cost", "0")
            
            print(f"   {i:>2}. \"{query}\"")
            print(f"       {impressions} показов | {clicks} кликов | CTR {ctr}% | {cost} руб")
        
        all_data["queries"] = data
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. СОХРАНЕНИЕ В CSV
    # ═══════════════════════════════════════════════════════════════════
    print_section("ЭКСПОРТ")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for name, data in all_data.items():
        if data:
            csv_file = f"logs/stats_{name}_{timestamp}.csv"
            with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            print(f"   ✅ {csv_file}")
    
    print("\n" + "="*60)
    print("✨ Готово!")
    print("="*60)


if __name__ == "__main__":
    main()
