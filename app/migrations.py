"""
Автомиграции для БД ydirect-vbai
Выполняются при старте сервиса
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def run_migrations(session: AsyncSession):
    """
    Выполнение миграций при старте сервиса
    """
    logger.info("🔄 Running database migrations...")
    
    # Создание таблицы ydirect_profiles
    create_table_sql = """
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
    """
    
    try:
        await session.execute(text(create_table_sql))
        await session.commit()
        logger.info("✅ Table 'ydirect_profiles' ready")
    except Exception as e:
        logger.warning(f"Migration note: {e}")
        await session.rollback()
    
    # Будущие миграции добавлять здесь:
    # await _add_column_if_not_exists(session, "ydirect_profiles", "new_column", "VARCHAR(255)")
    
    logger.info("✅ Migrations completed")


async def _add_column_if_not_exists(
    session: AsyncSession, 
    table: str, 
    column: str, 
    column_type: str
):
    """Добавить колонку если её нет"""
    try:
        await session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
        await session.commit()
        logger.info(f"Added column '{column}' to '{table}'")
    except Exception as e:
        if "Duplicate column" in str(e):
            logger.debug(f"Column '{column}' already exists")
        else:
            logger.warning(f"Could not add column '{column}': {e}")
        await session.rollback()

