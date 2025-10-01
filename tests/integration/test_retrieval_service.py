#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索服务集成测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.retrieval_service import get_retrieval_service


class TestRetrievalServiceIntegration:
    """检索服务集成测试"""
    
    @pytest.fixture
    def retrieval_service(self):
        """提供检索服务实例"""
        return get_retrieval_service()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, retrieval_service):
        """测试服务初始化"""
        assert retrieval_service is not None
        
        # 检查服务健康状态
        health_status = await retrieval_service.health_check()
        assert health_status.get("status") == "healthy"
    
    @pytest.mark.asyncio
    async def test_basic_search_functionality(self, retrieval_service):
        """测试基本搜索功能"""
        # 使用简单查询进行测试
        results = await retrieval_service.search("合同", top_k=5)
        
        # 检查返回结果
        assert isinstance(results, list)
        assert len(results) <= 5
        
        if results:  # 如果有结果
            first_result = results[0]
            assert "id" in first_result
            assert "content" in first_result
            assert "similarity" in first_result
            assert isinstance(first_result["similarity"], (int, float))
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, retrieval_service):
        """测试带过滤条件的搜索"""
        results = await retrieval_service.search(
            "刑法", 
            top_k=3, 
            document_type="law"
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, retrieval_service):
        """测试空查询处理"""
        results = await retrieval_service.search("", top_k=5)
        
        # 空查询应该返回空结果或错误处理
        assert isinstance(results, list)