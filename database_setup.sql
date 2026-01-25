-- SQL команды для создания базы данных stat-vbai в MySQL

-- ====================================
-- DEV ENVIRONMENT (172.16.0.35:3306)
-- ====================================

-- Создаем базу данных для DEV
CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Создаем пользователя для DEV
CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY 'VvK8mN2pL9xR4tQ7';

-- Даем права для DEV
GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';
FLUSH PRIVILEGES;

-- Проверяем подключение DEV:
-- mysql -h 172.16.0.35 -u stat_vbai -p stat_vbai


-- ====================================
-- STAGE ENVIRONMENT (172.16.0.106:3306)
-- ====================================

-- Создаем базу данных для STAGE
CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Создаем пользователя для STAGE
CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY 'StAgE_VvK8mN2pL9xR4tQ7';

-- Даем права для STAGE
GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';
FLUSH PRIVILEGES;

-- Проверяем подключение STAGE:
-- mysql -h 172.16.0.106 -u stat_vbai -p stat_vbai


-- ====================================
-- PRODUCTION ENVIRONMENT
-- ====================================

-- Создаем базу данных для PROD
CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Создаем пользователя для PROD (используй свой сильный пароль!)
CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY 'PROD_SuperSecurePassword_2024';

-- Даем права для PROD
GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';
FLUSH PRIVILEGES;


-- ====================================
-- CONNECTION STRINGS для Kubernetes Secrets
-- ====================================

-- DEV (values.yaml):
-- DATABASE_URL: "mysql+aiomysql://stat_vbai:VvK8mN2pL9xR4tQ7@172.16.0.35:3306/stat_vbai"

-- STAGE (values.stage.yaml):
-- DATABASE_URL: "mysql+aiomysql://stat_vbai:StAgE_VvK8mN2pL9xR4tQ7@172.16.0.106:3306/stat_vbai"

-- PROD:
-- DATABASE_URL: "mysql+aiomysql://stat_vbai:PROD_SuperSecurePassword_2024@PROD_HOST:3306/stat_vbai"


-- ====================================
-- Kubernetes Secret Creation Commands
-- ====================================

-- DEV environment:
-- kubectl create secret generic stat-vbai-secret \
--   --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:VvK8mN2pL9xR4tQ7@172.16.0.35:3306/stat_vbai" \
--   -n default

-- STAGE environment:
-- kubectl create secret generic stat-vbai-secret \
--   --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:StAgE_VvK8mN2pL9xR4tQ7@172.16.0.106:3306/stat_vbai" \
--   -n default

-- PROD environment:
-- kubectl create secret generic stat-vbai-secret \
--   --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:PROD_SuperSecurePassword_2024@PROD_HOST:3306/stat_vbai" \
--   -n default


-- ====================================
-- Проверка таблиц после первого запуска
-- ====================================

-- USE stat_vbai;
-- SHOW TABLES;
-- 
-- Должны быть созданы таблицы:
-- - revenue_records
-- - cost_records
-- - user_subscriptions
-- - daily_stats
-- - monthly_stats

