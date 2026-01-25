"""
Модели БД для хранения профилей Яндекс.Директ
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class YDirectProfile(Base):
    """
    Профиль Яндекс.Директ (токен доступа)
    
    Аналогично ssh-vbai: user_email + alias = уникальный ключ
    """
    __tablename__ = "ydirect_profiles"
    
    # user_email из JWT токена
    user_email = Column(String(255), primary_key=True, nullable=False)
    
    # alias профиля (например "myads", "client1")
    alias = Column(String(255), primary_key=True, nullable=False)
    
    # OAuth токен Яндекс.Директа (зашифрованный)
    token = Column(Text, nullable=False)
    
    # Опциональное описание
    description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Индекс для быстрого поиска по user_email
    __table_args__ = (
        Index('idx_user_email', 'user_email'),
    )

