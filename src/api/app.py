"""
FastAPI应用创建和配置
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from src.config.settings import settings
from src.utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)


def create_app() -> FastAPI:
    """
    创建和配置FastAPI应用
    
    Returns:
        FastAPI: 配置好的应用实例
    """
    
    # 创建FastAPI实例
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="智能法律匹配与咨询系统",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加可信主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["127.0.0.1", "localhost"]
    )
    
    # 添加请求处理时间中间件
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # 添加请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # 记录请求开始
        logger.info(f"📥 {request.method} {request.url.path}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录请求完成
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code}")
        
        return response
    
    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"❌ 全局异常: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "服务器内部错误",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "欢迎使用法智导航系统",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "文档已禁用"
        }
    
    # 这里将添加其他路由
    # from src.api.routes import api_router
    # app.include_router(api_router, prefix="/api/v1")
    
    return app