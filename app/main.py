from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.database import check_db_connection

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    # Startup
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}...")
    logger.info(f"📊 Log level: {settings.LOG_LEVEL}")
    
    # Проверка подключения к БД
    db_connected = await check_db_connection()
    if db_connected:
        logger.info("✅ Database connection established")
    else:
        logger.warning("⚠️ Failed to connect to database")
    
    yield
    
    # Shutdown
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")

app = FastAPI(
    title="Integrations VBAI",
    description="Integration Profiles Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": "1.0.0"
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
