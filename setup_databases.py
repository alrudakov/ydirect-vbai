#!/usr/bin/env python3
"""
Скрипт для создания баз данных и пользователей stat-vbai в DEV и STAGE
"""

import pymysql
import sys

# Конфигурация DEV
DEV_CONFIG = {
    'host': '172.16.0.35',
    'port': 3306,
    'user': 'root',
    'password': '1q2w3e4r5t'
}

# Конфигурация STAGE
STAGE_CONFIG = {
    'host': '172.16.0.106',
    'port': 3306,
    'user': 'root',
    'password': '1q2w3e4r5t'
}

# SQL команды для создания базы и пользователя
SQL_COMMANDS = [
    "CREATE DATABASE IF NOT EXISTS stat_vbai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    "CREATE USER IF NOT EXISTS 'stat_vbai'@'%' IDENTIFIED BY '{password}';",
    "GRANT ALL PRIVILEGES ON stat_vbai.* TO 'stat_vbai'@'%';",
    "FLUSH PRIVILEGES;"
]

def setup_database(config, env_name, db_password):
    """Создает базу данных и пользователя"""
    print(f"\n{'='*60}")
    print(f"Настройка {env_name} окружения ({config['host']})")
    print(f"{'='*60}")
    
    try:
        # Подключаемся к MySQL
        print(f"Подключение к {config['host']}...")
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        cursor = connection.cursor()
        print("✓ Подключение успешно!")
        
        # Выполняем SQL команды
        for sql in SQL_COMMANDS:
            formatted_sql = sql.format(password=db_password)
            print(f"\nВыполняю: {formatted_sql[:80]}...")
            cursor.execute(formatted_sql)
            print("✓ Успешно!")
        
        # Проверяем созданную базу
        cursor.execute("SHOW DATABASES LIKE 'stat_vbai';")
        result = cursor.fetchone()
        if result:
            print(f"\n✓ База данных 'stat_vbai' создана!")
        
        # Проверяем пользователя
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User = 'stat_vbai';")
        result = cursor.fetchone()
        if result:
            print(f"✓ Пользователь 'stat_vbai'@'%' создан!")
        
        # Тестируем подключение новым пользователем
        print(f"\nТестирую подключение новым пользователем...")
        test_conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user='stat_vbai',
            password=db_password,
            database='stat_vbai'
        )
        test_conn.close()
        print("✓ Подключение пользователем 'stat_vbai' успешно!")
        
        cursor.close()
        connection.close()
        
        print(f"\n{'='*60}")
        print(f"✅ {env_name} окружение настроено успешно!")
        print(f"{'='*60}")
        print(f"\nСтрока подключения:")
        print(f"mysql+aiomysql://stat_vbai:{db_password}@{config['host']}:3306/stat_vbai")
        
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ Ошибка: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("SETUP STAT-VBAI DATABASES")
    print("="*60)
    
    # Пароли для пользователей БД
    DEV_DB_PASSWORD = "VvK8mN2pL9xR4tQ7"
    STAGE_DB_PASSWORD = "StAgE_VvK8mN2pL9xR4tQ7"
    
    # Настройка DEV
    dev_success = setup_database(DEV_CONFIG, "DEV", DEV_DB_PASSWORD)
    
    # Настройка STAGE
    stage_success = setup_database(STAGE_CONFIG, "STAGE", STAGE_DB_PASSWORD)
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ")
    print("="*60)
    print(f"DEV (172.16.0.35):    {'✅ OK' if dev_success else '❌ FAILED'}")
    print(f"STAGE (172.16.0.106): {'✅ OK' if stage_success else '❌ FAILED'}")
    print("="*60)
    
    if dev_success and stage_success:
        print("\n🎉 Все базы данных успешно настроены!")
        print("\nKubernetes секреты уже созданы:")
        print("  - stat-vbai-secret (DEV)")
        print("  - stat-vbai-secret (STAGE)")
        print("\nТеперь можешь деплоить stat-vbai!")
        return 0
    else:
        print("\n⚠️  Некоторые окружения не настроены")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)

