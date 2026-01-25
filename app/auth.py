"""
Авторизация через JWT (как в ssh-vbai)
"""
import jwt
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_user_email_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Извлечь user_email из JWT токена.
    Подпись не проверяется (проверяется на gateway).
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, options={"verify_signature": False})
        user_email = payload.get('user_email')
        
        if not user_email:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token: no user_email claim"
            )
        
        return user_email
        
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token format")

