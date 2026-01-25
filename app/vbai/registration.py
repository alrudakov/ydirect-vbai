"""
Регистрация сервиса в API Gateway (api-vbai)
Аналогично ssh-vbai
"""
import os
import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

API_GATEWAY_URL = os.environ.get("GATEWAY_URL", settings.GATEWAY_URL)

# Эндпоинты для регистрации
ENDPOINTS = [
    # Управление профилями
    {"path": "/profiles/add", "method": "POST", "accessType": "Public"},
    {"path": "/profiles/list", "method": "POST", "accessType": "Public"},
    {"path": "/profiles/delete", "method": "POST", "accessType": "Public"},
    
    # AI endpoints (вызываются из aihandler)
    {"path": "/ai/campaigns", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/campaigns/create", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/campaigns/budget", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/campaigns/rsya", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/stats", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/adgroups", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/adgroups/create", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/keywords/add", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/ads", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/ads/create", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/ads/moderate", "method": "POST", "accessType": "Internal"},
    
    # Health checks
    {"path": "/health", "method": "GET", "accessType": "Public"},
    {"path": "/live", "method": "GET", "accessType": "Public"},
    {"path": "/ready", "method": "GET", "accessType": "Public"},
]


def register_service_and_endpoints(token: str) -> bool:
    """Регистрация сервиса и эндпоинтов в API Gateway"""
    url = f"{API_GATEWAY_URL}/register/services"
    headers = {"System": f"{token}"}
    
    data = {
        "name": settings.SERVICE_NAME,
        "endpoints": [
            {
                "serviceName": settings.SERVICE_NAME,
                "method": endpoint["method"],
                "path": endpoint["path"],
                "accessType": endpoint["accessType"]
            } for endpoint in ENDPOINTS
        ]
    }
    
    logger.info(f"Registering {settings.SERVICE_NAME} at {url}")
    logger.debug(f"Endpoints: {len(ENDPOINTS)}")
    
    # Запрос к внутреннему API без прокси
    with requests.Session() as s:
        s.trust_env = False
        response = s.post(url, headers=headers, json=data, timeout=30)
    
    if response.status_code != 200:
        if 'Duplicate entry' in response.text:
            logger.info("Service and endpoints already registered")
            return True
        else:
            logger.error(f"Error registering: {response.text}")
            return False
    
    logger.info("Service and endpoint registration successful")
    return True


def api_reg():
    """Главная функция регистрации"""
    token = os.environ.get("SERVICE_ACCOUNT_TOKEN")
    
    if not token:
        logger.warning("SERVICE_ACCOUNT_TOKEN not set, skipping gateway registration")
        return
    
    if not register_service_and_endpoints(token):
        logger.warning("Failed to register in API Gateway")
