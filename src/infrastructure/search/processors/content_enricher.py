#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容增强处理器
负责为搜索结果加载完整内容
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ContentEnricher:
    """内容增强处理器 - 专注于内容加载和增强逻辑"""
    
    def __init__(self, data_loader):
        """
        初始化内容增强器
        
        Args:
            data_loader: 数据加载器实例
        """
        self.data_loader = data_loader
        self.content_loaders = {
            'articles': self._load_article_content,
            'cases': self._load_case_content,
            'article': self._load_article_content,  # 兼容单数形式
            'case': self._load_case_content        # 兼容单数形式
        }
    
    def enrich_results_with_content(self, results: List[Dict[str, Any]], 
                                   include_content: bool = True,
                                   preview_length: int = 300,
                                   min_content_length: int = 20) -> List[Dict[str, Any]]:
        """
        为结果列表添加完整内容，并过滤内容过短的文档
        
        Args:
            results: 搜索结果列表
            include_content: 是否包含完整内容
            preview_length: 预览内容长度
            min_content_length: 最小内容长度，小于此长度的文档将被过滤
            
        Returns:
            增强并过滤后的结果列表
        """
        if not include_content:
            return results
        
        enriched_results = []
        filtered_count = 0
        
        for result in results:
            try:
                enriched_result = self.enrich_single_result(result, preview_length)
                
                # 检查内容长度，过滤掉内容过短的文档
                content = enriched_result.get('content', '')
                if content and len(content.strip()) >= min_content_length:
                    enriched_results.append(enriched_result)
                else:
                    filtered_count += 1
                    logger.debug(f"Filtered out document {result.get('id', 'unknown')} due to short content: {len(content.strip())} characters")
                    
            except Exception as e:
                logger.error(f"Error enriching result {result.get('id', 'unknown')}: {e}")
                # 保留原始结果，但仍然检查长度
                content = result.get('content', '')
                if content and len(content.strip()) >= min_content_length:
                    enriched_results.append(result)
                else:
                    filtered_count += 1
        
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} documents due to short content (< {min_content_length} characters)")
        
        return enriched_results
    
    def enrich_single_result(self, result: Dict[str, Any], 
                           preview_length: int = 300) -> Dict[str, Any]:
        """
        为单个结果添加完整内容
        
        Args:
            result: 搜索结果
            preview_length: 预览长度
            
        Returns:
            增强后的结果
        """
        result_type = result.get('type')
        if not result_type:
            logger.warning("Result missing type field")
            return result
        
        content_loader = self.content_loaders.get(result_type)
        if not content_loader:
            logger.warning(f"No content loader for type: {result_type}")
            return result
        
        # 如果已有内容，跳过加载
        if 'content' in result and result['content']:
            return self._update_preview(result, preview_length)
        
        # 加载完整内容
        content = content_loader(result)
        
        # 更新结果
        enriched_result = result.copy()
        if content and content != '内容加载失败':
            enriched_result['content'] = content
            enriched_result['content_preview'] = self._generate_preview(content, preview_length)
        else:
            # 确保content字段始终存在，符合API要求
            enriched_result['content'] = "暂无内容"
            enriched_result['content_preview'] = "暂无内容"
        
        return enriched_result
    
    def _load_article_content(self, result: Dict[str, Any]) -> Optional[str]:
        """
        加载法条完整内容
        
        Args:
            result: 法条结果
            
        Returns:
            完整内容或None
        """
        article_id = result.get('id', '')
        
        # 尝试直接通过ID加载
        content = self.data_loader.get_article_content(article_id)
        
        if not content or content == '内容加载失败':
            # 尝试通过article_number加载
            article_number = result.get('article_number')
            if article_number:
                alternative_ids = [
                    f"law_{article_number}_1",
                    f"article_{article_number}",
                    f"criminal_article_{article_number}"
                ]
                
                for alt_id in alternative_ids:
                    content = self.data_loader.get_article_content(alt_id)
                    if content and content != '内容加载失败':
                        logger.debug(f"Successfully loaded article content with ID: {alt_id}")
                        break
        
        return content
    
    def _load_case_content(self, result: Dict[str, Any]) -> Optional[str]:
        """
        加载案例完整内容
        
        Args:
            result: 案例结果
            
        Returns:
            完整内容或None
        """
        case_id = result.get('case_id') or result.get('id', '')
        
        # 生成可能的ID变体
        id_variants = self._generate_case_id_variants(case_id)
        
        # 尝试所有ID变体
        for try_id in id_variants:
            content = self.data_loader.get_case_content(try_id)
            if content and content != '内容加载失败':
                logger.debug(f"Successfully loaded case content with ID: {try_id}")
                return content
        
        logger.warning(f"Failed to load content for case: {case_id}")
        return None
    
    def _generate_case_id_variants(self, case_id: str) -> List[str]:
        """
        生成案例ID的可能变体
        
        Args:
            case_id: 原始案例ID
            
        Returns:
            ID变体列表
        """
        variants = [case_id]
        
        if not case_id:
            return variants
        
        # 处理重复前缀问题
        if case_id.startswith('case_case_'):
            variants.append(case_id.replace('case_case_', 'case_'))
        elif case_id.startswith('case_'):
            # 提取数字部分并尝试不同格式
            try:
                num_part = case_id.split('_')[-1]
                # 去掉前导0
                variants.append(f"case_{num_part.lstrip('0')}")
                # 补齐6位
                variants.append(f"case_{num_part.zfill(6)}")
                # 只有数字
                variants.append(num_part)
                variants.append(num_part.lstrip('0'))
            except (IndexError, ValueError):
                pass
        else:
            # 如果不是标准格式，尝试添加前缀
            variants.append(f"case_{case_id}")
            if case_id.isdigit():
                variants.append(f"case_{case_id.zfill(6)}")
        
        return variants
    
    def _generate_preview(self, content: str, preview_length: int) -> str:
        """
        生成内容预览
        
        Args:
            content: 完整内容
            preview_length: 预览长度
            
        Returns:
            预览内容
        """
        if not content:
            return ""
        
        if len(content) <= preview_length:
            return content
        
        # 截取预览，尝试在句号处断开
        preview = content[:preview_length]
        
        # 查找最后一个句号
        last_period = preview.rfind('。')
        if last_period > preview_length * 0.7:  # 如果句号位置在合理范围内
            preview = preview[:last_period + 1]
        else:
            preview = preview + "..."
        
        return preview
    
    def _update_preview(self, result: Dict[str, Any], preview_length: int) -> Dict[str, Any]:
        """
        更新已有内容的预览
        
        Args:
            result: 结果对象
            preview_length: 预览长度
            
        Returns:
            更新后的结果
        """
        content = result.get('content', '')
        if content:
            result['content_preview'] = self._generate_preview(content, preview_length)
        
        return result
    
    def batch_enrich_content(self, results: List[Dict[str, Any]], 
                           batch_size: int = 10,
                           preview_length: int = 300) -> List[Dict[str, Any]]:
        """
        批量增强内容（优化性能）
        
        Args:
            results: 结果列表
            batch_size: 批处理大小
            preview_length: 预览长度
            
        Returns:
            增强后的结果列表
        """
        enriched_results = []
        
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            
            # 批量处理
            for result in batch:
                try:
                    enriched_result = self.enrich_single_result(result, preview_length)
                    enriched_results.append(enriched_result)
                except Exception as e:
                    logger.error(f"Batch enrichment error for {result.get('id')}: {e}")
                    enriched_results.append(result)
        
        return enriched_results
    
    def preload_content_cache(self, document_ids: List[str], 
                            document_types: List[str]) -> Dict[str, Any]:
        """
        预加载内容到缓存
        
        Args:
            document_ids: 文档ID列表
            document_types: 对应的文档类型列表
            
        Returns:
            预加载统计信息
        """
        if len(document_ids) != len(document_types):
            raise ValueError("document_ids and document_types must have same length")
        
        preload_stats = {
            'total_requested': len(document_ids),
            'successful_loads': 0,
            'failed_loads': 0,
            'articles_loaded': 0,
            'cases_loaded': 0
        }
        
        for doc_id, doc_type in zip(document_ids, document_types):
            try:
                if doc_type == 'articles':
                    content = self.data_loader.get_article_content(doc_id)
                    if content and content != '内容加载失败':
                        preload_stats['successful_loads'] += 1
                        preload_stats['articles_loaded'] += 1
                    else:
                        preload_stats['failed_loads'] += 1
                        
                elif doc_type == 'cases':
                    content = self.data_loader.get_case_content(doc_id)
                    if content and content != '内容加载失败':
                        preload_stats['successful_loads'] += 1
                        preload_stats['cases_loaded'] += 1
                    else:
                        preload_stats['failed_loads'] += 1
                        
            except Exception as e:
                logger.error(f"Preload error for {doc_id}: {e}")
                preload_stats['failed_loads'] += 1
        
        return preload_stats
    
    def get_content_stats(self) -> Dict[str, Any]:
        """
        获取内容增强统计信息
        
        Returns:
            统计信息
        """
        if not self.data_loader:
            return {'error': 'Data loader not available'}
        
        data_loader_stats = self.data_loader.get_stats()
        
        return {
            'data_loader_ready': bool(self.data_loader),
            'cached_contents': data_loader_stats.get('cached_contents', 0),
            'cache_limit': self.data_loader.cache_size_limit if self.data_loader else 0,
            'supported_types': list(self.content_loaders.keys()),
            'original_data_available': data_loader_stats.get('original_data_checked', False)
        }