#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能检索服务
提供统一的法律文档检索接口，整合向量检索和传统检索
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.models.simple_index import SimpleVectorIndex
from src.models.simple_embedding import SimpleTextEmbedding

logger = setup_logger(__name__)

class RetrievalService:
    """智能检索服务类"""
    
    def __init__(self, index_path: str = None):
        """
        初始化检索服务
        
        Args:
            index_path: 索引存储路径，如果为None则从配置获取
        """
        self.index_path = index_path or os.path.join(settings.INDEX_STORAGE_PATH, "main_index")
        self.vector_index = SimpleVectorIndex()
        self.is_ready = False
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"检索服务初始化，索引路径: {self.index_path}")

    async def initialize(self) -> bool:
        """
        异步初始化检索服务
        
        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始初始化检索服务...")
            
            # 检查索引是否存在
            if os.path.exists(os.path.join(self.index_path, "metadata.json")):
                # 加载现有索引
                logger.info("发现现有索引，开始加载...")
                success = await self._load_index_async()
                if success:
                    self.is_ready = True
                    logger.info("检索服务初始化成功（从现有索引）")
                    return True
                else:
                    logger.warning("加载现有索引失败，将重新构建")
            
            # 构建新索引
            logger.info("开始构建新索引...")
            success = await self._build_index_async()
            if success:
                # 保存索引
                await self._save_index_async()
                self.is_ready = True
                logger.info("检索服务初始化成功（新建索引）")
                return True
            else:
                logger.error("索引构建失败")
                return False
                
        except Exception as e:
            logger.error(f"检索服务初始化失败: {e}")
            return False

    async def _build_index_async(self) -> bool:
        """异步构建索引"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.vector_index.build_from_data
        )

    async def _load_index_async(self) -> bool:
        """异步加载索引"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.vector_index.load_index,
            self.index_path
        )

    async def _save_index_async(self) -> None:
        """异步保存索引"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.vector_index.save_index,
            self.index_path
        )

    async def search(self, 
                    query: str,
                    top_k: int = 10,
                    min_similarity: float = 0.0,
                    doc_types: Optional[List[str]] = None,
                    include_metadata: bool = True) -> Dict[str, Any]:
        """
        执行智能检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            doc_types: 文档类型过滤 ["law", "case"]
            include_metadata: 是否包含元数据
            
        Returns:
            检索结果字典
        """
        if not self.is_ready:
            raise RuntimeError("检索服务未就绪，请先调用initialize()")
        
        if not query or not query.strip():
            return {
                "query": query,
                "results": [],
                "total": 0,
                "search_time": 0.0,
                "message": "查询不能为空"
            }
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"开始检索查询: '{query[:50]}...' (Top-{top_k})")
            
            # 执行向量检索
            raw_results = await self._vector_search_async(
                query, top_k, min_similarity
            )
            
            # 应用过滤器
            if doc_types:
                raw_results = [r for r in raw_results if r.get('type') in doc_types]
            
            # 格式化结果
            formatted_results = self._format_results(raw_results, include_metadata)
            
            search_time = time.time() - start_time
            
            result = {
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_time": round(search_time, 3),
                "message": "检索成功"
            }
            
            logger.info(f"检索完成，返回 {len(formatted_results)} 个结果，耗时 {search_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "search_time": 0.0,
                "message": f"检索失败: {str(e)}"
            }

    async def _vector_search_async(self, 
                                  query: str, 
                                  top_k: int, 
                                  min_similarity: float) -> List[Dict]:
        """异步向量检索"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.vector_index.search,
            query,
            top_k,
            min_similarity
        )

    def _format_results(self, 
                       raw_results: List[Dict], 
                       include_metadata: bool) -> List[Dict]:
        """格式化检索结果"""
        formatted = []
        
        for result in raw_results:
            formatted_result = {
                "id": result.get("id"),
                "type": result.get("type"),
                "title": result.get("title"),
                "content": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", ""),
                "score": round(result.get("score", 0.0), 4),
                "rank": result.get("rank", 0)
            }
            
            if include_metadata:
                formatted_result["metadata"] = {
                    k: v for k, v in result.items() 
                    if k not in ["id", "type", "title", "content", "score", "rank"]
                }
            
            formatted.append(formatted_result)
        
        return formatted

    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档详情
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档详情或None
        """
        if not self.is_ready:
            raise RuntimeError("检索服务未就绪，请先调用initialize()")
        
        try:
            loop = asyncio.get_event_loop()
            document = await loop.run_in_executor(
                self._executor,
                self.vector_index.get_document_by_id,
                doc_id
            )
            
            if document:
                return self._format_results([document], include_metadata=True)[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取文档失败 {doc_id}: {e}")
            return None

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取检索服务统计信息
        
        Returns:
            统计信息字典
        """
        if not self.is_ready:
            return {"status": "not_ready", "message": "服务未就绪"}
        
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                self._executor,
                self.vector_index.get_statistics
            )
            
            stats.update({
                "status": "ready",
                "index_path": self.index_path,
                "service_ready": self.is_ready
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"status": "error", "message": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            health_info = {
                "service": "retrieval_service",
                "status": "healthy" if self.is_ready else "not_ready",
                "timestamp": __import__('time').time(),
                "index_ready": self.is_ready
            }
            
            if self.is_ready:
                # 执行一个简单的测试查询
                test_result = await self.search("测试", top_k=1)
                health_info["test_search"] = "passed" if test_result["total"] >= 0 else "failed"
            
            return health_info
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "service": "retrieval_service",
                "status": "unhealthy",
                "timestamp": __import__('time').time(),
                "error": str(e)
            }

    async def rebuild_index(self) -> bool:
        """
        重新构建索引
        
        Returns:
            重建是否成功
        """
        try:
            logger.info("开始重新构建索引...")
            self.is_ready = False
            
            # 构建新索引
            success = await self._build_index_async()
            if success:
                # 保存索引
                await self._save_index_async()
                self.is_ready = True
                logger.info("索引重建成功")
                return True
            else:
                logger.error("索引重建失败")
                return False
                
        except Exception as e:
            logger.error(f"重建索引失败: {e}")
            return False

    def __del__(self):
        """清理资源"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


# 全局检索服务实例
_retrieval_service = None

async def get_retrieval_service() -> RetrievalService:
    """获取全局检索服务实例（单例模式）"""
    global _retrieval_service
    
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
        success = await _retrieval_service.initialize()
        if not success:
            logger.error("检索服务初始化失败")
            raise RuntimeError("检索服务初始化失败")
    
    return _retrieval_service


# 测试函数
async def test_retrieval_service():
    """测试检索服务的基本功能"""
    try:
        logger.info("开始测试检索服务...")
        
        # 创建检索服务
        service = RetrievalService()
        
        # 初始化服务
        success = await service.initialize()
        if not success:
            logger.error("检索服务初始化失败")
            return False
        
        # 测试健康检查
        health = await service.health_check()
        logger.info(f"健康检查结果: {health}")
        
        # 测试获取统计信息
        stats = await service.get_statistics()
        logger.info(f"统计信息: {stats}")
        
        # 测试检索
        test_queries = [
            "合同违约责任",
            "故意伤害",
            "公司法人财产权"
        ]
        
        for query in test_queries:
            logger.info(f"\n测试检索: '{query}'")
            result = await service.search(query, top_k=3)
            
            logger.info(f"查询: {result['query']}")
            logger.info(f"结果数量: {result['total']}")
            logger.info(f"检索时间: {result['search_time']}s")
            
            for i, doc in enumerate(result['results'][:2]):
                logger.info(f"  {i+1}. [{doc['type']}] {doc['title'][:30]}... (分数: {doc['score']})")
        
        # 测试根据ID获取文档
        if stats.get('total_documents', 0) > 0:
            # 假设第一个文档ID
            test_doc = await service.get_document_by_id("law_000000")
            if test_doc:
                logger.info(f"根据ID获取文档成功: {test_doc['title'][:30]}...")
        
        logger.info("检索服务测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"检索服务测试失败: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    async def main():
        success = await test_retrieval_service()
        if success:
            print("\n检索服务测试成功!")
            print("下一步: 可以开始创建API接口")
        else:
            print("\n测试失败，请检查错误信息")
    
    asyncio.run(main())