"""
Регистрация инструментов в tools-vbai
(Аналогично ssh-vbai)
"""
import httpx
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

TOOLS_SERVICE_URL = "http://tools-vbai-svc"
TOOL_ID = "ydirect"


class ToolsRegistrationError(Exception):
    """Ошибка регистрации инструментов"""
    pass


class ToolsRegistrationService:
    def __init__(self):
        self.base_url = TOOLS_SERVICE_URL
        self.tool_id = TOOL_ID
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _collect_functions(self, json_dir: Path) -> Dict[str, Any]:
        """Собирает все функции из JSON файлов в директории"""
        functions = []
        
        for json_path in json_dir.glob("*.json"):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("type") == "function" and "function" in data:
                        functions.append(data)
                        logger.info(f"Added function from {json_path.name}: {data['function']['name']}")
                    elif data.get("type") == "instruction":
                        functions.append(data)
                        logger.info(f"Added instruction from {json_path.name}")
            except Exception as e:
                logger.error(f"Error processing {json_path.name}: {str(e)}")
                continue
        
        return {
            "id": self.tool_id,
            "data": functions
        }
    
    async def register_tool_with_retry(
        self, 
        tool_data: Dict[str, Any], 
        max_retries: int = 5, 
        delay: int = 10
    ):
        """Регистрация инструмента с повторными попытками"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                
                response = await self.client.post(
                    "/register",
                    json=tool_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✓ Successfully registered tool {self.tool_id}")
                    return result
                
                logger.error(f"Registration failed (status {response.status_code}): {response.text}")
                last_error = f"HTTP {response.status_code}: {response.text}"
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {str(e)}")
                last_error = str(e)
            
            if attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)
                logger.info(f"Waiting {wait_time}s before next attempt...")
                await asyncio.sleep(wait_time)
        
        raise ToolsRegistrationError(
            f"Failed to register tool {self.tool_id} after {max_retries} attempts. Last error: {last_error}"
        )


async def register_tools() -> None:
    """Регистрация инструментов в tools-vbai"""
    try:
        logger.info("\n🔧 Starting Yandex.Direct tools registration...")
        
        json_dir = Path(__file__).parent
        
        async with ToolsRegistrationService() as service:
            # Собираем все функции в один JSON
            tool_data = service._collect_functions(json_dir)
            
            if not tool_data["data"]:
                raise ToolsRegistrationError("No functions found in JSON files")
            
            # Логируем собранный JSON
            logger.info(f"\nCollected {len(tool_data['data'])} tools for '{TOOL_ID}'")
            logger.info("="*50)
            
            # Регистрируем инструмент
            await service.register_tool_with_retry(tool_data)
            
    except Exception as e:
        logger.error(f"Tools registration failed: {str(e)}")
        # Не прерываем запуск сервиса если не удалось зарегистрировать тулзы
        # (tools-vbai может быть ещё не готов)

