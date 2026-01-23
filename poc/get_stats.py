"""
📊 Полная статистика кампании Яндекс Директ
Reports API v5: https://yandex.ru/dev/direct/doc/ru/reports
"""
import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Загружаем токен
TOKEN = Path("token.txt").read_text().strip()
CAMPAIGN_ID = "706552117"
REPORT_URL = "https://api.direct.yandex.com/json/v5/reports"

# Даты
DATE_FROM = "2026-01-22"  # Когда запустил кампанию
DATE_TO = datetime.now().strftime("%Y-%m-%d")

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

def fetch_report(report_type: str, field_names: list, report_name: str, order_by: str = None) -> list:
    """Получает отчёт из Reports API"""
    
    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": DATE_FROM,
                "DateTo": DATE_TO,
                "Filter": [
                    {"Field": "CampaignId", "Operator": "EQUALS", "Values": [CAMPAIGN_ID]}
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
    
    resp = requests.post(REPORT_URL, headers=get_headers(), json=body)
    
    if resp.status_code == 200:
        lines = resp.text.strip().split("\n")
        if len(lines) >= 2:
            headers = lines[0].split("\t")
            result = []
            for line in lines[1:]:
                data = line.split("\t")
                result.append(dict(zip(headers, data)))
            return result
    elif resp.status_code == 201 or resp.status_code == 202:
        print(f"   ⏳ Отчёт готовится... (status {resp.status_code})")
        return []
    else:
        print(f"   ❌ Ошибка {resp.status_code}: {resp.text[:200]}")
        return []
    
    return []


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print('='*60)


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        📈 СТАТИСТИКА КАМПАНИИ EXECAI - DEVOPS IT           ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Campaign ID: {CAMPAIGN_ID}                              ║")
    print(f"║  Период: {DATE_FROM} — {DATE_TO}                       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    all_data = {}
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. ОБЩАЯ СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════════
    print_section("ОБЩАЯ СТАТИСТИКА")
    
    data = fetch_report(
        "CAMPAIGN_PERFORMANCE_REPORT",
        ["Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
        "Total"
    )
    
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
    
    data = fetch_report(
        "CAMPAIGN_PERFORMANCE_REPORT",
        ["Date", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
        "Daily",
        "Date"
    )
    
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
    
    data = fetch_report(
        "CAMPAIGN_PERFORMANCE_REPORT",
        ["Device", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
        "Device",
        "Cost"
    )
    
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
    
    data = fetch_report(
        "CRITERIA_PERFORMANCE_REPORT",
        ["Criterion", "CriteriaType", "Impressions", "Clicks", "Ctr", "AvgCpc", "Cost"],
        "Keywords",
        "Cost"
    )
    
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
    
    data = fetch_report(
        "CAMPAIGN_PERFORMANCE_REPORT",
        ["LocationOfPresenceName", "Impressions", "Clicks", "Ctr", "Cost"],
        "Regions",
        "Cost"
    )
    
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
    
    data = fetch_report(
        "CAMPAIGN_PERFORMANCE_REPORT",
        ["AdNetworkType", "Placement", "Impressions", "Clicks", "Ctr", "Cost"],
        "Placements",
        "Cost"
    )
    
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
    
    data = fetch_report(
        "SEARCH_QUERY_PERFORMANCE_REPORT",
        ["Query", "Impressions", "Clicks", "Ctr", "Cost"],
        "SearchQueries",
        "Cost"
    )
    
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
