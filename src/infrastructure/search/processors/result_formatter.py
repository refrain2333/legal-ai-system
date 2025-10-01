#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果格式化处理器
负责搜索结果的格式化和标准化
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResultFormatter:
    """结果格式化处理器 - 专注于结果格式化逻辑"""
    
    def __init__(self):
        """初始化格式化器"""
        self.formatters = {
            'articles': self._format_article_result,
            'cases': self._format_case_result,
            'article': self._format_article_result,  # 兼容单数形式
            'case': self._format_case_result        # 兼容单数形式
        }
    
    def format_search_results(self, raw_results: List[Dict[str, Any]], 
                            result_type: str) -> List[Dict[str, Any]]:
        """
        格式化搜索结果
        
        Args:
            raw_results: 原始搜索结果
            result_type: 结果类型 ('articles' 或 'cases')
            
        Returns:
            格式化后的结果列表
        """
        formatter = self.formatters.get(result_type)
        if not formatter:
            logger.warning(f"No formatter found for type: {result_type}")
            return raw_results
        
        formatted_results = []
        for result in raw_results:
            try:
                formatted_result = formatter(result)
                formatted_results.append(formatted_result)
            except Exception as e:
                logger.error(f"Error formatting {result_type} result: {e}")
                # 保留原始结果，避免数据丢失
                formatted_results.append(result)
        
        return formatted_results
    
    def _format_article_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化法条结果
        
        Args:
            result: 原始法条结果
            
        Returns:
            格式化后的法条结果
        """
        meta = result.get('metadata', result)
        
        # 生成标准化的法条标题
        article_number = meta.get('article_number', '未知')
        title = meta.get('title') or f"中华人民共和国刑法 第{article_number}条"
        
        # 生成法条预览内容
        content_preview = self._generate_article_preview(meta)
        
        # 计算显示分数 - 前端使用score字段显示相关度
        similarity = float(result.get('similarity', 0))
        # 如果有final_fusion_score（来自RRF融合），优先使用它
        display_score = result.get('final_fusion_score', similarity)
        
        formatted_result = {
            'id': meta.get('id', f"article_{article_number}"),
            'title': title,
            'type': 'article',  # 修正：使用单数形式
            'similarity': similarity,
            'score': display_score,  # 🔧 添加score字段，前端使用此字段显示相关度百分比
            'article_number': int(article_number) if str(article_number).isdigit() else None,
            'chapter': meta.get('chapter', ''),
            'content_preview': content_preview,
            'content': result.get('content', "")  # 确保content字段存在
        }
        
        return formatted_result
    
    def _format_case_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化案例结果
        
        Args:
            result: 原始案例结果
            
        Returns:
            格式化后的案例结果
        """
        meta = result.get('metadata', result)
        
        # 生成标准化的案例标题
        case_id = meta.get('case_id', meta.get('id', ''))
        accusations = meta.get('accusations', [])
        
        if accusations:
            accusations_str = ', '.join(accusations) if isinstance(accusations, list) else str(accusations)
            title = f"案例 {case_id} - {accusations_str}"
        else:
            title = f"案例 {case_id}"
        
        # 生成案例预览内容
        content_preview = self._generate_case_preview(meta)
        
        # 处理ID重复前缀问题
        clean_id = self._clean_case_id(meta.get('id', case_id))
        clean_case_id = self._clean_case_id(case_id)
        
        # 计算显示分数 - 前端使用score字段显示相关度
        similarity = float(result.get('similarity', 0))
        # 如果有final_fusion_score（来自RRF融合），优先使用它
        display_score = result.get('final_fusion_score', similarity)
        
        formatted_result = {
            'id': clean_id,
            'title': title,
            'type': 'case',  # 修正：使用单数形式
            'similarity': similarity,
            'score': display_score,  # 🔧 添加score字段，前端使用此字段显示相关度百分比
            'case_id': clean_case_id,
            'accusations': accusations,
            'relevant_articles': meta.get('relevant_articles', []),
            'criminals': meta.get('criminals', []),
            'punish_of_money': meta.get('punish_of_money'),
            'death_penalty': meta.get('death_penalty'),
            'life_imprisonment': meta.get('life_imprisonment'),
            'imprisonment_months': meta.get('imprisonment_months'),
            'content_preview': content_preview,
            'content': result.get('content', ""),  # 确保content字段存在
            'fact': meta.get('fact', result.get('fact', result.get('content', meta.get('content', ""))))  # 🔧 添加fact字段，优先级：meta.fact > result.fact > result.content > meta.content
        }
        
        return formatted_result
    
    def _generate_article_preview(self, meta: Dict[str, Any]) -> str:
        """
        生成法条预览内容
        
        Args:
            meta: 法条元数据
            
        Returns:
            预览内容字符串
        """
        preview_parts = []
        
        article_number = meta.get('article_number')
        if article_number:
            preview_parts.append(f"第{article_number}条")
        
        chapter = meta.get('chapter')
        if chapter:
            preview_parts.append(f"章节: {chapter}")
        
        # 如果有内容长度信息
        content_length = meta.get('content_length')
        if content_length:
            preview_parts.append(f"长度: {content_length}字")
        
        return ' | '.join(preview_parts) if preview_parts else "法律条文"
    
    def _generate_case_preview(self, meta: Dict[str, Any]) -> str:
        """
        生成案例预览内容
        
        Args:
            meta: 案例元数据
            
        Returns:
            预览内容字符串
        """
        preview_parts = []
        
        case_id = meta.get('case_id')
        if case_id:
            preview_parts.append(f"案例ID: {case_id}")
        
        accusations = meta.get('accusations', [])
        if accusations:
            accusations_str = ', '.join(accusations) if isinstance(accusations, list) else str(accusations)
            preview_parts.append(f"罪名: {accusations_str}")
        
        relevant_articles = meta.get('relevant_articles', [])
        if relevant_articles:
            articles_str = ', '.join(map(str, relevant_articles))
            preview_parts.append(f"相关法条: {articles_str}")
        
        criminals = meta.get('criminals', [])
        if criminals:
            criminals_str = ', '.join(criminals) if isinstance(criminals, list) else str(criminals)
            preview_parts.append(f"被告人: {criminals_str}")
        
        # 添加刑罚信息
        sentence_info = []
        if meta.get('imprisonment_months'):
            sentence_info.append(f"有期徒刑{meta['imprisonment_months']}个月")
        if meta.get('punish_of_money'):
            sentence_info.append(f"罚金{meta['punish_of_money']}元")
        if meta.get('death_penalty'):
            sentence_info.append("死刑")
        if meta.get('life_imprisonment'):
            sentence_info.append("无期徒刑")
        
        if sentence_info:
            preview_parts.append(f"刑罚: {', '.join(sentence_info)}")
        
        return ' | '.join(preview_parts) if preview_parts else "刑事案例"
    
    def _clean_case_id(self, case_id: str) -> str:
        """
        清理案例ID，去掉重复前缀
        
        Args:
            case_id: 原始案例ID
            
        Returns:
            清理后的ID
        """
        if not case_id:
            return ""
        
        # 处理重复前缀：case_case_000001 -> case_000001
        if case_id.startswith('case_case_'):
            return case_id.replace('case_case_', 'case_')
        
        return case_id
    
    def format_single_document(self, document: Dict[str, Any], 
                             include_content: bool = True) -> Optional[Dict[str, Any]]:
        """
        格式化单个文档
        
        Args:
            document: 文档数据
            include_content: 是否包含完整内容
            
        Returns:
            格式化后的文档，失败返回None
        """
        doc_type = document.get('type')
        if not doc_type:
            logger.warning("Document missing type field")
            return None
        
        formatter = self.formatters.get(doc_type)
        if not formatter:
            logger.warning(f"No formatter for document type: {doc_type}")
            return None
        
        try:
            formatted_doc = formatter(document)
            
            # 根据需要移除内容字段
            if not include_content and 'content' in formatted_doc:
                del formatted_doc['content']
            
            return formatted_doc
        except Exception as e:
            logger.error(f"Error formatting document: {e}")
            return None
    
    def add_result_metadata(self, results: List[Dict[str, Any]], 
                           query: str, total_found: int) -> Dict[str, Any]:
        """
        为结果集添加元数据
        
        Args:
            results: 格式化后的结果列表
            query: 原始查询
            total_found: 找到的总数
            
        Returns:
            包含元数据的完整响应
        """
        type_distribution = {}
        similarity_stats = []
        
        for result in results:
            # 统计类型分布
            result_type = result.get('type', 'unknown')
            type_distribution[result_type] = type_distribution.get(result_type, 0) + 1
            
            # 收集相似度统计
            similarity = result.get('similarity', 0)
            similarity_stats.append(similarity)
        
        response_metadata = {
            'query': query,
            'total_returned': len(results),
            'total_found': total_found,
            'type_distribution': type_distribution,
            'similarity_range': {
                'min': min(similarity_stats) if similarity_stats else 0,
                'max': max(similarity_stats) if similarity_stats else 0,
                'avg': sum(similarity_stats) / len(similarity_stats) if similarity_stats else 0
            }
        }
        
        return {
            'success': True,
            'results': results,
            'metadata': response_metadata
        }
    
    def get_supported_types(self) -> List[str]:
        """
        获取支持的结果类型
        
        Returns:
            支持的类型列表
        """
        return list(self.formatters.keys())
    
    def validate_result_format(self, result: Dict[str, Any]) -> bool:
        """
        验证结果格式是否正确
        
        Args:
            result: 待验证的结果
            
        Returns:
            是否格式正确
        """
        required_fields = ['id', 'title', 'type', 'similarity']
        
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # 验证相似度范围
        similarity = result.get('similarity', 0)
        if not (0 <= similarity <= 1):
            logger.warning(f"Invalid similarity value: {similarity}")
            return False
        
        return True