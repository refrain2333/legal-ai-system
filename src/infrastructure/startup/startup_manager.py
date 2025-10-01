#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化启动管理器
管理系统加载状态，保持API兼容性
"""

import time
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class StartupManager:
    """简化启动管理器 - 支持渐进式进度显示"""
    
    def __init__(self):
        self._is_loading = True
        self._is_ready = False
        self._current_step = "初始化"
        self._error = None
        self._start_time = time.time()
        self.data_loader = None
        
        # 渐进式进度跟踪
        self._overall_progress = 0.0
        self._step_weights = {
            "初始化": 5,
            "加载向量数据": 15,
            "加载AI模型": 70,    # 主要耗时
            "初始化搜索引擎": 10,
            "就绪": 0
        }
        self._documents_loaded = {"articles": 0, "cases": 0}
    
    def _update_progress(self, step: str, step_progress: float = 100.0):
        """更新整体进度"""
        # 计算已完成步骤的进度
        completed_progress = 0.0
        current_step_start = 0.0
        
        for step_name, weight in self._step_weights.items():
            if step_name == step:
                current_step_start = completed_progress
                break
            completed_progress += weight
        
        # 当前步骤的进度贡献
        current_step_contribution = (step_progress / 100.0) * self._step_weights.get(step, 0)
        
        # 总进度 = 已完成步骤 + 当前步骤进度
        self._overall_progress = completed_progress + current_step_contribution
        
        # 确保进度在0-100范围内
        self._overall_progress = max(0.0, min(100.0, self._overall_progress))
    
    def initialize(self, data_loader):
        """初始化数据加载器 - 异步启动加载"""
        self.data_loader = data_loader
        # 异步启动加载，不阻塞初始化
        import threading
        loading_thread = threading.Thread(target=self.start_loading, daemon=True)
        loading_thread.start()
        logger.info("启动管理器初始化完成，后台加载已开始")
    
    def start_loading(self):
        """开始系统加载"""
        if self.data_loader is None:
            logger.error("数据加载器未初始化")
            return
        
        try:
            logger.info("开始后台加载所有组件...")
            self._load_all_components()
        except Exception as e:
            logger.error(f"系统加载失败: {e}")
            self._error = str(e)
            self._is_loading = False
    
    def _load_all_components(self):
        """执行所有组件加载 - 支持渐进式进度更新"""
        try:
            # 使用统一的load_all方法，确保所有组件都被正确初始化
            self._current_step = "加载所有组件"
            self._update_progress("加载所有组件", 0)
            logger.info("开始加载所有系统组件...")
            
            # 模拟进度更新
            import threading
            import time as time_module
            
            def simulate_loading_progress():
                """模拟加载进度"""
                progress_points = [10, 20, 35, 50, 65, 75, 85, 95]
                for i, progress in enumerate(progress_points):
                    time_module.sleep(5)  # 每5秒更新一次进度
                    if self._current_step == "加载所有组件" and self._is_loading:
                        self._update_progress("加载所有组件", progress)
            
            # 启动进度模拟线程
            progress_thread = threading.Thread(target=simulate_loading_progress, daemon=True)
            progress_thread.start()
            
            # 调用统一的load_all方法
            all_stats = self.data_loader.load_all()
            
            if not all_stats.get('success', False):
                raise Exception(f"组件加载失败: {all_stats.get('error', '未知错误')}")
            
            # 记录加载的文档数量
            if 'vectors' in all_stats:
                vector_stats = all_stats['vectors']
                if isinstance(vector_stats, dict):
                    self._documents_loaded["articles"] = vector_stats.get('articles', 0)
                    self._documents_loaded["cases"] = vector_stats.get('cases', 0)
            
            # 检查多路召回引擎是否成功初始化
            multi_engine_stats = all_stats.get('multi_retrieval_engine', {})
            if multi_engine_stats.get('status') == 'success':
                logger.info("✅ 多路召回引擎初始化成功")
            else:
                logger.warning(f"⚠️ 多路召回引擎初始化失败: {multi_engine_stats}")
            
            self._update_progress("加载所有组件", 90)
            
            # 初始化搜索引擎
            self._current_step = "初始化搜索引擎"
            logger.info("初始化搜索引擎...")
            
            from ..search.vector_search_engine import get_enhanced_search_engine
            search_engine = get_enhanced_search_engine()
            
            load_result = search_engine.load_data()
            
            if load_result.get('status') not in ['success', 'already_loaded', 'partial']:
                raise Exception(f"搜索引擎初始化失败: {load_result.get('error', '未知错误')}")
            
            # 加载完成
            self._current_step = "就绪"
            self._overall_progress = 100.0
            self._is_loading = False
            self._is_ready = True
            logger.info("🎉 系统启动完成 - 所有组件已加载")
            logger.info(f"📊 加载统计: {all_stats.get('performance_summary', {})}")
            
        except Exception as e:
            self._error = str(e)
            self._is_loading = False
            self._is_ready = False
            logger.error(f"❌ 系统启动失败: {e}")
            raise
    
    def is_loading(self) -> bool:
        """系统是否正在加载"""
        return self._is_loading
    
    def is_ready(self) -> bool:
        """系统是否准备就绪"""
        return self._is_ready and not self._error
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要 - 支持渐进式进度和文档统计"""
        total_documents = self._documents_loaded["articles"] + self._documents_loaded["cases"]
        
        return {
            "is_loading": self._is_loading,
            "overall_progress": self._overall_progress,
            "current_step": self._current_step,
            "total_steps": 3,
            "completed_steps": 3 if self._is_ready else (2 if self._current_step == "初始化搜索引擎" else (1 if self._current_step == "加载AI模型" else 0)),
            "success_steps": 3 if self._is_ready else 0,
            "failed_steps": 1 if self._error else 0,
            "total_duration": time.time() - self._start_time,
            "is_ready": self.is_ready(),
            "error": self._error,
            # 新增：文档统计信息
            "documents_loaded": {
                "total": total_documents,
                "articles": self._documents_loaded["articles"],
                "cases": self._documents_loaded["cases"],
                "breakdown": f"法条: {self._documents_loaded['articles']}条, 案例: {self._documents_loaded['cases']}个" if total_documents > 0 else "暂无数据"
            }
        }
    
    def get_current_status(self):
        """获取当前状态 - 兼容旧API格式"""
        class SimpleStatus:
            def __init__(self, manager):
                self.is_loading = manager._is_loading
                self.overall_progress = manager._overall_progress
                self.current_step = manager._current_step
                self.total_duration = time.time() - manager._start_time
                self.completed_steps = 3 if manager._is_ready else (2 if manager._current_step == "初始化搜索引擎" else (1 if manager._current_step == "加载AI模型" else 0))
                self.success_steps = 3 if manager._is_ready else 0
                self.failed_steps = 1 if manager._error else 0
                
                # 兼容性：模拟steps结构
                self.steps = {}
                steps_list = [
                    ("vectors_loading", "加载向量数据", "加载法条和案例向量数据"),
                    ("model_loading", "加载AI模型", "加载语义搜索模型"),
                    ("search_engine_init", "初始化搜索引擎", "初始化增强搜索引擎")
                ]
                
                for i, (step_id, name, desc) in enumerate(steps_list):
                    step_status = "success" if manager._is_ready else (
                        "loading" if manager._current_step == name else (
                            "success" if i < self.completed_steps else "pending"
                        )
                    )
                    
                    # 计算进度
                    if manager._is_ready:
                        progress = 100.0
                    elif manager._current_step == name:
                        if name == "加载AI模型":
                            # 从overall_progress反推当前步骤进度
                            step_start = 5 + 15  # 前两步的权重
                            step_weight = 70
                            step_progress = max(0, (manager._overall_progress - step_start) / step_weight * 100)
                            progress = min(100.0, step_progress)
                        else:
                            progress = 50.0  # 其他步骤显示50%
                    elif i < self.completed_steps:
                        progress = 100.0
                    else:
                        progress = 0.0
                    
                    # 创建步骤对象
                    step_obj = type('Step', (), {
                        'id': step_id,
                        'name': name,
                        'description': desc,
                        'status': type('Status', (), {'value': step_status})(),
                        'progress': progress,
                        'duration': self.total_duration if step_status == "success" else None,
                        'error_message': manager._error if step_status == "error" else None,
                        'details': {}
                    })()
                    
                    self.steps[step_id] = step_obj
        
        return SimpleStatus(self)
    
    def force_reload(self):
        """强制重新加载"""
        logger.info("强制重新加载系统...")
        self._is_loading = True
        self._is_ready = False
        self._current_step = "重新初始化"
        self._error = None
        self._start_time = time.time()
        self.start_loading()


# 全局启动管理器实例 - 简化单例
_startup_manager: Optional[StartupManager] = None

def get_startup_manager() -> StartupManager:
    """获取全局启动管理器实例"""
    global _startup_manager
    if _startup_manager is None:
        _startup_manager = StartupManager()
        # 使用单例数据加载器，避免重复实例
        from ..storage.data_loader import get_data_loader
        from ...config.settings import settings
        data_loader = get_data_loader(config=settings)  # 使用单例
        _startup_manager.initialize(data_loader)
    return _startup_manager