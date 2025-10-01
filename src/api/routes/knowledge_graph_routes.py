#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱路由模块
包含知识图谱相关的API接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..models import SearchRequest, SearchResponse
from src.services.search_service import SearchService
from src.infrastructure.repositories import get_legal_document_repository
from src.infrastructure.startup import get_startup_manager

logger = logging.getLogger(__name__)

# 创建知识图谱路由器
router = APIRouter()


def get_search_service() -> SearchService:
    """依赖注入：为每个请求创建新的搜索服务实例"""
    from src.infrastructure.llm.llm_client import LLMClient
    from src.config.settings import settings

    repository = get_legal_document_repository()
    llm_client = LLMClient(settings)
    return SearchService(repository, llm_client, debug_mode=False)


def _check_system_ready():
    """检查系统是否准备就绪"""
    startup_manager = get_startup_manager()
    if not startup_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="系统正在加载中，请稍后再试"
        )


@router.post("/search/kg_enhanced", response_model=SearchResponse)
async def search_kg_enhanced(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """知识图谱增强搜索 - 最高级的搜索功能"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

        # 调用知识图谱增强搜索
        result = await search_service.search_documents_kg_enhanced(
            query_text=request.query,
            articles_count=request.articles_count,
            cases_count=request.cases_count
        )

        if not result.get('success', False):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', '知识图谱增强搜索失败')
            )

        return SearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识图谱增强搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"知识图谱增强搜索失败: {str(e)}")


@router.post("/search/explain")
async def explain_search_reasoning(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """解释搜索推理过程"""
    try:
        # 检查系统是否准备就绪
        _check_system_ready()

        explanation = await search_service.explain_search_reasoning(request.query)

        return {
            "success": True,
            "query": request.query,
            "explanation": explanation
        }

    except Exception as e:
        logger.error(f"搜索推理解释失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索推理解释失败: {str(e)}")


@router.get("/stats")
async def get_knowledge_graph_stats(search_service: SearchService = Depends(get_search_service)):
    """获取知识图谱统计信息"""
    try:
        _check_system_ready()

        kg_status = search_service.get_kg_enhanced_status()

        return {
            "success": True,
            "knowledge_graph_status": kg_status
        }

    except Exception as e:
        logger.error(f"获取知识图谱状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取知识图谱状态失败: {str(e)}")


@router.get("/relations/{entity}")
async def get_entity_relations(
    entity: str,
    entity_type: str = "auto",
    search_service: SearchService = Depends(get_search_service)
):
    """获取实体的关系信息（用于可视化）"""
    try:
        _check_system_ready()

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                visualization_data = knowledge_graph.visualize_relations(entity, entity_type)
                return {
                    "success": True,
                    "entity": entity,
                    "entity_type": entity_type,
                    "visualization_data": visualization_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")


@router.get("/expand/{query}")
async def expand_query_with_kg(
    query: str,
    search_service: SearchService = Depends(get_search_service)
):
    """使用知识图谱扩展查询"""
    try:
        _check_system_ready()

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                expansion_result = knowledge_graph.expand_query_with_relations(query)
                expanded_query = knowledge_graph.generate_expanded_query(query)

                return {
                    "success": True,
                    "original_query": query,
                    "expanded_query": expanded_query,
                    "expansion_details": expansion_result
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询扩展失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询扩展失败: {str(e)}")


@router.get("/crimes")
async def get_all_crimes(
    search_service: SearchService = Depends(get_search_service)
):
    """获取所有罪名列表"""
    try:
        _check_system_ready()

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                crimes_data = []

                # 获取所有罪名及其统计信息
                for crime, articles in knowledge_graph.crime_article_map.items():
                    total_cases = sum(articles.values())
                    related_articles = list(articles.keys())

                    crimes_data.append({
                        "crime": crime,  # 修改字段名以匹配前端期望
                        "case_count": total_cases,
                        "related_articles": related_articles
                    })

                # 按案例数量排序
                crimes_data.sort(key=lambda x: x['case_count'], reverse=True)

                return {
                    "success": True,
                    "total_count": len(crimes_data),
                    "crimes": crimes_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取罪名列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取罪名列表失败: {str(e)}")


@router.get("/articles")
async def get_all_articles(
    search_service: SearchService = Depends(get_search_service)
):
    """获取所有法条列表"""
    try:
        _check_system_ready()

        # 获取知识图谱实例
        if hasattr(search_service.repository, 'data_loader'):
            knowledge_graph = search_service.repository.data_loader.get_knowledge_graph()
            if knowledge_graph:
                articles_data = []

                # 获取所有法条及其统计信息
                for article, crimes in knowledge_graph.article_crime_map.items():
                    total_cases = sum(crimes.values())
                    related_crimes = list(crimes.keys())

                    # 需要获取法条标题，先简单使用法条号
                    articles_data.append({
                        "article_number": article,
                        "title": f"第{article}条",  # 简化标题，实际应该从数据中获取
                        "case_count": total_cases,
                        "chapter": "刑法",  # 简化章节信息
                        "related_crimes": related_crimes
                    })

                # 按法条编号排序
                def sort_key(x):
                    try:
                        return int(x['article_number'])
                    except ValueError:
                        return 9999  # 非数字法条排在后面

                articles_data.sort(key=sort_key)

                return {
                    "success": True,
                    "total_count": len(articles_data),
                    "articles": articles_data
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取法条列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取法条列表失败: {str(e)}")


@router.get("/relation_cases/{crime}/{article}")
async def get_relation_cases(
    crime: str,
    article: str,
    limit: int = 5,
    search_service: SearchService = Depends(get_search_service)
):
    """获取特定罪名-法条关系的具体案例（前N个）"""
    try:
        _check_system_ready()

        # 获取知识图谱实例和数据加载器
        if hasattr(search_service.repository, 'data_loader'):
            data_loader = search_service.repository.data_loader
            knowledge_graph = data_loader.get_knowledge_graph()

            if knowledge_graph:
                # 首先从知识图谱获取关系详情
                relation_details = knowledge_graph.get_relation_details(crime, article)

                if not relation_details['exists']:
                    return {
                        "success": False,
                        "error": f"知识图谱中没有找到'{crime}罪'与'第{article}条'的关系",
                        "crime": crime,
                        "article": article,
                        "debug_info": {
                            "relation_exists": False,
                            "knowledge_graph_case_count": 0
                        }
                    }

                expected_case_count = relation_details['case_count']

                # 查找符合条件的案例
                matching_cases = []

                # 从数据加载器获取案例数据
                if not hasattr(data_loader, 'original_data') or 'cases' not in data_loader.original_data:
                    logger.info("触发案例数据加载...")
                    data_loader.load_original_data()
                    if not hasattr(data_loader, 'original_data'):
                        data_loader.original_data = {}
                    if 'cases' not in data_loader.original_data:
                        logger.info("强制加载案例数据到内存...")
                        try:
                            data_loader._load_original_data_type('cases')
                        except Exception as e:
                            logger.error(f"加载案例数据失败: {e}")
                            data_loader.original_data['cases'] = []

                cases_data = data_loader.original_data.get('cases', [])
                if cases_data:
                    for case in cases_data:
                        try:
                            # 获取案例的罪名和相关法条
                            case_accusations = getattr(case, 'accusations', [])
                            case_articles = getattr(case, 'relevant_articles', [])

                            # 优化的罪名匹配逻辑
                            crime_match = False
                            if case_accusations:
                                crime_normalized = crime.replace('罪', '').strip()
                                for acc in case_accusations:
                                    if not acc or not isinstance(acc, str):
                                        continue
                                    acc_normalized = acc.replace('罪', '').strip()
                                    if (crime == acc or
                                        crime_normalized == acc_normalized or
                                        crime in acc or acc in crime or
                                        crime_normalized in acc_normalized or acc_normalized in crime_normalized):
                                        crime_match = True
                                        break

                            # 增强的法条匹配逻辑
                            article_match = False
                            if case_articles:
                                target_article_str = str(article)
                                for art in case_articles:
                                    if art is None:
                                        continue
                                    art_str = str(art).strip()
                                    if (art_str == target_article_str or
                                        f"第{art_str}条" == f"第{target_article_str}条" or
                                        (art_str.isdigit() and target_article_str.isdigit() and
                                         int(art_str) == int(target_article_str))):
                                        article_match = True
                                        break

                            # 如果既匹配罪名又匹配法条，添加到结果中
                            if crime_match and article_match:
                                case_info = {
                                    "case_id": getattr(case, 'case_id', ''),
                                    "fact": getattr(case, 'fact', '')[:200] + '...' if len(getattr(case, 'fact', '')) > 200 else getattr(case, 'fact', ''),
                                    "accusations": case_accusations,
                                    "relevant_articles": case_articles,
                                    "criminals": getattr(case, 'criminals', []),
                                    "sentence_info": getattr(case, 'sentence_info', {
                                        "imprisonment_months": getattr(case, 'imprisonment_months', None),
                                        "fine_amount": getattr(case, 'fine_amount', getattr(case, 'punish_of_money', None)),
                                        "death_penalty": getattr(case, 'death_penalty', False),
                                        "life_imprisonment": getattr(case, 'life_imprisonment', False)
                                    })
                                }
                                matching_cases.append(case_info)

                                # 限制返回数量
                                if len(matching_cases) >= limit:
                                    break

                        except Exception as case_error:
                            # 单个案例解析错误不影响整体
                            continue

                return {
                    "success": True,
                    "crime": crime,
                    "article": article,
                    "total_found": len(matching_cases),
                    "limit": limit,
                    "cases": matching_cases,
                    "debug_info": {
                        "knowledge_graph_case_count": expected_case_count,
                        "actual_cases_found": len(matching_cases),
                        "total_cases_checked": len(cases_data),
                        "relation_confidence": relation_details['confidence'],
                        "search_params": f"Crime: '{crime}', Article: '{article}'",
                        "data_consistency": len(matching_cases) == expected_case_count
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="知识图谱不可用")
        else:
            raise HTTPException(status_code=503, detail="数据加载器不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关系案例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取关系案例失败: {str(e)}")