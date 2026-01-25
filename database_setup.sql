-- =============================================================================
-- SQL для создания БД и юзера ydirect-vbai
-- =============================================================================

-- =============================================================================
-- DEV Environment (172.16.0.35)
-- =============================================================================

-- Создание БД
CREATE DATABASE IF NOT EXISTS ydirect_vbai 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Создание юзера
CREATE USER IF NOT EXISTS 'ydirect_vbai'@'%' IDENTIFIED BY 'YdIr3ct_D3v_2026';

-- Права
GRANT ALL PRIVILEGES ON ydirect_vbai.* TO 'ydirect_vbai'@'%';
FLUSH PRIVILEGES;

-- Проверка
SELECT 'DEV: ydirect_vbai DB and user created' AS status;
SELECT User, Host FROM mysql.user WHERE User = 'ydirect_vbai';


-- =============================================================================
-- STAGE Environment (172.16.0.106)
-- =============================================================================

-- Создание БД
CREATE DATABASE IF NOT EXISTS ydirect_vbai 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Создание юзера
CREATE USER IF NOT EXISTS 'ydirect_vbai'@'%' IDENTIFIED BY 'YdIr3ct_St4g3_2026';

-- Права
GRANT ALL PRIVILEGES ON ydirect_vbai.* TO 'ydirect_vbai'@'%';
FLUSH PRIVILEGES;

-- Проверка
SELECT 'STAGE: ydirect_vbai DB and user created' AS status;


-- =============================================================================
-- Таблица (создаётся автоматически миграциями, но можно вручную)
-- =============================================================================

USE ydirect_vbai;

CREATE TABLE IF NOT EXISTS ydirect_profiles (
    user_email VARCHAR(255) NOT NULL,
    alias VARCHAR(255) NOT NULL,
    token TEXT NOT NULL,
    description VARCHAR(500) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_email, alias),
    INDEX idx_user_email (user_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Table ydirect_profiles ready' AS status;


-- =============================================================================
-- Быстрые команды для подключения:
-- =============================================================================
-- DEV:   mysql -h 172.16.0.35 -u ydirect_vbai -pYdIr3ct_D3v_2026 ydirect_vbai
-- STAGE: mysql -h 172.16.0.106 -u ydirect_vbai -pYdIr3ct_St4g3_2026 ydirect_vbai
-- =============================================================================
