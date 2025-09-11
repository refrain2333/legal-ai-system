"""
应用配置管理模块
"""

import os
from typing import List, Optional
from pydantic import BaseModel, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Legal Navigation AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 5005
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
    CORS_ORIGINS: List[str] = ["http://localhost:5005", "http://127.0.0.1:5005"]
    
    # 文件路径配置
    DATA_RAW_PATH: str = "./data/raw"
    DATA_PROCESSED_PATH: str = "./data/processed"
    MODEL_STORAGE_PATH: str = "./models"
    INDEX_STORAGE_PATH: str = "./data/indices"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # 处理逗号分隔的字符串
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5005", "http://127.0.0.1:5005"]  # 默认值
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra='allow'
    )


# 创建全局配置实例
def _load_settings() -> "Settings":
    """加载配置，优先使用.env文件"""
    from dotenv import load_dotenv
    import os
    
    env_path = Path(".env")
    
    if env_path.exists():
        print(f"Loading configuration from: {env_path.absolute()}")
        try:
            # 手动加载.env文件到环境变量
            load_dotenv(env_path, encoding='utf-8')
            
            # 特殊处理CORS_ORIGINS字段
            cors_origins = os.getenv('CORS_ORIGINS', '')
            if cors_origins:
                # 删除环境变量，避免Pydantic解析错误
                os.environ.pop('CORS_ORIGINS', None)
            
            # 创建Settings实例
            settings_instance = Settings()
            
            # 手动设置CORS_ORIGINS
            if cors_origins:
                settings_instance.CORS_ORIGINS = [url.strip() for url in cors_origins.split(',') if url.strip()]
            
            print(f"Configuration loaded successfully:")
            print(f"  - APP_NAME: {settings_instance.APP_NAME}")
            print(f"  - DEBUG: {settings_instance.DEBUG}")
            print(f"  - PORT: {settings_instance.PORT}")
            print(f"  - CORS_ORIGINS: {settings_instance.CORS_ORIGINS}")
            
            return settings_instance
            
        except Exception as e:
            print(f"Warning: Failed to load .env file ({e})")
            print("Falling back to default settings...")
            return Settings()
    else:
        print("Warning: .env file not found, using default settings")
        return Settings()

settings = _load_settings()