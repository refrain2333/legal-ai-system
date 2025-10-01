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
    """应用配置类"""

    # ==================== 应用基础配置 ====================
    APP_NAME: str = "Legal Navigation AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ==================== 服务器配置 ====================
    HOST: str = "127.0.0.1"
    PORT: int = 5006
    WORKERS: int = 1

    # ==================== LLM开关配置 ====================
    LLM_ENABLED: bool = True
    LLM_PROVIDER_CLOUDFLARE: bool = False
    LLM_PROVIDER_GLM: bool = False
    LLM_PROVIDER_GEMINI: bool = False
    LLM_PROVIDER_SILICONFLOW: bool = True

    # ==================== 模型配置 ====================
    MODEL_NAME: str = "thunlp/Lawformer"
    MODEL_CACHE_DIR: str = "./.cache/transformers"
    LOCAL_MODEL_PATH: str = "./.cache/transformers/models--thunlp--Lawformer"
    FINE_TUNED_MODEL_PATH: str = "./models/fine_tuned/lawformer_enhanced_v1.0.pt"
    USE_FINE_TUNED_MODEL: bool = True
    EMBEDDING_DIM: int = 768
    MAX_SEQUENCE_LENGTH: int = 4096
    MODEL_OFFLINE_MODE: bool = True

    # ==================== 检索配置 ====================
    DEFAULT_TOP_K: int = 10
    SEARCH_TIMEOUT: int = 30
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # ==================== API配置 ====================
    API_RATE_LIMIT: str = "100/minute"
    API_KEY: str = ""
    CORS_ORIGINS: List[str] = ["http://localhost:5006", "http://127.0.0.1:5006", "null"]

    # ==================== 安全配置 ====================
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ==================== LLM服务商配置 ====================
    GEMINI_API_KEY: str = ""
    GEMINI_API_BASE: str = "https://233-gemini-29.deno.dev/chat/completions"
    GEMINI_MODELS: List[str] = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

    GLM_API_KEY: str = ""
    GLM_API_BASE: str = "https://open.bigmodel.cn/api/paas/v4/"
    GLM_MODEL: str = "glm-4.5-flash"

    CF_ACCOUNT_ID: str = ""
    CF_API_TOKEN: str = ""
    CF_MODEL: str = "@cf/openai/gpt-oss-20b"  # Cloudflare具体模型名称

    # 硅基流动配置
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODELS: List[str] = [
        "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "deepseek-ai/DeepSeek-V2.5",
        "meta-llama/Meta-Llama-3.1-8B-Instruct"
    ]

    # ==================== LLM通用配置 ====================
    LLM_REQUEST_TIMEOUT: int = 60  # 增加到60秒，避免Cloudflare超时
    LLM_MAX_RETRIES: int = 1  # 减少重试次数，提高响应速度
    LLM_ENABLE_FALLBACK: bool = True
    LLM_MODEL_FALLBACK: bool = True

    # ==================== 文件路径配置 ====================
    DATA_RAW_PATH: str = "./data/raw"
    DATA_PROCESSED_PATH: str = "./data/processed"
    DATA_VECTORS_PATH: str = "./data/processed/vectors"
    DATA_CRIMINAL_PATH: str = "./data/processed/criminal"
    MODEL_STORAGE_PATH: str = "./models"
    INDEX_STORAGE_PATH: str = "./data/indices"

    # ==================== LLM分类配置 ====================
    # LLM问题分类参数
    CLASSIFICATION_MAX_TOKENS: int = 800  # 减少token数量，提高速度
    CLASSIFICATION_TEMPERATURE: float = 0.1  # 降低温度，提高稳定性
    CLASSIFICATION_TIMEOUT: int = 30  # 减少超时时间
    
    # LLM回答生成配置
    ANSWER_GENERATION_MAX_TOKENS: int = 1500
    ANSWER_GENERATION_TEMPERATURE: float = 0.3
    ANSWER_GENERATION_TIMEOUT: int = 60

    # LLM问题分类提示词模板（简化版，提高速度）
    CLASSIFICATION_PROMPT_TEMPLATE: str = """你是专业法律AI分类器，判断查询是否属于刑事法律范畴。

【用户查询】
"{query}"

【标准罪名】
{crimes_list}

【输出要求】
严格按照JSON格式输出：

{{
    "is_criminal_law": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "简要分析推理过程",
    "identified_crimes": [
        {{
            "crime_name": "标准罪名",
            "relevance": 0.0-1.0
        }}
    ],
    "query2doc_generated": "生成案例事实叙述（80字）",
    "hyde_answer": "生成法律条文说明（100字）",
    "bm25_keywords": [
        {{"keyword": "关键词", "weight": 0.0-1.0}}
    ]
}}

【注意】
- 非刑法问题时identified_crimes等为空
- 数值字段使用数字格式
- 关键词避免通用词汇"""

    # ==================== 知识图谱配置 ====================
    # 知识图谱基础配置
    ENABLE_KNOWLEDGE_GRAPH: bool = True
    KG_CONFIDENCE_THRESHOLD: float = 0.05  # 关系置信度阈值（5%）
    KG_RELATION_MIN_COUNT: int = 2  # 关系最小案例数量
    KG_STORAGE_PATH: str = "./data/processed/knowledge_graph/knowledge_graph.pkl"

    # 知识图谱增强搜索权重
    KG_ORIGINAL_WEIGHT: float = 0.5    # 原始查询权重
    KG_RELATED_ARTICLE_WEIGHT: float = 0.3  # 相关法条权重
    KG_RELATED_CRIME_WEIGHT: float = 0.2    # 相关罪名权重

    # Query2doc配置
    ENABLE_QUERY2DOC: bool = True
    QUERY2DOC_MAX_TOKENS: int = 120
    QUERY2DOC_TEMPERATURE: float = 0.3

    # HyDE配置
    ENABLE_HYDE: bool = True
    HYDE_MAX_TOKENS: int = 200
    HYDE_TEMPERATURE: float = 0.2

    # 多路召回权重
    HYBRID_WEIGHT: float = 0.4
    QUERY2DOC_WEIGHT: float = 0.35
    HYDE_WEIGHT: float = 0.25

    # ==================== LLM提示词配置 ====================
    # Query2doc法律专用提示词模板
    QUERY2DOC_PROMPT_TEMPLATE: str = """用户查询："{query}"

请生成一个与此查询最相关的法律案例事实叙述（50-100字），要求：
1. 模拟公诉机关指控书的表述风格
2. 包含时间、地点、具体行为、损害后果等要素
3. 使用专业的法律术语
4. 如涉及罪名，请明确指出
5. 重点关注刑事法律领域

生成的法律案例事实："""

    # HyDE法律专业回答模板
    HYDE_PROMPT_TEMPLATE: str = """作为专业法律AI助手，请回答用户问题："{query}"

要求：
1. 回答要专业准确，像法律解释或案例分析摘要
2. 包含相关法条信息（如果适用）
3. 如涉及具体罪名，请明确指出
4. 控制在150字以内
5. 使用标准法律术语
6. 重点关注刑事法律领域

专业回答："""

    # 系统提示词（用于LLM客户端）
    LEGAL_SYSTEM_PROMPT: str = "你是一个专业的刑事法律AI助手，精通中华人民共和国刑法。请用准确的法律术语回答问题，重点关注刑事法律领域的法条、案例和司法解释。"

    @field_validator('LLM_ENABLED', 'LLM_PROVIDER_CLOUDFLARE', 'LLM_PROVIDER_GLM', 'LLM_PROVIDER_GEMINI', 'LLM_PROVIDER_SILICONFLOW', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.strip().lower() in ('true','1','yes','on')
        return bool(v)

    # ==================== 验证器配置 ====================
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        """处理逗号分隔的CORS origins字符串"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5006", "http://127.0.0.1:5006", "null"]

    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """解析字符串形式的布尔值"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v

    @classmethod
    def load_knowledge_graph_crimes(cls) -> str:
        """从知识图谱文件动态加载标准罪名列表"""
        from pathlib import Path
        crimes_file = Path(__file__).parent.parent.parent / "data/processed/knowledge_graph/knowledge_graph_crimes_list.txt"

        if not crimes_file.exists():
            raise FileNotFoundError(f"知识图谱罪名文件不存在: {crimes_file}")

        try:
            with open(crimes_file, 'r', encoding='utf-8') as f:
                crimes_list = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # 跳过空行和注释
                        crimes_list.append(line)

                if not crimes_list:
                    raise ValueError("知识图谱罪名文件为空")

                # 每行就是一个完整罪名
                # 注意：不能使用顿号分隔，因为罪名本身包含顿号！
                # 使用换行符分隔，让AI能够正确解析每个完整罪名
                return '\n'.join(crimes_list)

        except Exception as e:
            raise RuntimeError(f"加载知识图谱罪名文件失败: {e}")

    @field_validator('GEMINI_MODELS', 'SILICONFLOW_MODELS', mode='before')
    @classmethod
    def parse_model_lists(cls, v):
        """解析模型列表（支持Gemini和SiliconFlow）"""
        if isinstance(v, str):
            # 从环境变量解析逗号分隔的字符串
            models = [model.strip() for model in v.split(',') if model.strip()]
            return models if models else None
        elif isinstance(v, list):
            return v
        return None

    @field_validator('GEMINI_MODELS', mode='after')
    @classmethod
    def set_default_gemini_models(cls, v):
        """设置Gemini模型的默认值"""
        if not v:
            return [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite"
            ]
        return v

    @field_validator('SILICONFLOW_MODELS', mode='after')
    @classmethod
    def set_default_siliconflow_models(cls, v):
        """设置硅基流动模型的默认值"""
        if not v:
            return [
                "Qwen/Qwen3-Next-80B-A3B-Instruct",
                "Qwen/Qwen2.5-7B-Instruct",
                "deepseek-ai/DeepSeek-V2.5",
                "meta-llama/Meta-Llama-3.1-8B-Instruct"
            ]
        return v

    model_config = ConfigDict(
        case_sensitive=True,
        extra='allow',
        env_file_encoding='utf-8',
        # 不要自动解析JSON，让字段验证器处理
        env_parse_none_str=None,
        # 禁用自动JSON解析复杂类型
        env_ignore_empty=True
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

        # 特殊处理模型列表字段
        cors_origins = os.getenv('CORS_ORIGINS', '')
        gemini_models = os.getenv('GEMINI_MODELS', '')
        siliconflow_models = os.getenv('SILICONFLOW_MODELS', '')

        if cors_origins:
            os.environ.pop('CORS_ORIGINS', None)
        if gemini_models:
            os.environ.pop('GEMINI_MODELS', None)
        if siliconflow_models:
            os.environ.pop('SILICONFLOW_MODELS', None)

        # 创建配置实例
        settings_instance = Settings()

        # 手动设置特殊字段
        if cors_origins:
            settings_instance.CORS_ORIGINS = [
                url.strip() for url in cors_origins.split(',') if url.strip()
            ]

        if gemini_models:
            settings_instance.GEMINI_MODELS = [
                model.strip() for model in gemini_models.split(',') if model.strip()
            ]

        if siliconflow_models:
            settings_instance.SILICONFLOW_MODELS = [
                model.strip() for model in siliconflow_models.split(',') if model.strip()
            ]

        # 输出关键配置信息
        print("成功: 配置加载成功")
        print(f"   - 应用名称: {settings_instance.APP_NAME}")
        print(f"   - 运行环境: {settings_instance.APP_ENV}")
        print(f"   - 调试模式: {settings_instance.DEBUG}")
        print(f"   - 服务端口: {settings_instance.PORT}")
        print(f"   - 硅基流动模型: {settings_instance.SILICONFLOW_MODELS}")

        return settings_instance

    except Exception as e:
        print(f"错误: 配置加载失败: {e}")
        print("信息: 使用默认配置...")
        return Settings()


# 全局配置实例
settings = load_settings()