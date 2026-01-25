# stat-vbai Setup Guide

## Быстрый старт

### 1. Создай MySQL базу и пользователя

```bash
# DEV (172.16.0.35)
mysql -h 172.16.0.35 -u root -p

# В MySQL консоли выполни:
CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY 'VvK8mN2pL9xR4tQ7';
GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';
FLUSH PRIVILEGES;
```

```bash
# STAGE (172.16.0.106)
mysql -h 172.16.0.106 -u root -p

# В MySQL консоли выполни:
CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY 'StAgE_VvK8mN2pL9xR4tQ7';
GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';
FLUSH PRIVILEGES;
```

### 2. Создай Kubernetes Secret

```bash
# DEV
kubectl create secret generic stat-vbai-secret \
  --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:VvK8mN2pL9xR4tQ7@172.16.0.35:3306/stat_vbai" \
  -n default

# STAGE
kubectl create secret generic stat-vbai-secret \
  --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:StAgE_VvK8mN2pL9xR4tQ7@172.16.0.106:3306/stat_vbai" \
  -n default
```

### 3. Деплой через Jenkins

Пуш в ветку `main` автоматически запустит Jenkins pipeline:
- Соберет Docker образ `velesbsdllc/stat-vbai:A41.1`
- Задеплоит через ArgoCD

### 4. Проверка работы

```bash
# Проверь поды
kubectl get pods -n default | grep stat-vbai

# Проверь логи
kubectl logs -f deployment/stat-vbai -n default

# Проверь endpoints через API Gateway
curl http://apidev2.velesbsd.com/stat-vbai/health
```

## Что происходит при старте

1. ✅ Приложение запускается
2. ✅ Подключается к MySQL БД
3. ✅ **Автоматически создает все таблицы** (миграции)
4. ✅ Регистрируется в API Gateway
5. ✅ Готов к работе!

## Таблицы в БД

После первого запуска будут созданы:
- `revenue_records` - записи о выручке
- `cost_records` - записи о расходах (AI API costs)
- `user_subscriptions` - история подписок
- `daily_stats` - дневная агрегированная статистика
- `monthly_stats` - месячная агрегированная статистика

## API Endpoints

Все endpoints автоматически регистрируются в API Gateway:

```
GET /api/v1/stats/revenue         - Статистика выручки
GET /api/v1/stats/profit          - Статистика прибыли
GET /api/v1/stats/users           - Статистика пользователей
GET /api/v1/stats/subscriptions   - Статистика подписок
GET /api/v1/stats/daily           - Дневная статистика
GET /api/v1/stats/monthly         - Месячная статистика
GET /health                       - Health check
```

## Helm Values

### DEV (values.yaml)
- Database: 172.16.0.35:3306
- Gateway: http://api-vbai-svc:80
- Log Level: DEBUG

### STAGE (values.stage.yaml)
- Database: 172.16.0.106:3306
- Gateway: http://api-vbai-svc:80
- Log Level: INFO

## Переменные окружения

Все енвы берутся из:
- **ConfigMap** `stat-vbai-cm` - публичные настройки
- **Secret** `stat-vbai-secret` - приватные данные (DATABASE_URL)
- **Secret** `api-token` - SERVICE_ACCOUNT_TOKEN

## Разработка в поде

```bash
# Подключись к поду для разработки
python pod.py dev --log

# Логи будут автоматически писаться в log.txt
tail -f log.txt
```

## Troubleshooting

### База не подключается
```bash
# Проверь секрет
kubectl get secret stat-vbai-secret -n default -o yaml

# Проверь что пользователь создан в MySQL
mysql -h 172.16.0.35 -u stat_vbai -pVvK8mN2pL9xR4tQ7 stat_vbai
```

### Сервис не регистрируется в Gateway
```bash
# Проверь логи
kubectl logs -f deployment/stat-vbai -n default

# Проверь что SERVICE_ACCOUNT_TOKEN доступен
kubectl get secret api-token -n default
```

### Таблицы не создались
Таблицы создаются автоматически при старте. Проверь логи:
```bash
kubectl logs deployment/stat-vbai -n default | grep "migration"
```

## Готово! 🚀

Сервис stat-vbai готов к работе. Теперь можно реализовывать бизнес-логику аналитики!

