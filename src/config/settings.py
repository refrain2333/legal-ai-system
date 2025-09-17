"""
应用配置管理模块
基于Pydantic的类型安全配置管理
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    支持环境变量自动加载和类型安全验证
    """
    
    # ==================== 应用基础配置 ====================
    APP_NAME: str = "Legal Navigation AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # ==================== 服务器配置 ====================
    HOST: str = "127.0.0.1"
    PORT: int = 5005
    WORKERS: int = 1
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # ==================== AI模型配置 ====================
    MODEL_NAME: str = "shibing624/text2vec-base-chinese"
    MODEL_CACHE_DIR: str = "./.cache/sentence_transformers"
    LOCAL_MODEL_PATH: Optional[str] = None  # 本地模型路径，如果存在则优先使用
    MODEL_OFFLINE_MODE: bool = True  # 优先使用离线模式
    EMBEDDING_DIM: int = 768
    MAX_SEQUENCE_LENGTH: int = 512
    
    # ==================== 检索服务配置 ====================
    DEFAULT_TOP_K: int = 10
    SEARCH_TIMEOUT: int = 30
    CACHE_SIZE_LIMIT: int = 1000  # 内容缓存大小限制
    CACHE_TTL: int = 3600
    
    # ==================== API配置 ====================
    API_RATE_LIMIT: str = "100/minute"
    API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = [
        "http://localhost:5005", 
        "http://127.0.0.1:5005", 
        "null"
    ]
    
    # ==================== 文件存储配置 ====================
    DATA_RAW_PATH: str = "./data/raw"
    DATA_PROCESSED_PATH: str = "./data/processed"
    DATA_VECTORS_PATH: str = "./data/processed/vectors"
    DATA_CRIMINAL_PATH: str = "./data/processed/criminal"
    MODEL_STORAGE_PATH: str = "./models"
    INDEX_STORAGE_PATH: str = "./data/indices"
    
    # ==================== 安全配置 ====================
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ==================== 验证器配置 ====================
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        """处理逗号分隔的CORS origins字符串"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5005", "http://127.0.0.1:5005", "null"]

    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """解析字符串形式的布尔值"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v

    model_config = ConfigDict(
        case_sensitive=True,
        extra='allow',
        env_file_encoding='utf-8'
    )


def load_settings() -> Settings:
    """
    加载应用配置
    
    优先级: 环境变量 > .env文件 > 默认值
    支持环境变量覆盖配置
    
    Returns:
        Settings: 配置实例
    """
    from dotenv import load_dotenv
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("警告: .env文件未找到，使用默认配置")
        return Settings()
    
    print(f"信息: 从文件加载配置: {env_path.absolute()}")
    
    try:
        # 加载.env文件到环境变量
        load_dotenv(env_path, encoding='utf-8')
        
        # 特殊处理CORS_ORIGINS字段
        cors_origins = os.getenv('CORS_ORIGINS', '')
        if cors_origins:
            os.environ.pop('CORS_ORIGINS', None)
        
        # 创建配置实例
        settings_instance = Settings()
        
        # 手动设置CORS_ORIGINS
        if cors_origins:
            settings_instance.CORS_ORIGINS = [
                url.strip() for url in cors_origins.split(',') if url.strip()
            ]
        
        # 输出关键配置信息
        print("成功: 配置加载成功")
        print(f"   - 应用名称: {settings_instance.APP_NAME}")
        print(f"   - 运行环境: {settings_instance.APP_ENV}")
        print(f"   - 调试模式: {settings_instance.DEBUG}")
        print(f"   - 服务端口: {settings_instance.PORT}")
        print(f"   - CORS源: {settings_instance.CORS_ORIGINS}")
        
        return settings_instance
        
    except Exception as e:
        print(f"错误: 配置加载失败: {e}")
        print("信息: 使用默认配置...")
        return Settings()


# 全局配置实例
settings = load_settings()