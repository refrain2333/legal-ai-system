# 任务2：实施第二阶段 - LLM双引擎增强

**目标**: 集成Query2doc和HyDE技术，借助大语言模型的生成能力填补Lawformer语义理解鸿沟，从根本上解决口语化查询理解问题。

**前置条件**: 第一阶段混合搜索已完成并通过验收

**关联文档**: `docs/优化/法智导航_核心优化策略概览.md`

**预计用时**: 3天

**核心理念**: "LLM增强"拔上限，突破语义理解瓶颈

---

## 核心工作分解 (WBS)

### 1. LLM API集成与配置 (0.5天)

#### 任务1.1: API选择与环境配置
- [ ] **选择LLM服务商**:
  - 主选：OpenAI GPT-3.5-turbo (成本低，效果好)
  - 备选：Google Gemini 2.5 Flash-Lite (免费额度高)
- [ ] **安装依赖**:
  ```bash
  pip install openai google-generativeai
  ```
- [ ] **API密钥配置**: 在`.env`文件中添加API密钥

#### 任务1.2: LLM客户端封装
- [ ] **创建文件**: `src/infrastructure/llm/llm_client.py`
- **核心功能**:
  ```python
  class LLMClient:
      def __init__(self, provider: str = "openai"):
          self.provider = provider
          self.client = self._initialize_client()
          self.request_timeout = 30
          self.max_retries = 2

      async def generate_text(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
          """统一的文本生成接口"""
          pass

      def _handle_rate_limits(self):
          """处理API频率限制"""
          pass

      def _fallback_to_backup(self):
          """备用API降级机制"""
          pass
  ```

### 2. Query2doc技术实现 (1天)

#### 任务2.1: Query2doc核心逻辑
- [ ] **创建文件**: `src/infrastructure/llm/query2doc_enhancer.py`
- **法律专用提示模板**:
  ```python
  class Query2docEnhancer:
      def __init__(self, llm_client: LLMClient):
          self.llm_client = llm_client
          self.legal_prompt_template = """
          用户查询："{query}"

          请生成一个与此查询最相关的法律文档片段（50-100字），要求：
          1. 包含专业的法律术语
          2. 描述相关的法条或案例要素
          3. 使用标准的法律表述
          4. 如涉及罪名，请明确指出

          生成的法律文档片段：
          """

      async def enhance_query(self, user_query: str) -> str:
          """使用Query2doc技术增强查询"""
          try:
              # 调用LLM生成假设文档
              prompt = self.legal_prompt_template.format(query=user_query)
              pseudo_doc = await self.llm_client.generate_text(
                  prompt,
                  max_tokens=120
              )

              if pseudo_doc:
                  # 组合原查询和扩展内容
                  enhanced_query = f"{user_query} [SEP] {pseudo_doc.strip()}"
                  logger.info(f"Query2doc增强: '{user_query}' -> '{pseudo_doc[:50]}...'")
                  return enhanced_query
              else:
                  return user_query

          except Exception as e:
              logger.error(f"Query2doc增强失败: {e}")
              return user_query  # 降级处理
  ```

#### 任务2.2: 向量搜索集成
- [ ] **修改文件**: `src/infrastructure/search/vector_search_engine.py`
- **集成Query2doc搜索**:
  ```python
  def query2doc_search(self, query: str, top_k: int = 20) -> List[Dict]:
      """Query2doc增强搜索"""
      try:
          # 生成增强查询
          enhanced_query = self.query2doc_enhancer.enhance_query(query)

          # 执行向量搜索
          results = self.search(enhanced_query, top_k, include_content=True)

          # 标记来源
          for result in results:
              result['source'] = 'query2doc'
              result['enhanced_query'] = enhanced_query

          return results

      except Exception as e:
          logger.error(f"Query2doc搜索失败: {e}")
          # 降级到原始搜索
          return self.search(query, top_k, include_content=True)
  ```

### 3. HyDE技术实现 (1天)

#### 任务3.1: HyDE核心逻辑
- [ ] **创建文件**: `src/infrastructure/llm/hyde_enhancer.py`
- **答案导向检索实现**:
  ```python
  class HyDEEnhancer:
      def __init__(self, llm_client: LLMClient):
          self.llm_client = llm_client
          self.legal_answer_template = """
          作为专业法律AI助手，请回答用户问题："{query}"

          要求：
          1. 回答要专业准确，像法律解释或案例分析摘要
          2. 包含相关法条信息（如果适用）
          3. 如涉及具体罪名，请明确指出
          4. 控制在150字以内
          5. 使用标准法律术语

          专业回答：
          """

      async def generate_hypothetical_answer(self, user_query: str) -> str:
          """生成假设性法律专业回答"""
          try:
              prompt = self.legal_answer_template.format(query=user_query)
              hypothetical_answer = await self.llm_client.generate_text(
                  prompt,
                  max_tokens=200
              )

              if hypothetical_answer:
                  logger.info(f"HyDE生成答案: '{user_query}' -> '{hypothetical_answer[:50]}...'")
                  return hypothetical_answer.strip()
              else:
                  return user_query

          except Exception as e:
              logger.error(f"HyDE生成失败: {e}")
              return user_query
  ```

#### 任务3.2: HyDE搜索集成
- [ ] **在vector_search_engine.py中添加**:
  ```python
  def hyde_search(self, query: str, top_k: int = 20) -> List[Dict]:
      """HyDE答案导向搜索"""
      try:
          # 生成假设性答案
          hypothetical_answer = self.hyde_enhancer.generate_hypothetical_answer(query)

          # 用假设答案进行向量搜索
          results = self.search(hypothetical_answer, top_k, include_content=True)

          # 标记来源
          for result in results:
              result['source'] = 'hyde'
              result['hypothetical_answer'] = hypothetical_answer

          return results

      except Exception as e:
          logger.error(f"HyDE搜索失败: {e}")
          return self.search(query, top_k, include_content=True)
  ```

### 4. 三路召回融合架构 (1天)

#### 任务4.1: 多路召回引擎
- [ ] **创建文件**: `src/infrastructure/search/multi_retrieval_engine.py`
- **三路并行搜索**:
  ```python
  class MultiRetrievalEngine:
      def __init__(self, vector_engine, data_loader):
          self.vector_engine = vector_engine
          self.data_loader = data_loader

      async def three_way_retrieval(self, query: str, top_k: int = 20) -> List[Dict]:
          """三路召回融合"""
          results_dict = {}

          try:
              # 路径1: 混合搜索 (第一阶段的成果)
              hybrid_results = self.vector_engine.hybrid_search(query, top_k * 2)
              self._merge_results(results_dict, hybrid_results, weight=0.4, source="hybrid")

              # 路径2: Query2doc增强搜索
              q2d_results = self.vector_engine.query2doc_search(query, top_k * 2)
              self._merge_results(results_dict, q2d_results, weight=0.35, source="query2doc")

              # 路径3: HyDE答案导向搜索
              hyde_results = self.vector_engine.hyde_search(query, top_k * 2)
              self._merge_results(results_dict, hyde_results, weight=0.25, source="hyde")

              # 最终融合排序
              final_results = self._final_rank_fusion(results_dict, top_k)

              logger.info(f"三路召回完成: {len(final_results)}个融合结果")
              return final_results

          except Exception as e:
              logger.error(f"三路召回失败: {e}")
              # 降级到混合搜索
              return self.vector_engine.hybrid_search(query, top_k)

      def _merge_results(self, results_dict: Dict, new_results: List, weight: float, source: str):
          """合并搜索结果到结果字典"""
          for result in new_results:
              doc_id = result['id']
              score = result.get('similarity', 0) * weight

              if doc_id in results_dict:
                  results_dict[doc_id]['score'] += score
                  results_dict[doc_id]['sources'].append(source)
              else:
                  results_dict[doc_id] = {
                      'score': score,
                      'sources': [source],
                      'original_result': result
                  }

      def _final_rank_fusion(self, results_dict: Dict, top_k: int) -> List[Dict]:
          """最终排序融合"""
          sorted_results = sorted(
              results_dict.items(),
              key=lambda x: x[1]['score'],
              reverse=True
          )

          final_results = []
          for doc_id, meta in sorted_results[:top_k]:
              result = meta['original_result'].copy()
              result['fusion_score'] = meta['score']
              result['sources'] = meta['sources']
              result['confidence'] = len(meta['sources']) / 3.0  # 多路验证置信度
              final_results.append(result)

          return final_results
  ```

#### 任务4.2: 服务层集成
- [ ] **修改文件**: `src/services/search_service.py`
- **集成三路召回**:
  ```python
  async def search_documents_enhanced(self, query_text: str, articles_count: int = 5, cases_count: int = 5):
      """LLM增强版搜索"""
      start_time = time.time()

      try:
          # 使用三路召回引擎
          if hasattr(self, 'multi_retrieval_engine'):
              raw_results = await self.multi_retrieval_engine.three_way_retrieval(
                  query_text,
                  top_k=(articles_count + cases_count) * 2
              )
          else:
              # 降级到混合搜索
              raw_results = self.repository.search_engine.hybrid_search(
                  query_text, (articles_count + cases_count) * 2
              )

          # 分离和转换结果
          articles_results = [r for r in raw_results if 'article' in r['id']][:articles_count]
          cases_results = [r for r in raw_results if 'case' in r['id']][:cases_count]

          domain_articles = await self._convert_to_domain_objects(articles_results)
          domain_cases = await self._convert_to_domain_objects(cases_results)

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

      except Exception as e:
          logger.error(f"LLM增强搜索失败: {e}")
          # 渐进式降级
          return await self._progressive_fallback_search(query_text, articles_count, cases_count)
  ```

### 5. 配置与监控 (0.5天)

#### 任务5.1: 配置文件更新
- [ ] **修改**: `src/config/settings.py`
  ```python
  class Settings(BaseSettings):
      # LLM配置
      llm_provider: str = "openai"  # "openai" or "gemini"
      openai_api_key: str = ""
      gemini_api_key: str = ""

      # Query2doc配置
      enable_query2doc: bool = True
      query2doc_max_tokens: int = 120
      query2doc_temperature: float = 0.3

      # HyDE配置
      enable_hyde: bool = True
      hyde_max_tokens: int = 200
      hyde_temperature: float = 0.2

      # 多路召回权重
      hybrid_weight: float = 0.4
      query2doc_weight: float = 0.35
      hyde_weight: float = 0.25

      # API调用限制
      llm_request_timeout: int = 30
      llm_max_retries: int = 2
      daily_llm_limit: int = 1000
  ```

#### 任务5.2: 成本监控
- [ ] **创建**: `src/infrastructure/llm/cost_monitor.py`
  ```python
  class LLMCostMonitor:
      def __init__(self):
          self.daily_requests = 0
          self.total_tokens = 0
          self.estimated_cost = 0.0

      def track_request(self, tokens_used: int, model: str):
          """跟踪API调用成本"""
          self.daily_requests += 1
          self.total_tokens += tokens_used

          # GPT-3.5-turbo价格估算
          if model == "gpt-3.5-turbo":
              self.estimated_cost += tokens_used * 0.000001  # $0.001/1K tokens

          # 预警机制
          if self.daily_requests > 800:
              logger.warning(f"LLM调用接近每日限制: {self.daily_requests}/1000")

      def get_daily_report(self) -> Dict:
          return {
              'requests': self.daily_requests,
              'tokens': self.total_tokens,
              'estimated_cost': round(self.estimated_cost, 4)
          }
  ```

## 测试与验证

### 单元测试
- [ ] **创建**: `tests/test_llm_enhancement.py`
- **测试用例**:
  ```python
  async def test_query2doc_enhancement():
      # 测试Query2doc查询增强
      enhancer = Query2docEnhancer(mock_llm_client)
      enhanced = await enhancer.enhance_query("偷东西怎么判")
      assert "盗窃罪" in enhanced or "法律" in enhanced

  async def test_hyde_generation():
      # 测试HyDE假设答案生成
      enhancer = HyDEEnhancer(mock_llm_client)
      answer = await enhancer.generate_hypothetical_answer("交通肇事逃逸量刑")
      assert len(answer) > 20  # 确保生成了内容

  async def test_three_way_retrieval():
      # 测试三路召回融合
      engine = MultiRetrievalEngine(mock_vector_engine, mock_data_loader)
      results = await engine.three_way_retrieval("盗窃罪判多少年", 10)
      assert len(results) <= 10
      assert all('confidence' in r for r in results)
  ```

### 效果验证
- [ ] **专项测试查询**:
  ```python
  llm_test_queries = [
      "开车撞死人没跑要坐牢吗",     # 口语化案情描述
      "偷了一千块钱怎么判",        # 数量化犯罪描述
      "打架把人打成轻伤",          # 结果导向描述
      "网上骗钱被抓了",            # 新兴犯罪形式
      "醉驾撞人逃跑的处罚"         # 复合犯罪情节
  ]
  ```

### A/B测试
- [ ] **对比验证**:
  - 基准：第一阶段混合搜索结果
  - 测试：第二阶段LLM增强结果
  - 指标：准确率、相关性、用户满意度

## 验收标准

### 功能验收
- [ ] LLM API集成成功，支持OpenAI和Gemini双选
- [ ] Query2doc和HyDE技术正常工作，生成质量符合预期
- [ ] 三路召回融合架构运行稳定
- [ ] 降级机制完善，API失败时自动降级

### 性能验收
- [ ] LLM调用响应时间 < 3秒 (95%请求)
- [ ] 口语化查询理解能力明显提升
- [ ] "案例→法条"搜索性能显著改善
- [ ] 综合评估得分 > 50%

### 成本控制
- [ ] 日均LLM调用成本 < $5
- [ ] API调用成功率 > 95%
- [ ] 降级机制有效，不影响系统可用性

### 代码质量
- [ ] 所有新增代码通过单元测试
- [ ] 完善的错误处理和日志记录
- [ ] 配置灵活，支持运行时调整参数
- [ ] 成本监控功能正常

## 风险控制

### 潜在风险
1. **API稳定性**: LLM服务可能出现延迟或失败
2. **成本控制**: API调用费用可能超预算
3. **质量一致性**: LLM生成内容质量可能不稳定
4. **响应时间**: 增加LLM调用可能影响响应速度

### 应对措施
1. **多重降级**: LLM失败→混合搜索→语义搜索→BM25搜索
2. **成本监控**: 实时跟踪API使用量和成本
3. **质量控制**: 设置生成内容的最小长度和关键词检查
4. **异步优化**: 使用异步调用和连接池优化响应时间
5. **缓存策略**: 对常见查询的LLM结果进行缓存

## 下一步准备

完成第二阶段后，为第三阶段知识图谱做准备：
- [ ] 分析现有案例数据中的罪名-法条关系
- [ ] 设计轻量级知识图谱存储结构
- [ ] 准备关系抽取和图谱构建算法

---

**成功标志**: 当用户输入"开车撞死人没跑要坐牢吗"时，系统能通过Query2doc生成专业法律文档片段，通过HyDE生成标准法律回答，并融合三路搜索结果，准确返回交通肇事罪相关法条和案例，且"案例→法条"搜索性能显著提升。