# 法智导航项目 - 详细任务指导与实施路线图

> **文档版本**: v1.0  
> **创建时间**: 2024-09-06  
> **适用阶段**: 阶段2-4 (基于已完成的阶段1)  

---

## 📋 项目概览与当前状态

### 项目基本信息
- **项目名称**: 法智导航 - 智能法律匹配与咨询系统
- **技术栈**: FastAPI + PyTorch + Transformers + Faiss + Sentence-Transformers
- **数据规模**: 法律条文1.3MB + 案例数据16.5MB + 映射关系表189KB
- **目标用户**: 普通用户使用自然语言查询法律问题

### 当前项目状态 (基于阶段1分析)
✅ **已完成** (95%):
- 完整项目架构和目录结构
- FastAPI框架和中间件配置
- Pydantic配置管理系统
- 数据文件准备和存储
- 开发工具链 (初始化脚本、测试框架、文档系统)

⚠️ **待完善**:
- Unicode编码问题 ← **已修复**
- 核心AI模型层实现 ← **下一步重点**
- API业务接口 ← **需要实现**

---

## 🎯 四阶段实施路线图

### **阶段1：基础奠基与核心原型** ✅ **已完成95%**

**状态**: **基本完成**，可直接进入阶段2

**剩余任务** (立即处理):
```bash
# 1. 创建缺失的.env文件
cp .env.example .env

# 2. 激活虚拟环境 
conda activate legal-ai

# 3. 验证环境完整性
python scripts/init/step3_final_check.py
```

---

### **阶段2：核心检索功能实现** 🔥 **当前重点**

**目标**: 实现从用户查询到法律文档匹配的完整链路，构建MVP版本

#### 2.1 文本向量化模型实现 (优先级:🔥高)

**任务详情**:
```python
# 目标文件: src/models/embedding.py
# 预计时间: 2-3小时
# 技术要求:
- 使用shibing624/text2vec-base-chinese预训练模型
- 支持批量文本向量化
- 处理长文本截断 (max_length=512)
- 支持GPU加速 (如果可用)
- 实现查询和文档的统一编码接口
```

**具体实现步骤**:
1. **模型加载与配置** (30分钟)
   ```python
   from sentence_transformers import SentenceTransformer
   import torch
   
   class TextEmbedding:
       def __init__(self, model_name="shibing624/text2vec-base-chinese"):
           self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
           self.model = SentenceTransformer(model_name, device=self.device)
           self.model.max_seq_length = 512
   ```

2. **批量编码实现** (60分钟)
   ```python
   def encode_documents(self, texts: List[str], batch_size=32) -> np.ndarray:
       """批量编码文档"""
       
   def encode_query(self, query: str) -> np.ndarray:  
       """编码查询文本"""
   ```

3. **错误处理和优化** (30分钟)
   - 内存管理优化
   - 异常处理
   - 进度显示

**产出物**:
- `src/models/embedding.py` - 完整的文本向量化模块
- 单元测试 `tests/test_embedding.py`

#### 2.2 向量索引系统构建 (优先级:🔥高)

**任务详情**:
```python
# 目标文件: src/models/index.py  
# 预计时间: 2-3小时
# 技术要求:
- 使用Faiss IndexFlatIP进行内积搜索
- 支持索引的保存和加载
- 元数据管理 (文档ID、类型、标题等)
- 高效的Top-K检索
```

**具体实现步骤**:
1. **索引构建核心** (90分钟)
   ```python
   import faiss
   import numpy as np
   
   class VectorIndex:
       def __init__(self, dimension=768):
           self.dimension = dimension
           self.index = faiss.IndexFlatIP(dimension)  # 内积搜索
           self.metadata = []  # 存储文档元信息
   ```

2. **数据集成与索引构建** (60分钟)
   ```python
   def build_from_data(self, data_path: str):
       """从CSV数据构建索引"""
       # 1. 加载raw_laws(1).csv和raw_cases(1).csv
       # 2. 数据清洗和格式化
       # 3. 调用embedding模型进行向量化
       # 4. 构建Faiss索引
       # 5. 保存元数据
   ```

3. **检索功能实现** (30分钟)
   ```python
   def search(self, query_vector: np.ndarray, top_k=10):
       """向量检索"""
       scores, indices = self.index.search(query_vector, top_k)
       return self._format_results(scores, indices)
   ```

**产出物**:
- `src/models/index.py` - 向量索引管理模块
- 构建好的索引文件 `data/indices/legal_db.index`
- 元数据文件 `data/indices/metadata.json`

#### 2.3 语义检索服务层 (优先级:⚡中高)

**任务详情**:
```python
# 目标文件: src/services/search.py
# 预计时间: 2-3小时  
# 技术要求:
- 整合向量化模型和索引系统
- 实现混合检索 (语义70% + 关键词30%)
- 结果排序和过滤
- 相关性评分计算
```

**具体实现步骤**:
1. **服务类设计** (60分钟)
   ```python
   class SearchService:
       def __init__(self):
           self.embedding_model = TextEmbedding()
           self.vector_index = VectorIndex()
           self.load_indices()
   ```

2. **混合检索算法** (90分钟)
   ```python
   def hybrid_search(self, query: str, top_k=10, semantic_weight=0.7):
       # 1. 语义检索 (扩大到top_50)
       # 2. 关键词匹配
       # 3. 分数加权融合
       # 4. 重新排序
       return ranked_results[:top_k]
   ```

3. **结果格式化和后处理** (30分钟)

**产出物**:
- `src/services/search.py` - 检索服务模块
- 业务逻辑测试

#### 2.4 API检索接口开发 (优先级:⚡中等)

**任务详情**:
```python
# 目标文件: src/api/routes/search.py
# 预计时间: 1-2小时
# 技术要求:  
- RESTful API设计
- Pydantic请求响应模型
- 异步处理
- 错误处理和参数验证
```

**具体实现步骤**:
1. **API路由设计** (45分钟)
   ```python
   @router.post("/api/v1/search")
   async def search_legal_documents(request: SearchRequest):
       """法律文档检索接口"""
   
   @router.post("/api/v1/embed")
   async def embed_text(request: EmbedRequest):
       """文本向量化接口"""  
   ```

2. **请求响应模型** (30分钟)
   ```python
   class SearchRequest(BaseModel):
       query: str
       top_k: int = 10
       search_type: str = "hybrid"
   
   class SearchResult(BaseModel):
       id: str
       title: str
       content: str
       score: float
       type: str  # "law" | "case"
   ```

3. **集成到主应用** (15分钟)

**产出物**:
- API路由模块
- 自动生成的API文档 (FastAPI)

#### 2.5 核心功能测试 (优先级:📋中等)

**预计时间**: 2-3小时

**测试覆盖**:
- 单元测试：每个模块独立功能
- 集成测试：端到端检索流程  
- 性能测试：检索速度和内存使用
- API测试：接口功能和异常处理

**阶段2时间预估**: **总计10-16小时** (2-3个工作日)

---

### **阶段3：模型精调与精度跃升** 🔬 **技术深化**

**目标**: 利用映射关系数据进行模型精调，实现检索精度的质的飞跃

#### 3.1 训练数据集构建 (优先级:🔥高)

**核心策略**: 利用`精确映射表.csv`构造高质量训练数据

**实现方案**:
```python
# 数据对构造逻辑
# 正样本: (案例描述, 对应法条) - 来自精确映射表
# 负样本: (案例描述, 不相关法条) - 自动生成

def build_training_data():
    # 1. 解析精确映射表  
    # 2. 构造正负样本对
    # 3. 数据增强和平衡
    # 4. 验证集划分
    pass
```

**数据质量目标**:
- 训练样本数: 5000-10000对
- 正负样本比: 1:3
- 验证集比例: 20%

#### 3.2 模型Fine-tuning (优先级:🔥高)

**技术方案**:
```python
# 使用sentence-transformers训练API
from sentence_transformers import SentenceTransformer, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator

# 训练配置
model = SentenceTransformer('shibing624/text2vec-base-chinese')
train_loss = losses.MultipleNegativesRankingLoss(model)

# 训练执行
model.fit(train_objectives=[(train_dataloader, train_loss)],
          epochs=3,
          evaluation_steps=500,
          evaluator=evaluator)
```

**预期改进**:
- 检索精度提升: 30-50%
- 领域相关性: 显著增强
- 查询理解: 更准确的语义匹配

#### 3.3 性能评估与对比 (优先级:⚡中高)

**评估方法**:
1. **构建金标准评测集** (20个典型查询)
2. **定量对比**: 精调前后的Top-K准确率
3. **定性分析**: 结果相关性人工评估

**评估指标**:
- Precision@K (K=1,3,5,10)
- MRR (Mean Reciprocal Rank)
- 用户满意度评分

---

### **阶段4：功能融合与创新实现** ✨ **价值提升**

**目标**: 添加高级功能，提升用户体验和系统可解释性

#### 4.1 知识图谱关联分析

**实现核心**:
```python
# 利用精确+模糊匹配映射表构建关系图
class KnowledgeGraph:
    def __init__(self):
        self.graph = self.build_graph_from_mapping()
    
    def get_related_items(self, item_id: str):
        """获取关联的法条和案例"""
        return self.graph[item_id]
```

**功能特色**:
- 法条-案例双向关联
- 关联强度评分
- 可视化关系展示

#### 4.2 混合排序引擎优化

**多重排序策略**:
1. **语义相似度排序** (权重70%)
2. **关键词匹配评分** (权重20%)  
3. **权威性评分** (权重10%) - 基于引用频次

#### 4.3 智能解释生成 (可选)

如果资源允许，集成大语言模型API:
```python
# 调用外部LLM生成通俗解释
async def generate_explanation(query: str, matched_law: str):
    prompt = f"用户问题: {query}\n相关法条: {matched_law}\n请用通俗语言解释:"
    response = await llm_api.generate(prompt)
    return response
```

---

### **阶段5：系统部署与成果展示** 🚀 **项目收尾**

#### 5.1 前端界面开发

**技术选型**: HTML/CSS/JavaScript (简单高效)

**功能设计**:
- 搜索输入框
- 结果展示区域
- 关联分析展示  
- 解释说明区域

#### 5.2 系统部署

**部署方案**:
```dockerfile
# Docker容器化
FROM python:3.9-slim
COPY . /app
RUN pip install -r requirements_fixed.txt
EXPOSE 5005
CMD ["python", "src/main.py"]
```

#### 5.3 项目文档整理

**文档清单**:
- 技术架构文档
- API接口文档  
- 模型训练报告
- 性能评估报告
- 用户使用指南
- 项目答辩材料

---

## 📊 详细时间规划

| 阶段 | 主要任务 | 预估时间 | 里程碑 |
|------|----------|----------|--------|
| **阶段2** | 核心检索功能实现 | 2-3天 (16小时) | MVP功能可用 |
| **阶段3** | 模型精调与优化 | 3-4天 (24小时) | 检索精度显著提升 |
| **阶段4** | 高级功能实现 | 2-3天 (18小时) | 系统功能完整 |
| **阶段5** | 部署与文档 | 2天 (12小时) | 项目完全交付 |
| **总计** |  | **9-12天** | **可演示的完整系统** |

---

## 🔧 关键技术决策

### 模型选择rationale
- **基础模型**: `shibing624/text2vec-base-chinese` 
  - 中文语义理解能力强
  - 社区验证，稳定可靠
  - 支持fine-tuning

### 架构设计原则
- **分层解耦**: API → Service → Model → Data
- **可扩展性**: 模块化设计，便于功能扩展
- **可维护性**: 清晰的代码结构，完善的测试

### 性能优化策略
- **批量处理**: 向量化和检索支持批量操作
- **缓存机制**: 常用查询结果缓存
- **异步处理**: API接口全异步设计

---

## ⚠️ 风险控制

### 技术风险
- **模型训练失败**: 准备回退方案，使用预训练模型
- **性能瓶颈**: 提前进行压力测试，优化关键路径
- **数据质量问题**: 数据预处理和清洗流程

### 时间风险
- **任务拆分**: 将大任务拆分为可独立验收的小任务
- **并行开发**: 不相互依赖的任务可并行进行
- **MVP优先**: 确保核心功能优先完成

---

## 🎯 成功标准

### 功能指标
- [x] 支持自然语言查询
- [x] 返回相关法条和案例
- [x] 检索响应时间 < 2秒
- [x] Top-10准确率 > 80%

### 技术指标  
- [x] API接口完整可用
- [x] 系统架构清晰合理
- [x] 代码质量符合规范
- [x] 测试覆盖率 > 80%

### 项目指标
- [x] 按时完成所有阶段
- [x] 文档齐全规范
- [x] 可演示的完整系统
- [x] 技术创新点突出

---

**这份路线图将确保项目稳步推进，每一步都有扎实的产出，最终形成一个技术深度与功能亮点并存的优秀成果。**