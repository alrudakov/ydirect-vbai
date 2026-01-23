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
    goals: list[str] | None = None,
    attribution_models: list[str] | None = None,
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

    if goals:
        body["params"]["Goals"] = goals
    if attribution_models:
        body["params"]["AttributionModels"] = attribution_models
    
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
    parser.add_argument(
        "--section",
        default="all",
        choices=["all", "total", "daily", "device", "criteria", "regions", "placements", "queries", "ads"],
        help="Какой раздел выгружать (чтобы не зависало — запускай по одному разделу).",
    )
    parser.add_argument(
        "--goals",
        default=None,
        help="ID целей Метрики через запятую. Пример: 20002,20003 (не номер счётчика!)",
    )
    parser.add_argument(
        "--attrib",
        default=None,
        help="Модели атрибуции через запятую. Пример: LC,LSC,LYDC,AUTO",
    )
    args = parser.parse_args()

    campaign_id = str(args.campaign_id).strip()

    date_to = args.date_to or datetime.now().strftime("%Y-%m-%d")
    if args.date_from:
        date_from = args.date_from
    else:
        date_from = (datetime.now() - timedelta(days=max(1, args.days))).strftime("%Y-%m-%d")

    goals = None
    if args.goals:
        goals = [g.strip() for g in args.goals.split(",") if g.strip()]
        if not goals:
            goals = None

    attrib = None
    if args.attrib:
        attrib = [a.strip() for a in args.attrib.split(",") if a.strip()]
        if not attrib:
            attrib = None

    section = args.section

    print("╔════════════════════════════════════════════════════════════╗")
    print("║              📈 СТАТИСТИКА КАМПАНИИ Я.ДИРЕКТ               ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Campaign ID: {campaign_id:<42}║")
    print(f"║  Период: {date_from} — {date_to:<30}║")
    print("╚════════════════════════════════════════════════════════════╝")
    if goals:
        print(f"🎯 Goals: {', '.join(goals)}")
        print("   (в ответе колонки будут вида Conversions_<goalId>_<model>)")
    if attrib:
        print(f"🧭 AttributionModels: {', '.join(attrib)}")
    
    all_data = {}
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. ОБЩАЯ СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════════
    if section in ("all", "total"):
        print_section("ОБЩАЯ СТАТИСТИКА")
    
        try:
            data = fetch_report(
                campaign_id,
                date_from,
                date_to,
                "CAMPAIGN_PERFORMANCE_REPORT",
                ["Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Sessions", "Conversions", "ConversionRate", "CostPerConversion"],
                "Total",
                goals=goals,
                attribution_models=attrib,
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
            sessions = row.get("Sessions")

            print(f"""
   👁️  Показы:         {impressions:,}
   🖱️  Клики:          {clicks:,}
   📈 CTR:            {ctr}%
   💰 Расход:         {cost} руб
   💵 Ср. цена клика: {avg_cpc} руб
   🧭 Sessions:       {sessions if sessions is not None else '—'}
""")
            all_data["total"] = data

    if section == "total":
        # Экспорт только того, что успели собрать
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
        return
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. ПО ДНЯМ
    # ═══════════════════════════════════════════════════════════════════
    if section in ("all", "daily"):
        print_section("ПО ДНЯМ")
    
        try:
            data = fetch_report(
                campaign_id,
                date_from,
                date_to,
                "CAMPAIGN_PERFORMANCE_REPORT",
                ["Date", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Sessions"],
                "Daily",
                "Date",
                goals=goals,
                attribution_models=attrib,
            )
        except KeyboardInterrupt:
            print("\n   ⚠️ Прервано пользователем")
            return
    
        if data:
            # Сортируем по дате
            data.sort(key=lambda x: x.get("Date", ""))

            print(f"   {'Дата':<12} {'Показы':>8} {'Клики':>7} {'CTR':>7} {'CPC':>8} {'Расход':>10} {'Sess':>7}")
            print("   " + "-"*64)

            for row in data:
                date = row.get("Date", "")
                impressions = row.get("Impressions", "0")
                clicks = row.get("Clicks", "0")
                ctr = row.get("Ctr", "0")
                cpc = row.get("AvgCpc", "0")
                cost = row.get("Cost", "0")
                sessions = row.get("Sessions", "—")

                print(f"   {date:<12} {impressions:>8} {clicks:>7} {ctr:>6}% {cpc:>7}р {cost:>9}р {sessions:>7}")

            all_data["daily"] = data

    if section == "daily":
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
        return
    
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
            ["Device", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Sessions", "Conversions", "ConversionRate", "CostPerConversion"],
            "Device",
            "Cost",
            goals=goals,
            attribution_models=attrib,
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

    if section == "device":
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
        return
    
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
            ["Criterion", "CriteriaType", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost", "Sessions", "Conversions", "ConversionRate", "CostPerConversion"],
            "Keywords",
            "Cost",
            goals=goals,
            attribution_models=attrib,
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

    if section == "criteria":
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
        return
    
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
            ["LocationOfPresenceName", "Impressions", "Clicks", "Ctr", "Cost", "Sessions", "Conversions", "ConversionRate", "CostPerConversion"],
            "Regions",
            "Cost",
            goals=goals,
            attribution_models=attrib,
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

    if section == "regions":
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
        return
    
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
            ["AdNetworkType", "Placement", "Impressions", "Clicks", "Ctr", "Cost", "Sessions", "Conversions", "ConversionRate", "CostPerConversion"],
            "Placements",
            "Cost",
            goals=goals,
            attribution_models=attrib,
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

    if section == "placements":
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
        return
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. ПОИСКОВЫЕ ЗАПРОСЫ (что реально вводили)
    # ═══════════════════════════════════════════════════════════════════
    # SEARCH_QUERY часто самый тяжёлый отчёт. Для --section=ads и т.п. его пропускаем.
    if section in ("all", "queries"):
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
                goals=goals,
                attribution_models=attrib,
            )
        except KeyboardInterrupt:
            print("\n   ⚠️ Прервано пользователем")
            return

    # ═══════════════════════════════════════════════════════════════════
    # 8. ПО ОБЪЯВЛЕНИЯМ (AD_PERFORMANCE_REPORT)
    # ═══════════════════════════════════════════════════════════════════
    if section in ("all", "ads"):
        print_section("ПО ОБЪЯВЛЕНИЯМ (TOP-20 по расходу)")

        try:
            data = fetch_report(
                campaign_id,
                date_from,
                date_to,
                "AD_PERFORMANCE_REPORT",
                [
                    "AdId",
                    "AdGroupId",
                    "Impressions",
                    "Clicks",
                    "Ctr",
                    "AvgCpc",
                    "Cost",
                    "Sessions",
                    "Conversions",
                    "ConversionRate",
                    "CostPerConversion",
                ],
                "Ads",
                "Cost",
                goals=goals,
                attribution_models=attrib,
            )
            if data:
                all_data["ads"] = data
                for row in data[:20]:
                    print(
                        f"   AdId={row.get('AdId')} | "
                        f"impr={row.get('Impressions')} clicks={row.get('Clicks')} "
                        f"cost={row.get('Cost')} ctr={row.get('Ctr')}%"
                    )
        except KeyboardInterrupt:
            print("\n   ⚠️ Прервано пользователем")
            return

    if section == "ads":
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

    if section == "queries":
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
        return
    
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
