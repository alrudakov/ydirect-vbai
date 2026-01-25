"""
API для управления профилями Яндекс.Директ
(Аналог manage_user_cred в ssh-vbai)
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_user_email_from_token
from app.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profiles", tags=["profiles"])


# =========== SCHEMAS ===========

class ProfileCreate(BaseModel):
    """Создание/обновление профиля"""
    alias: str
    token: str
    description: Optional[str] = None


class ProfileResponse(BaseModel):
    """Ответ с профилем (без токена)"""
    alias: str
    description: Optional[str]
    created_at: Optional[str]


class ProfileDelete(BaseModel):
    """Удаление профиля"""
    alias: str


# =========== ENDPOINTS ===========

@router.post("/add")
async def add_profile(
    profile: ProfileCreate,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить/обновить профиль Яндекс.Директ
    
    - alias: уникальное имя профиля (например "myads", "client1")
    - token: OAuth токен Яндекс.Директа
    - description: опциональное описание
    """
    logger.info(f"Adding profile '{profile.alias}' for user {user_email}")
    
    try:
        # Шифруем токен
        encrypted_token = encrypt_data(profile.token)
        
        # Upsert запрос
        query = text("""
            INSERT INTO ydirect_profiles (user_email, alias, token, description)
            VALUES (:user_email, :alias, :token, :description)
            ON DUPLICATE KEY UPDATE
                token = VALUES(token),
                description = VALUES(description),
                updated_at = NOW()
        """)
        
        await db.execute(query, {
            "user_email": user_email,
            "alias": profile.alias,
            "token": encrypted_token,
            "description": profile.description
        })
        await db.commit()
        
        logger.info(f"Profile '{profile.alias}' saved for user {user_email}")
        return {"status": "success", "message": f"Profile '{profile.alias}' saved"}
        
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list")
async def list_profiles(
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
) -> List[ProfileResponse]:
    """
    Получить список профилей пользователя
    """
    logger.info(f"Listing profiles for user {user_email}")
    
    try:
        query = text("""
            SELECT alias, description, created_at
            FROM ydirect_profiles
            WHERE user_email = :user_email
            ORDER BY alias
        """)
        
        result = await db.execute(query, {"user_email": user_email})
        rows = result.fetchall()
        
        profiles = []
        for row in rows:
            profiles.append(ProfileResponse(
                alias=row[0],
                description=row[1],
                created_at=str(row[2]) if row[2] else None
            ))
        
        return profiles
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_profile(
    profile: ProfileDelete,
    user_email: str = Depends(get_user_email_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Удалить профиль
    """
    logger.info(f"Deleting profile '{profile.alias}' for user {user_email}")
    
    try:
        query = text("""
            DELETE FROM ydirect_profiles
            WHERE user_email = :user_email AND alias = :alias
        """)
        
        result = await db.execute(query, {
            "user_email": user_email,
            "alias": profile.alias
        })
        await db.commit()
        
        if result.rowcount > 0:
            return {"status": "success", "message": f"Profile '{profile.alias}' deleted"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Profile '{profile.alias}' not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========== INTERNAL FUNCTIONS ===========

async def get_profile_token(
    user_email: str,
    alias: str,
    db: AsyncSession
) -> str:
    """
    Получить расшифрованный токен профиля (для внутреннего использования)
    """
    query = text("""
        SELECT token FROM ydirect_profiles
        WHERE user_email = :user_email AND alias = :alias
    """)
    
    result = await db.execute(query, {
        "user_email": user_email,
        "alias": alias
    })
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{alias}' not found"
        )
    
    # Расшифровываем токен
    return decrypt_data(row[0])

