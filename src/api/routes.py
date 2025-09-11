#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的API路由 - 只提供基本搜索功能
"""

from fastapi import APIRouter, HTTPException
from .models import SearchRequest, SearchResponse, StatusResponse, SearchResult
from ..engines.enhanced_search_engine import get_enhanced_search_engine as get_search_engine

# 创建路由器
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """搜索接口"""
    try:
        engine = get_search_engine()
        raw_results = engine.search(request.query, request.top_k, include_content=True)
        
        # 获取数据加载器以便在API层直接加载内容
        from ..core.data_loader import get_data_loader
        loader = get_data_loader()
        
        # 转换为响应格式并强制加载完整内容
        results = []
        for item in raw_results:
            # 先尝试获取完整内容
            full_content = ''
            
            if item.get('type') == 'cases':
                # 尝试多种ID格式来获取案例内容
                case_id = item.get('case_id') or item.get('id', '')
                full_content = loader.get_case_content(case_id)
                
                # 如果失败，尝试去掉重复前缀
                if not full_content and case_id.startswith('case_case_'):
                    alt_case_id = case_id.replace('case_case_', 'case_')
                    full_content = loader.get_case_content(alt_case_id)
                
                # 获取案例的详细元数据
                case_details = {}
                
                # 尝试从原始数据获取完整的详细信息
                loader._load_original_data_type('cases')
                if 'cases' in loader.original_data:
                    for case in loader.original_data['cases']:
                        case_actual_id = getattr(case, 'case_id', None)
                        if loader._ids_match(case_actual_id, case_id):
                            # 直接从case对象获取信息（不在meta子对象中）
                            if hasattr(case, 'criminals'):
                                case_details['criminals'] = case.criminals
                            if hasattr(case, 'accusations'):
                                case_details['accusations'] = case.accusations
                            if hasattr(case, 'relevant_articles'):
                                case_details['relevant_articles'] = case.relevant_articles
                            
                            # 从sentence_info字典获取刑期信息
                            if hasattr(case, 'sentence_info') and case.sentence_info:
                                sentence_info = case.sentence_info
                                case_details['punish_of_money'] = sentence_info.get('fine_amount')
                                case_details['imprisonment_months'] = sentence_info.get('imprisonment_months')
                                case_details['death_penalty'] = sentence_info.get('death_penalty')
                                case_details['life_imprisonment'] = sentence_info.get('life_imprisonment')
                            
                            break
                    
            elif item.get('type') == 'articles':
                article_id = item.get('id', '')
                full_content = loader.get_article_content(article_id)
                
                # 如果法条内容加载失败，尝试其他方法
                if not full_content:
                    # 尝试直接从原始数据加载，使用不同的字段
                    if article_id:
                        # 尝试加载原始法条数据
                        loader._load_original_data_type('articles')
                        if 'articles' in loader.original_data:
                            for article in loader.original_data['articles']:
                                # 尝试不同的ID匹配和字段
                                article_actual_id = getattr(article, 'id', None) or getattr(article, 'article_id', None)
                                if (article_actual_id == article_id or 
                                    str(getattr(article, 'article_number', '')) == article_id.replace('article_', '')):
                                    # 尝试不同的内容字段
                                    for field in ['content', 'text', 'article_content', 'law_content']:
                                        if hasattr(article, field):
                                            content = getattr(article, field)
                                            if content:
                                                full_content = content
                                                break
                                    if full_content:
                                        break
            
            # 确保内容字段有有意义的值
            content = full_content or item.get('content', '') or item.get('content_preview', '') or '内容加载中...'
            
            # 构建结果对象
            result_data = {
                'id': item.get('id', ''),
                'title': item.get('title', ''),
                'content': content,
                'similarity': item.get('similarity', 0.0),
                'type': item.get('type', '')
            }
            
            # 添加类型特定的字段
            if item.get('type') == 'cases':
                result_data.update({
                    'case_id': item.get('case_id'),
                    'criminals': case_details.get('criminals'),
                    'accusations': case_details.get('accusations'),
                    'relevant_articles': case_details.get('relevant_articles'),
                    'punish_of_money': case_details.get('punish_of_money'),
                    'death_penalty': case_details.get('death_penalty'),
                    'life_imprisonment': case_details.get('life_imprisonment'),
                    'imprisonment_months': case_details.get('imprisonment_months')
                })
            elif item.get('type') == 'articles':
                result_data.update({
                    'article_number': item.get('article_number'),
                    'chapter': item.get('chapter')
                })
            
            result = SearchResult(**result_data)
            results.append(result)
        
        return SearchResponse(
            success=True,
            results=results,
            total=len(results),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """获取系统状态"""
    try:
        engine = get_search_engine()
        stats = engine.get_stats()
        
        return StatusResponse(
            status="ok",
            ready=stats.get('ready', False),
            total_documents=stats.get('total_documents', 0)
        )
        
    except Exception as e:
        return StatusResponse(
            status="error",
            ready=False,
            total_documents=0
        )