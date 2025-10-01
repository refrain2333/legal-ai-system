#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索调试数据模型
用于前端可视化搜索过程的完整数据结构定义
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ModuleStatus(str, Enum):
    """模块运行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class SearchPath(str, Enum):
    """搜索路径类型"""
    KNOWLEDGE_GRAPH = "knowledge_graph"
    LLM_ENHANCED = "llm_enhanced"
    BM25_HYBRID = "bm25_hybrid"
    BASIC_SEMANTIC = "basic_semantic"
    GENERAL_AI = "general_ai"


class ModuleTrace(BaseModel):
    """模块执行trace数据 - 统一格式"""
    module_name: str = Field(description="模块名称")
    stage: str = Field(description="处理阶段")
    status: ModuleStatus = Field(default=ModuleStatus.PENDING, description="执行状态")
    input_data: Any = Field(description="输入数据")
    output_data: Any = Field(description="输出数据")
    processing_time_ms: float = Field(default=0.0, description="处理耗时(毫秒)")
    confidence_score: Optional[float] = Field(None, description="置信度分数 0-1")

    # 调试信息
    debug_info: Dict[str, Any] = Field(default_factory=dict, description="调试信息")
    error_message: Optional[str] = Field(None, description="错误信息")
    fallback_triggered: bool = Field(default=False, description="是否触发降级")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    class Config:
        use_enum_values = True


class ClassificationTrace(BaseModel):
    """阶段1: LLM问题分类的trace数据"""
    is_criminal_law: bool = Field(description="是否刑法相关")
    confidence: float = Field(description="分类置信度")
    reasoning: str = Field(description="分类推理过程")
    keywords_detected: List[str] = Field(default_factory=list, description="检测到的关键词")
    llm_model_used: str = Field(description="使用的LLM模型")
    prompt_tokens: int = Field(default=0, description="提示词token数")
    response_tokens: int = Field(default=0, description="回复token数")


class ExtractionTrace(BaseModel):
    """阶段2: 结构化信息提取的trace数据"""
    identified_crimes: List[Dict[str, Any]] = Field(default_factory=list, description="识别的罪名")
    query2doc_enhanced: str = Field(description="Query2doc增强后的查询")
    hyde_hypothetical: str = Field(description="HyDE生成的假设答案")
    bm25_keywords: List[str] = Field(default_factory=list, description="BM25关键词")
    crimes_list_version: str = Field(description="罪名列表版本")


class RoutingTrace(BaseModel):
    """阶段3: 智能路由决策的trace数据"""
    selected_paths: List[SearchPath] = Field(description="选择的搜索路径")
    routing_reasoning: str = Field(description="路由决策推理")
    parallel_execution: bool = Field(default=True, description="是否并行执行")
    path_priorities: Dict[str, float] = Field(default_factory=dict, description="路径优先级")


class FusionTrace(BaseModel):
    """阶段5: 结果融合的trace数据"""
    fusion_algorithm: str = Field(description="融合算法")
    confidence_scores: List[float] = Field(default_factory=list, description="各结果置信度")
    consistency_bonus: float = Field(default=0.0, description="一致性奖励分")
    final_answer: str = Field(description="最终AI回答")
    sources_used: int = Field(description="使用的数据源数量")


class SearchPipelineTrace(BaseModel):
    """完整搜索管道trace数据"""
    request_id: str = Field(description="请求ID")
    user_query: str = Field(description="用户查询")
    total_duration_ms: float = Field(default=0.0, description="总处理时间")
    processing_mode: str = Field(description="处理模式: criminal_law或general_ai")

    # 各阶段trace数据
    classification: Optional[ModuleTrace] = Field(None, description="问题分类trace")
    extraction: Optional[ModuleTrace] = Field(None, description="信息提取trace")
    routing: Optional[ModuleTrace] = Field(None, description="路由决策trace")
    searches: Dict[str, ModuleTrace] = Field(default_factory=dict, description="搜索模块traces")
    fusion: Optional[ModuleTrace] = Field(None, description="结果融合trace")

    # 统计摘要
    summary: Dict[str, Any] = Field(default_factory=dict, description="执行摘要")

    class Config:
        use_enum_values = True


class SearchDebugResponse(BaseModel):
    """调试搜索API响应格式"""
    success: bool = Field(description="请求是否成功")
    request_id: str = Field(description="请求ID")
    trace: SearchPipelineTrace = Field(description="完整trace数据")
    final_result: Dict[str, Any] = Field(description="最终搜索结果")
    debug_enabled: bool = Field(description="调试模式是否启用")


class ModuleStatusInfo(BaseModel):
    """模块状态信息"""
    module_name: str = Field(description="模块名称")
    status: str = Field(description="状态: ok/warning/error")
    reason: str = Field(description="状态原因")
    last_check: datetime = Field(description="最后检查时间")
    performance_stats: Dict[str, Any] = Field(default_factory=dict, description="性能统计")


class SystemDebugInfo(BaseModel):
    """系统整体调试信息"""
    modules_status: List[ModuleStatusInfo] = Field(description="各模块状态")
    recent_searches: List[Dict[str, Any]] = Field(description="最近搜索记录")
    performance_metrics: Dict[str, Any] = Field(description="性能指标")
    system_health: str = Field(description="系统健康状态")


# 工具函数
def create_module_trace(
    module_name: str,
    stage: str,
    input_data: Any = None,
    success: bool = True,
    processing_time_ms: float = 0.0,
    **kwargs
) -> ModuleTrace:
    """创建标准化的ModuleTrace"""
    return ModuleTrace(
        module_name=module_name,
        stage=stage,
        status=ModuleStatus.SUCCESS if success else ModuleStatus.ERROR,
        input_data=input_data or {},
        output_data=kwargs.get('output_data', {}),
        processing_time_ms=processing_time_ms,
        confidence_score=kwargs.get('confidence_score'),
        debug_info=kwargs.get('debug_info', {}),
        error_message=kwargs.get('error_message'),
        fallback_triggered=kwargs.get('fallback_triggered', False),
        metadata=kwargs.get('metadata', {})
    )


def create_search_pipeline_trace(
    request_id: str,
    user_query: str,
    processing_mode: str = "criminal_law"
) -> SearchPipelineTrace:
    """创建搜索管道trace"""
    return SearchPipelineTrace(
        request_id=request_id,
        user_query=user_query,
        processing_mode=processing_mode,
        summary={
            "created_at": datetime.now().isoformat(),
            "stages_completed": 0,
            "total_modules_used": 0,
            "successful_modules": 0,
            "highest_confidence": 0.0
        }
    )


# 示例数据（用于测试）
def create_sample_trace() -> SearchPipelineTrace:
    """创建示例trace数据"""
    import uuid

    trace = create_search_pipeline_trace(
        request_id=str(uuid.uuid4()),
        user_query="打架致人轻伤怎么判？"
    )

    # 示例分类trace
    trace.classification = create_module_trace(
        module_name="llm_classifier",
        stage="问题分类",
        input_data={"query": "打架致人轻伤怎么判？"},
        processing_time_ms=250.0,
        confidence_score=0.95,
        output_data={
            "is_criminal_law": True,
            "confidence": 0.95,
            "reasoning": "涉及故意伤害等刑事犯罪行为"
        }
    )

    # 示例搜索trace
    trace.searches["knowledge_graph"] = create_module_trace(
        module_name="knowledge_graph_search",
        stage="知识图谱搜索",
        processing_time_ms=890.0,
        confidence_score=0.88,
        output_data={"articles_found": 3, "cases_found": 5}
    )

    trace.total_duration_ms = 1250.0
    trace.summary.update({
        "stages_completed": 5,
        "total_modules_used": 3,
        "successful_modules": 3,
        "highest_confidence": 0.95
    })

    return trace


if __name__ == "__main__":
    # 测试数据模型
    sample = create_sample_trace()
    print("✅ 数据模型创建成功")
    print(f"请求ID: {sample.request_id}")
    print(f"分类置信度: {sample.classification.confidence_score}")
    print(f"总耗时: {sample.total_duration_ms}ms")