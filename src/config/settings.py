"""
应用配置管理模块
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Legal Navigation AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # 模型配置
    MODEL_NAME: str = "shibing624/text2vec-base-chinese"
    MODEL_CACHE_DIR: str = "./models/pretrained"
    EMBEDDING_DIM: int = 768
    MAX_SEQUENCE_LENGTH: int = 512
    
    # 检索配置
    DEFAULT_TOP_K: int = 10
    SEARCH_TIMEOUT: int = 30
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600
    
    # API配置
    API_RATE_LIMIT: str = "100/minute"
    API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 文件路径配置
    DATA_RAW_PATH: str = "./data/raw"
    DATA_PROCESSED_PATH: str = "./data/processed"
    MODEL_STORAGE_PATH: str = "./models"
    INDEX_STORAGE_PATH: str = "./data/indices"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    @validator('CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator('DEBUG', pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True


# 创建全局配置实例
settings = Settings()