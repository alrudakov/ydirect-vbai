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


По `BidModifiers.get` **`SelectionCriteria.Levels` обязателен** и допустимые значения там ровно два: **`CAMPAIGN`** и **`AD_GROUP`**. ([Yandex][1])

### Какие значения Levels допустимы

* `CAMPAIGN` (корректировки, заданные на уровне кампаний)
* `AD_GROUP` (корректировки, заданные на уровне групп объявлений) ([Yandex][1])

Можно передать **оба** в массиве, если хочешь получить корректировки и по кампаниям, и по группам. ([Yandex][1])

---

## JSON пример `BidModifiers.get` с обязательным `Levels`

Минимально нужно:

* `params.SelectionCriteria` (обязателен)
* в нем `Levels` (обязателен)
* плюс хотя бы один из `CampaignIds` / `AdGroupIds` / `Ids`
* и `FieldNames` (обязателен) ([Yandex][1])

Пример: получить корректировки по **кампании** и по **ее группам** (оба уровня), вывести базовые поля + значения для mobile/tablet:

```json
{
  "method": "get",
  "params": {
    "SelectionCriteria": {
      "CampaignIds": [12345678],
      "Levels": ["CAMPAIGN", "AD_GROUP"]
    },
    "FieldNames": ["Id", "CampaignId", "AdGroupId", "Level", "Type"],
    "MobileAdjustmentFieldNames": ["BidModifier", "OperatingSystemType"],
    "TabletAdjustmentFieldNames": ["BidModifier", "OperatingSystemType"],
    "Page": { "Limit": 10000, "Offset": 0 }
  }
}
```

`Levels` тут обязателен, и список значений именно `CAMPAIGN | AD_GROUP`. ([Yandex][1])

---

### Быстрые подсказки

* Если хочешь **только кампанийные** корректировки: `Levels: ["CAMPAIGN"]`.
* Если хочешь **только групповые**: `Levels: ["AD_GROUP"]` (и логично фильтровать `AdGroupIds`, либо `CampaignIds`, если нужно “все группы кампании”). ([Yandex][1])

[1]: https://yandex.com/dev/direct/doc/en/bidmodifiers/get "get | Yandex Direct API"



BIDS


Сервис предназначен для назначения ставок ключевым фразам и автотаргетингам.

Сервис позволяет также получить данные, полезные при подборе ставок: цены позиций показа и охвата аудитории, ставки конкурентов.

Все ставки и цены указываются в валюте пользователя.

Методы
set | setAuto | get

Адрес WSDL-описания
https://api.direct.yandex.com/v5/bids?wsdl

https://api.direct.yandex.com/v501/bids?wsdl

Адрес для SOAP-запросов
https://api.direct.yandex.com/v5/bids

https://api.direct.yandex.com/v501/bids

Адрес для JSON-запросов
https://api.direct.yandex.com/json/v5/bids

https://api.direct.yandex.com/json/v501/bids



get
Возвращает ставки для ключевых фраз и автотаргетингов, отвечающих заданным критериям, а также данные, полезные при подборе ставок: данные аукциона по позициям показа на поиске и ставки для охвата различных долей аудитории в сетях.

Ставки можно получить независимо от того, какая стратегия выбрана в кампании — ручная или автоматическая.

Alert

Все возвращаемые денежные значения представляют собой целые числа — результат умножения ставки или цены на 1 000 000.

Узнайте больше
Как работает метод get
Автотаргетинг
Ограничения
Метод возвращает не более 10 000 объектов.

Запрос
Структура запроса в формате JSON:

{
  "method": "get",
  "params": { /* params */
    "SelectionCriteria": {  /* BidsSelectionCriteria */
      "KeywordIds": [(long), ... ],
      "AdGroupIds": [(long), ... ],
      "CampaignIds": [(long), ... ],
      "ServingStatuses": [( "ELIGIBLE" | "RARELY_SERVED" ), ... ]
    }, /* required */
    "FieldNames": [( "KeywordId" | ... | "AuctionBids" ), ... ], /* required */
    "Page": {  /* LimitOffset */
      "Limit": (long),
      "Offset": (long)
    }
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / GetRequest (для SOAP)

SelectionCriteria

BidsSelectionCriteria

Критерий отбора ключевых фраз и автотаргетингов.

Да

FieldNames

array of BidFieldEnum

Имена параметров верхнего уровня, которые требуется получить.

Не запрашивайте параметры CompetitorsBids, SearchPrices, MinSearchPrice, CurrentSearchPrice, AuctionBids, если в кампании отключены показы на поиске (стратегия на поиске SERVING_OFF).

Не запрашивайте параметр ContextCoverage, если в кампании отключены показы в сетях (стратегия в сетях SERVING_OFF).

Да

Page

LimitOffset

Структура, задающая страницу при постраничной выборке данных.

Нет

Структура BidsSelectionCriteria

KeywordIds

array of long

Получить ставки для указанных ключевых фраз и автотаргетингов. Не более 10 000 элементов в массиве.

Один из параметров KeywordIds, AdGroupIds и CampaignIds (могут присутствовать все)

AdGroupIds

array of long

Получить ставки для ключевых фраз и автотаргетингов в указанных группах объявлений. От 1 до 1000 элементов в массиве.

CampaignIds

array of long

Получить ставки для ключевых фраз и автотаргетингов в указанных кампаниях. От 1 до 10 элементов в массиве.

ServingStatuses

array of ServingStatusEnum

Получить ставки для ключевых фраз и автотаргетингов с указанными статусами возможности показов группы. Описание статусов см. в разделе Статус возможности показов группы.

Нет

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "Bids": [{  /* BidGetItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "ServingStatus": ( "ELIGIBLE" | "RARELY_SERVED" ),
      "Bid": (long),
      "AutotargetingSearchBidIsAuto" : ("YES"|"NO"),
      "ContextBid": (long),
      "StrategyPriority": "NORMAL", /* nillable */
      "CompetitorsBids": [(long), ... ],
      "SearchPrices": [{  /* SearchPrices */
        "Position": ( "PREMIUMFIRST" | "PREMIUMBLOCK" | "FOOTERFIRST" | "FOOTERBLOCK" ),
        "Price": (long)
      }, ... ],
      "ContextCoverage": {  /* ContextCoverage */
        "Items": [{  /* ContextCoverageItem */
          "Probability": (decimal), /* required */
          "Price": (long) /* required */
        }, ... ]
      }, /* nillable */
      "MinSearchPrice": (long), /* nillable */
      "CurrentSearchPrice": (long), /* nillable */
      "AuctionBids": [{  /* AuctionBidItem */
        "Position": (string),
        "Bid": (long),
        "Price": (long)
      }, ... ]
    }, ... ],
    "LimitedBy": (long)
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / GetResponse (для SOAP)

Bids

array of BidGetItem

Ставки.

LimitedBy

long

Порядковый номер последнего возвращенного объекта. Передается в случае, если количество объектов в ответе было ограничено лимитом. См. раздел Постраничная выборка.

Структура BidGetItem

CampaignId

long

Идентификатор кампании, к которой относится ключевая фраза или автотаргетинг.

AdGroupId

long

Идентификатор группы объявлений, к которой относится ключевая фраза или автотаргетинг.

KeywordId

long

Идентификатор ключевой фразы или автотаргетинга.

ServingStatus

ServingStatusEnum

Статус возможности показов группы объявлений. Описание статусов см. в разделе Статус возможности показов группы.

Bid

long

Ставка на поиске.

AutotargetingSearchBidIsAuto

YesNoEnum

Признак включения опции автоматической ставки.

ContextBid

long

Ставка в сетях.

StrategyPriority

PriorityEnum, nillable

Приоритет ключевой фразы или автотаргетинга: NORMAL.

CompetitorsBids

array of long

Массив минимальных ставок для данной фразы за все позиции в спецразмещении и в блоке гарантированных показов.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), параметр не возвращается.

Для автотаргетинга параметр не возвращается.

SearchPrices

array of SearchPrices

Минимальные ставки для данной фразы за позиции показа на поиске.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), параметр не возвращается.

Для автотаргетинга параметр не возвращается.

ContextCoverage

ContextCoverage, nillable

Ставки для данной фразы, позволяющие достичь охвата различных долей аудитории сетей (прогноз). Служат ориентиром при подборе ставок.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), возвращается null (nil).

Если в кампании выбрана стратегия показа в сетях SERVING_OFF или NETWORK_DEFAULT, возвращается null (nil).

Для автотаргетинга возвращается null (nil).

MinSearchPrice

long, nillable

Минимальная ставка, при которой возможен показ на поиске.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), возвращается null (nil).

Для автотаргетинга возвращается null (nil).

CurrentSearchPrice

long, nillable

Текущая цена клика на поиске. Эта цена может быть списана при клике по объявлению на странице результатов поиска (по запросу, точно соответствующему ключевой фразе). Подробнее см. в разделе Расчет цены клика помощи Директа.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), возвращается null (nil).

Для автотаргетинга возвращается null (nil).

AuctionBids

array of AuctionBidItem

Результаты торгов по фразе.

Если в группе только графические объявления, параметр не возвращается.

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), параметр не возвращается.

Для автотаргетинга параметр не возвращается.

Структура SearchPrices

Position

PositionEnum

Позиция показа на поиске:

FOOTERBLOCK — минимальная ставка за 4-ю позицию в гарантии (вход в блок гарантированных показов);
FOOTERFIRST — минимальная ставка за 1-ю позицию в гарантии;
PREMIUMBLOCK — минимальная ставка за 4-ю позицию в спецразмещении (вход в спецразмещение);
PREMIUMFIRST — минимальная ставка за 1-ю позицию в спецразмещении.
Price

long

Минимальная ставка за указанную позицию.

Структура ContextCoverage

Items

array of ContextCoverageItem

Ставки для данной фразы, позволяющие достичь охвата различных долей аудитории в сетях (прогноз). Служат ориентиром при подборе ставок.

Структура ContextCoverageItem

Probability

decimal

Частота показа (доля аудитории) в сетях. Указывается в процентах от 0 до 100.

Price

long

Ставка в сетях, при которой прогнозируется указанная частота показа.

Структура AuctionBidItem

Position

string

Позиция показа: Pmn, где

m — номер блока (1 — спецразмещение, 2 — блок гарантированных показов);
n — номер позиции в рамках блока.
Например, P12 — 2-я позиция в спецразмещении, P21 — 1-я позиция в блоке гарантированных показов.

Bid

long

Минимальная ставка за указанную позицию.

Price

long

Списываемая цена для указанной позиции.

Примеры
Пример запроса

{
  "method" : "get",
  "params" : {
    "SelectionCriteria" : {
      "KeywordIds" : [
        151289987,
        151289988,
        414808783,
        414808784,
        414808785,
        414811825,
        414811826,
        414811827,
        1574449505
      ]
    },
    "FieldNames" : [
      "KeywordId",
      "Bid",
      "ContextBid"
    ]
  }
}

Пример ответа

{
  "result" : {
    "Bids" : [
      {
        "KeywordId" : 414808783,
        "Bid" : 10000,
        "ContextBid" : 0
      },
      {
        "Bid" : 10000,
        "KeywordId" : 414808784,
        "ContextBid" : 0
      },
      {
        "Bid" : 10000,
        "KeywordId" : 414808785,
        "ContextBid" : 0
      },
      {
        "Bid" : 10000,
        "KeywordId" : 1574449505,
        "ContextBid" : 0
      }
    ]
  }
}





set
Назначает фиксированные ставки для ключевых фраз и автотаргетингов.

Ставку можно назначить:

для отдельной ключевой фразы или автотаргетинга;

для всех ключевых фраз и автотаргетинга в группе объявлений;

для всех ключевых фраз и автотаргетингов в кампании.

Ставку можно назначить в зависимости от того, какая стратегия показа выбрана в кампании:

Если выбрана стратегия показа на поиске HIGHEST_POSITION, то можно указать параметр SearchBid.
Если выбрана стратегия показа в сетях MAXIMUM_COVERAGE или MANUAL_CPM, то можно указать параметр NetworkBid.
В случае если элемент входного массива содержит параметры, не соответствующие стратегии, то значения этих параметров изменены не будут.

Если элемент входного массива содержит одновременно и параметры, соответствующие стратегии, и параметры, не соответствующие стратегии, то в результате операции будут изменены значения только параметров, соответствующих стратегии, и выдано предупреждение.
Если элемент входного массива содержит только параметры, не соответствующие стратегии, то операция не будет выполнена и будет возвращена ошибка.
Alert

Ставки и цены передаются через API Директа в виде целых чисел. Передаваемое значение представляет собой ставку или цену, умноженную на 1 000 000.

Все ставки и цены указываются в валюте пользователя.

Узнайте больше
Операции над массивом объектов
Автотаргетинг
Ограничения
В одном запросе можно назначить ставки только для однородных объектов — либо только для кампаний, либо только для групп, либо только для ключевых фраз и автотаргетингов.

Количество объектов в одном вызове метода:

кампаний — не более 10;
групп — не более 1000;
ключевых фраз и автотаргетингов — не более 10 000.
Запрос
Структура запроса в формате JSON:

{
  "method": "set",
  "params": { /* params */
    "Bids": [{  /* BidSetItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "Bid": (long),
      "AutotargetingSearchBidIsAuto" : ("YES"|"NO"),
      "ContextBid": (long),
      "StrategyPriority": ( "LOW" | "NORMAL" | "HIGH" )
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / SetRequest (для SOAP)

Bids

array of BidSetItem

Ставки.

Да

Структура BidSetItem

CampaignId

long

Идентификатор кампании. Указывается, если требуется назначить единую ставку для всех ключевых фраз и автотаргетингов в кампании.

Либо CampaignId, либо AdGroupId, либо KeywordId

AdGroupId

long

Идентификатор группы объявлений. Указывается, если требуется назначить единую ставку для всех ключевых фраз и автотаргетингов в группе.

KeywordId

long

Идентификатор фразы. Указывается, если требуется назначить ставку для отдельной ключевой фразы или автотаргетинга.

Bid

long

Ставка на поиске, умноженная на 1 000 000. Целое число. Только для ручной стратегии.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Хотя бы один из параметров Bid, ContextBid, StrategyPriority, AutotargetingSearchBidIsAuto

AutotargetingSearchBidIsAuto

YesNoEnum

Признак включения опции автоматической ставки.

Можно одновременно указать ручную ставку (Bid) и включить автоставку (AutotargetingSearchBidIsAuto). В этом случае будет работать автоставка, а ручная будет использоваться в случае отключения автоматической.

Если указана ручная ставка Bid: значение автоматической ставки (AutotargetingSearchBidIsAuto) будет выставлено NO, если в явном виде не прислано иное значение автоставки.

Если не указана ручная ставка Bid: значение автоматической ставки (AutotargetingSearchBidIsAuto) будет выставлено YES, если в явном виде не прислано иное значение автоставки.

ContextBid

long

Ставка в сетях, умноженная на 1 000 000. Целое число. Только для ручной стратегии с независимым управлением ставками в сетях.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Alert

Показ графического объявления возможен только при условии, что ставка не ниже минимальной ставки для объявления с включенным в него изображением.

StrategyPriority

PriorityEnum

Приоритет фразы: LOW, NORMAL или HIGH. Только для автоматической стратегии.

Alert

Параметр не используется, переданное значение игнорируется.

Alert

Параметры CampaignId, AdGroupId и KeywordId являются взаимоисключающими. В одном запросе можно указывать только один из этих параметров.

Ответ
Структура ответа в формате JSON:

{
  "result": {  /* result */
    "SetResults": [{  /* BidActionResult */
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long)
    }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / SetResponse (для SOAP)

SetResults

array of BidActionResult

Результаты назначения ставок.

Структура BidActionResult

CampaignId

long

Идентификатор кампании. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

AdGroupId

long

Идентификатор группы объявлений. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

KeywordId

long

Идентификатор ключевой фразы или автотаргетинга. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.

Примеры
Пример запроса

{
  "method" : "set",
  "params" : {
    "Bids" : [
      {
        "StrategyPriority" : "HIGH",
        "CampaignId" : 4193065
      },
      {
        "Bid" : 14000,
        "CampaignId" : 7273721
      }
    ]
  }
}

Пример ответа

{
  "result" : {
    "SetResults" : [
      {
        "CampaignId" : 4193065
      },
      {
        "CampaignId" : 7273721
      }
    ]
  }
}





setAuto
Конструктор ставок — рассчитывает ставки для фраз по заданному алгоритму.

Метод выполняет назначение ставок в асинхронном режиме и не возвращает ставки. Получить ставки можно методом get.

Ставку можно назначить, только если в кампании выбрана ручная стратегия.

Метод не сбрасывает значение автоматической ставки (AutotargetingSearchBidIsAuto).

В случае если элемент входного массива содержит ставки, не соответствующие стратегии, то эти ставки применены не будут.

Если в кампании автоматическая стратегия, возвращается ошибка.
Если в кампании отключены показы на поиске, а в параметре Scope передано только значение SEARCH, то возвращается ошибка. Если переданы оба значения — SEARCH и NETWORK, то будут обновлены ставки только в сетях и выдано предупреждение.
Если в кампании ручная стратегия на поиске, при этом не предусмотрено независимое управление ставками в сетях или показы в сетях отключены, а в параметре Scope передано только значение NETWORK, то возвращается ошибка. Если переданы оба значения — SEARCH и NETWORK, то будут обновлены ставки только на поиске и выдано предупреждение.
Alert

Ставки и цены передаются через API Директа в виде целых чисел. Передаваемое значение представляет собой ставку или цену, умноженную на 1 000 000.

Все ставки и цены указываются в валюте пользователя.

Чтобы назначить ставки на поиске, передайте в параметре Scope значение SEARCH.

Для расчета ставки используются значения, переданные в параметрах Position, IncreasePercent, CalculateBy, MaxBid.

Position

CalculateBy

Формула расчета ставки

FOOTERBLOCK

VALUE

Минимальная ставка за 4-ю позицию в гарантии + минимальная ставка за 4-ю позицию в гарантии × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 4-ю позицию в гарантии + (минимальная ставка за 1-ю позицию – минимальная ставка за 4-ю позицию в гарантии) × IncreasePercent / 100,

но не более MaxBid

FOOTERFIRST

VALUE

Минимальная ставка за 1-ю позицию в гарантии + минимальная ставка за 1-ю позицию в гарантии × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 1-ю позицию в гарантии + (минимальная ставка за 3-ю позицию в спецразмещении – минимальная ставка за 1-ю позицию в гарантии) × IncreasePercent / 100,

но не более MaxBid

PREMIUMBLOCK или P14

VALUE

Минимальная ставка за 4-ю позицию в спецразмещении + минимальная ставка за 4-ю позицию в спецразмещении × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 4-ю позицию в спецразмещении + (минимальная ставка за 3-ю позицию в спецразмещении – минимальная ставка за 4-ю позицию в спецразмещении) × IncreasePercent / 100,

но не более MaxBid

P13

VALUE

Минимальная ставка за 3-ю позицию в спецразмещении + минимальная ставка за 3-ю позицию в спецразмещении × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 3-ю позицию в спецразмещении + (минимальная ставка за 2-ю позицию в спецразмещении – минимальная ставка за 3-ю позицию в спецразмещении) × IncreasePercent / 100,

но не более MaxBid

P12

VALUE

Минимальная ставка за 2-ю позицию в спецразмещении + минимальная ставка за 2-ю позицию в спецразмещении × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 2-ю позицию в спецразмещении + (минимальная ставка за 1-ю позицию в спецразмещении – минимальная ставка за 2-ю позицию в спецразмещении) × IncreasePercent / 100,

но не более MaxBid

PREMIUMFIRST или P11

VALUE

Минимальная ставка за 1-ю позицию в спецразмещении + минимальная ставка за 1-ю позицию в спецразмещении × IncreasePercent / 100,

но не более MaxBid

DIFF

Минимальная ставка за 1-ю позицию в спецразмещении, но не более MaxBid

Note

Со временем активность конкурентов может поднять минимальную ставку за позицию, и она превысит ставку пользователя. Чем выше надбавка, тем больше вероятность, что объявление будет показываться на выбранной позиции, но и выше возможные расходы.









Узнайте больше
Операции над массивом объектов
Ограничения
В одном запросе можно назначить ставки только для однородных объектов — либо только для кампаний, либо только для групп, либо только для фраз. Метод не поддерживает назначение ставки отдельному автотаргетингу.

Количество объектов в одном вызове метода:

кампаний — не более 10;
групп — не более 1000;
фраз — не более 10 000.
Запрос
Структура запроса в формате JSON:

{
  "method": "setAuto",
  "params": { /* params */
    "Bids": [{  /* BidSetAutoItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "MaxBid": (long),
      "Position": ( "PREMIUMFIRST" | "PREMIUMBLOCK" | "FOOTERFIRST" | "FOOTERBLOCK" | "P11" | "P12" | "P13" | "P14" | "P21" | "P22" | "P23" | "P24" ),
      "IncreasePercent": (int),
      "CalculateBy": ( "VALUE" | "DIFF" ),
      "ContextCoverage": (int),
      "Scope": [( "SEARCH" | "NETWORK" ), ... ] /* required */
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / SetAutoRequest (для SOAP)

Bids

array of BidSetAutoItem

Параметры расчета ставок.

Да

Структура BidSetAutoItem

CampaignId

long

Идентификатор кампании. Указывается, если требуется обновить ставки для всех фраз кампании.

Либо CampaignId, либо AdGroupId, либо KeywordId

AdGroupId

long

Идентификатор группы объявлений. Указывается, если требуется обновить ставки для всех фраз группы.

KeywordId

long

Идентификатор фразы. Указывается, если требуется обновить ставку для отдельной фразы.

Alert

Идентификатор автотаргетинга не допускается.

Scope

array of ScopeEnum

Указывает, какие ставки назначить. Массив может содержать следующие элементы (один или оба):

SEARCH — назначить ставки на поиске (Bid). Для расчета ставок используются значения, переданные в параметрах Position, IncreasePercent, CalculateBy, MaxBid.
NETWORK — назначить ставки в сетях (ContextBid). Для расчета ставок используются значения, переданные в параметрах ContextCoverage, IncreasePercent, MaxBid.
Да

MaxBid

long

Ограничение на ставку, умноженное на 1 000 000. Целое число.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Нет

Position

PositionEnum

Позиция показа, ставка за которую используется как основа для расчета ставок на поиске.

К цене указанной позиции прибавляется надбавка (см. параметры IncreasePercent и CalculateBy).

Если в массиве Scope присутствует значение Search

IncreasePercent

int

Процент надбавки от 0 до 1000. Если не задан, надбавка не рассчитывается.

Нет

CalculateBy

CalculateByEnum

База, на основе которой рассчитывается надбавка:

VALUE — цена позиции, указанной в Position.

DIFF — разница между минимальной ставкой за позицию, указанную в параметре Position, и за следующую позицию.

При выборе позиции PREMIUMFIRST (P11) следующая позиция отсутствует и надбавка равна нулю. Это же верно при выборе позиции FOOTERFIRST (P21), если стоимость следующей позиции PREMIUMBLOCK (P14) меньше (редкая, но возможная ситуация).

Если в массиве Scope присутствует значение Search и задан параметр IncreasePercent

ContextCoverage

int

Частота показа (доля аудитории) в сетях. Указывается в процентах от 1 до 100.

К ставке, необходимой для охвата выбранной доли аудитории, прибавляется надбавка (см. параметр IncreasePercent).

Если в массиве Scope присутствует значение Network

Alert

Параметры CampaignId, AdGroupId и KeywordId являются взаимоисключающими. В одном запросе можно указывать только один из этих параметров.

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "SetAutoResults": [{  /* BidActionResult */
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
     }, ... ],
    "CampaignId": (long),
    "AdGroupId": (long),
    "KeywordId": (long)
   }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / SetAutoResponse (для SOAP)

SetAutoResults

array of BidActionResult

Результаты назначения ставок.

Структура BidActionResult

CampaignId

long

Идентификатор кампании. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

AdGroupId

long

Идентификатор группы объявлений. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

KeywordId

long

Идентификатор ключевой фразы. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.

Примеры
Пример запроса

Назначить на поиске цену 1-го места в гарантии + 50% от разницы до спецразмещения, но не более 0,25.

{
  "method" : "setAuto",
  "params" : {
    "Bids" : [
      {
        "Scope" : [
          "SEARCH"
        ],
        "IncreasePercent" : 50,
        "CalculateBy" : "DIFF",
        "Position" : "FOOTERFIRST",
        "KeywordId" : 1574449505,
        "MaxBid" : 250000
      }
    ]
  }
}

Пример ответа

{
  "result" : {
    "SetAutoResults" : [
      {
        "KeywordId" : 1574449505
      }
    ]
  }
}




BidModifiers
Сервис предназначен для управления корректировками ставок.

Методы
add | delete | get | set

Адрес WSDL-описания
https://api.direct.yandex.com/v5/bidmodifiers?wsdl

https://api.direct.yandex.com/v501/bidmodifiers?wsdl

Адрес для SOAP-запросов
https://api.direct.yandex.com/v5/bidmodifiers

https://api.direct.yandex.com/v501/bidmodifiers

Адрес для JSON-запросов
https://api.direct.yandex.com/json/v5/bidmodifiers

https://api.direct.yandex.com/json/v501/bidmodifiers




add
Создает корректировки ставок.

Узнайте больше
Как работает метод add
Как обрабатывать ошибки
Корректировки (BidModifier)
Ограничения
Не более 1 корректировки ставок на мобильных для одной кампании или группы объявлений.

Не более 1 корректировки ставок для видеодополнений для одной кампании или группы объявлений.

Не более 12 корректировок по полу и возрасту для одной кампании или группы объявлений.

Не более 100 корректировок для целевой аудитории для одной кампании или группы объявлений.

Корректировки на мобильных нельзя создать для кампаний и групп объявлений для продвижения мобильных приложений.

Корректировки на компьютерах, планшетах, Smart TV можно создать для групп текстово-графических и медийных объявлений.

Корректировки для видеодополнений можно создать только для кампаний и групп текстово-графических объявлений.

Корректировки на группу можно создать только для единых перфоманс групп.

Подробнее о соответствии типов корректировок типам кампаний и групп объявлений см. в разделе Соответствие типов корректировок типам кампаний и групп.

Запрос
Структура запроса в формате JSON:

{
  "method": "add",
  "params": { /* params */
    "BidModifiers": [{  /* BidModifierAddItem */
      "MobileAdjustment": {  /* MobileAdjustmentAdd */
        "BidModifier": (int), /* required */
        "OperatingSystemType": ( "IOS" | "ANDROID" )
      },
      "TabletAdjustment": {  /* MobileAdjustmentAdd */
        "BidModifier": (int), /* required */
        "OperatingSystemType": ( "IOS" | "ANDROID" )
      },
      "DesktopAdjustment": {  /* DesktopAdjustmentAdd */
        "BidModifier": (int) /* required */
      },
      "DesktopOnlyAdjustment": {  /* DesktopAdjustmentAdd */
        "BidModifier": (int) /* required */
      },
      "SmartTvAdjustment": {  /* SmartTvAdjustmentAdd */
        "BidModifier": (int) /* required */
      },
      "DemographicsAdjustments": [{  /* DemographicsAdjustmentAdd */
        "Gender": ( "GENDER_MALE" | "GENDER_FEMALE" ),
        "Age": ( "AGE_0_17" | "AGE_18_24" | "AGE_25_34" | "AGE_35_44" | "AGE_45" | "AGE_45_54" | "AGE_55" ),
        "BidModifier": (int) /* required */
      }, ... ],
      "RetargetingAdjustments": [{  /* RetargetingAdjustmentAdd */
        "RetargetingConditionId": (long), /* required */
        "BidModifier": (int) /* required */
      }, ... ],
      "RegionalAdjustments": [{    /* RegionalAdjustmentAdd */
        "RegionId": (long), /* required */
        "BidModifier": (int) /* required */
      }, ... ],
      "VideoAdjustment": { /* VideoAdjustmentAdd */
        "BidModifier": (int) /* required */
      },
      "SmartAdAdjustment" : { /* SmartAdAdjustmentAdd */
        "BidModifier": (int) /* required */
      },
      "SerpLayoutAdjustments": [{  /* SerpLayoutAdjustmentAdd */
        "SerpLayout": ( "ALONE" | "SUGGEST" ), /* required */
        "BidModifier": (int) /* required */
      }, ... ],
      "IncomeGradeAdjustments": [{  /* IncomeGradeAdjustmentAdd */
        "Grade": ( "VERY_HIGH" | "HIGH" | "ABOVE_AVERAGE" ), /* required */
        "BidModifier": (int) /* required */
      }, ... ],
      "AdGroupAdjustment" : {
        "BidModifier" : (int) /* required */
      }
      "CampaignId": (long),
      "AdGroupId": (long)
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / AddRequest (для SOAP)

BidModifiers

array of BidModifierAddItem

Корректировки, которые требуется добавить. Не более 1000 элементов в массиве.

Да

Структура BidModifierAddItem

CampaignId

long

Идентификатор кампании. Указывается при создании корректировки на уровне кампании.

Либо CampaignId, либо AdGroupId

AdGroupId

long

Идентификатор группы объявлений. Указывается при создании корректировок на уровне группы.

MobileAdjustment

MobileAdjustmentAdd

Корректировка на мобильных.

Либо MobileAdjustment, либо TabletAdjustment, либо DesktopAdjustment, либо DesktopOnlyAdjustment, либо DemographicsAdjustments, либо RetargetingAdjustments, либо RegionalAdjustments, либо VideoAdjustment, либо SmartAdAdjustment, либо SerpLayoutAdjustments либо IncomeGradeAdjustments либо AdGroupAdjustment.

TabletAdjustment

TabletAdjustmentAdd

Корректировка на планшетах.

DesktopAdjustment

DesktopAdjustmentAdd

Корректировка на компьютерах, Smart TV.

DesktopOnlyAdjustment

DesktopOnlyAdjustmentAdd

Корректировка только на компьютерах.

SmartTvAdjustment

SmartTvAdjustmentAdd

Корректировка только на Smart TV.

DemographicsAdjustments

array of DemographicsAdjustmentAdd

Корректировки по полу и возрасту. Не более 12 элементов в массиве.

RetargetingAdjustments

array of RetargetingAdjustmentAdd

Корректировки для целевой аудитории. Не более 100 элементов в массиве.

RegionalAdjustments

array of RegionalAdjustmentAdd

Корректировки по региону показа.

VideoAdjustment

VideoAdjustmentAdd

Корректировка для видеодополнений.

SmartAdAdjustment

SmartAdAdjustmentAdd

Корректировка для смарт-объявлений.

SerpLayoutAdjustments

array of SerpLayoutAdjustmentAdd

Корректировки на эксклюзивное размещение.

IncomeGradeAdjustments

array of IncomeGradeAdjustmentAdd

Корректировки на платежеспособность.

AdGroupAdjustment

array of AdGroupAdjustmentAdd

Корректировки на группу.

Структура MobileAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений на мобильных телефонах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

Да

OperatingSystemType

OperatingSystemTypeEnum

Тип операционной системы.

Если параметр не указан, подразумевается любая операционная система.

Нет

Структура TabletAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений на планшетах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

Да

OperatingSystemType

OperatingSystemTypeEnum

Тип операционной системы.

Если параметр не указан, подразумевается любая операционная система.

Нет

Структура DesktopAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений на компьютерах, Smart TV.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

В одной группе объявлений коэффициент для показа на мобильных без указания операционной системы и коэффициент для показа на компьютерах, планшетах, Smart TV не допускается устанавливать одновременно равными 0.

Да

Структура DesktopOnlyAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений только на компьютерах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

В одной группе объявлений коэффициент для показа на мобильных без указания операционной системы и коэффициент для показа только на компьютерах не допускается устанавливать одновременно равными 0.

Да

Структура DemographicsAdjustmentAdd

Gender

GenderEnum

Пол пользователя: GENDER_MALE или GENDER_FEMALE.

Если параметр не указан, подразумевается любой пол (в этом случае требуется указать параметр Age).

Хотя бы один из параметров Gender или Age.

Age

AgeRangeEnum

Возрастная группа пользователя: одно из значений AGE_0_17, AGE_18_24, AGE_25_34, AGE_35_44, AGE_45_54 или AGE_55.

Значение AGE_45 устарело, рекомендуется создать отдельные корректировки для возрастных групп AGE_45_54 и AGE_55.

Если параметр не указан, подразумевается любой возраст (в этом случае требуется указать параметр Gender).

Alert

Срезы аудитории, для которых задаются корректировки, не должны совпадать или пересекаться. Например, нельзя задать корректировки одновременно для групп AGE_25_34 и GENDER_MALE+AGE_25_34.

BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям указанного пола и/или возрастной группы.

Указывается в процентах от 0 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура RetargetingAdjustmentAdd

RetargetingConditionId

long

Идентификатор условия ретаргетинга и подбора аудитории. Допускается только условие с типом RETARGETING. См. раздел Условие ретаргетинга и подбора аудитории (RetargetingList).

Да

BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям, отвечающим условию ретаргетинга и подбора аудитории.

Указывается в процентах от 0 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура RegionalAdjustmentAdd

RegionId

long

Идентификатор региона из справочника регионов.

Справочник регионов можно получить с помощью метода Dictionaries.get.

Да

BidModifier

int

Значение коэффициента к ставке для показа объявлений в указанном регионе.

Указывается в процентах от 10 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура VideoAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений с видеодополнением.

Указывается в процентах от 50 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура SmartAdAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа смарт-объявления с одним товарным предложением.

Указывается в процентах от 20 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура SerpLayoutAdjustmentAdd

SerpLayout

SerpLayoutEnum

Блок показа объявления:

ALONE — Эксклюзивное размещение.
SUGGEST — Реклама в саджесте.
Да

BidModifier

int

Значение коэффициента к ставке для показа объявлений в указанной позиции.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура IncomeGradeAdjustmentAdd

Grade

IncomeGradeEnum

Уровень платежеспособности:

VERY_HIGH
HIGH
ABOVE_AVERAGE
Да

BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям с определенным уровнем платежеспособности.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.

Да

Структура AdGroupAdjustmentAdd

BidModifier

int

Значение коэффициента к ставке для показа объявлений из определенной группы.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.

Да

Ответ
Alert

Добавление корректировок по полу и возрасту для одной кампании или группы объявлений считается единой операцией. В случае ошибки в одном из коэффициентов не будет создан ни один.

Добавление корректировок для целевой аудитории для одной кампании или группы объявлений считается единой операцией. В случае ошибки в одном из коэффициентов не будет создан ни один.

Добавление корректировок по региону показа для одной кампании считается единой операцией. В случае ошибки в одном из коэффициентов не будет создан ни один.

Структура ответа в формате JSON:

{
  "result": { /* result */
    "AddResults": [{  /* MultiIdsActionResult */
      "Ids": [(long), ... ],
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ]
    }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / AddResponse (для SOAP)

AddResults

array of MultiIdsActionResult

Результаты добавления корректировок.

Структура MultiIdsActionResult

Ids

array of long

Идентификаторы созданных корректировок. Возвращаются в случае отсутствия ошибок, см. раздел Операции над массивом объектов. Следуют в том же порядке, что и корректировки в запросе.

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.

Примеры
Пример запроса

    {
      "method": "add",
      "params": {
        "BidModifiers": [
          { // 1. Две корректировки по полу и возрасту
            "CampaignId": 10001,
            "DemographicsAdjustments": [
              {
                "Gender": "GENDER_MALE",
                "Age": "AGE_25_34",
                "BidModifier": 101
              },
              {
                "Age": "AGE_45_54",
                "BidModifier": 140
              }
            ]
          },
          { // 2. Корректировки с пересекающимися срезами аудитории
            "CampaignId": 10002,
            "DemographicsAdjustments": [
              {
                "Gender": "GENDER_MALE",
                "Age": "AGE_25_34",
                "BidModifier": 120
              },
              {
                "Age": "AGE_25_34",
                "BidModifier": 170
              }
            ]
          },
          { // 3. Недопустимое значение коэффициента
            "CampaignId": 10003,
            "DemographicsAdjustments": [
              {
                "Gender": "GENDER_MALE",
                "Age": "AGE_25_34",
                "BidModifier": 120
              },
              {
                "Gender": "GENDER_FEMALE",
                "Age": "AGE_35_44",
                "BidModifier": 10000
              }
            ]
          },
          { // 4. Корректировка для целевой аудитории на уровне группы объявлений
            "AdGroupId": 500001,
            "RetargetingAdjustments": [
              {
                "RetargetingConditionId": 2004,
                "BidModifier": 201
              }
            ]
          }
        ]
      }
    }

Пример ответа

    {
      "result" : {
        "AddResults" : [
          { // 1. Созданы две корректировки по полу и возрасту
            "Ids": [ 1003, 1004 ]
          },
          { // 2. Пересекающиеся срезы - ни одна корректировка не создана
            "Errors": [
              {
                "Code": 6000,
                "Message": "Неконсистентное состояние объекта",
                "Details": "Пересекаются условия корректировок в наборе"
              }
            ]
          },
          { // 3. Недопустимое значение - ни одна корректировка не создана
            "Errors": [
              {
                "Code": 5005,
                "Message": "Поле задано неверно",
                "Details": "Значение коэффициента не может быть больше 1300"
              }
            ]
          },
          { // 4. Создана корректировка для целевой аудитории на уровне группы объявлений
            "Ids": [ 1005 ]
          }
        ]
      }
    }




    delete
Удаляет корректировки ставок.

Узнайте больше
Как работает метод delete
Как обрабатывать ошибки
Ограничения
Не более 1000 корректировок в одном вызове метода.

Запрос
Структура запроса в формате JSON:

{
  "method": "delete",
  "params": { /* params */
    "SelectionCriteria": {  /* IdsCriteria */
      "Ids": [(long), ... ] /* required */
    } /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / DeleteRequest (для SOAP)

SelectionCriteria

IdsCriteria

Критерий отбора корректировок, которые требуется удалить.

Да

Структура IdsCriteria

Ids

array of long

Идентификаторы корректировок, которые требуется удалить (не более 1000).

Да

Ответ
Структура ответа в формате JSON:

{
  "result": {
    "DeleteResults": [{  /* ActionResult */
      "Id": (long),
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ]
    }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / DeleteResponse (для SOAP)

DeleteResults

array of ActionResult

Результаты удаления корректировок.

Структура ActionResult

Id

long

Идентификатор удаленной корректировки. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов.

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.




get
Возвращает параметры корректировок, отвечающих заданным критериям.

Узнайте больше
Как работает метод get
Корректировки (BidModifier)
Ограничения
Метод возвращает не более 10 000 объектов.

Сумма значений параметров Limit и Offset не должна превышать 120 000 (если Limit не указан, значение Offset не должно превышать 110 000).

Запрос
Структура запроса в формате JSON:

{
  "method": "get",
  "params": { /* params */
    "SelectionCriteria": {  /* BidModifiersSelectionCriteria */
      "CampaignIds": [(long), ... ],
      "AdGroupIds": [(long), ... ],
      "Ids": [(long), ... ],
      "Types": [( "MOBILE_ADJUSTMENT" | "TABLET_ADJUSTMENT" | "DESKTOP_ADJUSTMENT" | "DESKTOP_ONLY_ADJUSTMENT" | "DEMOGRAPHICS_ADJUSTMENT" | "RETARGETING_ADJUSTMENT" | "REGIONAL_ADJUSTMENT" | "VIDEO_ADJUSTMENT" | "SMART_AD_ADJUSTMENT" | "SERP_LAYOUT_ADJUSTMENT" | "INCOME_GRADE_ADJUSTMENT" | "AD_GROUP_ADJUSTMENT" ), ... ],
      "Levels": [( "CAMPAIGN" | "AD_GROUP" ), ... ] /* required */
    }, /* required */
    "FieldNames": [( "Id" | "CampaignId" | "AdGroupId" | "Level" | "Type" ), ... ], /* required */
    "MobileAdjustmentFieldNames": [( "BidModifier" | "OperatingSystemType" ), ... ],
    "TabletAdjustmentFieldNames": [( "BidModifier" | "OperatingSystemType" ), ... ],
    "DesktopAdjustmentFieldNames": [( "BidModifier" )],
    "DesktopOnlyAdjustmentFieldNames": [( "BidModifier" )],
    "DemographicsAdjustmentFieldNames": [( "Gender" | "Age" | "BidModifier" | "Enabled" ), ... ],
    "RetargetingAdjustmentFieldNames": [( "RetargetingConditionId" | "BidModifier" | "Accessible" | "Enabled" ), ... ],
    "RegionalAdjustmentFieldNames": [( "RegionId" | "BidModifier" | "Enabled" ), ... ],
    "VideoAdjustmentFieldNames": [( "BidModifier" )],
    "SmartAdAdjustmentFieldNames": [( "BidModifier" )],
    "SerpLayoutAdjustmentFieldNames": [( "SerpLayout" | "BidModifier" | "Enabled" ), ... ],
    "IncomeGradeAdjustmentFieldNames": [( "Grade" | "BidModifier" | "Enabled" ), ... ],
    "AdGroupAdjustmentFieldNames" : [ ("BidModifier") ],
    "Page": {  /* LimitOffset */
      "Limit": (long),
      "Offset": (long)
    }
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / GetRequest (для SOAP)

SelectionCriteria

BidModifiersSelectionCriteria

Критерий отбора корректировок.

Да

FieldNames

array of BidModifierFieldEnum

Имена параметров верхнего уровня, которые требуется получить.

Да

MobileAdjustmentFieldNames

array of MobileAdjustmentFieldEnum

Имена параметров корректировок на мобильных, которые требуется получить.

Нет

TabletAdjustmentFieldNames

array of TabletAdjustmentFieldEnum

Имена параметров корректировок на планшетах, которые требуется получить.

Нет

DesktopAdjustmentFieldNames

array of DesktopAdjustmentFieldEnum

Имена параметров корректировок на компьютерах, Smart TV, которые требуется получить.

Нет

DesktopOnlyAdjustmentFieldNames

array of DesktopOnlyAdjustmentFieldEnum

Имена параметров корректировок только на компьютерах, которые требуется получить.

Нет

DemographicsAdjustmentFieldNames

array of DemographicsAdjustmentFieldEnum

Имена параметров корректировок по полу и возрасту, которые требуется получить.

Нет

RetargetingAdjustmentFieldNames

array of RetargetingAdjustmentFieldEnum

Имена параметров корректировок для целевой аудитории, которые требуется получить.

Нет

RegionalAdjustmentFieldNames

array of RegionalAdjustmentFieldEnum

Имена параметров корректировок по региону показа, которые требуется получить.

Нет

VideoAdjustmentFieldNames

array of VideoAdjustmentFieldEnum

Имена параметров корректировок для видеодополнений, которые требуется получить.

Нет

SmartAdAdjustmentFieldNames

array of SmartAdAdjustmentFieldEnum

Имена параметров корректировок для смарт-объявлений, которые требуется получить.

Нет

SerpLayoutAdjustmentFieldNames

array of SerpLayoutAdjustmentFieldEnum

Имена параметров корректировок на эксклюзивное размещение, которые требуется получить.

Нет

IncomeGradeAdjustmentFieldNames

array of IncomeGradeAdjustmentFieldEnum

Имена параметров корректировок на платежеспособность, которые требуется получить.

Нет

AdGroupAdjustmentFieldNames

array of AdGroupAdjustmentFieldEnum

Имена параметров корректировок на группу, которые требуется получить.

Нет

Page

LimitOffset

Структура, задающая страницу при постраничной выборке данных.

Нет

Структура BidModifiersSelectionCriteria

CampaignIds

array of long

Отбирать корректировки, заданные для указанных кампаний и/или дочерних групп.

От 1 до 10 элементов в массиве.

Хотя бы один из параметров CampaignIds, AdGroupIds и Ids

AdGroupIds

array of long

Отбирать корректировки, заданные для указанных групп.

От 1 до 1000 элементов в массиве.

Ids

array of long

Отбирать корректировки с указанными идентификаторами. От 1 до 10 000 элементов в массиве.

Types

array of BidModifierTypeEnum

Отбирать корректировки указанных типов. См. Типы корректировок.

Нет

Levels

array of BidModifierLevelEnum

Отбирать корректировки указанных уровней:

CAMPAIGN — корректировки, заданные для кампаний;
AD_GROUP — корректировки, заданные для групп объявлений.
Да

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "BidModifiers": [{  /* BidModifierGetItem */
      "CampaignId": (long),
      "AdGroupId": (long), /* nillable */
      "Id": (long),
      "Level": ( "CAMPAIGN" | "AD_GROUP" ),
      "Type": ( "MOBILE_ADJUSTMENT" | "TABLET_ADJUSTMENT" | "DESKTOP_ADJUSTMENT" | "DESKTOP_ONLY_ADJUSTMENT" | "DEMOGRAPHICS_ADJUSTMENT" | "RETARGETING_ADJUSTMENT" | "REGIONAL_ADJUSTMENT" | "VIDEO_ADJUSTMENT" | "SMART_AD_ADJUSTMENT" | "SERP_LAYOUT_ADJUSTMENT" | "INCOME_GRADE_ADJUSTMENT" | "AD_GROUP_ADJUSTMENT" ),
      "MobileAdjustment": {  /* MobileAdjustmentGet */
        "BidModifier": (int),
        "OperatingSystemType": ( "IOS" | "ANDROID" )
      },
      "TabletAdjustment": {  /* MobileAdjustmentGet */
        "BidModifier": (int), /* required */
        "OperatingSystemType": ( "IOS" | "ANDROID" )
      },
      "DesktopAdjustment": {  /* DesktopAdjustmentGet */
        "BidModifier": (int)
      },
      "DesktopOnlyAdjustment": {  /* DesktopAdjustmentGet */
        "BidModifier": (int) /* required */
      },
      "DemographicsAdjustment": {  /* DemographicsAdjustmentGet */
        "Gender": ( "GENDER_MALE" | "GENDER_FEMALE" ), /* nillable */
        "Age": ( "AGE_0_17" | "AGE_18_24" | "AGE_25_34" | "AGE_35_44" | "AGE_45" | "AGE_45_54" | "AGE_55" ), /* nillable */
        "BidModifier": (int),
        "Enabled": ( "YES" | "NO" )
      },
      "RetargetingAdjustment": {  /* RetargetingAdjustmentGet */
        "RetargetingConditionId": (long),
        "BidModifier": (int),
        "Accessible": ( "YES" | "NO" ),
        "Enabled": ( "YES" | "NO" )
      },
      "RegionalAdjustment": {  /* RegionalAdjustmentGet */
        "RegionId": (long),
        "BidModifier": (int),
        "Enabled": ("YES"|"NO")
      },
      "VideoAdjustment": {  /* VideoAdjustmentGet */
        "BidModifier": (int)
      },
      "SmartAdAdjustment" : { /* SmartAdAdjustmentGet */
        "BidModifier": (int)
      },
      "SerpLayoutAdjustment": {  /* SerpLayoutAdjustmentGet */
        "SerpLayout": ( "ALONE" | "SUGGEST" ),
        "BidModifier": (int),
        "Enabled": ( "YES" | "NO" )
      },
      "IncomeGradeAdjustment": {  /* IncomeGradeAdjustmentGet */
        "Grade": ( "VERY_HIGH" | "HIGH" | "ABOVE_AVERAGE" ),
        "BidModifier": (int),
        "Enabled": ( "YES" | "NO" )
      },
      "AdGroupAdjustment" : {
        "BidModifier" : (integer)
      }
    }, ... ],
    "LimitedBy": (long)
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / GetResponse (для SOAP)

BidModifiers

array of BidModifierGetItem

Корректировки ставок.

LimitedBy

long

Порядковый номер последнего возвращенного объекта. Передается в случае, если количество объектов в ответе было ограничено лимитом. См. раздел Постраничная выборка.

Структура BidModifierGetItem

CampaignId

long

Идентификатор кампании, для которой задана корректировка, или идентификатор кампании, которой принадлежит группа объявлений, для которой задана корректировка.

AdGroupId

long, nillable

Идентификатор группы объявлений, для которой задана корректировка.

Id

long

Идентификатор корректировки.

Level

BidModifierLevelEnum

Уровень корректировки: задана для кампании или для группы.

Type

BidModifierTypeEnum

Тип корректировки.

MobileAdjustment

MobileAdjustmentGet

Параметры корректировки на мобильных.

TabletAdjustment

TabletAdjustmentGet

Параметры корректировки на планшетах.

DesktopAdjustment

DesktopAdjustmentGet

Параметры корректировки на компьютерах, Smart TV.

DesktopOnlyAdjustment

DesktopOnlyAdjustmentGet

Параметры корректировки только на компьютерах.

VideoAdjustment

VideoAdjustmentGet

Параметры корректировки для видеодополнений.

DemographicsAdjustment

DemographicsAdjustmentGet

Параметры корректировки ставок по полу и возрасту.

RetargetingAdjustment

RetargetingAdjustmentGet

Параметры корректировки ставок для целевой аудитории.

RegionalAdjustment

RegionalAdjustmentGet

Параметры корректировки ставок по региону показа.

SmartAdAdjustment

SmartAdAdjustmentGet

Параметры корректировки ставок для смарт-баннеров.

IncomeGradeAdjustment

IncomeGradeAdjustmentGet

Параметры корректировки на платежеспособность.

SerpLayoutAdjustment

SerpLayoutAdjustmentGet

Параметры корректировки на эксклюзивное размещение.

AdGroupAdjustment

AdGroupAdjustmentGet

Параметры корректировки на группу.

Структура MobileAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений на мобильных телефонах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

OperatingSystemType

OperatingSystemTypeEnum

Тип операционной системы.

Если параметр не указан, подразумевается любая операционная система.

Структура TabletAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений на планшетах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

OperatingSystemType

OperatingSystemTypeEnum

Тип операционной системы.

Если параметр не указан, подразумевается любая операционная система.

Структура DesktopAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений на компьютерах, Smart TV.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

В одной группе объявлений коэффициент для показа на мобильных без указания операционной системы и коэффициент для показа на компьютерах, планшетах, Smart TV не допускается устанавливать одновременно равными 0.

Структура DesktopOnlyAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений только на компьютерах.

Указывается в процентах:

От 0 до 1300 — для корректировок во всех типах кампаний и групп.
Ставка умножается на значение BidModifier/100.

В одной группе объявлений коэффициент для показа на мобильных без указания операционной системы и коэффициент для показа только на компьютерах не допускается устанавливать одновременно равными 0.

Структура DemographicsAdjustmentGet

Gender

GenderEnum, nillable

Пол пользователя: GENDER_MALE или GENDER_FEMALE.

Если параметр не указан, подразумевается любой пол.

Age

AgeRangeEnum, nillable

Возрастная группа пользователя: одно из значений AGE_0_17, AGE_18_24, AGE_25_34, AGE_35_44, AGE_45_54 или AGE_55.

Значение AGE_45 устарело, рекомендуется создать отдельные корректировки для возрастных групп AGE_45_54 и AGE_55.

Если параметр не указан, подразумевается любой возраст.

BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям указанного пола и/или возрастной группы.

Указывается в процентах от 0 до 1300. Ставка умножается на значение BidModifier/100.

Enabled

YesNoEnum

Включен или отключен набор корректировок по полу и возрасту.

Структура RetargetingAdjustmentGet

RetargetingConditionId

long

Идентификатор условия ретаргетинга и подбора аудитории. Допускается только условие с типом RETARGETING. См. раздел Условие ретаргетинга и подбора аудитории (RetargetingList).

BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям, отвечающим условию ретаргетинга и подбора аудитории.

Указывается в процентах от 0 до 1300. Ставка умножается на значение BidModifier/100.

Accessible

YesNoEnum

Признак того, что все цели и сегменты в условии ретаргетинга и подбора аудитории доступны пользователю. Значение NO — одна или несколько целей или один или несколько сегментов недоступны.

Enabled

YesNoEnum

Включен или отключен набор корректировок для целевой аудитории.

Структура RegionalAdjustmentGet

RegionId

long

Идентификатор региона из справочника регионов.

Справочник регионов можно получить с помощью метода Dictionaries.get.

BidModifier

int

Значение коэффициента к ставке для показа объявлений в указанном регионе.

Указывается в процентах от 10 до 1300. Ставка умножается на значение BidModifier/100.

Enabled

YesNoEnum

Включен или отключен набор корректировок по региону показа.

Структура VideoAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений с видеодополнением.

Указывается в процентах от 50 до 1300. Ставка умножается на значение BidModifier/100.

Структура SmartAdAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа смарт-объявления с одним товарным предложением.

Указывается в процентах от 20 до 1300. Ставка умножается на значение BidModifier/100.

Структура SerpLayoutAdjustmentGet

SerpLayout

SerpLayoutEnum

Блок показа объявления:

ALONE — Эксклюзивное размещение.
SUGGEST — Реклама в саджесте.
BidModifier

int

Значение коэффициента к ставке для показа объявлений в указанной позиции.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.

Enabled

YesNoEnum

Включен или отключен набор корректировок на эксклюзивное размещение.

Структура IncomeGradeAdjustmentGet

Grade

IncomeGradeEnum

Уровень платежеспособности:

VERY_HIGH
HIGH
ABOVE_AVERAGE
BidModifier

int

Значение коэффициента к ставке для показа объявлений пользователям с определенным уровнем платежеспособности.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.

Enabled

YesNoEnum

Включен или отключен набор корректировок на платежеспособность.

Структура AdGroupAdjustmentGet

BidModifier

int

Значение коэффициента к ставке для показа объявлений из определенной группы.

Указывается в процентах от 1 до 1300. Ставка умножается на значение BidModifier/100.



set
Изменяет значения коэффициентов в корректировках ставок.

Узнайте больше
Как работают методы, изменяющие данные
Как обрабатывать ошибки
Запрос
Структура запроса в формате JSON:

{
  "method": "set",
  "params": { /* params */
    "BidModifiers": [{  /* BidModifierSetItem */
      "Id": (long), /* required */
      "BidModifier": (int) /* required */
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / SetRequest (для SOAP)

BidModifiers

array of BidSetItem

Значения коэффициентов. Не более 1000 элементов в массиве.

Да

Структура BidModifierSetItem

Id

long

Идентификатор корректировки.

Да

BidModifier

int

Значение коэффициента.

Указывается в процентах:

От 0 до 1300 — для корректировок на мобильных (во всех типах кампаний и групп); на компьютерах, планшетах, Smart TV (во всех типах кампаний и групп); по полу и возрасту; для целевой аудитории.
От 1 до 1300 – для корректировок эксклюзивное размещение, платежеспособность, на группу.
От 10 до 1300 — для корректировок по региону показа.
От 20 до 1300 — для корректировок для смарт-баннеров.
Ставка умножается на значение BidModifier/100.

Да

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "SetResults": [{  /* ActionResult */
      "Id": (long),
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ]
    }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / SetResponse (для SOAP)

SetResults

array of ActionResult

Результаты изменения коэффициентов.

Структура ActionResult

Id

long

Идентификатор корректировки. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов.

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.




KeywordBids
Сервис предназначен для назначения ставок ключевым фразам и автотаргетингам и для получения данных, полезных при назначении ставок.

Все ставки и цены указываются в валюте пользователя.

Методы
get | set | setAuto

Адрес WSDL-описания
https://api.direct.yandex.com/v5/keywordbids?wsdl

https://api.direct.yandex.com/v501/keywordbids?wsdl

Адрес для SOAP-запросов
https://api.direct.yandex.com/v5/keywordbids

https://api.direct.yandex.com/v501/keywordbids

Адрес для JSON-запросов
https://api.direct.yandex.com/json/v5/keywordbids

https://api.direct.yandex.com/json/v501/keywordbids



get
Возвращает ставки для ключевых фраз и автотаргетингов, отвечающих заданным критериям, а также данные торгов: ставки и списываемые цены для различных объемов трафика на поиске и ставки для охвата различных долей аудитории в сетях.

Ставки можно получить независимо от того, какая стратегия выбрана в кампании — ручная или автоматическая.

Alert

Все возвращаемые денежные значения представляют собой целые числа — результат умножения ставки или цены на 1 000 000.

Узнайте больше
Как работает метод get
Автотаргетинг
Ограничения
Метод возвращает не более page-size объектов.

Запрос
Структура запроса в формате JSON:

{
  "method": "get",
  "params": { /* params */
    "SelectionCriteria": { /* KeywordBidsSelectionCriteria */
      "CampaignIds": [(long), ... ],
      "AdGroupIds": [(long), ... ],
      "KeywordIds": [(long), ... ],
      "ServingStatuses": [( "ELIGIBLE" | "RARELY_SERVED" ), ... ]
    }, /* required */
    "FieldNames": [( "KeywordId" | "AdGroupId" | "CampaignId" | "ServingStatus" | "StrategyPriority" ), ... ], /* required */
    "SearchFieldNames": [( "Bid" | "AutotargetingSearchBidIsAuto" | "AuctionBids" ), ... ],
    "NetworkFieldNames": [( "Bid" | "Coverage" ), ... ],
    "Page": {  /* LimitOffset */
      "Limit": (long),
      "Offset": (long)
    }
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / GetRequest (для SOAP)

SelectionCriteria

KeywordBidsSelectionCriteria

Критерий отбора ключевых фраз и автотаргетингов.

Да

FieldNames

array of KeywordBidFieldEnum

Имена параметров верхнего уровня, которые требуется получить.

Да

SearchFieldNames

array of KeywordBidSearchFieldEnum

Имена параметров торгов на поиске, которые требуется получить.

Не запрашивайте параметр AuctionBids, если в кампании отключены показы на поиске (стратегия на поиске SERVING_OFF).

Нет

NetworkFieldNames

array of KeywordBidNetworkFieldEnum

Имена параметров торгов в сетях, которые требуется получить.

Не запрашивайте параметр Coverage, если в кампании отключены показы в сетях (стратегия в сетях SERVING_OFF).

Нет

Page

LimitOffset

Структура, задающая страницу при постраничной выборке данных.

Нет

Структура KeywordBidsSelectionCriteria

CampaignIds

array of long

Получить ставки для ключевых фраз и автотаргетингов в указанных кампаниях. От 1 до campaign-ids-select элементов в массиве.

Один из параметров KeywordIds, AdGroupIds и CampaignIds (могут присутствовать все)

AdGroupIds

array of long

Получить ставки для ключевых фраз и автотаргетингов в указанных группах объявлений. От 1 до adgroup-ids-select элементов в массиве.

KeywordIds

array of long

Получить ставки для указанных ключевых фраз и автотаргетингов. Не более ids-select элементов в массиве.

ServingStatuses

array of ServingStatusEnum

Получить ставки для ключевых фраз и автотаргетингов с указанными статусами возможности показов группы. Описание статусов см. в разделе Статус возможности показов группы.

Нет

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "KeywordBids": [{  /* KeywordBidGetItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "ServingStatus": ( "ELIGIBLE" | "RARELY_SERVED" ),
      "StrategyPriority": "NORMAL", /* nillable */
      "Search": { /* Search */
        "Bid": (long),
        "AutotargetingSearchBidIsAuto",: ( "YES" | "NO" ),
        "AuctionBids": { /* AuctionBids */
          "AuctionBidItems": [{  /* AuctionBidItem */
            "TrafficVolume": (int), /* required */
            "Bid": (long), /* required */
            "Price": (long) /* required */
          }, ... ]
        } /* nillable */
      },
      "Network": { /* Network */
        "Bid": (long),
        "Coverage": {  /* Coverage */
          "CoverageItems": [{ /* NetworkCoverageItem */
            "Probability": (decimal), /* required */
            "Bid": (long) /* required */
          }, ... ]
        }  /* nillable */
      }
    }, ... ],
    "LimitedBy": (long)
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / GetResponse (для SOAP)

KeywordBids

array of KeywordBidGetItem

Ставки.

LimitedBy

long

Порядковый номер последнего возвращенного объекта. Передается в случае, если количество объектов в ответе было ограничено лимитом. См. раздел Постраничная выборка.

Структура KeywordBidGetItem

CampaignId

long

Идентификатор кампании, к которой относится ключевая фраза или автотаргетинг.

AdGroupId

long

Идентификатор группы объявлений, к которой относится ключевая фраза или автотаргетинг.

KeywordId

long

Идентификатор ключевой фразы или автотаргетинга.

ServingStatus

ServingStatusEnum

Статус возможности показов группы объявлений. Описание статусов см. в разделе Статус возможности показов группы.

StrategyPriority

PriorityEnum, nillable

Приоритет ключевой фразы или автотаргетинга: NORMAL.

Search

Search

Ставка и данные торгов на поиске.

Network

Network

Ставка и данные торгов в сетях.

Структура Search

Bid

long

Ставка на поиске, назначенная пользователем.

AutotargetingSearchBidIsAuto

YesNoEnum

Признак включения опции автоматической ставки.

AuctionBids

AuctionBids, nillable

Ставки и списываемые цены на поиске, соответствующие различным объемам трафика для данной фразы.

Если в группе только графические объявления, возвращается null (nil).

Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), возвращается null (nil).

Для автотаргетинга возвращается null (nil).

Структура AuctionBids

AuctionBidItems

array of AuctionBidItem

Массив ставок и списываемых цен на поиске, соответствующих различным объемам трафика.

Структура AuctionBidItem

TrafficVolume

int

Объем трафика.

Bid

long

Ставка на поиске, соответствующая указанному объему трафика.

Price

long

Списываемая цена, соответствующая указанному объему трафика.

Структура Network

Bid

long

Ставка в сетях, назначенная пользователем.

Coverage

Coverage, nillable

Ставки в сетях, соответствующие охвату различных долей аудитории для данной фразы.
Если в группе объявлений мало показов (значение RARELY_SERVED параметра ServingStatus), возвращается null (nil).

Если в кампании выбрана стратегия показа в сетях SERVING_OFF или NETWORK_DEFAULT, возвращается null (nil).

Для автотаргетинга возвращается null (nil).

Структура Coverage

CoverageItems

NetworkCoverageItem

Массив ставок, соответствующих охвату различных долей аудитории.

Структура NetworkCoverageItem

Probability

decimal

Частота показа (доля аудитории) в сетях. Указывается в процентах от 0 до 100.

Bid

long

Ставка в сетях, соответствующая указанной частоте показа.



set
Назначает фиксированные ставки для ключевых фраз и автотаргетингов.

Ставку можно назначить:

для отдельной ключевой фразы или автотаргетинга;

для всех ключевых фраз и автотаргетинга в группе объявлений;

для всех ключевых фраз и автотаргетингов в кампании.

Ставку можно назначить в зависимости от того, какая стратегия показа выбрана в кампании:

Если выбрана стратегия показа на поиске HIGHEST_POSITION, то можно указать параметр SearchBid.
Если выбрана стратегия показа в сетях MAXIMUM_COVERAGE или MANUAL_CPM, то можно указать параметр NetworkBid.
В случае если элемент входного массива содержит параметры, не соответствующие стратегии, то значения этих параметров изменены не будут.

Если элемент входного массива содержит одновременно и параметры, соответствующие стратегии, и параметры, не соответствующие стратегии, то в результате операции будут изменены значения только параметров, соответствующих стратегии, и выдано предупреждение.

Если элемент входного массива содержит только параметры, не соответствующие стратегии, то операция не будет выполнена и будет возвращена ошибка.

Узнайте больше
Операции над массивом объектов
Автотаргетинг
Ограничения
В одном запросе можно назначить ставки только для однородных объектов — либо только для кампаний, либо только для групп, либо только для ключевых фраз и автотаргетингов.

Количество объектов в одном вызове метода:

кампаний — не более campaign-ids-select;
групп — не более adgroup-ids-select;
ключевых фраз и автотаргетингов — не более ids-select.
Запрос
Структура запроса в формате JSON:

{
  "method": "set",
  "params": { /* params */
    "KeywordBids": [{  /* KeywordBidSetItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "SearchBid": (long),
      "AutotargetingSearchBidIsAuto" : ("YES"|"NO"),
      "NetworkBid": (long),
      "StrategyPriority": ( "LOW" | "NORMAL" | "HIGH" )
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / SetRequest (для SOAP)

KeywordBids

array of KeywordBidSetItem

Ставки.

Да

Структура KeywordBidSetItem

CampaignId

long

Идентификатор кампании. Указывается, если требуется назначить единую ставку для всех ключевых фраз и автотаргетингов в кампании.

Либо CampaignId, либо AdGroupId, либо KeywordId

AdGroupId

long

Идентификатор группы объявлений. Указывается, если требуется назначить единую ставку для всех ключевых фраз и автотаргетингов в группе.

KeywordId

long

Идентификатор фразы. Указывается, если требуется назначить ставку для отдельной ключевой фразы или автотаргетинга.

SearchBid

long

Ставка на поиске, умноженная на 1 000 000. Целое число. Только для ручной стратегии.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Хотя бы один из параметров SearchBid, NetworkBid, StrategyPriority, AutotargetingSearchBidIsAuto

AutotargetingSearchBidIsAuto

YesNoEnum

Признак включения опции автоматической ставки.

Можно одновременно указать ручную ставку (SearchBid) и включить автоставку (AutotargetingSearchBidIsAuto). В этом случае будет работать автоставка, а ручная будет использоваться в случае отключения автоматической.

Если указана только ручная ставка (SearchBid):

Для операции с указанием CampaignId или AdGroupId значение автоставки не будет стерто после использования метода.
Для операции с указанием KeywordId значение автоставки будет выставлено в "NO". Чтобы сохранить эту настройку, укажите ее в явном виде для операции с KeywordId.
NetworkBid

long

Ставка в сетях, умноженная на 1 000 000. Целое число. Только для ручной стратегии с независимым управлением ставками в сетях.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Alert

Показ графического объявления возможен только при условии, что ставка не ниже минимальной ставки для объявления с включенным в него изображением.

StrategyPriority

PriorityEnum

Приоритет фразы: LOW, NORMAL или HIGH. Только для автоматической стратегии.

Alert

Параметр не используется, переданное значение игнорируется.

Alert

Параметры CampaignId, AdGroupId и KeywordId являются взаимоисключающими. В одном запросе можно указывать только один из этих параметров.

Ответ
Структура ответа в формате JSON:

{
  "result": {  /* result */
    "SetResults": [{  /* KeywordBidActionResult */
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long)
    }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / SetResponse (для SOAP)

SetResults

array of KeywordBidActionResult

Результаты назначения ставок.

Структура KeywordBidActionResult

CampaignId

long

Идентификатор кампании. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

AdGroupId

long

Идентификатор группы объявлений. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

KeywordId

long

Идентификатор ключевой фразы или автотаргетинга. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.

Пример
Запрос

    {
      "method" : "set",
      "params" : {
        "KeywordBids" : [
          {
            "StrategyPriority" : "HIGH",
            "CampaignId" : 4193065
          },
          {
            "SearchBid" : 14000,
            "CampaignId" : 7273721
          }
        ]
      }
    }

Ответ

    {
      "result" : {
        "SetResults" : [
          {
            "CampaignId" : 4193065
          },
          {
            "CampaignId" : 7273721
          }
        ]
      }
    }


    setAuto
Назначает для фраз ставки на поиске в зависимости от желаемого объема трафика или ставки в сетях в зависимости от желаемой частоты показа (доли аудитории).

Формула расчета ставки:

Ставка, соответствующая объему трафика [TargetTrafficVolume](*TargetTrafficVolume) × (1 + [IncreasePercent](*IncreasePercent) / 100),

но не более [BidCeiling](*BidCeiling).

Со временем активность конкурентов может поднять ставку за желаемый объем трафика, и она превысит ставку пользователя. Чем выше надбавка, тем больше объем трафика, но и выше возможные расходы.




Метод не возвращает назначенные ставки, получить их можно методом get.

Метод не сбрасывает значение автоматической ставки (AutotargetingSearchBidIsAuto).

Узнайте больше
Операции над массивом объектов
Ограничения
Ставку на поиске можно назначить, только если в кампании выбрана стратегия показа на поиске HIGHEST_POSITION. В противном случае возвращается ошибка.

Ставку в сетях можно назначить, только если в кампании выбрана стратегия показа в сетях MAXIMUM_COVERAGE или MANUAL_CPM. В противном случае возвращается ошибка.

В одном запросе можно назначить ставки только для однородных объектов — либо только для кампаний, либо только для групп, либо только для фраз.

Метод не поддерживает назначение ставки отдельному автотаргетингу. Обновление ставок на поиске для всех фраз группы объявлений или кампании может повлиять на ставку для автотаргетинга.

Количество объектов в одном вызове метода:

кампаний — не более campaign-ids-select;
групп — не более adgroup-ids-select;
фраз — не более ids-select.
Запрос
Структура запроса в формате JSON:

{
  "method": "setAuto",
  "params": { /* params */
    "KeywordBids": [{  /* KeywordBidSetAutoItem */
      "CampaignId": (long),
      "AdGroupId": (long),
      "KeywordId": (long),
      "BiddingRule": { /* BiddingRule */
        "SearchByTrafficVolume": { /* SearchByTrafficVolume */
          "TargetTrafficVolume": (int), /* required */
          "IncreasePercent": (int),
          "BidCeiling": (long)
        },
        "NetworkByCoverage": { /* NetworkByCoverage */
          "TargetCoverage": (int), /* required */
          "IncreasePercent": (int),
          "BidCeiling": (long)
        }
      } /* required */
    }, ... ] /* required */
  }
}

Параметр

Тип

Описание

Обязательный

Структура params (для JSON) / SetAutoRequest (для SOAP)

KeywordBids

array of KeywordBidSetAutoItem

Параметры расчета ставок.

Да

Структура KeywordBidSetAutoItem

CampaignId

long

Идентификатор кампании. Указывается, если требуется обновить ставки для всех фраз кампании.

Либо CampaignId, либо AdGroupId, либо KeywordId

AdGroupId

long

Идентификатор группы объявлений. Указывается, если требуется обновить ставки для всех фраз группы.

KeywordId

long

Идентификатор фразы. Указывается, если требуется обновить ставку для отдельной фразы.

Alert

Идентификатор автотаргетинга не допускается.

BiddingRule

BiddingRule

Параметры для формулы расчета ставок.

Да

Структура BiddingRule

SearchByTrafficVolume

SearchByTrafficVolume

Параметры для формулы расчета ставок на поиске.

Либо SearchByTrafficVolume, либо NetworkByCoverage

NetworkByCoverage

NetworkByCoverage

Параметры для формулы расчета ставок в сетях.

Структура SearchByTrafficVolume

TargetTrafficVolume

int

Желаемый объем трафика на поиске. Указывается в процентах от 5 до 100.

К ставке, соответствующей выбранному объему трафика, прибавляется надбавка (см. параметр IncreasePercent).

Да

IncreasePercent

int

Процент надбавки от 0 до 1000. Если не задан, надбавка не рассчитывается.

Нет

BidCeiling

long

Ограничение на ставку, умноженное на 1 000 000. Целое число.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Нет

Структура NetworkByCoverage

TargetCoverage

int

Желаемая частота показа (доля аудитории) в сетях. Указывается в процентах от 1 до 100.

К ставке, соответствующей выбранной частоте показа, прибавляется надбавка (см. параметр IncreasePercent).

Да

IncreasePercent

int

Процент надбавки от 0 до 1000. Если не задан, надбавка не рассчитывается.

Нет

BidCeiling

long

Ограничение на ставку, умноженное на 1 000 000. Целое число.

Указывается в валюте пользователя. Ограничения представлены в справочнике валют, который можно получить с помощью метода Dictionaries.get, указав в запросе имя справочника Currencies.

Нет

Alert

Параметры CampaignId, AdGroupId и KeywordId являются взаимоисключающими. В одном запросе можно указывать только один из этих параметров.

Ответ
Структура ответа в формате JSON:

{
  "result": { /* result */
    "SetAutoResults": [{  /* KeywordBidActionResult */
      "Warnings": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
      }, ... ],
      "Errors": [{  /* ExceptionNotification */
        "Code": (int), /* required */
        "Message": (string), /* required */
        "Details": (string)
     }, ... ],
    "CampaignId": (long),
    "AdGroupId": (long),
    "KeywordId": (long)
   }, ... ]
  }
}

Параметр

Тип

Описание

Структура result (для JSON) / SetAutoResponse (для SOAP)

SetAutoResults

array of KeywordBidActionResult

Результаты назначения ставок.

Структура KeywordBidActionResult

CampaignId

long

Идентификатор кампании. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

AdGroupId

long

Идентификатор группы объявлений. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

KeywordId

long

Идентификатор ключевой фразы. Возвращается в случае отсутствия ошибок, см. раздел Операции над массивом объектов (если был указан в запросе).

Warnings

array of ExceptionNotification

Предупреждения, возникшие при выполнении операции.

Errors

array of ExceptionNotification

Ошибки, возникшие при выполнении операции.

Примеры
Пример запроса

Назначить всем фразам в группе объявлений ставку на поиске для получения объема трафика 75, увеличенную на 10%, но не более 12.

    {
      "method": "setAuto",
      "params": {
        "KeywordBids": [{
          "AdGroupId": 636056397,
          "BiddingRule": {
            "SearchByTrafficVolume": {
              "TargetTrafficVolume": 75,
              "IncreasePercent": 10,
              "BidCeiling": 12000000,
            }
          }
        }]
      }
    }

Пример ответа

    {
      "result" : {
        "SetAutoResults" : [
          {
            "AdGroupId" : 636056397
          }
        ]
      }
    }












    Ниже именно про **Reports v5**: как подтянуть **Метрику (sessions + цели/конверсии)**, какие **ReportType** это умеют, что такое **Goals / AttributionModels**, какие **предусловия** нужны, и 2 JSON-примера (CAMPAIGN + AD) с конверсиями.

---

## 1) Какие ReportType поддерживают Sessions / Conversions / ConversionRate / CostPerConversion

По списку допустимых полей в Reports:

* **Conversions / ConversionRate / CostPerConversion**: доступны во **всех** типах отчетов Reports (ACCOUNT, AD, ADGROUP, CAMPAIGN, CRITERIA, CUSTOM, REACH_AND_FREQUENCY, SEARCH_QUERY) как метрики Метрики. ([Yandex][1])
* **Sessions**: доступен **везде, кроме SEARCH_QUERY_PERFORMANCE_REPORT** (в таблице для Sessions последний столбец “–”, а для Query наоборот только последний столбец заполнен, то есть это именно SEARCH_QUERY). ([Yandex][1])

Важно: в таблице эти поля помечены как **метрика**, то есть без Метрики они не появятся.

---

## 2) Предусловия, чтобы в отчетах были Метрика-сессии и конверсии

Минимальный набор:

1. **На сайте стоит счетчик Яндекс.Метрики**, и его номер указан в кампании в параметре **CounterIds**. ([Yandex][2])
2. Для **Conversions / ConversionRate / CostPerConversion** в этом счетчике должны быть **настроены цели**. ([Yandex][2])
3. Желательно (и по умолчанию включено) чтобы в настройках кампании был Option **ADD_METRICA_TAG**: он автоматически добавляет в ссылки метку `yclid`, чтобы точнее стыковать клики Директа с визитами/целями в Метрике. ([Yandex][3])

Про “линк Direct↔Metrica”: в практическом смысле для Reports это сводится к тому, что **кампания “знает” CounterIds**, а у вашего логина есть доступ к этому счетчику/целям.

---

## 3) Как работают params.Goals и params.AttributionModels (и какие значения допустимы)

### Goals

`Goals` = массив ID целей Метрики (строками), максимум 10.

Если `Goals` задан, то в ответе **вместо агрегированных** полей:

* `Conversions`, `ConversionRate`, `CostPerConversion`, `GoalsRoi`, `Revenue`

вы получите **поля по каждой цели отдельно** с именами вида:
`<Поле>_<goalId>_<attributionModel>` ([Yandex][4])

Пример из документации: в запросе вы указываете просто `Conversions`, а в ответе приходят `Conversions_20002_LSC`, `Conversions_20003_LSC`, и т.д. ([Yandex][5])

### AttributionModels

`AttributionModels` = массив моделей атрибуции (если несколько, то данные будут по каждой модели отдельно). Значение по умолчанию: **LC**. ([Yandex][4])

Допустимые значения (актуальный enum из спецификации отчета):

* `FC` (first click)
* `LC` (last click)
* `LSC` (last significant click)
* `LYDC` (last click from Yandex Direct)
* `FCCD` (first click cross-device)
* `LSCCD` (last significant cross-device)
* `LYDCCD` (last click from Yandex Direct cross-device)
* `AUTO` (automatic) ([Yandex][4])

Нюанс по датам: для `LYDC`, `LSC`, `FC` “датой визита” считается **дата клика**, который стал источником визита (а не фактическая дата визита). Это может сдвигать попадание конверсий в период отчета. ([Yandex][4])

---

## 4) JSON пример: CAMPAIGN_PERFORMANCE_REPORT с сессиями и конверсиями по целям

Пример: по 1 кампании, за период, с 2 целями и 2 моделями атрибуции (получите поля вида `Conversions_<goal>_<model>` и т.п.).

```json
{
  "params": {
    "ReportName": "Campaign performance with Metrica goals",
    "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
    "DateRangeType": "CUSTOM_DATE",
    "Format": "TSV",
    "IncludeVAT": "YES",
    "IncludeDiscount": "NO",

    "SelectionCriteria": {
      "DateFrom": "2026-01-01",
      "DateTo": "2026-01-15",
      "Filter": [
        {
          "Field": "CampaignId",
          "Operator": "IN",
          "Values": ["123456789"]
        }
      ]
    },

    "Goals": ["20002", "20003"],
    "AttributionModels": ["LC", "LSC"],

    "FieldNames": [
      "Date",
      "CampaignId",
      "CampaignName",
      "Impressions",
      "Clicks",
      "Ctr",
      "AvgCpc",
      "Cost",

      "Sessions",

      "Conversions",
      "ConversionRate",
      "CostPerConversion"
    ],

    "OrderBy": [
      { "Field": "Date", "SortOrder": "ASCENDING" }
    ]
  }
}
```

Что вы увидите в TSV-ответе по целям:

* `Conversions_20002_LC`, `Conversions_20002_LSC`, `Conversions_20003_LC`, ...
* `ConversionRate_20002_LC`, ...
* `CostPerConversion_20002_LC`, ... ([Yandex][4])

---

## 5) JSON пример: AD_PERFORMANCE_REPORT с конверсиями по целям

```json
{
  "params": {
    "ReportName": "Ad performance with Metrica goals",
    "ReportType": "AD_PERFORMANCE_REPORT",
    "DateRangeType": "CUSTOM_DATE",
    "Format": "TSV",
    "IncludeVAT": "YES",
    "IncludeDiscount": "NO",

    "SelectionCriteria": {
      "DateFrom": "2026-01-01",
      "DateTo": "2026-01-15",
      "Filter": [
        {
          "Field": "CampaignId",
          "Operator": "IN",
          "Values": ["123456789"]
        }
      ]
    },

    "Goals": ["20002"],
    "AttributionModels": ["LSC"],

    "FieldNames": [
      "Date",
      "CampaignId",
      "AdGroupId",
      "AdId",
      "Impressions",
      "Clicks",
      "Ctr",
      "AvgCpc",
      "Cost",

      "Sessions",

      "Conversions",
      "ConversionRate",
      "CostPerConversion"
    ],

    "OrderBy": [
      { "Field": "Cost", "SortOrder": "DESCENDING" }
    ]
  }
}
```

---

## 6) Быстрый чеклист “почему Conversions/Sessions пустые или не приходят”

* CounterIds **не задан** в кампании или счетчик **не установлен** на сайте. ([Yandex][2])
* Цели в Метрике **не настроены/не накопили статистику** (для конверсий цели должны существовать). ([Yandex][2])
* Вы включили `Goals`, но смотрите в ответе колонки `Conversions` без суффиксов: при `Goals` они **заменяются** на `Conversions_<goal>_<model>`. ([Yandex][4])
* Период “не бьется” из-за модели атрибуции (для `LYDC/LSC/FC` считается дата клика). ([Yandex][4])

Если скажешь, какие именно разрезы тебе нужны (дата+кампания+устройство/регион/площадка/ключи) и какие цели (ID), я соберу готовые FieldNames/Filters под конкретные отчеты так, чтобы они не конфликтовали (у Директа там есть “несовместимые поля и зависимости”).

[1]: https://yandex.com/dev/direct/doc/en/fields-list "Допустимые поля | Yandex Direct API"
[2]: https://yandex.com/dev/direct/doc/en/restrictions?utm_source=chatgpt.com "Restrictions | Yandex Direct API"
[3]: https://yandex.ru/dev/direct/doc/en/annex/campaign-options "Настройки кампаний (параметр Option) | Yandex Direct API"
[4]: https://yandex.ru/dev/direct/doc/ru/spec "Запрос: спецификация отчета | Яндекс Директ API"
[5]: https://yandex.com/dev/direct/doc/en/example-metrika "Пример: данные Яндекс Метрики | Yandex Direct API"
