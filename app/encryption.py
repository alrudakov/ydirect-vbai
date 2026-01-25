"""
Шифрование токенов (как в ssh-vbai)
"""
import os
import base64
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Путь к ключу шифрования (как в ssh-vbai)
ENCRYPT_KEY_PATH = os.getenv("ENCRYPT_KEY_PATH", "/ntsb/au/tsb")

_fernet = None


def load_encryption_key(path: str = None) -> bytes:
    """Загрузка ключа шифрования из файла"""
    key_path = path or ENCRYPT_KEY_PATH
    
    try:
        with open(key_path, "rb") as f:
            key = f.read().strip()
        
        # Проверяем что ключ валидный
        if len(key) == 32:
            # Если 32 байта - кодируем в base64
            key = base64.urlsafe_b64encode(key)
        
        return key
    except FileNotFoundError:
        logger.warning(f"Encryption key not found at {key_path}, using fallback")
        # Fallback ключ для разработки (НЕ для продакшена!)
        return base64.urlsafe_b64encode(b"development_key_32_bytes_long!!")
    except Exception as e:
        logger.error(f"Failed to load encryption key: {e}")
        raise


def get_fernet() -> Fernet:
    """Получить Fernet instance (singleton)"""
    global _fernet
    if _fernet is None:
        key = load_encryption_key()
        _fernet = Fernet(key)
    return _fernet


def encrypt_data(data: str) -> str:
    """Зашифровать строку"""
    fernet = get_fernet()
    encrypted = fernet.encrypt(data.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """Расшифровать строку"""
    fernet = get_fernet()
    decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
    return decrypted.decode('utf-8')

