#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的语义搜索引擎
使用统一的数据加载器，支持完整内容加载
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class EnhancedSemanticSearch:
    """增强的语义搜索引擎"""
    
    def __init__(self):
        self.data_loader = None
        self.loaded = False
    
    def _get_data_loader(self):
        """获取数据加载器"""
        if self.data_loader is None:
            from ..storage.data_loader import get_data_loader
            self.data_loader = get_data_loader()
        return self.data_loader
    
    def load_data(self) -> Dict[str, Any]:
        """加载所有必需数据"""
        if self.loaded:
            return {'status': 'already_loaded'}
        
        loader = self._get_data_loader()
        
        # 加载向量数据和模型（原始数据延迟加载）
        vector_stats = loader.load_vectors()
        model_stats = loader.load_model()
        
        self.loaded = (vector_stats.get('status') in ['success', 'already_loaded'] and 
                      model_stats.get('status') in ['success', 'already_loaded'])
        
        return {
            'status': 'success' if self.loaded else 'partial',
            'vectors': vector_stats,
            'model': model_stats,
            'total_documents': loader.get_total_document_count()
        }
    
    def search(self, query: str, top_k: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            include_content: 是否包含完整内容
        """
        if not self.loaded:
            load_stats = self.load_data()
            if load_stats['status'] not in ['success', 'partial']:
                return []
        
        loader = self._get_data_loader()
        
        # 编码查询
        query_vector = loader.encode_query(query)
        if query_vector is None:
            logger.error("Failed to encode query")
            return []
        
        all_results = []
        
        # 搜索法条
        articles_results = self._search_in_data_type('articles', query_vector, top_k//2)
        all_results.extend(articles_results)
        
        # 搜索案例
        cases_results = self._search_in_data_type('cases', query_vector, top_k//2)
        all_results.extend(cases_results)
        
        # 合并排序
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        final_results = all_results[:top_k]
        
        # 按需加载完整内容
        if include_content:
            self._enrich_with_content(final_results)
        
        return final_results
    
    def _search_in_data_type(self, data_type: str, query_vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """在特定数据类型中搜索"""
        loader = self._get_data_loader()
        
        vectors = loader.get_vectors(data_type)
        metadata = loader.get_metadata(data_type)
        
        if vectors is None or metadata is None:
            return []
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, vectors)[0]
        
        # 获取top-k结果
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if idx < len(metadata):
                meta = metadata[idx]
                
                # 构建基本结果 - 根据数据类型生成合适的标题
                if data_type == 'articles':
                    title = meta.get('title', f"中华人民共和国刑法 第{meta.get('article_number', '未知')}条")
                elif data_type == 'cases':
                    # 案例使用case_summary或基于case_id和accusations生成标题
                    if meta.get('case_summary'):
                        title = meta.get('case_summary')
                    else:
                        accusations_str = ', '.join(meta.get('accusations', ['未知罪名']))
                        title = f"案例 {meta.get('case_id', '')} - {accusations_str}"
                else:
                    title = meta.get('title', '未知标题')
                
                result = {
                    'id': meta.get('id', f"{data_type}_{idx}"),
                    'title': title,
                    'type': data_type,
                    'similarity': float(similarities[idx])
                }
                
                # 添加类型特定的元数据
                if data_type == 'articles':
                    result.update({
                        'article_number': meta.get('article_number'),
                        'chapter': meta.get('chapter'),
                        'content_preview': f"第{meta.get('article_number')}条法律条文"
                    })
                elif data_type == 'cases':
                    # 生成更丰富的案例预览内容
                    accusations_str = ', '.join(meta.get('accusations', ['未知罪名']))
                    case_id = meta.get('case_id', '')
                    
                    # 从原始数据补充缺失的字段
                    enriched_meta = self._enrich_case_metadata(meta)
                    
                    # 构建详细的案例预览
                    preview_parts = [f"案例ID: {case_id}"]
                    if enriched_meta.get('accusations'):
                        preview_parts.append(f"罪名: {accusations_str}")
                    if enriched_meta.get('relevant_articles'):
                        articles_str = ', '.join(map(str, enriched_meta.get('relevant_articles', [])))
                        preview_parts.append(f"相关法条: {articles_str}")
                    if enriched_meta.get('criminals'):
                        criminals_str = ', '.join(enriched_meta.get('criminals', []))
                        preview_parts.append(f"被告人: {criminals_str}")
                    
                    content_preview = ' | '.join(preview_parts)
                    
                    result.update({
                        'case_id': enriched_meta.get('case_id'),
                        'accusations': enriched_meta.get('accusations', []),
                        'relevant_articles': enriched_meta.get('relevant_articles', []),
                        'criminals': enriched_meta.get('criminals', []),
                        'punish_of_money': enriched_meta.get('punish_of_money'),
                        'death_penalty': enriched_meta.get('death_penalty'),
                        'life_imprisonment': enriched_meta.get('life_imprisonment'), 
                        'imprisonment_months': enriched_meta.get('imprisonment_months'),
                        'content_preview': content_preview
                    })
                
                results.append(result)
        
        return results
    
    def _enrich_case_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """从原始数据补充案例元数据缺失的字段"""
        enriched_meta = meta.copy()
        case_id = meta.get('case_id')
        
        if not case_id:
            return enriched_meta
        
        try:
            # 获取数据加载器并加载原始案例数据
            loader = self._get_data_loader()
            if 'cases' not in loader.original_data:
                loader._load_original_data_type('cases')
            
            if 'cases' in loader.original_data:
                # 查找匹配的原始案例
                for case in loader.original_data['cases']:
                    actual_case_id = getattr(case, 'case_id', None)
                    if actual_case_id == case_id:
                        # 补充criminals字段
                        if not enriched_meta.get('criminals'):
                            enriched_meta['criminals'] = getattr(case, 'criminals', [])
                        
                        # 从sentence_info补充刑罚信息
                        sentence_info = getattr(case, 'sentence_info', {})
                        if sentence_info:
                            # 映射API期望的字段名
                            if not enriched_meta.get('imprisonment_months'):
                                enriched_meta['imprisonment_months'] = sentence_info.get('imprisonment_months')
                            
                            if not enriched_meta.get('punish_of_money'):
                                # 映射fine_amount到punish_of_money
                                enriched_meta['punish_of_money'] = sentence_info.get('fine_amount')
                            
                            if enriched_meta.get('death_penalty') is None:
                                enriched_meta['death_penalty'] = sentence_info.get('death_penalty')
                            
                            if enriched_meta.get('life_imprisonment') is None:
                                enriched_meta['life_imprisonment'] = sentence_info.get('life_imprisonment')
                        
                        break
        
        except Exception as e:
            logger.error(f"Error enriching case metadata for {case_id}: {e}")
        
        return enriched_meta
    
    def _enrich_with_content(self, results: List[Dict[str, Any]]):
        """为结果添加完整内容"""
        loader = self._get_data_loader()
        
        for result in results:
            if result['type'] == 'articles':
                # 处理法条ID格式问题
                article_id = result.get('id', '')
                content = loader.get_article_content(article_id)
                
                if not content or content == '内容加载失败':
                    # 尝试其他ID格式
                    if article_id.startswith('article_'):
                        # 尝试使用article_number
                        article_number = result.get('article_number')
                        if article_number:
                            # 尝试通过article_number查找
                            alt_id = f"law_{article_number}_1"
                            content = loader.get_article_content(alt_id)
                            logger.debug(f"Trying alternative article ID {alt_id}, got content: {bool(content)}")
                
                if content and content != '内容加载失败':
                    result['content'] = content  # 完整内容
                    # 生成合适长度的预览，保持完整性
                    preview_length = 300  # 增加预览长度
                    result['content_preview'] = content[:preview_length] + "..." if len(content) > preview_length else content
                else:
                    logger.warning(f"Failed to load content for article: {article_id}")
                    result['content'] = "内容加载失败"
                    result['content_preview'] = "内容加载失败"
                    
            elif result['type'] == 'cases':
                # 使用case_id获取案例内容，如果没有则使用id
                case_id = result.get('case_id') or result.get('id', '')
                logger.debug(f"Loading content for case_id: {case_id}")
                
                # 尝试多种ID格式
                content = None
                id_variants = [case_id]
                
                # 生成ID变体
                if case_id.startswith('case_case_'):
                    id_variants.append(case_id.replace('case_case_', 'case_'))
                elif case_id.startswith('case_'):
                    # 提取数字部分并尝试不同格式
                    try:
                        num_part = case_id.split('_')[-1]
                        id_variants.append(f"case_{num_part.lstrip('0')}")  # 去掉前导0
                        id_variants.append(f"case_{num_part.zfill(6)}")  # 补齐6位
                    except:
                        pass
                
                # 尝试所有变体
                for try_id in id_variants:
                    content = loader.get_case_content(try_id)
                    if content and content != '内容加载失败':
                        logger.debug(f"Successfully loaded content with ID {try_id}: {len(content)} characters")
                        break
                
                if content and content != '内容加载失败':
                    result['content'] = content  # 完整内容
                    preview_length = 300  # 增加预览长度
                    result['content_preview'] = content[:preview_length] + "..." if len(content) > preview_length else content
                else:
                    logger.warning(f"All attempts failed for case {case_id}")
                    result['content'] = "内容加载失败"
                    result['content_preview'] = "内容加载失败"
    
    def search_articles_only(self, query: str, top_k: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
        """只搜索法条"""
        if not self.loaded:
            self.load_data()
        
        loader = self._get_data_loader()
        query_vector = loader.encode_query(query)
        if query_vector is None:
            return []
        
        results = self._search_in_data_type('articles', query_vector, top_k)
        
        if include_content:
            self._enrich_with_content(results)
        
        return results
    
    def search_cases_only(self, query: str, top_k: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
        """只搜索案例"""
        if not self.loaded:
            self.load_data()
        
        loader = self._get_data_loader()
        query_vector = loader.encode_query(query)
        if query_vector is None:
            return []
        
        results = self._search_in_data_type('cases', query_vector, top_k)
        
        if include_content:
            self._enrich_with_content(results)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.loaded:
            self.load_data()
        
        loader = self._get_data_loader()
        loader_stats = loader.get_stats()
        
        return {
            'ready': self.loaded and loader_stats.get('total_documents', 0) > 0,
            'total_documents': loader_stats.get('total_documents', 0),
            'articles_count': loader.get_metadata('articles') and len(loader.get_metadata('articles')) or 0,
            'cases_count': loader.get_metadata('cases') and len(loader.get_metadata('cases')) or 0,
            'model_loaded': loader_stats.get('model_loaded', False),
            'vectors_loaded': loader_stats.get('vectors_loaded', False),
            'memory_usage_mb': loader_stats.get('memory_usage_mb', 0),
            'cached_contents': loader_stats.get('cached_contents', 0)
        }
    
    def get_document_by_id(self, doc_id: str, include_content: bool = True) -> Optional[Dict[str, Any]]:
        """根据ID获取特定文档"""
        if not self.loaded:
            self.load_data()
        
        loader = self._get_data_loader()
        
        # 搜索法条
        articles_metadata = loader.get_metadata('articles')
        if articles_metadata:
            for i, meta in enumerate(articles_metadata):
                if meta.get('id') == doc_id:
                    result = {
                        'id': meta.get('id'),
                        'title': meta.get('title'),
                        'type': 'articles',
                        'article_number': meta.get('article_number'),
                        'chapter': meta.get('chapter')
                    }
                    
                    if include_content:
                        content = loader.get_article_content(doc_id)
                        if content:
                            result['content'] = content
                    
                    return result
        
        # 搜索案例
        cases_metadata = loader.get_metadata('cases')
        if cases_metadata:
            for i, meta in enumerate(cases_metadata):
                if meta.get('id') == doc_id or meta.get('case_id') == doc_id:
                    # 从原始数据补充缺失的字段
                    enriched_meta = self._enrich_case_metadata(meta)
                    
                    result = {
                        'id': enriched_meta.get('id'),
                        'case_id': enriched_meta.get('case_id'),
                        'title': f"案例 {enriched_meta.get('case_id')}",
                        'type': 'cases',
                        'accusations': enriched_meta.get('accusations', []),
                        'relevant_articles': enriched_meta.get('relevant_articles', []),
                        'criminals': enriched_meta.get('criminals', []),
                        'punish_of_money': enriched_meta.get('punish_of_money'),
                        'death_penalty': enriched_meta.get('death_penalty'),
                        'life_imprisonment': enriched_meta.get('life_imprisonment'),
                        'imprisonment_months': enriched_meta.get('imprisonment_months')
                    }
                    
                    if include_content:
                        content = loader.get_case_content(meta.get('case_id', ''))
                        if content:
                            result['content'] = content
                    
                    return result
        
        return None


# 全局实例
_enhanced_search_engine = None

def get_enhanced_search_engine() -> EnhancedSemanticSearch:
    """获取增强搜索引擎实例"""
    global _enhanced_search_engine
    if _enhanced_search_engine is None:
        _enhanced_search_engine = EnhancedSemanticSearch()
    return _enhanced_search_engine