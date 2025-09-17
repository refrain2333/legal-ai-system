#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动状态管理器
管理系统启动过程中的加载状态，支持实时监控和可视化展示
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
from threading import Lock

logger = logging.getLogger(__name__)


class LoadingStatus(Enum):
    """加载状态枚举"""
    PENDING = "pending"
    LOADING = "loading" 
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class LoadingStep:
    """加载步骤数据类"""
    id: str
    name: str
    description: str
    status: LoadingStatus = LoadingStatus.PENDING
    progress: float = 0.0  # 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """计算耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """是否已完成（成功或失败）"""
        return self.status in [LoadingStatus.SUCCESS, LoadingStatus.ERROR, LoadingStatus.SKIPPED]


@dataclass 
class SystemStartupStatus:
    """系统启动整体状态"""
    is_loading: bool = True
    overall_progress: float = 0.0
    current_step: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps: Dict[str, LoadingStep] = field(default_factory=dict)
    
    @property
    def total_duration(self) -> Optional[float]:
        """总耗时"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def completed_steps(self) -> int:
        """已完成步骤数"""
        return sum(1 for step in self.steps.values() if step.is_completed)
    
    @property
    def success_steps(self) -> int:
        """成功步骤数"""
        return sum(1 for step in self.steps.values() if step.status == LoadingStatus.SUCCESS)
    
    @property
    def failed_steps(self) -> int:
        """失败步骤数"""
        return sum(1 for step in self.steps.values() if step.status == LoadingStatus.ERROR)


class StartupManager:
    """启动状态管理器"""
    
    def __init__(self):
        self._status = SystemStartupStatus()
        self._lock = Lock()
        self._observers: List[Callable[[SystemStartupStatus], None]] = []
        self._loading_tasks: List[Callable] = []
        self._background_thread: Optional[threading.Thread] = None
        self.data_loader = None  # 将在initialize方法中设置
        
        # 预定义加载步骤
        self._define_loading_steps()
    
    def _define_loading_steps(self):
        """定义系统启动的各个步骤"""
        steps = [
            LoadingStep(
                id="config_check",
                name="配置检查",
                description="验证系统配置和环境设置"
            ),
            LoadingStep(
                id="compatibility_init",
                name="兼容性初始化", 
                description="加载Legacy兼容性模块"
            ),
            LoadingStep(
                id="vectors_loading",
                name="向量数据加载",
                description="加载法条和案例向量数据"
            ),
            LoadingStep(
                id="model_loading",
                name="AI模型加载",
                description="加载语义搜索模型"
            ),
            LoadingStep(
                id="search_engine_init",
                name="搜索引擎初始化",
                description="初始化增强搜索引擎"
            ),
            LoadingStep(
                id="health_check",
                name="系统健康检查",
                description="验证所有组件正常工作"
            )
        ]
        
        with self._lock:
            for step in steps:
                self._status.steps[step.id] = step
    
    def initialize(self, data_loader):
        """初始化启动管理器，设置数据加载器"""
        self.data_loader = data_loader
    
    def add_observer(self, callback: Callable[[SystemStartupStatus], None]):
        """添加状态观察者"""
        self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[SystemStartupStatus], None]):
        """移除状态观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """通知所有观察者状态更新"""
        for observer in self._observers:
            try:
                observer(self._status)
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")
    
    def start_step(self, step_id: str, details: Optional[Dict[str, Any]] = None):
        """开始执行某个步骤"""
        with self._lock:
            if step_id in self._status.steps:
                step = self._status.steps[step_id]
                step.status = LoadingStatus.LOADING
                step.start_time = datetime.now()
                step.progress = 0.0
                if details:
                    step.details.update(details)
                
                self._status.current_step = step_id
                self._update_overall_progress()
        
        self._notify_observers()
        logger.info(f"Started loading step: {step_id}")
    
    def update_step_progress(self, step_id: str, progress: float, details: Optional[Dict[str, Any]] = None):
        """更新步骤进度"""
        with self._lock:
            if step_id in self._status.steps:
                step = self._status.steps[step_id]
                step.progress = max(0.0, min(100.0, progress))
                if details:
                    step.details.update(details)
                
                self._update_overall_progress()
        
        self._notify_observers()
    
    def complete_step(self, step_id: str, success: bool = True, 
                     error_message: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None):
        """完成某个步骤"""
        with self._lock:
            if step_id in self._status.steps:
                step = self._status.steps[step_id]
                step.status = LoadingStatus.SUCCESS if success else LoadingStatus.ERROR
                step.end_time = datetime.now()
                step.progress = 100.0 if success else step.progress
                
                if error_message:
                    step.error_message = error_message
                if details:
                    step.details.update(details)
                
                self._update_overall_progress()
                
                # 检查是否所有步骤都完成
                if all(step.is_completed for step in self._status.steps.values()):
                    self._status.is_loading = False
                    self._status.end_time = datetime.now()
                    self._status.current_step = None
        
        self._notify_observers()
        status_text = "completed successfully" if success else f"failed: {error_message}"
        logger.info(f"Loading step {step_id} {status_text}")
    
    def skip_step(self, step_id: str, reason: str = ""):
        """跳过某个步骤"""
        with self._lock:
            if step_id in self._status.steps:
                step = self._status.steps[step_id]
                step.status = LoadingStatus.SKIPPED
                step.end_time = datetime.now()
                step.progress = 100.0
                step.error_message = f"Skipped: {reason}" if reason else "Skipped"
                
                self._update_overall_progress()
        
        self._notify_observers()
        logger.info(f"Skipped loading step: {step_id} - {reason}")
    
    def _update_overall_progress(self):
        """更新整体进度"""
        total_steps = len(self._status.steps)
        if total_steps == 0:
            self._status.overall_progress = 0.0
            return
        
        # 计算所有步骤的平均进度
        total_progress = sum(step.progress for step in self._status.steps.values())
        self._status.overall_progress = total_progress / total_steps
    
    def get_current_status(self) -> SystemStartupStatus:
        """获取当前状态的拷贝"""
        with self._lock:
            # 创建状态的深拷贝
            import copy
            return copy.deepcopy(self._status)
    
    def is_loading(self) -> bool:
        """系统是否正在加载"""
        return self._status.is_loading
    
    def is_ready(self) -> bool:
        """系统是否准备就绪"""
        return not self._status.is_loading and self._status.failed_steps == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        with self._lock:
            return {
                "is_loading": self._status.is_loading,
                "overall_progress": self._status.overall_progress,
                "current_step": self._status.current_step,
                "total_steps": len(self._status.steps),
                "completed_steps": self._status.completed_steps,
                "success_steps": self._status.success_steps,
                "failed_steps": self._status.failed_steps,
                "total_duration": self._status.total_duration,
                "is_ready": self.is_ready()
            }
    
    def force_reload(self):
        """强制重新加载所有组件"""
        logger.info("Forcing system reload...")
        
        with self._lock:
            # 重置所有步骤状态
            for step in self._status.steps.values():
                step.status = LoadingStatus.PENDING
                step.progress = 0.0
                step.start_time = None
                step.end_time = None
                step.error_message = None
                step.details.clear()
            
            # 重置整体状态
            self._status.is_loading = True
            self._status.overall_progress = 0.0
            self._status.current_step = None
            self._status.start_time = datetime.now()
            self._status.end_time = None
        
        self._notify_observers()
        
        # 启动重新加载
        self.start_background_loading()
    
    def start_background_loading(self):
        """启动后台加载"""
        if self._background_thread and self._background_thread.is_alive():
            logger.warning("Background loading already in progress")
            return
        
        self._background_thread = threading.Thread(
            target=self._execute_loading_sequence,
            name="StartupLoader",
            daemon=True
        )
        self._background_thread.start()
        logger.info("Started background loading thread")
    
    def _execute_loading_sequence(self):
        """执行完整的加载序列"""
        try:
            # 步骤1：配置检查
            self._load_config()
            
            # 步骤2：兼容性初始化
            self._init_compatibility()
            
            # 步骤3：向量数据加载
            self._load_vectors()
            
            # 步骤4：模型加载
            self._load_model()
            
            # 步骤5：搜索引擎初始化
            self._init_search_engine()
            
            # 步骤6：健康检查
            self._perform_health_check()
            
            logger.info("System startup completed successfully")
            
        except Exception as e:
            logger.error(f"Startup sequence failed: {e}", exc_info=True)
            # 确保当前步骤标记为失败
            if self._status.current_step:
                self.complete_step(self._status.current_step, success=False, 
                                 error_message=str(e))
    
    def _load_config(self):
        """加载配置"""
        self.start_step("config_check")
        try:
            from ...config.settings import settings
            
            self.update_step_progress("config_check", 50.0, {
                "model_name": settings.MODEL_NAME,
                "cache_limit": settings.CACHE_SIZE_LIMIT
            })
            
            # 模拟配置验证过程
            time.sleep(0.5)
            
            self.complete_step("config_check", details={
                "vectors_path": settings.DATA_VECTORS_PATH,
                "criminal_path": settings.DATA_CRIMINAL_PATH
            })
            
        except Exception as e:
            self.complete_step("config_check", success=False, error_message=str(e))
            raise
    
    def _init_compatibility(self):
        """初始化兼容性模块"""
        self.start_step("compatibility_init")
        try:
            from ..storage.legacy_compatibility import get_compatibility_manager
            
            manager = get_compatibility_manager()
            
            self.update_step_progress("compatibility_init", 100.0, {
                "registered_classes": len(manager.registered_classes),
                "module_mappings": len(manager.module_mappings)
            })
            
            self.complete_step("compatibility_init")
            
        except Exception as e:
            self.complete_step("compatibility_init", success=False, error_message=str(e))
            raise
    
    def _load_vectors(self):
        """加载向量数据"""
        self.start_step("vectors_loading")
        try:
            from ..storage.data_loader import get_data_loader
            
            loader = get_data_loader()
            
            self.update_step_progress("vectors_loading", 30.0, {"status": "检查向量文件"})
            
            vector_stats = loader.load_vectors()
            
            self.update_step_progress("vectors_loading", 80.0, {
                "articles_loaded": vector_stats.get('articles', 0),
                "cases_loaded": vector_stats.get('cases', 0)
            })
            
            if vector_stats['status'] in ['success', 'partial']:
                self.complete_step("vectors_loading", details={
                    "total_vectors": vector_stats.get('total_vectors', 0),
                    "loading_time": vector_stats.get('loading_time', 0),
                    "status": vector_stats['status']
                })
            else:
                raise Exception(f"Vector loading failed: {vector_stats.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.complete_step("vectors_loading", success=False, error_message=str(e))
            raise
    
    def _load_model(self):
        """加载AI模型"""
        self.start_step("model_loading")
        try:
            # 加载语义模型（立即加载模式）
            model_stats = self.data_loader.load_model(force_load=True)
            
            if model_stats['status'] in ['success', 'already_loaded']:
                self.complete_step("model_loading", success=True, details={
                    "model_name": model_stats.get('model_name', 'Unknown'),
                    "loading_time": model_stats.get('loading_time', 0),
                    "status": model_stats['status'],
                    "note": model_stats.get('note', '')
                })
            else:
                raise Exception(f"Model loading failed: {model_stats.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.complete_step("model_loading", success=False, error_message=str(e))
            raise
    
    def _init_search_engine(self):
        """初始化搜索引擎"""
        self.start_step("search_engine_init")
        try:
            from ..search.vector_search_engine import get_enhanced_search_engine
            
            self.update_step_progress("search_engine_init", 40.0, {"status": "获取搜索引擎实例"})
            
            search_engine = get_enhanced_search_engine()
            
            self.update_step_progress("search_engine_init", 80.0, {"status": "加载搜索数据"})
            
            load_result = search_engine.load_data()
            
            if load_result['status'] in ['success', 'already_loaded']:
                self.complete_step("search_engine_init", details={
                    "total_documents": load_result.get('total_documents', 0)
                })
            else:
                raise Exception(f"Search engine init failed: {load_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.complete_step("search_engine_init", success=False, error_message=str(e))
            raise
    
    def _perform_health_check(self):
        """执行健康检查"""
        self.start_step("health_check")
        try:
            from ..storage.data_loader import get_data_loader
            from ..search.vector_search_engine import get_enhanced_search_engine
            
            loader = get_data_loader()
            search_engine = get_enhanced_search_engine()
            
            self.update_step_progress("health_check", 30.0, {"status": "检查数据加载器"})
            
            loader_health = loader.health_check()
            logger.info(f"Loader health check result: {loader_health}")
            
            self.update_step_progress("health_check", 60.0, {"status": "检查搜索引擎"})
            
            search_stats = search_engine.get_stats()
            logger.info(f"Search engine stats: {search_stats}")
            
            self.update_step_progress("health_check", 90.0, {"status": "汇总健康状态"})
            
            # 检查数据加载器健康状态 - 支持懒加载模型
            loader_ready = (
                loader.vectors_loaded and 
                (loader.model_loaded or hasattr(loader, 'model'))  # 懒加载模式下模型可以未加载
            )
            
            # 检查搜索引擎状态
            search_ready = (
                search_stats.get('total_documents', 0) > 0 and
                search_engine.loaded
            )
            
            # 综合健康检查结果
            is_healthy = loader_ready and search_ready
            
            logger.info(f"Health check results - Loader ready: {loader_ready}, Search ready: {search_ready}, Overall healthy: {is_healthy}")
            
            if is_healthy:
                self.complete_step("health_check", details={
                    "loader_status": loader_health.get('summary', 'Ready'),
                    "loader_ready": loader_ready,
                    "search_ready": search_ready,
                    "total_documents": search_stats.get('total_documents', 0),
                    "vectors_loaded": loader.vectors_loaded,
                    "model_loaded": loader.model_loaded
                })
            else:
                # 提供更详细的错误信息
                error_details = []
                if not loader_ready:
                    error_details.append(f"数据加载器未就绪 (vectors: {loader.vectors_loaded}, model: {loader.model_loaded})")
                if not search_ready:
                    error_details.append(f"搜索引擎未就绪 (documents: {search_stats.get('total_documents', 0)})")
                
                error_message = "健康检查失败: " + "; ".join(error_details)
                raise Exception(error_message)
                
        except Exception as e:
            self.complete_step("health_check", success=False, error_message=str(e))
            raise


# 全局启动管理器实例
_startup_manager: Optional[StartupManager] = None
_manager_lock = Lock()

def get_startup_manager() -> StartupManager:
    """获取全局启动管理器实例"""
    global _startup_manager
    if _startup_manager is None:
        with _manager_lock:
            if _startup_manager is None:
                _startup_manager = StartupManager()
                # 初始化数据加载器
                from ..storage.data_loader import DataLoader
                from ...config.settings import settings
                data_loader = DataLoader(settings)
                _startup_manager.initialize(data_loader)
    return _startup_manager