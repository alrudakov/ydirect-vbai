Ниже по BidModifiers v5 (JSON) и Campaigns.update для минус-площадок, с тем, как реально “вырубить” показы на устройстве.

## BidModifiers v5: куда слать и как выглядит JSON

JSON-эндпоинт: `https://api.direct.yandex.com/json/v5/bidmodifiers` (есть и `.../json/v501/bidmodifiers`). ([Yandex][1])
Методы: `add | delete | get | set | toggle`. ([Yandex][1])

`BidModifier` в API это коэффициент в процентах, ставка умножается на `BidModifier/100`. Допустимый диапазон для Mobile/Tablet (и для device-корректировок вообще) в `add` описан как **от 0 до 1300**. ([Yandex][2])

### Как это сопоставляется с “-100%..+1200%” в интерфейсе

В справке Директа часто пишут, что корректировка бывает от **-100% (показы отключены)** до **+1200%**. ([Yandex][3])
В API это выглядит так:

* **-100% в UI = BidModifier = 0** (множитель 0, показы на этом устройстве фактически обнуляются)
* **0% в UI = BidModifier = 100** (множитель 1.0, “без корректировки”)
* **+1200% в UI = BidModifier = 1300** (множитель 13.0)

То есть ответ на “0 или -100?”: **в API ставишь 0**. Значений -100 в `BidModifier` для Mobile/Tablet в API нет, там 0..1300. ([Yandex][2])

---

## 1) Отключение мобильных устройств (MobileAdjustment)

Создать корректировку на уровне кампании и “убить” мобильный трафик: `BidModifier: 0`, без `OperatingSystemType` (значит для любой ОС). ([Yandex][2])

```json
{
  "method": "add",
  "params": {
    "BidModifiers": [
      {
        "CampaignId": 12345678,
        "MobileAdjustment": {
          "BidModifier": 0
        }
      }
    ]
  }
}
```

Если нужно отключить только iOS или только Android, указываешь `OperatingSystemType`. ([Yandex][2])

```json
{
  "method": "add",
  "params": {
    "BidModifiers": [
      {
        "CampaignId": 12345678,
        "MobileAdjustment": {
          "BidModifier": 0,
          "OperatingSystemType": "IOS"
        }
      }
    ]
  }
}
```

---

## 2) Отключение планшетов (TabletAdjustment)

Абсолютно так же, только `TabletAdjustment`. Диапазон `BidModifier` и смысл такие же. ([Yandex][2])

```json
{
  "method": "add",
  "params": {
    "BidModifiers": [
      {
        "CampaignId": 12345678,
        "TabletAdjustment": {
          "BidModifier": 0
        }
      }
    ]
  }
}
```

---

## Важное ограничение: нельзя “обнулить все устройства”

В доке `add` прямо есть ограничение для device-корректировок на уровне группы: **нельзя одновременно поставить 0 на мобильные (без указания ОС) и на “компьютеры/планшеты/Smart TV”**. Иначе говоря, полностью выключить все устройства через корректировки нельзя, хотя один конкретный тип (например, mobile) выключить можно. ([Yandex][2])

Практически:

* хочешь “только десктоп” -> mobile=0, tablet=0, desktop=100 (или не задавать), но следи, чтобы не получилось “все 0”.
* хочешь “только mobile” -> desktop/tablet=0, mobile=100 (или не задавать) и т.д.

---

## 3) Добавление минус-площадок (ExcludedSites) в кампанию через Campaigns.update

Это не BidModifiers, это Campaigns.update. Поле: `ExcludedSites.Items` (до 1000 элементов). Можно передавать домены сайтов, bundle/package приложений, названия SSP (их можно взять через Dictionaries.get). ([Yandex][4])

JSON пример:

```json
{
  "method": "update",
  "params": {
    "Campaigns": [
      {
        "Id": 12345678,
        "ExcludedSites": {
          "Items": [
            "example.com",
            "badsite.ru",
            "com.someapp.android",
            "1234567890" 
          ]
        }
      }
    ]
  }
}
```

---

## Коротко по твоим вопросам

* **Какие значения BidModifier допустимы?** Для MobileAdjustment/TabletAdjustment: **0..1300**, ставка умножается на `BidModifier/100`. ([Yandex][2])
* **Как полностью отключить показы на устройстве?** Ставишь `BidModifier: 0` для нужного `*Adjustment`. Это эквивалент “-100%” из интерфейса. ([Yandex][2])
* **0 или -100?** В API именно **0** (а -100% это термин интерфейса/справки). ([Yandex][2])

Если скажешь, ты правишь корректировки на уровне кампании или групп (и какой тип кампании: Text/Unified), я дам готовые шаблоны под `set` (когда корректировка уже существует) и под массовое обновление пачки кампаний/групп без дублей и конфликтов.

[1]: https://yandex.com/dev/direct/doc/en/bidmodifiers/bidmodifiers?utm_source=chatgpt.com "BidModifiers | Yandex Direct API"
[2]: https://yandex.com/dev/direct/doc/en/bidmodifiers/add "add | Yandex Direct API"
[3]: https://mobi.yandex.com/support/direct/en/impressions/bids-adjustment?utm_source=chatgpt.com "Bid adjustments - Targeting (identify your target audience) | Yandex Direct"
[4]: https://yandex.com/dev/direct/doc/en/campaigns/update "update | Yandex Direct API"






### Ads.moderate (API v5): что обязательно

По документации у `Ads.moderate` **обязателен `params.SelectionCriteria`**, и внутри него **обязателен `Ids`**. То есть это не “Ids или SelectionCriteria”, а **SelectionCriteria с Ids**. ([Yandex][1])

---

## JSON пример запроса (отправить объявления на модерацию)

POST на JSON-эндпоинт сервиса Ads:
`https://api.direct.yandex.com/json/v5/ads` (или `.../json/v501/ads`). ([Yandex][2])

Тело:

```json
{
  "method": "moderate",
  "params": {
    "SelectionCriteria": {
      "Ids": [11111111, 22222222, 33333333]
    }
  }
}
```

Это ровно тот формат, который приведен в доке (IdsCriteria). ([Yandex][1])

---

## Ограничения, из-за которых часто “не отправляется”

* За один вызов: **до 10 000 объявлений**. ([Yandex][1])
* На модерацию можно отправить только объявления со статусом **DRAFT**. ([Yandex][1])
* Нельзя отправить, если в группе нет условий показа (ключи/аудитории/динамика), или если кампания архивная. ([Yandex][1])

---

Если хочешь, скину еще готовый `curl` с нужными заголовками (Authorization, Client-Login для агентского, Accept-Language), но по сути для метода в JSON главное именно структура выше.

[1]: https://yandex.com/dev/direct/doc/en/ads/moderate "moderate | Yandex Direct API"
[2]: https://yandex.com/dev/direct/doc/en/ads/ads?utm_source=chatgpt.com "Ads | Yandex Direct API"
