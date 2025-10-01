#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索服务 (Search Service)
封装搜索业务逻辑，解耦API层和基础设施层
"""

import time
import json
from typing import List, Optional, Dict, Any, Tuple
import logging
import uuid

from ..domains.entities import LegalDocument, Article, Case
from ..domains.value_objects import SearchQuery, SearchResult, SearchContext
from ..domains.repositories import ILegalDocumentRepository
from ..types.debug_interfaces import (
    ModuleTrace, SearchPipelineTrace, ModuleStatus,
    create_module_trace, create_search_pipeline_trace
)
from ..config.settings import settings
from ..infrastructure.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SearchService:
    """搜索业务服务类 - 业务逻辑核心"""

    def __init__(self, repository: ILegalDocumentRepository, llm_client: Optional[LLMClient] = None, debug_mode: bool = False):
        """
        初始化搜索服务

        Args:
            repository: 法律文档存储库实现
            llm_client: LLM客户端实例
            debug_mode: 是否启用调试模式
        """
        self.repository = repository
        self.llm_client = llm_client
        self.debug_mode = debug_mode
        self.websocket_manager = None  # 新增：WebSocket管理器
        
    def set_websocket_manager(self, websocket_manager):
        """设置WebSocket管理器用于实时推送"""
        self.websocket_manager = websocket_manager
        logger.info(f"🔗 WebSocket管理器已设置，调试模式: {self.debug_mode}, 连接数: {len(websocket_manager.active_connections) if websocket_manager else 0}")

    async def search_documents_intelligent_debug(self, query_text: str, debug: bool = True) -> Dict[str, Any]:
        """
        AI驱动的智能搜索 - 完整调试模式 (增强版：带实时阶段推送)
        实现5阶段搜索管道：LLM分类→信息提取→智能路由→多路搜索→融合

        Args:
            query_text: 用户查询文本
            debug: 是否启用调试模式

        Returns:
            完整的trace数据和搜索结果
        """
        request_id = str(uuid.uuid4())
        pipeline_trace = create_search_pipeline_trace(request_id, query_text)
        pipeline_start = time.time()

        async def _broadcast_stage_completion(stage_number: int, stage_name: str, trace_data: ModuleTrace):
            logger.info(f"🚀 尝试广播阶段{stage_number}完成，调试模式: {self.debug_mode}, WebSocket管理器: {self.websocket_manager is not None}")

            if self.debug_mode and self.websocket_manager:
                try:
                    # 转换trace_data为可JSON序列化的字典
                    trace_dict = trace_data.dict()

                    # 处理datetime对象
                    if 'timestamp' in trace_dict and trace_dict['timestamp']:
                        trace_dict['timestamp'] = trace_dict['timestamp'].isoformat()

                    message = {
                        "type": "stage_completed",
                        "stage_number": stage_number,
                        "stage_name": stage_name,
                        "status": trace_data.status,  # 移除.value，因为ModuleStatus已经是字符串
                        "processing_time_ms": trace_data.processing_time_ms,
                        "trace_data": trace_dict,
                        "timestamp": int(time.time() * 1000)
                    }

                    logger.info(f"📡 准备发送WebSocket消息: {message['type']}, 阶段: {stage_number}, 连接数: {len(self.websocket_manager.active_connections)}")

                    await self.websocket_manager.broadcast(message)
                    logger.info(f"✅ [实时推送] 阶段{stage_number} ({stage_name}) 完成: {trace_data.processing_time_ms:.0f}ms")
                except Exception as e:
                    logger.error(f"❌ WebSocket推送阶段{stage_number}完成状态失败: {e}")
            else:
                logger.warning(f"⚠️ 跳过WebSocket推送 - 调试模式: {self.debug_mode}, WebSocket管理器: {self.websocket_manager is not None}")

        try:
            # 阶段1: LLM问题分类
            classification_trace, is_criminal = await self._llm_classification_stage(query_text, pipeline_trace)
            await _broadcast_stage_completion(1, "classification", classification_trace)

            if is_criminal:
                # 阶段2: 结构化信息提取
                extraction_trace, structured_data = await self._structured_extraction_stage(query_text, pipeline_trace)
                await _broadcast_stage_completion(2, "extraction", extraction_trace)

                # 阶段3: 智能路由决策
                routing_trace, selected_paths = await self._intelligent_routing_stage(structured_data, pipeline_trace)
                await _broadcast_stage_completion(3, "routing", routing_trace)

                # 阶段4: 多路搜索执行
                search_results = await self._multi_path_search_stage(query_text, structured_data, selected_paths, pipeline_trace)
                # Stage 4 broadcasts are handled inside _multi_path_search_stage for each module

                # 阶段5: 结果融合与回答生成
                fusion_trace, final_result = await self._fusion_and_generation_stage(search_results, query_text, pipeline_trace)
                await _broadcast_stage_completion(5, "fusion", fusion_trace)

                processing_mode = "criminal_law"
            else:
                # 非刑法问题，使用通用AI模式
                final_result = await self._general_ai_mode(query_text, pipeline_trace)
                processing_mode = "general_ai"

            pipeline_trace.total_duration_ms = (time.time() - pipeline_start) * 1000
            pipeline_trace.processing_mode = processing_mode
            pipeline_trace.summary.update({
                "stages_completed": 5 if is_criminal else 1,
                "total_modules_used": len(pipeline_trace.searches) + (1 if is_criminal else 0),
                "successful_modules": len([s for s in pipeline_trace.searches.values() if s.status == ModuleStatus.SUCCESS]),
                "highest_confidence": max([s.confidence_score or 0 for s in pipeline_trace.searches.values()] + [0])
            })

            if debug or self.debug_mode:
                return {
                    'success': True,
                    'request_id': request_id,
                    'trace': pipeline_trace.dict(),
                    'final_result': final_result,
                    'debug_enabled': True
                }
            else:
                return final_result

        except Exception as e:
            logger.error(f"Intelligent search failed: {str(e)}")
            error_trace = create_module_trace(
                module_name="intelligent_search_pipeline",
                stage="error_handling",
                input_data={"query": query_text},
                success=False,
                error_message=str(e)
            )
            pipeline_trace.searches["error"] = error_trace
            return self._create_error_response(f"智能搜索失败: {str(e)}")

    async def _llm_classification_stage(self, query_text: str, pipeline_trace: SearchPipelineTrace) -> Tuple[ModuleTrace, bool]:
        """阶段1: LLM问题分类 - 仅使用LLM进行语义分析"""
        stage_start = time.time()

        try:
            # 使用配置文件中的提示词模板，动态加载知识图谱罪名
            try:
                crimes_list = settings.load_knowledge_graph_crimes()
                classification_prompt = settings.CLASSIFICATION_PROMPT_TEMPLATE.format(
                    query=query_text,
                    crimes_list=crimes_list
                )
            except Exception as e:
                logger.error(f"加载知识图谱罪名失败: {e}")
                # 如果加载失败，使用简化版提示词
                classification_prompt = f"""你是专业的中国法律AI分类器，判断查询是否属于刑事法律范畴。

查询："{query_text}"

请严格按照JSON格式输出，包含以下字段：
{{
    "is_criminal_law": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "分析推理过程",
    "identified_crimes": [],
    "query2doc_generated": "",
    "hyde_answer": "",
    "bm25_keywords": []
}}"""

            # 必须有LLM客户端才能进行分类
            if not self.llm_client:
                error_trace = create_module_trace(
                    module_name="llm_classifier",
                    stage="问题分类",
                    input_data={"query": query_text},
                    success=False,
                    processing_time_ms=(time.time() - stage_start) * 1000,
                    error_message="LLM客户端未配置，无法进行问题分类"
                )
                pipeline_trace.classification = error_trace
                return error_trace, False

            # 调用LLM分类
            llm_start = time.time()
            response_text = await self.llm_client.generate_text(
                prompt=classification_prompt,
                max_tokens=settings.CLASSIFICATION_MAX_TOKENS,
                temperature=settings.CLASSIFICATION_TEMPERATURE
            )
            llm_time = (time.time() - llm_start) * 1000

            if not response_text:
                error_trace = create_module_trace(
                    module_name="llm_classifier",
                    stage="问题分类",
                    input_data={"query": query_text},
                    success=False,
                    processing_time_ms=(time.time() - stage_start) * 1000,
                    error_message="LLM返回空响应"
                )
                pipeline_trace.classification = error_trace
                return error_trace, False

            # 解析LLM返回的JSON
            try:
                classification_data = json.loads(response_text.strip())
                is_criminal = classification_data.get("is_criminal_law", False)
                confidence = classification_data.get("confidence", 0.5)

                # 构建输出数据 - 集成所有AI增强技术到阶段1
                classification_output = {
                    "is_criminal_law": is_criminal,
                    "confidence": confidence,
                    "reasoning": classification_data.get("reasoning", "LLM语义分析结果"),
                    "classification_method": "llm_semantic_analysis",
                    "identified_crimes": classification_data.get("identified_crimes", []),
                    # Query2doc和HyDE增强内容
                    "query2doc_generated": classification_data.get("query2doc_generated", ""),
                    "hyde_answer": classification_data.get("hyde_answer", ""),
                    # BM25关键词生成
                    "bm25_keywords": classification_data.get("bm25_keywords", [])
                }

            except json.JSONDecodeError as e:
                error_trace = create_module_trace(
                    module_name="llm_classifier",
                    stage="问题分类",
                    input_data={"query": query_text},
                    success=False,
                    processing_time_ms=(time.time() - stage_start) * 1000,
                    error_message=f"LLM返回JSON格式错误: {e}"
                )
                pipeline_trace.classification = error_trace
                return error_trace, False

            # 创建成功的分类trace - 增强版，包含完整输入输出
            classification_trace = create_module_trace(
                module_name="llm_classifier",
                stage="问题分类",
                input_data={
                    "query": query_text,
                    "prompt_template": "CLASSIFICATION_PROMPT_TEMPLATE",
                    "full_prompt_preview": classification_prompt[:500] + "..." if len(classification_prompt) > 500 else classification_prompt
                },
                output_data={
                    **classification_output,
                    "raw_llm_response": response_text,  # 添加原始LLM响应
                    "parsed_successfully": True
                },
                processing_time_ms=(time.time() - stage_start) * 1000,
                confidence_score=confidence,
                debug_info={
                    "method_used": "llm_semantic_analysis",
                    "llm_model": self.llm_client.get_current_service(),
                    "llm_response_time_ms": llm_time,
                    "prompt_tokens": len(classification_prompt.split()),
                    "response_tokens": len(response_text.split()),
                    "config_max_tokens": settings.CLASSIFICATION_MAX_TOKENS,
                    "config_temperature": settings.CLASSIFICATION_TEMPERATURE,
                    "config_timeout": settings.CLASSIFICATION_TIMEOUT,
                    "crimes_detected": len(classification_data.get("identified_crimes", [])),
                    "query2doc_generated": bool(classification_data.get("query2doc_generated")),
                    "hyde_generated": bool(classification_data.get("hyde_answer")),
                    "bm25_keywords_count": len(classification_data.get("bm25_keywords", []))
                }
            )

            pipeline_trace.classification = classification_trace
            return classification_trace, is_criminal

        except Exception as e:
            logger.error(f"LLM分类阶段出错: {e}", exc_info=True)
            error_trace = create_module_trace(
                module_name="llm_classifier",
                stage="问题分类",
                input_data={"query": query_text},
                success=False,
                processing_time_ms=(time.time() - stage_start) * 1000,
                error_message=str(e)
            )
            pipeline_trace.classification = error_trace
            return error_trace, False

    async def _structured_extraction_stage(self, query_text: str, pipeline_trace: SearchPipelineTrace) -> Tuple[ModuleTrace, Dict]:
        """阶段2: 结构化信息提取（从阶段1 LLM JSON中提取并展示）"""
        stage_start = time.time()

        try:
            classification_output = {}
            if pipeline_trace and pipeline_trace.classification and isinstance(pipeline_trace.classification.output_data, dict):
                classification_output = pipeline_trace.classification.output_data or {}

            identified_crimes = classification_output.get("identified_crimes") or []
            q2d = (classification_output.get("query2doc_generated") or "").strip()
            hyde = (classification_output.get("hyde_answer") or "").strip()
            bm25_keywords = classification_output.get("bm25_keywords") or []

            if q2d:
                query2doc_enhanced = f"{query_text} [SEP] {q2d}"
            else:
                query2doc_enhanced = query_text

            crimes_list_version = "unknown"
            try:
                crimes_text = settings.load_knowledge_graph_crimes()
                lines = crimes_text.split("\n") if crimes_text else []
                head = lines[0] if lines else ""
                tail = lines[-1] if lines else ""
                crimes_list_version = f"lines={len(lines)}; head={head[:8]}; tail={tail[:8]}"
            except Exception:
                crimes_list_version = "unavailable"

            structured_data = {
                "identified_crimes": identified_crimes,
                "query2doc_enhanced": query2doc_enhanced,
                "hyde_hypothetical": hyde,
                "bm25_keywords": bm25_keywords,
                "crimes_list_version": crimes_list_version,
            }

            extraction_trace = create_module_trace(
                module_name="structured_extractor",
                stage="结构化提取",
                input_data={"query": query_text},
                output_data=structured_data,
                processing_time_ms=(time.time() - stage_start) * 1000,
                confidence_score=classification_output.get("confidence"),
                debug_info={
                    "source": "stage1_llm_json",
                    "has_query2doc": bool(q2d),
                    "has_hyde": bool(hyde),
                    "bm25_keywords_count": len(bm25_keywords),
                }
            )

            pipeline_trace.extraction = extraction_trace
            return extraction_trace, structured_data

        except Exception as e:
            error_trace = create_module_trace(
                module_name="structured_extractor",
                stage="结构化提取",
                input_data={"query": query_text},
                success=False,
                processing_time_ms=(time.time() - stage_start) * 1000,
                error_message=str(e)
            )
            pipeline_trace.extraction = error_trace
            return error_trace, {}
    async def _extract_crimes_from_knowledge_graph(self, query_text: str) -> List[Dict]:
        """从知识图谱中提取罪名信息"""
        try:
            # 尝试从知识图谱获取罪名
            if hasattr(self.repository, 'data_loader') and self.repository.data_loader:
                knowledge_graph = self.repository.data_loader.get_knowledge_graph()
                if knowledge_graph:
                    return knowledge_graph.extract_crimes_from_query(query_text)
            
            # 降级到本地罪名词典匹配
            return self._local_crime_matching(query_text)
            
        except Exception as e:
            logger.warning(f"知识图谱罪名提取失败: {e}")
            return self._local_crime_matching(query_text)
    
    def _local_crime_matching(self, query_text: str) -> List[Dict]:
        """本地罪名匹配 - 基于关键词"""
        # 扩展的罪名词典
        crimes_map = {
            "故意伤害": {"crime_name": "故意伤害罪", "confidence": 0.9, "article_number": 234},
            "故意杀人": {"crime_name": "故意杀人罪", "confidence": 0.95, "article_number": 232},
            "盗窃": {"crime_name": "盗窃罪", "confidence": 0.85, "article_number": 264},
            "抢劫": {"crime_name": "抢劫罪", "confidence": 0.9, "article_number": 263},
            "诈骗": {"crime_name": "诈骗罪", "confidence": 0.88, "article_number": 266},
            "强奸": {"crime_name": "强奸罪", "confidence": 0.95, "article_number": 236},
            "绑架": {"crime_name": "绑架罪", "confidence": 0.92, "article_number": 239},
            "敲诈": {"crime_name": "敲诈勒索罪", "confidence": 0.9, "article_number": 274},
            "贪污": {"crime_name": "贪污罪", "confidence": 0.93, "article_number": 382},
            "受贿": {"crime_name": "受贿罪", "confidence": 0.93, "article_number": 385},
            "交通肇事": {"crime_name": "交通肇事罪", "confidence": 0.85, "article_number": 133},
            "危险驾驶": {"crime_name": "危险驾驶罪", "confidence": 0.88, "article_number": 133},
            "醉驾": {"crime_name": "危险驾驶罪", "confidence": 0.9, "article_number": 133},
            "毒品": {"crime_name": "非法持有毒品罪", "confidence": 0.8, "article_number": 348},
            "贩毒": {"crime_name": "贩卖毒品罪", "confidence": 0.95, "article_number": 347},
        }
        
        detected_crimes = []
        query_lower = query_text.lower()
        
        for keyword, crime_info in crimes_map.items():
            if keyword in query_lower:
                detected_crimes.append(crime_info)
        
        return detected_crimes

    async def _fallback_structured_extraction(self, query_text: str) -> Dict:
        """降级的结构化提取方法"""
        try:
            # 1. 本地罪名识别
            identified_crimes = self._local_crime_matching(query_text)
            
            # 2. 生成Query2doc（简化版）
            query2doc_enhanced = self._generate_simple_query2doc(query_text, identified_crimes)
            
            # 3. 生成HyDE（简化版）
            hyde_hypothetical = self._generate_simple_hyde(query_text, identified_crimes)
            
            # 4. 提取BM25关键词
            bm25_keywords = self._extract_bm25_keywords(query_text, identified_crimes)
            
            return {
                "identified_crimes": identified_crimes,
                "query2doc_enhanced": query2doc_enhanced,
                "hyde_hypothetical": hyde_hypothetical,
                "bm25_keywords": bm25_keywords
            }
            
        except Exception as e:
            logger.error(f"降级结构化提取失败: {e}")
            return {
                "identified_crimes": [],
                "query2doc_enhanced": "",
                "hyde_hypothetical": "",
                "bm25_keywords": []
            }

    def _generate_simple_query2doc(self, query_text: str, crimes: List[Dict]) -> str:
        """生成简单的Query2doc增强查询"""
        if crimes:
            crime_names = [crime.get("crime_name", "") for crime in crimes]
            articles = [f"第{crime.get('article_number', '')}条" for crime in crimes if crime.get('article_number')]
            
            enhanced = f"根据《中华人民共和国刑法》相关规定，涉及{', '.join(crime_names)}等罪名。"
            if articles:
                enhanced += f"相关法条包括{', '.join(articles)}。"
            enhanced += f"针对'{query_text}'的法律分析和处理依据。"
            return enhanced
        else:
            return f"关于'{query_text}'的法律条文和相关案例分析。"

    def _generate_simple_hyde(self, query_text: str, crimes: List[Dict]) -> str:
        """生成简单的HyDE假设答案"""
        if crimes:
            crime_name = crimes[0].get("crime_name", "相关犯罪")
            article_num = crimes[0].get("article_number", "")
            
            hyde = f"根据法律规定，{query_text}可能涉及{crime_name}。"
            if article_num:
                hyde += f"依据《刑法》第{article_num}条，"
            hyde += f"此类行为的法律后果包括刑事责任和相应的刑罚措施。具体量刑需要根据案件的具体情况、犯罪情节、社会危害程度等因素综合判定。"
            return hyde
        else:
            return f"关于{query_text}的法律问题，需要根据具体情况分析适用的法律条文和相关判例，以确定相应的法律责任和处理方式。"

    def _extract_bm25_keywords(self, query_text: str, crimes: List[Dict]) -> List[Dict]:
        """提取带权重的BM25搜索关键词"""
        keywords = []
        
        # 避免的通用词汇
        common_words = {
            "刑事", "犯罪", "受害者", "被告人", "法律", "处罚", "责任", "行为", 
            "构成", "依据", "规定", "条文", "案件", "事实", "情节", "社会", 
            "危害", "后果", "怎么", "如何", "什么", "哪个", "判刑", "定罪"
        }
        
        # 1. 添加法条编号（最高权重）
        for crime in crimes:
            article_num = crime.get("article_number")
            if article_num:
                keywords.append({"keyword": f"第{article_num}条", "weight": 0.95})
                keywords.append({"keyword": str(article_num), "weight": 0.9})
        
        # 2. 添加具体罪名（高权重）
        for crime in crimes:
            crime_name = crime.get("crime_name", "")
            if crime_name and crime_name not in common_words:
                keywords.append({"keyword": crime_name, "weight": 0.85})
                # 添加罪名的核心词
                core_word = crime_name.replace("罪", "")
                if core_word != crime_name and core_word not in common_words:
                    keywords.append({"keyword": core_word, "weight": 0.8})
        
        # 3. 添加查询中的专业术语（中等权重）
        import re
        # 改进的中文分词 - 提取有意义的词汇
        query_words = []
        
        # 专业术语词典（包含完整词汇）
        professional_terms = {
            "轻伤": 0.75, "重伤": 0.8, "死亡": 0.85,
            "数额较大": 0.7, "数额巨大": 0.75, "数额特别巨大": 0.8,
            "情节严重": 0.7, "情节特别严重": 0.75,
            "故意": 0.65, "过失": 0.65, "暴力": 0.7,
            "秘密窃取": 0.7, "公然抢夺": 0.7, "入户": 0.65,
            "持有": 0.6, "贩卖": 0.7, "运输": 0.65,
            "伤害": 0.6, "杀人": 0.75, "盗窃": 0.7, "抢劫": 0.75,
            "醉酒": 0.7, "驾驶": 0.65, "机动车": 0.6,
            "诈骗": 0.75, "敲诈": 0.7, "勒索": 0.7,
            "绑架": 0.8, "强奸": 0.8, "抢夺": 0.7
        }
        
        # 先检查专业术语
        for term, weight in professional_terms.items():
            if term in query_text and term not in common_words:
                keywords.append({"keyword": term, "weight": weight})
        
        # 再提取其他中文词汇
        other_words = re.findall(r'[\u4e00-\u9fff]{2,}', query_text)
        for word in other_words:
            if (word not in common_words and 
                not any(kw["keyword"] == word for kw in keywords) and
                not any(term in word for term in professional_terms.keys())):
                # 根据词汇长度和特征给予不同权重
                if len(word) >= 4:
                    weight = 0.55  # 较长词汇权重稍高
                else:
                    weight = 0.45
                keywords.append({"keyword": word, "weight": weight})
        
        # 按权重排序并去重
        keywords.sort(key=lambda x: x["weight"], reverse=True)
        
        # 去重（保留权重最高的）
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw["keyword"] not in seen:
                seen.add(kw["keyword"])
                unique_keywords.append(kw)
        
        # 返回前8个最重要的关键词
        return unique_keywords[:8]

    def _validate_and_clean_structured_data(self, structured_data: Dict, query_text: str) -> Dict:
        """验证和清理结构化数据"""
        # 确保所有字段存在
        cleaned_data = {
            "identified_crimes": structured_data.get("identified_crimes", []),
            "query2doc_enhanced": structured_data.get("query2doc_enhanced", ""),
            "hyde_hypothetical": structured_data.get("hyde_hypothetical", ""),
            "bm25_keywords": structured_data.get("bm25_keywords", [])
        }
        
        # 验证罪名格式
        valid_crimes = []
        for crime in cleaned_data["identified_crimes"]:
            if isinstance(crime, dict) and crime.get("crime_name"):
                valid_crimes.append(crime)
        cleaned_data["identified_crimes"] = valid_crimes
        
        # 确保Query2doc和HyDE不为空
        if not cleaned_data["query2doc_enhanced"]:
            cleaned_data["query2doc_enhanced"] = self._generate_simple_query2doc(query_text, valid_crimes)
        
        if not cleaned_data["hyde_hypothetical"]:
            cleaned_data["hyde_hypothetical"] = self._generate_simple_hyde(query_text, valid_crimes)
        
        # 确保BM25关键词不为空
        if not cleaned_data["bm25_keywords"]:
            cleaned_data["bm25_keywords"] = self._extract_bm25_keywords(query_text, valid_crimes)
        
        return cleaned_data

    async def _intelligent_routing_stage(self, structured_data: Dict, pipeline_trace: SearchPipelineTrace) -> Tuple[ModuleTrace, List[str]]:
        """阶段3: 智能路由决策"""
        stage_start = time.time()

        try:
            selected_paths = []
            routing_reasoning = []

            # 根据提取的信息决定搜索路径
            if structured_data.get("identified_crimes"):
                selected_paths.append("knowledge_graph")
                routing_reasoning.append("检测到明确罪名，启用知识图谱搜索")

            if structured_data.get("query2doc_enhanced"):
                selected_paths.append("query2doc")
                routing_reasoning.append("Query2doc增强可用，启用Query2doc搜索")

            if structured_data.get("hyde_hypothetical"):
                selected_paths.append("hyde")
                routing_reasoning.append("HyDE假设答案可用，启用HyDE搜索")

            if structured_data.get("bm25_keywords"):
                selected_paths.append("bm25_hybrid")
                routing_reasoning.append("关键词提取成功，启用BM25混合搜索")

            # 始终添加基础语义搜索作为核心路径之一
            selected_paths.append("basic_semantic")
            routing_reasoning.append("添加基础语义搜索（纯向量，直接用户输入）")

            routing_output = {
                "selected_paths": selected_paths,
                "routing_reasoning": "; ".join(routing_reasoning),
                "parallel_execution": True,
                "path_priorities": {path: 1.0 / (i + 1) for i, path in enumerate(selected_paths)},
                "execution_plan": {
                    "mode": "concurrent_async",
                    "timeout_ms": 30000,  # 30秒超时
                    "minimum_engines": max(1, len(selected_paths) // 2),  # 至少一半的引擎成功
                    "fallback_strategy": "graceful_degradation"
                },
                "routing_confidence": 0.9 if len(selected_paths) >= 3 else 0.7,
                "path_details": [
                    {
                        "engine": path,
                        "priority": 1.0 / (i + 1),
                        "expected_contribution": 0.8 if i == 0 else 0.6 - (i * 0.1),
                        "reason": reasoning
                    } for i, (path, reasoning) in enumerate(zip(selected_paths, routing_reasoning))
                ]
            }

            routing_trace = create_module_trace(
                module_name="intelligent_router",
                stage="路由决策",
                input_data=structured_data,
                output_data=routing_output,
                processing_time_ms=(time.time() - stage_start) * 1000,
                confidence_score=0.9,
                debug_info={
                    "decision_factors": list(structured_data.keys()),
                    "routing_algorithm": "rule_based_v1"
                }
            )

            pipeline_trace.routing = routing_trace
            return routing_trace, selected_paths

        except Exception as e:
            error_trace = create_module_trace(
                module_name="intelligent_router",
                stage="路由决策",
                input_data=structured_data,
                success=False,
                processing_time_ms=(time.time() - stage_start) * 1000,
                error_message=str(e)
            )
            pipeline_trace.routing = error_trace
            return error_trace, ["basic_semantic"]  # 错误时默认基础搜索

    async def _multi_path_search_stage(self, query_text: str, structured_data: Dict,
                                 selected_paths: List[str], pipeline_trace: SearchPipelineTrace) -> Dict:
        """阶段4: 多路搜索执行（优化版：并行执行 + 实时推送）"""
        import asyncio
        all_results: Dict[str, Any] = {}
        
        logger.info(f"开始并行执行{len(selected_paths)}个搜索模块")
        
        async def run_path(path: str):
            start = time.time()
            try:
                logger.info(f"模块{path}开始执行...")
                
                # 根据路径执行相应搜索
                if path == "knowledge_graph":
                    res = await self._execute_knowledge_graph_search(query_text, structured_data)
                elif path == "query2doc":
                    res = await self._execute_query2doc_search(query_text, structured_data)
                elif path == "hyde":
                    res = await self._execute_hyde_search(query_text, structured_data)
                elif path == "bm25_hybrid":
                    res = await self._execute_bm25_hybrid_search(query_text, structured_data)
                elif path == "basic_semantic":
                    res = await self._execute_basic_semantic_search(query_text)
                else:
                    res = {"success": False, "error": f"未知路径: {path}"}
                
                processing_time = (time.time() - start) * 1000
                status = ModuleStatus.SUCCESS if (isinstance(res, dict) and res.get('success')) else ModuleStatus.ERROR
                
                # 创建模块trace
                trace = create_module_trace(
                    module_name=f"{path}_search",
                    stage=f"{path}搜索",
                    input_data={"query": query_text, "path": path},
                    output_data=res,
                    processing_time_ms=processing_time,
                    success=(status == ModuleStatus.SUCCESS),
                    confidence_score=res.get('confidence_score') if isinstance(res, dict) else None,
                    debug_info={"concurrent": True, "execution_order": len(pipeline_trace.searches) + 1}
                )
                
                # 立即添加到pipeline_trace
                pipeline_trace.searches[path] = trace
                
                # 🚀 关键优化：每个模块完成后立即推送给前端
                if self.debug_mode and self.websocket_manager:
                    try:
                        # 转换trace为可JSON序列化的字典
                        trace_dict = trace.dict()

                        # 处理datetime对象
                        if 'timestamp' in trace_dict and trace_dict['timestamp']:
                            trace_dict['timestamp'] = trace_dict['timestamp'].isoformat()

                        # 实时WebSocket广播
                        await self.websocket_manager.broadcast({
                            "type": "module_completed",
                            "module_name": path,
                            "status": status,  # 移除.value，因为ModuleStatus已经是字符串
                            "processing_time_ms": processing_time,
                            "results_count": len(res.get('articles', [])) + len(res.get('cases', [])) if isinstance(res, dict) else 0,
                            "trace_data": trace_dict,  # 关键新增：包含完整的模块trace
                            "timestamp": int(time.time() * 1000)
                        })
                        logger.info(f"[实时推送] 模块{path}完成: {processing_time:.0f}ms, 状态: {status}")
                    except Exception as ws_error:
                        logger.warning(f"WebSocket推送失败: {ws_error}")
                elif self.debug_mode:
                    # fallback日志
                    logger.info(f"[调试模式] 模块{path}完成: {processing_time:.0f}ms, 状态: {status}")
                
                logger.info(f"模块{path}执行完成: {processing_time:.0f}ms, 结果: {len(res.get('articles', [])) if isinstance(res, dict) else 0}法条 + {len(res.get('cases', [])) if isinstance(res, dict) else 0}案例")
                return path, res
                
            except Exception as e:
                processing_time = (time.time() - start) * 1000
                logger.error(f"模块{path}执行失败: {e}")
                
                error_trace = create_module_trace(
                    module_name=f"{path}_search",
                    stage=f"{path}搜索",
                    input_data={"query": query_text, "path": path},
                    success=False,
                    processing_time_ms=processing_time,
                    error_message=str(e)
                )
                pipeline_trace.searches[path] = error_trace
                return path, {"success": False, "error": str(e)}

        # 去重并保持原有顺序
        seen = set()
        ordered_paths = [p for p in selected_paths if not (p in seen or seen.add(p))]
        
        # 🚀 关键优化：使用asyncio.as_completed实现真正的并行执行和实时处理
        tasks = [run_path(p) for p in ordered_paths]
        completed_count = 0
        
        for coro in asyncio.as_completed(tasks):
            try:
                path, res = await coro
                all_results[path] = res
                completed_count += 1
                
                # 实时显示进度
                logger.info(f"✅ 模块{path}完成 ({completed_count}/{len(ordered_paths)}) - 剩余{len(ordered_paths) - completed_count}个模块")
                
                # 这里可以立即处理单个模块的结果，而不等待所有模块完成
                # 例如：立即发送给前端显示这个模块的结果
                
            except Exception as e:
                logger.error(f"处理并行搜索结果失败: {e}")
                completed_count += 1
        
        logger.info(f"🎉 所有{len(ordered_paths)}个搜索模块已完成")
        return all_results

    async def _execute_knowledge_graph_search(self, query_text: str, structured_data: Dict) -> Dict:
        """执行知识图谱搜索"""
        try:
            # 检查是否有知识图谱支持
            if not hasattr(self.repository, 'data_loader') or not self.repository.data_loader:
                logger.warning("数据加载器未初始化，跳过知识图谱搜索")
                return {"success": False, "error": "数据加载器未初始化"}

            knowledge_graph = self.repository.data_loader.get_knowledge_graph()
            if not knowledge_graph:
                logger.warning("知识图谱未初始化，跳过知识图谱搜索")
                return {"success": False, "error": "知识图谱未初始化"}

            # 从structured_data获取识别的罪名
            crimes = structured_data.get("identified_crimes", [])
            crime_names = [crime.get("crime_name", "") for crime in crimes if crime.get("crime_name")]
            
            if crime_names:
                # 使用识别的罪名进行知识图谱搜索
                crime_based_query = " ".join(crime_names)
                logger.info(f"执行知识图谱搜索: 原查询'{query_text}' -> 罪名查询'{crime_based_query}'")
                search_query = crime_based_query
            else:
                logger.info(f"执行知识图谱搜索: 使用原查询'{query_text}'")
                search_query = query_text

            # 使用知识图谱扩展查询
            expansion_results = knowledge_graph.expand_query_with_relations(search_query)

            # 📊 转换知识图谱结果为标准搜索格式
            # 如果知识图谱返回了相关法条和案例，需要转换为标准格式
            articles = []
            cases = []
            
            # 处理相关法条
            related_articles = expansion_results.get('related_articles', [])
            for article_info in related_articles[:5]:  # 最多5条
                article_number = article_info.get('article_number')
                article_content = ''
                
                # 🔧 修复：从DataLoader获取完整法条内容
                if article_number and hasattr(self.repository, 'data_loader') and self.repository.data_loader:
                    try:
                        # 通过article_id或article_number获取完整内容
                        article_id = f"article_{article_number}"
                        article_content = self.repository.data_loader.get_article_content(article_id)
                        if not article_content:
                            # 如果通过ID获取失败，直接通过编号获取
                            article_content = self.repository.data_loader._get_article_by_number(article_number)
                        logger.debug(f"知识图谱法条{article_number}内容长度: {len(article_content) if article_content else 0}")
                    except Exception as e:
                        logger.warning(f"获取法条{article_number}完整内容失败: {e}")
                        article_content = article_info.get('content', '暂无内容')
                else:
                    article_content = article_info.get('content', '暂无内容')
                
                # 🎯 增强：添加知识图谱权重和来源信息
                kg_total_score = article_info.get('kg_total_score', article_info.get('confidence', 0.8))
                kg_sources = article_info.get('kg_sources', ['knowledge_graph'])
                
                articles.append({
                    'id': f"article_{article_number or 'unknown'}",
                    'type': 'article',
                    'title': f'中华人民共和国刑法 第{article_number}条' if article_number else '未知法条',  # 🔧 统一标题格式，与其他模块保持一致
                    'content': article_content,
                    'article_number': article_number,  # 🔧 添加article_number字段
                    'chapter': '',  # 🔧 添加章节字段保持格式一致
                    'similarity': article_info.get('confidence', 0.8),  # 知识图谱置信度
                    'score': article_info.get('confidence', 0.8),  # 🔧 添加score字段，前端使用此字段显示相关度
                    'kg_total_score': kg_total_score,  # 🎯 知识图谱权重
                    'kg_sources': kg_sources,  # 🎯 知识图谱来源
                    'source': '数据集',  # 🔧 统一来源显示
                    'search_method': 'knowledge_graph'  # 搜索方法作为技术信息
                })
            
            # 处理相关案例（如果有的话）
            related_cases = expansion_results.get('related_cases', [])
            for case_info in related_cases[:5]:  # 最多5个案例
                case_id = case_info.get('case_id', 'unknown')
                case_content = ''
                
                # 🔧 修复：从DataLoader获取完整案例内容
                if case_id != 'unknown' and hasattr(self.repository, 'data_loader') and self.repository.data_loader:
                    try:
                        # 通过case_id获取完整内容
                        case_content = self.repository.data_loader.get_case_content(case_id)
                        if not case_content:
                            case_content = case_info.get('content', '暂无内容')
                        logger.debug(f"知识图谱案例{case_id}内容长度: {len(case_content) if case_content else 0}")
                    except Exception as e:
                        logger.warning(f"获取案例{case_id}完整内容失败: {e}")
                        case_content = case_info.get('content', '暂无内容')
                else:
                    case_content = case_info.get('content', '暂无内容')
                
                # 🎯 增强：添加知识图谱权重和来源信息
                kg_total_score = case_info.get('kg_total_score', case_info.get('confidence', 0.8))
                kg_sources = case_info.get('kg_sources', ['knowledge_graph'])
                
                cases.append({
                    'id': f"case_{case_id}",
                    'type': 'case', 
                    'title': case_info.get('case_title', f'案例{case_id}'),
                    'content': case_content,
                    'fact': case_content,  # 🔧 添加fact字段，前端需要此字段显示案情描述
                    'case_id': case_id,  # 🔧 添加case_id字段
                    'accusations': case_info.get('accusations', []),  # 🔧 添加罪名字段
                    'similarity': case_info.get('confidence', 0.8),
                    'score': case_info.get('confidence', 0.8),  # 🔧 添加score字段，前端使用此字段显示相关度
                    'kg_total_score': kg_total_score,  # 🎯 知识图谱权重
                    'kg_sources': kg_sources,  # 🎯 知识图谱来源
                    'source': '数据集',  # 🔧 统一来源显示
                    'search_method': 'knowledge_graph'  # 搜索方法作为技术信息
                })

            # 构建标准格式的返回结果
            result = {
                'success': True,
                'articles': articles,
                'cases': cases,
                'total': len(articles) + len(cases),
                'search_meta': {
                    'method': 'knowledge_graph',
                    'search_type': 'entity_expansion',
                    'detected_crimes': len(expansion_results.get('detected_entities', {}).get('crimes', [])),
                    'expanded_keywords': expansion_results.get('expanded_keywords', []),
                    'query': query_text
                },
                'knowledge_expansion': expansion_results  # 保留原始知识图谱数据
            }

            logger.info(f"知识图谱搜索完成: 检测到{len(expansion_results.get('detected_entities', {}).get('crimes', []))}个罪名, {len(expansion_results.get('related_articles', []))}个相关法条")
            return result

        except Exception as e:
            logger.error(f"知识图谱搜索失败: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_query2doc_search(self, query_text: str, structured_data: Dict) -> Dict:
        """执行Query2doc增强搜索"""
        try:
            # 从structured_data获取Query2doc增强内容
            query2doc_enhanced = structured_data.get("query2doc_enhanced", "")
            
            if not query2doc_enhanced:
                logger.warning("没有Query2doc增强内容，使用原始查询")
                enhanced_query = query_text
            else:
                enhanced_query = query2doc_enhanced
                logger.info(f"执行Query2doc搜索: 原查询'{query_text}' -> 增强查询'{enhanced_query[:50]}...'")

            # 使用增强查询进行向量搜索
            result = await self.search_documents_hybrid(enhanced_query, 5, 5)
            
            # 添加搜索元信息
            if result.get("success"):
                result["search_meta"] = {
                    "method": "query2doc",
                    "used_enhancement": bool(query2doc_enhanced),
                    "enhanced_query": enhanced_query[:100] + "..." if len(enhanced_query) > 100 else enhanced_query
                }
                
                # 🔧 统一来源显示
                for article in result.get('articles', []):
                    article['source'] = '数据集'
                    article['search_method'] = 'query2doc'
                for case in result.get('cases', []):
                    case['source'] = '数据集' 
                    case['search_method'] = 'query2doc'
            
            return result

        except Exception as e:
            logger.error(f"Query2doc搜索失败: {e}")
            return {"success": False, "error": str(e), "articles": [], "cases": []}

    async def _execute_hyde_search(self, query_text: str, structured_data: Dict) -> Dict:
        """执行HyDE增强搜索"""
        try:
            # 从structured_data获取HyDE假设答案
            hyde_hypothetical = structured_data.get("hyde_hypothetical", "")
            
            if not hyde_hypothetical:
                logger.warning("没有HyDE假设答案，使用原始查询")
                enhanced_query = query_text
            else:
                enhanced_query = hyde_hypothetical
                logger.info(f"执行HyDE搜索: 原查询'{query_text}' -> 假设答案'{enhanced_query[:50]}...'")

            # 使用假设答案进行向量搜索
            result = await self.search_documents_hybrid(enhanced_query, 5, 5)
            
            # 添加搜索元信息
            if result.get("success"):
                result["search_meta"] = {
                    "method": "hyde",
                    "used_enhancement": bool(hyde_hypothetical),
                    "hypothetical_answer": enhanced_query[:100] + "..." if len(enhanced_query) > 100 else enhanced_query
                }
                
                # 🔧 统一来源显示
                for article in result.get('articles', []):
                    article['source'] = '数据集'
                    article['search_method'] = 'hyde'
                for case in result.get('cases', []):
                    case['source'] = '数据集'
                    case['search_method'] = 'hyde'
            
            return result

        except Exception as e:
            logger.error(f"HyDE搜索失败: {e}")
            return {"success": False, "error": str(e), "articles": [], "cases": []}

    async def _execute_bm25_hybrid_search(self, query_text: str, structured_data: Dict) -> Dict:
        """执行BM25混合搜索 - 使用提取的关键词"""
        try:
            # 从structured_data获取BM25关键词
            bm25_keywords = structured_data.get("bm25_keywords", [])
            
            if bm25_keywords:
                # 构建关键词查询
                if isinstance(bm25_keywords[0], dict):
                    # 新格式：带权重的关键词对象
                    keyword_query = " ".join([kw.get("keyword", "") for kw in bm25_keywords[:5]])
                else:
                    # 旧格式：简单字符串列表
                    keyword_query = " ".join(bm25_keywords[:5])
                
                logger.info(f"执行BM25混合搜索: 原查询'{query_text}' -> 关键词查询'{keyword_query}'")
                enhanced_query = f"{query_text} {keyword_query}"
            else:
                logger.warning("没有有效的BM25关键词，使用原始查询")
                enhanced_query = query_text

            # 使用增强查询进行混合搜索
            result = await self.search_documents_hybrid(enhanced_query, 5, 5)
            
            # 添加搜索元信息
            if result.get("success"):
                result["search_meta"] = {
                    "method": "bm25_hybrid",
                    "used_keywords": bool(bm25_keywords),
                    "keywords_count": len(bm25_keywords),
                    "enhanced_query": enhanced_query[:100] + "..." if len(enhanced_query) > 100 else enhanced_query
                }
                
                # 🔧 统一来源显示
                for article in result.get('articles', []):
                    article['source'] = '数据集'
                    article['search_method'] = 'bm25_hybrid'
                for case in result.get('cases', []):
                    case['source'] = '数据集'
                    case['search_method'] = 'bm25_hybrid'
            
            return result

        except Exception as e:
            logger.error(f"BM25混合搜索失败: {e}")
            return {"success": False, "error": str(e), "articles": [], "cases": []}

    async def _execute_llm_enhanced_search(self, query_text: str, structured_data: Dict) -> Dict:
        """执行LLM增强搜索 - 同时使用Query2doc和HyDE"""
        try:
            # 检查是否有多路召回引擎
            if not hasattr(self.repository, 'multi_retrieval_engine') or not self.repository.multi_retrieval_engine:
                logger.warning("多路召回引擎未初始化，降级到混合搜索")
                return await self.search_documents_hybrid(query_text, 5, 5)

            logger.info(f"执行LLM增强搜索（三路召回）: '{query_text}'")
            
            # 使用三路召回引擎进行搜索
            raw_results = await self.repository.multi_retrieval_engine.three_way_retrieval(
                query_text, top_k=10
            )
            
            if not raw_results:
                return {"success": False, "error": "LLM增强搜索无结果", "articles": [], "cases": []}
            
            # 分离法条和案例
            articles = [r for r in raw_results if r.get('type') == 'article'][:5]
            cases = [r for r in raw_results if r.get('type') == 'case'][:5]
            
            # 添加搜索元信息
            result = {
                "success": True,
                "articles": articles,
                "cases": cases,
                "total": len(articles) + len(cases),
                "search_meta": {
                    "method": "llm_enhanced",
                    "search_type": "three_way_fusion",
                    "used_query2doc": bool(structured_data.get("query2doc_enhanced")),
                    "used_hyde": bool(structured_data.get("hyde_hypothetical")),
                    "query": query_text
                }
            }
            
            logger.info(f"LLM增强搜索完成: {len(articles)}条法条, {len(cases)}个案例")
            return result

        except Exception as e:
            logger.error(f"LLM增强搜索失败: {e}")
            return {"success": False, "error": str(e), "articles": [], "cases": []}

    async def _execute_basic_semantic_search(self, query_text: str) -> Dict:
        """执行基础语义搜索 - 纯向量搜索，不使用BM25"""
        try:
            logger.info(f"执行基础语义搜索（纯向量）: '{query_text}'")
            
            # 🔧 检查搜索引擎状态
            if not hasattr(self.repository, 'search_engine') or not self.repository.search_engine:
                error_msg = "搜索引擎未初始化"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "articles": [], "cases": []}
            
            # 检查搜索引擎健康状态
            try:
                health_check = self.repository.search_engine.health_check()
                logger.debug(f"搜索引擎健康检查: {health_check}")
                if not health_check.get('healthy', False):
                    error_msg = f"搜索引擎不健康: {health_check.get('error', '未知错误')}"
                    logger.warning(error_msg)
                    # 不立即返回错误，尝试继续搜索
            except Exception as health_error:
                logger.warning(f"健康检查失败: {health_error}")
            
            # 直接使用向量搜索，不混合BM25
            search_result = self.repository.search_engine.search(
                query_text, 
                top_k=10, 
                include_content=True
            )
            
            # 🔧 修复：检查正确的字段名，SearchCoordinator返回的是success字段，不是status字段
            if not search_result or not search_result.get('success', False):
                error_msg = search_result.get('error', '基础语义搜索无结果') if search_result else '搜索引擎未返回结果'
                logger.warning(f"基础语义搜索失败: {error_msg}")
                return {"success": False, "error": error_msg, "articles": [], "cases": []}
            
            # 分离法条和案例
            all_results = search_result.get('articles', []) + search_result.get('cases', [])
            articles = [r for r in all_results if r.get('type') == 'article'][:5]
            cases = [r for r in all_results if r.get('type') == 'case'][:5]
            
            # 添加搜索元信息
            result = {
                "success": True,
                "articles": articles,
                "cases": cases,
                "total": len(articles) + len(cases),
                "search_meta": {
                    "method": "basic_semantic",
                    "search_type": "pure_vector",
                    "no_bm25": True,
                    "query": query_text
                }
            }
            
            # 🔧 统一来源显示
            for article in articles:
                article['source'] = '数据集'
                article['search_method'] = 'basic_semantic'
            for case in cases:
                case['source'] = '数据集'
                case['search_method'] = 'basic_semantic'
            
            logger.info(f"基础语义搜索完成: {len(articles)}条法条, {len(cases)}个案例")
            return result

        except Exception as e:
            logger.error(f"基础语义搜索失败: {e}")
            return {"success": False, "error": str(e), "articles": [], "cases": []}

    async def _fusion_and_generation_stage(self, search_results: Dict, query_text: str,
                                         pipeline_trace: SearchPipelineTrace) -> Tuple[ModuleTrace, Dict]:
        """阶段5: 结果融合与AI回答生成"""
        stage_start = time.time()

        try:
            # 🎆 收集所有有效的法条和案例结果
            all_articles = []
            all_cases = []
            path_confidence_scores = {}
            
            logger.info(f"开始融合{len(search_results)}个搜索模块的结果")
            
            for path, results in search_results.items():
                if isinstance(results, dict) and results.get('success'):
                    path_articles = results.get('articles', [])
                    path_cases = results.get('cases', [])
                    
                    # 添加路径标识
                    for article in path_articles:
                        article['search_path'] = path
                        article['path_priority'] = len(all_articles) + 1
                        article['source'] = '数据集'  # 🔧 统一来源
                        article['search_method'] = path  # 搜索方法
                        all_articles.append(article)
                    
                    for case in path_cases:
                        case['search_path'] = path
                        case['path_priority'] = len(all_cases) + 1
                        case['source'] = '数据集'  # 🔧 统一来源
                        case['search_method'] = path  # 搜索方法
                        all_cases.append(case)
                    
                    # 计算该路径的平均置信度
                    all_path_results = path_articles + path_cases
                    if all_path_results:
                        path_confidence = sum(r.get('similarity', 0) for r in all_path_results) / len(all_path_results)
                        path_confidence_scores[path] = path_confidence
                        logger.info(f"路径 {path}: {len(path_articles)}条法条, {len(path_cases)}个案例, 平均置信度: {path_confidence:.3f}")
                    else:
                        path_confidence_scores[path] = 0.0
                        logger.warning(f"路径 {path}: 无有效结果")
                else:
                    logger.warning(f"路径 {path}: 搜索失败或无结果")
            
            # 🎯 使用增强RRF算法融合结果
            final_articles = self._apply_enhanced_rrf_fusion(all_articles, target_count=5)
            final_cases = self._apply_enhanced_rrf_fusion(all_cases, target_count=5)
            
            logger.info(f"RRF融合完成: 最终获得{len(final_articles)}条法条, {len(final_cases)}个案例")
            
            # 🤖 调用LLM生成智能回答
            llm_start = time.time()
            ai_answer, final_confidence = await self._generate_ai_answer(
                query_text, final_articles, final_cases, path_confidence_scores
            )
            llm_time = (time.time() - llm_start) * 1000
            
            # 构建融合输出数据
            fusion_output = {
                "fusion_algorithm": "Enhanced_RRF",
                "input_sources_count": len([k for k, v in search_results.items() if v.get('success')]),
                "total_input_results": len(all_articles) + len(all_cases),
                "final_results_count": len(final_articles) + len(final_cases),
                "final_articles": final_articles,
                "final_cases": final_cases,
                "final_answer": ai_answer,
                "final_confidence": final_confidence,
                "path_confidence_scores": path_confidence_scores,
                "llm_generation_time_ms": llm_time,
                "fusion_details": {
                    "articles_before_fusion": len(all_articles),
                    "articles_after_fusion": len(final_articles),
                    "cases_before_fusion": len(all_cases),
                    "cases_after_fusion": len(final_cases),
                    "rrf_algorithm": "weighted_with_diversity",
                    "diversity_penalty": 0.1
                }
            }

            fusion_trace = create_module_trace(
                module_name="fusion_and_generation_engine",
                stage="结果融合与AI生成",
                input_data={
                    "query": query_text,
                    "search_modules": list(search_results.keys()),
                    "total_input_articles": len(all_articles),
                    "total_input_cases": len(all_cases)
                },
                output_data=fusion_output,
                processing_time_ms=(time.time() - stage_start) * 1000,
                confidence_score=final_confidence,
                debug_info={
                    "fusion_method": "enhanced_rrf_with_diversity",
                    "llm_generation_enabled": bool(self.llm_client),
                    "llm_generation_time_ms": llm_time,
                    "path_contributions": path_confidence_scores,
                    "answer_length": len(ai_answer) if ai_answer else 0,
                    "sources_used": len([k for k, v in search_results.items() if v.get('success')])
                }
            )

            pipeline_trace.fusion = fusion_trace

            # 构建最终结果
            final_result = {
                'success': True,
                'articles': final_articles,
                'cases': final_cases,
                'total_articles': len(final_articles),
                'total_cases': len(final_cases),
                'query': query_text,
                'ai_analysis': ai_answer,
                'final_confidence': final_confidence,
                'search_context': {
                    'fusion_applied': True,
                    'sources_used': len([k for k, v in search_results.items() if v.get('success')]),
                    'path_confidence_scores': path_confidence_scores,
                    'fusion_algorithm': 'enhanced_rrf_with_llm',
                    'processing_time_ms': (time.time() - stage_start) * 1000
                }
            }

            return fusion_trace, final_result

        except Exception as e:
            logger.error(f"阶段5融合与生成失败: {e}", exc_info=True)
            error_trace = create_module_trace(
                module_name="fusion_and_generation_engine",
                stage="结果融合与AI生成",
                input_data={"search_results": list(search_results.keys()) if search_results else []},
                success=False,
                processing_time_ms=(time.time() - stage_start) * 1000,
                error_message=str(e)
            )
            pipeline_trace.fusion = error_trace

            # 返回基础结果
            return error_trace, self._create_error_response(f"结果融合与AI生成失败: {str(e)}")

    def _apply_enhanced_rrf_fusion(self, results: List[Dict], target_count: int = 5) -> List[Dict]:
        """
        应用增强版RRF（Reciprocal Rank Fusion）算法融合结果
        包含多样性惩罚和路径权重调整
        
        Args:
            results: 结果列表
            target_count: 目标数量
            
        Returns:
            融合后的结果列表
        """
        if not results:
            return []
        
        logger.info(f"开始增强RRF融合，输入{len(results)}个结果，目标{target_count}个")
        
        # 1. 按搜索路径分组
        path_groups = {}
        for result in results:
            path = result.get('search_path', 'unknown')
            if path not in path_groups:
                path_groups[path] = []
            path_groups[path].append(result)
        
        # 2. 优化路径权重设置（提高基础权重）
        path_weights = {
            'knowledge_graph': 2.5,  # 知识图谱权重最高
            'query2doc': 2.2,        # Query2doc增强权重高
            'hyde': 2.2,             # HyDE增强权重高
            'bm25_hybrid': 2.0,      # BM25混合标准权重
            'basic_semantic': 1.8    # 基础语义权重适中
        }
        
        # 3. 计算每个结果的增强RRF分数
        enhanced_scores = {}
        diversity_seen_content = set()  # 用于多样性检查
        
        for path, path_results in path_groups.items():
            path_weight = path_weights.get(path, 2.0)  # 默认权重提升到2.0
            
            # 对每个路径内的结果按相似度排序
            sorted_path_results = sorted(path_results, 
                                       key=lambda x: x.get('similarity', 0), 
                                       reverse=True)
            
            for rank, result in enumerate(sorted_path_results):
                doc_id = result.get('id', f"doc_{len(enhanced_scores)}")
                
                # RRF基础分数（调整k参数，降低分母）
                k = 20  # 从60降低到20，提高RRF分数
                base_rrf_score = 1.0 / (k + rank + 1)
                
                # 相似度增强（相似度越高，增强越多）
                similarity = result.get('similarity', 0)
                similarity_boost = 1.0 + (similarity * 1.5)  # 最高可提升2.5倍
                
                # 路径权重调整
                weighted_score = base_rrf_score * path_weight * similarity_boost
                
                # 多样性惩罚（轻微调整）
                content_snippet = (result.get('content', '') or '')[:100].lower()
                diversity_penalty = 1.0
                if content_snippet in diversity_seen_content:
                    diversity_penalty = 0.85  # 轻微惩罚，从0.7提升到0.85
                else:
                    diversity_seen_content.add(content_snippet)
                
                # 最终分数
                final_score = weighted_score * diversity_penalty
                
                if doc_id in enhanced_scores:
                    # 如果同一文档在多个路径中出现，累加分数
                    enhanced_scores[doc_id]['score'] += final_score
                    enhanced_scores[doc_id]['path_count'] += 1
                    enhanced_scores[doc_id]['paths'].append(path)
                else:
                    enhanced_scores[doc_id] = {
                        'score': final_score,
                        'data': result,
                        'path_count': 1,
                        'paths': [path]
                    }
                    # 更新结果数据
                    result['rrf_score'] = base_rrf_score
                    result['path_weight'] = path_weight
                    result['similarity_boost'] = similarity_boost
                    result['diversity_penalty'] = diversity_penalty
        
        # 4. 多路径一致性奖励（增强版）
        for doc_id, score_data in enhanced_scores.items():
            if score_data['path_count'] > 1:
                # 多个路径都找到了同一文档，给予更大的一致性奖励
                consistency_bonus = 0.3 * (score_data['path_count'] - 1)  # 从0.1提升到0.3
                score_data['score'] *= (1 + consistency_bonus)
                score_data['data']['consistency_bonus'] = consistency_bonus
        
        # 5. 按最终分数排序并返回结果
        sorted_results = sorted(enhanced_scores.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        final_results = []
        for i, (doc_id, score_data) in enumerate(sorted_results[:target_count]):
            result_data = score_data['data']
            # 将分数转换为百分比显示（大幅提升显示效果）
            # 确保分数至少有一定的基础值，避免显示0.0%
            base_score = max(score_data['score'], 0.001)  # 设置最小基础分数
            display_score = min(base_score * 100, 100)  # 乘以100提升显示效果
            result_data['final_fusion_score'] = round(display_score, 1)
            result_data['fusion_rank'] = i + 1
            result_data['path_count'] = score_data['path_count']
            result_data['contributing_paths'] = score_data['paths']
            # 🔧 统一来源和方法显示
            result_data['source'] = '数据集'
            result_data['search_method'] = result_data.get('search_path', 'unknown')
            final_results.append(result_data)
        
        logger.info(f"增强RRF融合完成: 从{len(results)}个结果中选出{len(final_results)}个最佳结果")
        logger.info(f"融合分数范围: {final_results[0]['final_fusion_score']:.1f}% - {final_results[-1]['final_fusion_score']:.1f}%")
        return final_results

    async def _generate_ai_answer(self, query_text: str, final_articles: List[Dict], 
                                 final_cases: List[Dict], path_confidence_scores: Dict) -> Tuple[str, float]:
        """
        使用LLM生成智能法律回答
        
        Args:
            query_text: 用户查询
            final_articles: 融合后的法条
            final_cases: 融合后的案例
            path_confidence_scores: 路径置信度分数
            
        Returns:
            (AI回答文本, 最终置信度)
        """
        try:
            if not self.llm_client:
                logger.warning("LLM客户端未配置，使用默认回答模板")
                return self._generate_fallback_answer(query_text, final_articles, final_cases), 0.6
            
            # 构建高质量的提示词
            prompt = self._build_legal_analysis_prompt(
                query_text, final_articles, final_cases, path_confidence_scores
            )
            
            logger.info(f"调用LLM生成回答，提示词长度: {len(prompt)}字符")
            
            # 调用LLM生成回答
            ai_response = await self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=getattr(settings, 'ANSWER_GENERATION_MAX_TOKENS', 1500),
                temperature=getattr(settings, 'ANSWER_GENERATION_TEMPERATURE', 0.3)
            )
            
            if not ai_response or len(ai_response.strip()) < 50:
                logger.warning("LLM返回回答过短或为空，使用备用方案")
                return self._generate_fallback_answer(query_text, final_articles, final_cases), 0.5
            
            # 计算最终置信度
            final_confidence = self._calculate_final_confidence(
                path_confidence_scores, len(final_articles), len(final_cases)
            )
            
            logger.info(f"LLM回答生成成功，长度: {len(ai_response)}字符，置信度: {final_confidence:.3f}")
            return ai_response.strip(), final_confidence
            
        except Exception as e:
            logger.error(f"LLM回答生成失败: {e}")
            return self._generate_fallback_answer(query_text, final_articles, final_cases), 0.4
    
    def _build_legal_analysis_prompt(self, query_text: str, articles: List[Dict], 
                                   cases: List[Dict], confidence_scores: Dict) -> str:
        """
        构建法律分析提示词
        
        Args:
            query_text: 用户查询
            articles: 相关法条
            cases: 相关案例
            confidence_scores: 置信度分数
            
        Returns:
            完整的提示词
        """
        # 基础提示词模板
        base_prompt = """你是专业的中国刑法律师和法官，拥有丰富的司法实践经验。请基于提供的法条和案例，对用户的法律问题进行专业、准确、全面的分析回答。

【用户问题】
{query}

【相关法条】
{articles_section}

【相关案例】
{cases_section}

【回答要求】
1. 首先明确回答用户的核心问题
2. 引用具体的法条条文进行法理分析
3. 结合相关案例说明司法实践
4. 分析可能的法律后果和处罚标准
5. 提供实用的法律建议
6. 语言专业但通俗易懂，条理清晰

【专业分析】"""
        
        # 构建法条部分
        articles_section = ""
        if articles:
            articles_section = "根据检索系统找到以下相关法条：\n\n"
            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', f'第{i}条')
                content = article.get('content', '暂无内容')[:500]  # 限制长度
                similarity = article.get('similarity', 0)
                
                articles_section += f"{i}. {title} (相关度: {similarity:.1%})\n"
                articles_section += f"   {content}\n\n"
        else:
            articles_section = "未找到直接相关的法条，请基于刑法一般原则进行分析。\n\n"
        
        # 构建案例部分
        cases_section = ""
        if cases:
            cases_section = "相关司法案例参考：\n\n"
            for i, case in enumerate(cases[:5], 1):
                title = case.get('title', f'案例{i}')
                content = case.get('content', '暂无内容')[:400]  # 限制长度
                similarity = case.get('similarity', 0)
                
                cases_section += f"{i}. {title} (相关度: {similarity:.1%})\n"
                cases_section += f"   {content}\n\n"
        else:
            cases_section = "未找到直接相关的案例，请基于法理和一般司法实践进行分析。\n\n"
        
        # 组装完整提示词
        full_prompt = base_prompt.format(
            query=query_text,
            articles_section=articles_section,
            cases_section=cases_section
        )
        
        return full_prompt
    
    def _generate_fallback_answer(self, query_text: str, articles: List[Dict], cases: List[Dict]) -> str:
        """
        生成备用回答（当LLM不可用时）
        
        Args:
            query_text: 用户查询
            articles: 相关法条
            cases: 相关案例
            
        Returns:
            备用回答文本
        """
        fallback_answer = f"针对您咨询的问题'{query_text}'，基于检索到的法律资源，现提供以下分析：\n\n"
        
        if articles:
            fallback_answer += f"【相关法条】\n根据检索结果，找到{len(articles)}条相关法条：\n"
            for i, article in enumerate(articles[:3], 1):
                title = article.get('title', f'第{i}条')
                fallback_answer += f"{i}. {title}\n"
            fallback_answer += "\n"
        
        if cases:
            fallback_answer += f"【相关案例】\n系统检索到{len(cases)}个相关案例可供参考。\n\n"
        
        fallback_answer += "【建议】\n建议您：\n"
        fallback_answer += "1. 详细了解上述法条的具体内容\n"
        fallback_answer += "2. 参考相关案例的处理方式\n"
        fallback_answer += "3. 如需具体法律意见，请咨询专业律师\n\n"
        fallback_answer += "*本回答基于AI检索系统生成，仅供参考，不构成正式法律意见。"
        
        return fallback_answer
    
    def _calculate_final_confidence(self, path_scores: Dict, articles_count: int, cases_count: int) -> float:
        """
        计算最终置信度
        
        Args:
            path_scores: 各路径置信度分数
            articles_count: 法条数量
            cases_count: 案例数量
            
        Returns:
            最终置信度 (0-1)
        """
        try:
            # 基础置信度：各路径平均分
            if path_scores:
                base_confidence = sum(path_scores.values()) / len(path_scores)
            else:
                base_confidence = 0.3
            
            # 结果数量奖励
            result_bonus = 0.0
            if articles_count >= 3 and cases_count >= 3:
                result_bonus = 0.15  # 法条和案例都充足
            elif articles_count >= 2 or cases_count >= 2:
                result_bonus = 0.1   # 其中一类结果充足
            elif articles_count >= 1 or cases_count >= 1:
                result_bonus = 0.05  # 至少有一些结果
            
            # 多路径一致性奖励
            consistency_bonus = 0.0
            if len(path_scores) >= 3:
                consistency_bonus = 0.1  # 多个搜索路径都有结果
            elif len(path_scores) >= 2:
                consistency_bonus = 0.05
            
            # 计算最终置信度
            final_confidence = min(base_confidence + result_bonus + consistency_bonus, 0.95)
            final_confidence = max(final_confidence, 0.1)  # 最低置信度保护
            
            return final_confidence
            
        except Exception as e:
            logger.warning(f"置信度计算失败: {e}")
            return 0.5  # 默认中等置信度

    async def _general_ai_mode(self, query_text: str, pipeline_trace: SearchPipelineTrace) -> Dict:
        """通用AI助手模式（非刑法问题）"""
        stage_start = time.time()

        try:
            # 通用AI回答生成
            general_response = {
                'success': True,
                'query': query_text,
                'ai_response': f"这是一个通用问题：{query_text}。建议咨询相关专业人士获取准确信息。",
                'mode': 'general_ai',
                'search_context': {
                    'duration_ms': (time.time() - stage_start) * 1000,
                    'specialized_search': False
                }
            }

            # 记录通用AI trace
            general_trace = create_module_trace(
                module_name="general_ai_assistant",
                stage="通用AI回答",
                input_data={"query": query_text},
                output_data=general_response,
                processing_time_ms=(time.time() - stage_start) * 1000,
                confidence_score=0.6,
                debug_info={
                    "response_type": "general_assistance",
                    "specialized_search_skipped": True
                }
            )

            pipeline_trace.searches["general_ai"] = general_trace
            return general_response

        except Exception as e:
            logger.error(f"通用AI模式失败: {e}")
            return self._create_error_response(f"通用AI回答生成失败: {str(e)}")
    
    async def search_documents(self, query_text: str, max_results: int = 10, 
                             document_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        搜索法律文档 - 完整业务流程
        
        Args:
            query_text: 查询文本
            max_results: 最大结果数
            document_types: 文档类型过滤
            
        Returns:
            包含搜索结果和元信息的字典
        """
        start_time = time.time()
        
        try:
            # 1. 创建搜索查询值对象
            search_query = SearchQuery(
                query_text=query_text,
                max_results=max_results,
                document_types=document_types
            )
            
            # 2. 验证查询有效性
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")
            
            # 3. 执行搜索
            results, context = await self.repository.search_documents(search_query)
            
            # 4. 转换为API响应格式
            api_results = []
            for result in results:
                api_result = self._convert_domain_result_to_api(result)
                api_results.append(api_result)
            
            # 5. 构建响应
            end_time = time.time()
            response = {
                'success': True,
                'results': api_results,
                'total': len(api_results),
                'query': query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'total_documents_searched': context.total_documents_searched,
                    'performance_info': context.get_performance_info()
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Document search error: {str(e)}")
            return self._create_error_response(f"搜索过程中发生错误: {str(e)}")
    
    async def search_documents_mixed(self, query_text: str, articles_count: int = 5, 
                                   cases_count: int = 5) -> Dict[str, Any]:
        """
        混合搜索 - 分别返回法条和案例
        
        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量
            
        Returns:
            包含分类结果的字典
        """
        start_time = time.time()
        
        try:
            # 1. 创建搜索查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )
            
            # 2. 验证查询
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")
            
            # 3. 执行混合搜索
            mixed_results = await self.repository.search_documents_mixed(
                search_query, articles_count, cases_count
            )
            
            # 4. 转换结果格式
            api_articles = []
            for result in mixed_results.get('articles', []):
                api_result = self._convert_domain_result_to_api(result)
                api_articles.append(api_result)
            
            api_cases = []
            for result in mixed_results.get('cases', []):
                api_result = self._convert_domain_result_to_api(result)
                api_cases.append(api_result)
            
            # 5. 构建响应
            end_time = time.time()
            return {
                'success': True,
                'articles': api_articles,
                'cases': api_cases,
                'total_articles': len(api_articles),
                'total_cases': len(api_cases),
                'query': query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'articles_requested': articles_count,
                    'cases_requested': cases_count
                }
            }
            
        except Exception as e:
            logger.error(f"Mixed search error: {str(e)}")
            return self._create_error_response(f"混合搜索过程中发生错误: {str(e)}")

    async def search_documents_hybrid(self, query_text: str, articles_count: int = 5,
                                    cases_count: int = 5) -> Dict[str, Any]:
        """
        增强版混合搜索 - 使用BM25+语义搜索融合

        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量

        Returns:
            包含分类结果的字典
        """
        start_time = time.time()

        try:
            # 1. 创建搜索查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )

            # 2. 验证查询
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")

            # 3. 使用混合搜索引擎
            raw_results = []  # 🔧 修复：初始化raw_results变量
            try:
                # 检查是否有混合搜索功能
                if hasattr(self.repository.search_engine, 'hybrid_search'):
                    # 🔧 修复：使用execute_mixed_search确保返回正确数量的法条和案例
                    search_coordinator = self.repository.search_engine._get_search_coordinator()
                    if search_coordinator and hasattr(search_coordinator, 'execute_mixed_search'):
                        logger.info(f"使用execute_mixed_search，保证返回{articles_count}条法条+{cases_count}个案例")
                        mixed_results = search_coordinator.execute_mixed_search(
                            query_text, articles_count, cases_count, include_content=True
                        )
                        
                        if mixed_results.get('success'):
                            # 直接使用分离好的结果
                            domain_articles = mixed_results.get('articles', [])
                            domain_cases = mixed_results.get('cases', [])
                        else:
                            logger.warning(f"execute_mixed_search失败: {mixed_results.get('error')}")
                            # 降级到原始hybrid_search
                            raw_results = self.repository.search_engine.hybrid_search(
                                query_text, (articles_count + cases_count) * 2
                            )
                            # 分离法条和案例结果
                            articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                            cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]
                            
                            # 转换为领域对象
                            domain_articles = await self._convert_to_domain_objects(articles_results)
                            domain_cases = await self._convert_to_domain_objects(cases_results)
                    else:
                        logger.warning("无法获取SearchCoordinator，使用原始hybrid_search")
                        raw_results = self.repository.search_engine.hybrid_search(
                            query_text, (articles_count + cases_count) * 2
                        )
                        # 分离法条和案例结果
                        articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                        cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]
                        
                        # 转换为领域对象
                        domain_articles = await self._convert_to_domain_objects(articles_results)
                        domain_cases = await self._convert_to_domain_objects(cases_results)
                        
                    logger.info(f"混合搜索完成: {len(domain_articles)}条法条, {len(domain_cases)}个案例")
                else:
                    # 降级到原始搜索
                    logger.warning("混合搜索功能不可用，降级到原始搜索")
                    mixed_results = await self.repository.search_documents_mixed(
                        search_query, articles_count, cases_count
                    )
                    # 转换为领域对象
                    domain_articles = await self._convert_to_domain_objects(mixed_results.get('articles', []))
                    domain_cases = await self._convert_to_domain_objects(mixed_results.get('cases', []))

                # 6. 构建响应
                end_time = time.time()
                return {
                    'success': True,
                    'articles': domain_articles,
                    'cases': domain_cases,
                    'total_articles': len(domain_articles),
                    'total_cases': len(domain_cases),
                    'query': query_text,
                    'search_context': {
                        'duration_ms': round((end_time - start_time) * 1000, 2),
                        'hybrid_search_used': hasattr(self.repository.search_engine, 'hybrid_search'),
                        'fusion_method': 'RRF',
                        'articles_requested': articles_count,
                        'cases_requested': cases_count,
                        'raw_results_count': len(raw_results) if raw_results else 0
                    }
                }

            except Exception as e:
                logger.warning(f"混合搜索失败，降级到传统搜索: {e}")
                return await self._fallback_search_mixed(query_text, articles_count, cases_count)

        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            return self._create_error_response(f"混合搜索过程中发生错误: {str(e)}")

    async def _convert_to_domain_objects(self, raw_results: List[Dict]) -> List[Dict[str, Any]]:
        """
        将原始搜索结果转换为API格式

        Args:
            raw_results: 原始搜索结果

        Returns:
            API格式的结果列表
        """
        api_results = []

        for result in raw_results:
            try:
                # 如果已经是领域对象格式，直接转换
                if hasattr(result, 'document') and hasattr(result, 'similarity_score'):
                    api_result = self._convert_domain_result_to_api(result)
                    api_results.append(api_result)
                    continue

                # 转换为API格式
                api_result = {
                    'id': result.get('id', ''),
                    'title': self._normalize_article_title(result.get('title', result.get('id', ''))),  # 统一标题格式
                    'content': result.get('content', ''),
                    'similarity': result.get('similarity', result.get('fusion_score', 0.0)),
                    'type': self._determine_document_type(result.get('id', '')),
                    'search_method': result.get('search_method', 'hybrid'),
                    'source': '数据集'  # 统一来源显示
                }

                # 添加类型特定字段
                doc_id = result.get('id', '')
                if 'case_' in doc_id:
                    api_result.update({
                        'case_id': result.get('case_id', doc_id),
                        'accusations': result.get('accusations', []),
                        'relevant_articles': result.get('relevant_articles', []),
                        'imprisonment_months': result.get('imprisonment_months', 0)
                    })
                elif 'article_' in doc_id:
                    api_result.update({
                        'article_number': result.get('article_number', ''),
                        'chapter': result.get('chapter', ''),
                        'law_name': result.get('law_name', '刑法')
                    })

                api_results.append(api_result)

            except Exception as e:
                logger.warning(f"转换结果失败: {e}, 跳过结果: {result.get('id', 'unknown')}")
                continue

        return api_results

    async def _fallback_search_mixed(self, query_text: str, articles_count: int,
                                   cases_count: int) -> Dict[str, Any]:
        """
        降级搜索方法

        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量

        Returns:
            搜索结果
        """
        try:
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )

            mixed_results = await self.repository.search_documents_mixed(
                search_query, articles_count, cases_count
            )

            # 转换结果格式
            api_articles = []
            for result in mixed_results.get('articles', []):
                api_result = self._convert_domain_result_to_api(result)
                api_articles.append(api_result)

            api_cases = []
            for result in mixed_results.get('cases', []):
                api_result = self._convert_domain_result_to_api(result)
                api_cases.append(api_result)

            return {
                'success': True,
                'articles': api_articles,
                'cases': api_cases,
                'total_articles': len(api_articles),
                'total_cases': len(api_cases),
                'query': query_text,
                'search_context': {
                    'duration_ms': 0,
                    'hybrid_search_used': False,
                    'fallback_reason': 'hybrid_search_unavailable'
                }
            }

        except Exception as e:
            logger.error(f"降级搜索也失败: {e}")
            return self._create_error_response(f"所有搜索方法都失败: {str(e)}")

    def _determine_document_type(self, doc_id: str) -> str:
        """
        根据文档ID确定文档类型

        Args:
            doc_id: 文档ID

        Returns:
            文档类型字符串
        """
        if 'case_' in doc_id:
            return 'case'
        elif 'article_' in doc_id:
            return 'article'
        else:
            return 'unknown'
    
    def _normalize_article_title(self, title: str) -> str:
        """
        统一法条标题格式
        
        Args:
            title: 原始标题
            
        Returns:
            规范化后的标题
        """
        import re
        
        # 提取法条编号
        article_match = re.search(r'第?(─*[0-9]+)条', title)
        if article_match:
            article_num = article_match.group(1).strip('─')  # 去除可能的破折号
            return f'第{article_num}条'
        
        # 如果包含article_前缀，提取编号
        if 'article_' in title:
            try:
                article_num = title.split('article_')[1].split('_')[0]
                if article_num.isdigit():
                    return f'第{article_num}条'
            except:
                pass
        
        # 如果是纯数字，添加第一条格式
        if title.isdigit():
            return f'第{title}条'
            
        # 其他情况返回原标题
        return title
    
    async def search_documents_for_crime_consistency(self, query_text: str, cases_count: int = None) -> Dict[str, Any]:
        """
        罪名一致性专用搜索 - 3个法条 + 10个案例
        
        Args:
            query_text: 搜索查询文本
            cases_count: 案例数量，默认固定10个
            
        Returns:
            搜索结果字典
        """
        # 罪名一致性评估的固定配置
        articles_count = 3  # 固定返回3个法条
        if cases_count is None:
            cases_count = 10  # 固定返回10个案例
        
        logger.info(f"罪名一致性搜索: {query_text} - 请求{articles_count}条法条, {cases_count}个案例")
        
        start_time = time.time()
        
        try:
            # 1. 创建搜索查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )
            
            # 2. 验证查询
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")
            
            # 3. 执行混合搜索
            mixed_results = await self.repository.search_documents_mixed(
                search_query, articles_count, cases_count
            )
            
            # 4. 转换结果格式
            api_articles = []
            for result in mixed_results.get('articles', []):
                api_result = self._convert_domain_result_to_api(result)
                api_articles.append(api_result)
            
            api_cases = []
            for result in mixed_results.get('cases', []):
                api_result = self._convert_domain_result_to_api(result)
                api_cases.append(api_result)
            
            # 5. 构建响应
            end_time = time.time()
            return {
                'success': True,
                'articles': api_articles,
                'cases': api_cases,
                'total_articles': len(api_articles),
                'total_cases': len(api_cases),
                'query': query_text,
                'search_type': 'crime_consistency',
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'articles_requested': articles_count,
                    'cases_requested': cases_count,
                    'actual_cases_returned': len(api_cases)
                }
            }
            
        except Exception as e:
            logger.error(f"Crime consistency search error: {str(e)}")
            return self._create_error_response(f"罪名一致性搜索过程中发生错误: {str(e)}")
    
    async def load_more_cases(self, query_text: str, offset: int = 0, 
                            limit: int = 5) -> Dict[str, Any]:
        """
        分页加载更多案例
        
        Args:
            query_text: 查询文本
            offset: 偏移量
            limit: 返回数量
            
        Returns:
            分页案例结果
        """
        start_time = time.time()
        
        try:
            # 1. 创建分页查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=limit,
                document_types=['cases']
            )
            
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")
            
            # 2. 执行分页搜索
            paginated_results = await self.repository.load_more_cases(
                search_query, offset, limit
            )
            
            # 3. 转换结果格式
            api_cases = []
            for result in paginated_results.get('cases', []):
                api_result = self._convert_domain_result_to_api(result)
                api_cases.append(api_result)
            
            # 4. 构建响应
            end_time = time.time()
            return {
                'success': True,
                'cases': api_cases,
                'offset': offset,
                'limit': limit,
                'returned_count': len(api_cases),
                'has_more': paginated_results.get('has_more', False),
                'query': query_text,
                'search_context': {
                    'duration_ms': round((end_time - start_time) * 1000, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Load more cases error: {str(e)}")
            return self._create_error_response(f"加载更多案例时发生错误: {str(e)}")
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典或None
        """
        try:
            document = await self.repository.get_document_by_id(document_id)
            if document is None:
                return None
            
            return self._convert_domain_document_to_api(document)
            
        except Exception as e:
            logger.error(f"获取文档失败 (ID: {document_id}): {str(e)}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        try:
            is_ready = self.repository.is_ready()
            document_counts = self.repository.get_total_document_count()
            
            return {
                'status': 'ok' if is_ready else 'not_ready',
                'ready': is_ready,
                'total_documents': document_counts.get('total', 0),
                'document_breakdown': document_counts
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                'status': 'error',
                'ready': False,
                'total_documents': 0,
                'error': str(e)
            }
    
    def _convert_domain_result_to_api(self, domain_result: SearchResult) -> Dict[str, Any]:
        """将领域搜索结果转换为API格式"""
        document = domain_result.document
        
        base_result = {
            'id': document.id,
            'title': document.get_display_title(),
            'content': document.content,
            'similarity': domain_result.similarity_score,
            'type': document.document_type,
            'confidence_level': domain_result.confidence_level,
            'rank': domain_result.rank
        }
        
        # 添加类型特定字段
        if isinstance(document, Case):
            base_result.update({
                'case_id': document.case_id,
                'criminals': document.criminals,
                'accusations': document.accusations,
                'relevant_articles': document.relevant_articles,
                'punish_of_money': document.punish_of_money,
                'death_penalty': document.death_penalty,
                'life_imprisonment': document.life_imprisonment,
                'imprisonment_months': document.imprisonment_months,
                'is_severe_case': document.has_severe_punishment()
            })
        elif isinstance(document, Article):
            base_result.update({
                'article_number': document.article_number,
                'chapter': document.chapter,
                'law_name': document.law_name
            })
        
        return base_result
    
    def _convert_domain_document_to_api(self, document: LegalDocument) -> Dict[str, Any]:
        """将领域文档实体转换为API格式"""
        base_doc = {
            'id': document.id,
            'title': document.get_display_title(),
            'content': document.content,
            'type': document.document_type,
            'searchable_text': document.get_searchable_text()
        }
        
        # 添加类型特定字段
        if isinstance(document, Case):
            base_doc.update({
                'case_id': document.case_id,
                'criminals': document.criminals,
                'accusations': document.accusations,
                'relevant_articles': document.relevant_articles,
                'punish_of_money': document.punish_of_money,
                'death_penalty': document.death_penalty,
                'life_imprisonment': document.life_imprisonment,
                'imprisonment_months': document.imprisonment_months
            })
        elif isinstance(document, Article):
            base_doc.update({
                'article_number': document.article_number,
                'chapter': document.chapter,
                'law_name': document.law_name
            })
        
        return base_doc

    # ==================== LLM增强搜索方法 ====================

    async def search_documents_enhanced(self, query_text: str, articles_count: int = 5,
                                      cases_count: int = 5) -> Dict[str, Any]:
        """
        LLM增强版搜索 - 使用三路召回融合

        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量

        Returns:
            包含分类结果的字典
        """
        start_time = time.time()

        try:
            # 1. 创建搜索查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )

            # 2. 验证查询
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")

            # 3. 尝试使用三路召回引擎
            try:
                if hasattr(self.repository, 'multi_retrieval_engine') and self.repository.multi_retrieval_engine:
                    logger.info("使用三路召回增强搜索")
                    raw_results = await self.repository.multi_retrieval_engine.three_way_retrieval(
                        query_text,
                        top_k=(articles_count + cases_count) * 2
                    )

                    # 分离和转换结果
                    articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                    cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]

                    domain_articles = await self._convert_to_domain_objects_enhanced(articles_results, 'article')
                    domain_cases = await self._convert_to_domain_objects_enhanced(cases_results, 'case')

                    end_time = time.time()
                    return {
                        'success': True,
                        'articles': domain_articles,
                        'cases': domain_cases,
                        'total_articles': len(domain_articles),
                        'total_cases': len(domain_cases),
                        'query': query_text,
                        'search_context': {
                            'duration_ms': round((end_time - start_time) * 1000, 2),
                            'llm_enhanced': True,
                            'retrieval_paths': ['hybrid', 'query2doc', 'hyde'],
                            'fusion_method': 'weighted_multi_path'
                        }
                    }
                else:
                    logger.warning("三路召回引擎不可用，降级到混合搜索")
                    return await self._progressive_fallback_search(query_text, articles_count, cases_count)

            except Exception as e:
                logger.error(f"LLM增强搜索失败: {e}")
                return await self._progressive_fallback_search(query_text, articles_count, cases_count)

        except Exception as e:
            logger.error(f"增强搜索服务错误: {e}")
            return self._create_error_response(f"增强搜索失败: {str(e)}")

    async def _progressive_fallback_search(self, query_text: str, articles_count: int,
                                         cases_count: int) -> Dict[str, Any]:
        """
        渐进式降级搜索策略

        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量

        Returns:
            搜索结果
        """
        try:
            # 尝试混合搜索
            logger.info("尝试混合搜索作为降级方案")
            return await self.search_documents_hybrid(query_text, articles_count, cases_count)

        except Exception as e:
            logger.warning(f"混合搜索也失败: {e}")

            try:
                # 最后降级到原始搜索
                logger.info("最后降级到原始搜索")
                return await self.search_documents_mixed(query_text, articles_count, cases_count)

            except Exception as e2:
                logger.error(f"所有搜索方法都失败: {e2}")
                return self._create_error_response(f"所有搜索方法都失败: {str(e2)}")

    async def _convert_to_domain_objects_enhanced(self, results: List[Dict], doc_type: str) -> List[Dict[str, Any]]:
        """
        将搜索结果转换为领域对象格式

        Args:
            results: 原始搜索结果
            doc_type: 文档类型

        Returns:
            转换后的领域对象列表
        """
        converted_results = []

        for result in results:
            try:
                # 获取完整文档内容
                doc_id = result.get('id')
                if not doc_id:
                    continue

                full_document = await self.repository.get_document_by_id(doc_id)
                if full_document:
                    api_result = self._convert_domain_document_to_api(full_document)

                    # 添加搜索相关的元信息
                    api_result.update({
                        'similarity': result.get('similarity', 0),
                        'fusion_score': result.get('fusion_score', 0),
                        'confidence': result.get('confidence', 0),
                        'sources': result.get('sources', []),
                        'search_meta': result.get('search_meta', {})
                    })

                    converted_results.append(api_result)

            except Exception as e:
                logger.warning(f"转换文档 {result.get('id')} 失败: {e}")
                continue

        return converted_results

    def get_llm_enhancement_status(self) -> Dict[str, Any]:
        """
        获取LLM增强功能状态

        Returns:
            LLM增强功能状态信息
        """
        try:
            has_multi_retrieval = (hasattr(self.repository, 'multi_retrieval_engine') and
                                 self.repository.multi_retrieval_engine is not None)

            if has_multi_retrieval:
                stats = self.repository.multi_retrieval_engine.get_retrieval_stats()
            else:
                stats = None

            return {
                'llm_enhancement_available': has_multi_retrieval,
                'multi_retrieval_engine_status': stats,
                'fallback_available': True,
                'supported_methods': ['three_way_fusion', 'hybrid', 'mixed'] if has_multi_retrieval else ['hybrid', 'mixed']
            }

        except Exception as e:
            logger.error(f"获取LLM增强状态失败: {e}")
            return {
                'llm_enhancement_available': False,
                'error': str(e),
                'fallback_available': True,
                'supported_methods': ['hybrid', 'mixed']
            }

    # ==================== 知识图谱增强搜索方法 ====================

    async def search_documents_kg_enhanced(self, query_text: str, articles_count: int = 5,
                                         cases_count: int = 5) -> Dict[str, Any]:
        """
        知识图谱增强版搜索 - 最高级的搜索功能

        Args:
            query_text: 查询文本
            articles_count: 法条数量
            cases_count: 案例数量

        Returns:
            包含分类结果的字典
        """
        start_time = time.time()

        try:
            # 1. 创建搜索查询
            search_query = SearchQuery(
                query_text=query_text,
                max_results=articles_count + cases_count,
                document_types=None
            )

            # 2. 验证查询
            if not search_query.is_valid():
                return self._create_error_response("无效的查询文本")

            # 3. 尝试使用知识图谱增强搜索
            try:
                if hasattr(self.repository, 'kg_enhanced_engine') and self.repository.kg_enhanced_engine:
                    logger.info("使用知识图谱增强搜索")
                    raw_results = await self.repository.kg_enhanced_engine.knowledge_enhanced_search(
                        query_text,
                        top_k=(articles_count + cases_count) * 2
                    )

                    # 分离和转换结果
                    articles_results = [r for r in raw_results if 'article' in r.get('id', '')][:articles_count]
                    cases_results = [r for r in raw_results if 'case' in r.get('id', '')][:cases_count]

                    domain_articles = await self._convert_to_domain_objects_enhanced(articles_results, 'article')
                    domain_cases = await self._convert_to_domain_objects_enhanced(cases_results, 'case')

                    end_time = time.time()
                    return {
                        'success': True,
                        'articles': domain_articles,
                        'cases': domain_cases,
                        'total_articles': len(domain_articles),
                        'total_cases': len(domain_cases),
                        'query': query_text,
                        'search_context': {
                            'duration_ms': round((end_time - start_time) * 1000, 2),
                            'kg_enhanced': True,
                            'knowledge_expansion': raw_results[0].get('knowledge_expansion', {}) if raw_results else {},
                            'fusion_method': 'knowledge_graph_enhanced'
                        }
                    }

                else:
                    logger.info("知识图谱增强引擎不可用，降级到LLM增强搜索")
                    return await self.search_documents_enhanced(query_text, articles_count, cases_count)

            except Exception as e:
                logger.error(f"知识图谱增强搜索失败: {e}")
                # 降级到LLM增强搜索
                return await self.search_documents_enhanced(query_text, articles_count, cases_count)

        except Exception as e:
            logger.error(f"知识图谱增强搜索完全失败: {e}")
            return await self._fallback_search_mixed(query_text, articles_count, cases_count)

    async def explain_search_reasoning(self, query_text: str) -> Dict[str, Any]:
        """
        解释搜索推理过程

        Args:
            query_text: 查询文本

        Returns:
            搜索推理解释
        """
        try:
            if hasattr(self.repository, 'kg_enhanced_engine') and self.repository.kg_enhanced_engine:
                explanation = await self.repository.kg_enhanced_engine.explain_search_reasoning(query_text)
                return {
                    'success': True,
                    'explanation': explanation
                }
            else:
                return {
                    'success': False,
                    'error': '知识图谱增强引擎不可用',
                    'fallback': '使用标准搜索推理'
                }

        except Exception as e:
            logger.error(f"搜索推理解释失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_kg_enhanced_status(self) -> Dict[str, Any]:
        """
        获取知识图谱增强搜索状态

        Returns:
            状态信息
        """
        try:
            has_kg_engine = (hasattr(self.repository, 'kg_enhanced_engine') and
                           self.repository.kg_enhanced_engine is not None)

            if has_kg_engine:
                stats = self.repository.kg_enhanced_engine.get_search_statistics()
            else:
                stats = None

            knowledge_graph = None
            if hasattr(self.repository, 'data_loader'):
                knowledge_graph = self.repository.data_loader.get_knowledge_graph()

            kg_stats = None
            if knowledge_graph:
                kg_stats = knowledge_graph.get_graph_statistics()

            return {
                'kg_enhancement_available': has_kg_engine,
                'kg_enhanced_engine_status': stats,
                'knowledge_graph_stats': kg_stats,
                'fallback_available': True,
                'supported_methods': ['kg_enhanced', 'three_way_fusion', 'hybrid', 'mixed'] if has_kg_engine else ['hybrid', 'mixed']
            }

        except Exception as e:
            logger.error(f"获取知识图谱增强状态失败: {e}")
            return {
                'kg_enhancement_available': False,
                'error': str(e),
                'fallback_available': True,
                'supported_methods': ['hybrid', 'mixed']
            }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'results': [],
            'total': 0,
            'query': '',
            'error': error_message
        }

