"""
Яндекс.Директ Integration Service (ydirect-vbai)

Микросервис для работы с Яндекс.Директ API v5.
Аналогично ssh-vbai: профили с токенами + AI endpoints для aihandler.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.database import check_db_connection, engine, Base, AsyncSessionLocal
from app.routers import profiles, ai
from app.vbai.registration import api_reg
from app.toolset.reg import register_tools
from app.migrations import run_migrations

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация таблиц БД через миграции"""
    async with AsyncSessionLocal() as session:
        await run_migrations(session)
    
    logger.info("✅ Database initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    # ========== STARTUP ==========
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")
    logger.info(f"📊 Log level: {settings.LOG_LEVEL}")
    
    # Проверка подключения к БД
    db_connected = await check_db_connection()
    if db_connected:
        logger.info("✅ Database connection established")
        # Инициализация таблиц
        await init_db()
    else:
        logger.warning("⚠️ Failed to connect to database")
    
    # Регистрация в api-vbai gateway
    try:
        api_reg()
        logger.info("✅ Registered in API Gateway")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register in API Gateway: {e}")
    
    # Регистрация инструментов в tools-vbai
    try:
        await register_tools()
        logger.info("✅ Tools registered in tools-vbai")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register tools: {e}")
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")


app = FastAPI(
    title="Yandex.Direct Integration Service",
    description="API для работы с Яндекс.Директ через профили с OAuth токенами",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(profiles.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": "1.0.0",
        "description": "Yandex.Direct Integration Service"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    db_ok = await check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected"
    }


@app.get("/live")
async def liveness():
    """Liveness probe"""
    return {"status": "alive"}


@app.get("/ready")
async def readiness():
    """Readiness probe"""
    db_ok = await check_db_connection()
    if db_ok:
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}, 503


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
