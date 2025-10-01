#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索响应工厂
消除重复的格式化代码，统一响应格式
"""

from typing import Dict, Any, List, Optional
from ...api.models import SearchResponse, SearchResult


class SearchResponseFactory:
    """搜索响应工厂 - 消除重复的格式化代码"""

    @staticmethod
    def create_mixed_response(
        service_result: Dict[str, Any],
        query: str
    ) -> SearchResponse:
        """
        创建混合搜索响应

        Args:
            service_result: 服务层返回的结果
            query: 查询文本

        Returns:
            标准的SearchResponse对象
        """
        builder = SearchResponseBuilder()

        return (builder
                .set_success(service_result.get('success', False))
                .set_query(query)
                .add_articles(service_result.get('articles', []))
                .add_cases(service_result.get('cases', []))
                .build())

    @staticmethod
    def create_error_response(error_message: str, query: str = "") -> SearchResponse:
        """
        创建错误响应

        Args:
            error_message: 错误信息
            query: 查询文本

        Returns:
            错误响应对象
        """
        return SearchResponse(
            success=False,
            error=error_message,
            query=query,
            results=[],
            total=0
        )

    @staticmethod
    def create_simple_response(
        results: List[Dict[str, Any]],
        query: str,
        success: bool = True
    ) -> SearchResponse:
        """
        创建简单搜索响应

        Args:
            results: 搜索结果列表
            query: 查询文本
            success: 是否成功

        Returns:
            简单响应对象
        """
        builder = SearchResponseBuilder()

        return (builder
                .set_success(success)
                .set_query(query)
                .add_mixed_results(results)
                .build())


class SearchResponseBuilder:
    """搜索响应建造者 - 支持链式调用"""

    def __init__(self):
        self.response_data = {
            'success': True,
            'results': [],
            'total': 0,
            'query': '',
            'error': None
        }

    def set_success(self, success: bool) -> 'SearchResponseBuilder':
        """设置成功状态"""
        self.response_data['success'] = success
        return self

    def set_query(self, query: str) -> 'SearchResponseBuilder':
        """设置查询文本"""
        self.response_data['query'] = query
        return self

    def set_error(self, error: str) -> 'SearchResponseBuilder':
        """设置错误信息"""
        self.response_data['error'] = error
        self.response_data['success'] = False
        return self

    def add_articles(self, articles: List[Dict]) -> 'SearchResponseBuilder':
        """
        添加法条结果

        Args:
            articles: 法条结果列表
        """
        for item in articles:
            result = self._create_article_result(item)
            self.response_data['results'].append(result)
        return self

    def add_cases(self, cases: List[Dict]) -> 'SearchResponseBuilder':
        """
        添加案例结果

        Args:
            cases: 案例结果列表
        """
        for item in cases:
            result = self._create_case_result(item)
            self.response_data['results'].append(result)
        return self

    def add_mixed_results(self, results: List[Dict]) -> 'SearchResponseBuilder':
        """
        添加混合结果（自动判断类型）

        Args:
            results: 混合结果列表
        """
        for item in results:
            result_type = item.get('type', 'unknown')
            if result_type == 'article':
                result = self._create_article_result(item)
            elif result_type == 'case':
                result = self._create_case_result(item)
            else:
                # 兜底处理：根据字段判断类型
                if item.get('article_number') is not None:
                    result = self._create_article_result(item)
                elif item.get('case_id') is not None:
                    result = self._create_case_result(item)
                else:
                    # 默认作为通用结果处理
                    result = SearchResult(
                        id=item.get('id', ''),
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        similarity=item.get('similarity', 0.0),
                        type='unknown'
                    )
            self.response_data['results'].append(result)
        return self

    def _create_article_result(self, item: Dict) -> SearchResult:
        """创建法条结果"""
        return SearchResult(
            id=item.get('id', ''),
            title=item.get('title', ''),
            content=item.get('content', ''),
            similarity=item.get('similarity', 0.0),
            type=item.get('type', 'article'),
            # 法条特有字段
            article_number=item.get('article_number'),
            chapter=item.get('chapter'),
            # 案例字段设为None
            case_id=None, criminals=None, accusations=None, relevant_articles=None,
            punish_of_money=None, death_penalty=None, life_imprisonment=None, imprisonment_months=None
        )

    def _create_case_result(self, item: Dict) -> SearchResult:
        """创建案例结果"""
        return SearchResult(
            id=item.get('id', ''),
            title=item.get('title', ''),
            content=item.get('content', ''),
            similarity=item.get('similarity', 0.0),
            type=item.get('type', 'case'),
            # 案例特有字段
            case_id=item.get('case_id'),
            criminals=item.get('criminals'),
            accusations=item.get('accusations'),
            relevant_articles=item.get('relevant_articles'),
            punish_of_money=item.get('punish_of_money'),
            death_penalty=item.get('death_penalty'),
            life_imprisonment=item.get('life_imprisonment'),
            imprisonment_months=item.get('imprisonment_months'),
            # 法条字段设为None
            article_number=None, chapter=None
        )

    def build(self) -> SearchResponse:
        """
        构建最终响应

        Returns:
            完整的SearchResponse对象
        """
        self.response_data['total'] = len(self.response_data['results'])
        return SearchResponse(**self.response_data)