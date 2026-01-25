import os
import requests
import logging
from app.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_GATEWAY_URL = os.environ.get("GATEWAY_URL")
ENDPOINTS = [
    # Terminal POC
    {"path": "/api/ssh/creds", "method": "GET", "accessType": "Internal"},
    {"path": "/api/terminal/connect", "method": "POST", "accessType": "Internal"},
    # NOTE: api-vbai gateway allows wildcard only at the end of the path and
    # internally normalizes endpoints to ".../*".
    # Our actual routes:
    # - GET  /api/terminal/windows/{session_id}
    # - POST /api/terminal/windows/{session_id}/select
    #
    # Therefore we register:
    # - GET  /api/terminal/windows/*
    # - POST /api/terminal/windows/*
    # NOTE: api-vbai gateway stores endpoints by PATH (method gets overwritten on re-register),
    # so we use POST for both list + select under the same wildcard entry.
    {"path": "/api/terminal/windows/*", "method": "POST", "accessType": "Internal"},
    # AI tools (called by aihandler inside cluster; can be System)
    {"path": "/ai/terminal_input", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/terminal_keys", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/terminal_view", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/terminal_screen", "method": "POST", "accessType": "Internal"},
    {"path": "/ai/terminal_wait", "method": "POST", "accessType": "Internal"},
    # WebSocket handshake is HTTP GET. Gateway обычно проверяет allow-list путей.
    # Важно: реальный путь = /ws/terminal/{sessionId}, gateway матчит через wildcard candidates.
    {"path": "/ws/terminal/*", "method": "GET", "accessType": "Public"},
]

def register_service_and_endpoints(token):
    url = f"{API_GATEWAY_URL}/register/services"
    headers = {"System": f"{token}"}
    data = {
        "name": settings.APP_NAME,
        "endpoints": [
            {
                "serviceName": settings.APP_NAME,
                "method": endpoint["method"],
                "path": endpoint["path"],
                "accessType": endpoint["accessType"]
            } for endpoint in ENDPOINTS
        ]
    }
    
    logging.info(f"Registering service and endpoints at {url} with data {data} and headers {headers}")
    # Запрос к внутреннему API должен идти БЕЗ прокси
    with requests.Session() as s:
        s.trust_env = False  # не использовать системные переменные прокси
        response = s.post(url, headers=headers, json=data)

    if response.status_code != 200:
        if 'Duplicate entry' in response.text:
            logging.info("Service and endpoints already registered.")
            return False
        else:
            logging.error(f"Error registering service and endpoints: {response.text}")
            raise Exception("Error registering service and endpoints: " + response.text)
    
    logging.info("Service and endpoint registration successful.")
    return True

def api_reg():
    token = os.environ.get("SERVICE_ACCOUNT_TOKEN")
    if not token:
        raise Exception("Error reading service account token")

    if not register_service_and_endpoints(token):
        raise Exception("Error registering service and endpoints")

    logging.info("Service and endpoint registration successful")

