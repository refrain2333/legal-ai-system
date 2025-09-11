# 法智导航系统 - 技术架构文档

## 🏗️ 系统概览

法智导航是一个基于深度学习的智能法律检索系统，采用现代化的微服务架构和AI技术栈，实现自然语言到法律条文的精准匹配。

### 核心技术栈
- **后端框架**: FastAPI + Python 3.9+
- **AI框架**: PyTorch + Transformers + Sentence-Transformers
- **向量检索**: Faiss
- **数据处理**: Pandas + NumPy
- **配置管理**: PyYAML + Pydantic
- **日志系统**: Loguru
- **容器化**: Docker
- **前端**: HTML/CSS/JavaScript (简洁版)

---

## 🎯 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │────│   API网关       │────│   业务逻辑层     │
│  Web UI         │    │  FastAPI        │    │  Service Layer  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ↓
                       ┌─────────────────┐
                       │   AI模型层      │
                       │  Model Layer    │
                       └─────────────────┘
                                ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   向量索引      │    │   数据存储      │    │   配置管理      │
│  Faiss Index    │    │  CSV/Pickle     │    │  Config Files   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件

#### 1. 数据处理层 (Data Processing Layer)
```python
data/
├── raw/                    # 原始数据
│   ├── raw_laws(1).csv    # 法律条文原始数据
│   ├── raw_cases(1).csv   # 案例原始数据
│   └── 精确映射表.csv      # 条文案例映射关系
└── processed/             # 处理后数据
    ├── unified_kb.csv     # 统一知识库
    ├── embeddings.npy     # 向量表示
    └── metadata.json      # 元数据信息
```

**职责**:
- 数据清洗和标准化
- 文本预处理和分词
- 统一数据格式和编码

#### 2. AI模型层 (AI Model Layer)
```python
src/models/
├── embedder.py           # 文本向量化
├── retriever.py         # 检索引擎
├── trainer.py           # 模型训练
├── evaluator.py         # 性能评估
└── knowledge_graph.py   # 知识图谱
```

**核心模块**:

**a) 文本嵌入模块 (Text Embedder)**
```python
class LegalEmbedder:
    """法律文本向量化器"""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model = SentenceTransformer(model_name)
        self.device = device
        
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """将文本转换为向量"""
        embeddings = self.model.encode(
            texts, 
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        return embeddings
```

**b) 检索引擎 (Retriever)**
```python
class LegalRetriever:
    """法律文档检索器"""
    
    def __init__(self, index_path: str, embedder: LegalEmbedder):
        self.index = faiss.read_index(index_path)
        self.embedder = embedder
        self.metadata = self._load_metadata()
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """检索相关文档"""
        # 1. 查询向量化
        query_embedding = self.embedder.embed_texts([query])
        
        # 2. 向量检索
        scores, indices = self.index.search(query_embedding, top_k)
        
        # 3. 结果整理
        results = []
        for score, idx in zip(scores[0], indices[0]):
            result = self.metadata[idx].copy()
            result['score'] = float(score)
            results.append(result)
        
        return results
```

#### 3. API服务层 (API Service Layer)
```python
src/api/
├── main.py              # FastAPI应用入口
├── endpoints.py         # API路由定义
├── models.py           # Pydantic数据模型
├── dependencies.py     # 依赖注入
└── middleware.py       # 中间件
```

**API架构**:
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    include_laws: bool = True
    include_cases: bool = True

@app.post("/api/v1/search")
async def search_documents(
    request: SearchRequest,
    retriever: LegalRetriever = Depends(get_retriever)
):
    results = retriever.search(
        query=request.query,
        top_k=request.top_k
    )
    return {"status": "success", "data": {"results": results}}
```

#### 4. 配置管理层 (Configuration Layer)
```yaml
# config/config.yaml
model:
  pretrained_model_name: "shibing624/text2vec-base-chinese"
  embedding_dim: 768
  max_sequence_length: 512

retrieval:
  index_type: "IndexFlatIP"
  top_k: 10
  search_batch_size: 32

api:
  host: "0.0.0.0"
  port: 8000
  timeout_seconds: 30
```

---

## 🧠 AI算法设计

### 1. 语义向量化 (Semantic Embedding)

**算法流程**:
```
原始文本 → 文本预处理 → BERT编码 → 向量表示 → 标准化
```

**技术细节**:
- **预训练模型**: shibing624/text2vec-base-chinese
- **向量维度**: 768维
- **最大序列长度**: 512 tokens
- **标准化方法**: L2 normalization

### 2. 向量检索 (Vector Retrieval)

**索引结构**:
```python
# Faiss索引配置
index = faiss.IndexFlatIP(768)  # 内积搜索
index = faiss.IndexIVFFlat(quantizer, 768, nlist)  # 倒排索引（大数据集）
```

**检索策略**:
1. **粗召回**: Faiss快速检索Top-K候选
2. **精排序**: 语义相似度 + 关键词匹配
3. **后处理**: 去重、关联分析、结果增强

### 3. 混合排序算法 (Hybrid Ranking)

```python
def hybrid_ranking(query: str, candidates: List[Dict], alpha: float = 0.7):
    """混合排序：语义相似度 + 关键词匹配"""
    
    # 1. 语义相似度得分 (70%)
    semantic_scores = [doc['semantic_score'] for doc in candidates]
    
    # 2. 关键词匹配得分 (30%)  
    keyword_scores = []
    query_keywords = extract_keywords(query)
    
    for doc in candidates:
        doc_keywords = extract_keywords(doc['content'])
        keyword_score = jaccard_similarity(query_keywords, doc_keywords)
        keyword_scores.append(keyword_score)
    
    # 3. 加权融合
    final_scores = []
    for sem_score, kw_score in zip(semantic_scores, keyword_scores):
        final_score = alpha * sem_score + (1 - alpha) * kw_score
        final_scores.append(final_score)
    
    # 4. 重新排序
    sorted_indices = np.argsort(final_scores)[::-1]
    return [candidates[i] for i in sorted_indices]
```

---

## 📊 数据架构

### 1. 数据模型

**统一知识库结构**:
```python
@dataclass
class LegalDocument:
    id: str                    # 唯一标识符
    type: str                 # 类型: "law" | "case"
    title: str                # 标题
    content: str              # 正文内容
    category: str             # 分类
    source: str               # 来源
    keywords: List[str]       # 关键词
    created_date: datetime    # 创建时间
    embedding: np.ndarray     # 向量表示
    related_ids: List[str]    # 关联文档ID
```

**映射关系模型**:
```python
@dataclass
class DocumentMapping:
    law_id: str              # 法条ID
    case_id: str             # 案例ID
    relation_type: str       # 关系类型
    confidence: float        # 置信度
    source: str              # 映射来源
```

### 2. 数据流转

```
原始CSV数据 → 数据清洗 → 统一格式 → 向量化 → 索引构建 → 服务部署
     ↓            ↓          ↓         ↓         ↓         ↓
   raw_data → clean_data → kb_data → embeddings → index → api
```

**处理管道**:
```python
class DataPipeline:
    """数据处理管道"""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedder = LegalEmbedder(config.model.name)
    
    def process(self):
        # 1. 加载原始数据
        raw_data = self.load_raw_data()
        
        # 2. 数据清洗
        clean_data = self.clean_data(raw_data)
        
        # 3. 文本向量化
        embeddings = self.embedder.embed_texts(clean_data['content'])
        
        # 4. 构建索引
        index = self.build_index(embeddings)
        
        # 5. 保存结果
        self.save_results(clean_data, embeddings, index)
```

---

## 🚀 性能优化

### 1. 模型优化

**量化加速**:
```python
# 模型量化（未来版本）
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)
```

**批处理优化**:
```python
def batch_embed(texts: List[str], batch_size: int = 32):
    """批量向量化优化"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch_texts)
        embeddings.extend(batch_embeddings)
    return np.array(embeddings)
```

### 2. 索引优化

**分层索引**:
```python
# 大数据集使用IVF索引
nlist = 100  # 聚类中心数量
quantizer = faiss.IndexFlatL2(768)
index = faiss.IndexIVFFlat(quantizer, 768, nlist)
index.train(embeddings)
```

**GPU加速**:
```python
# GPU索引加速
if torch.cuda.is_available():
    res = faiss.StandardGpuResources()
    gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
```

### 3. 缓存策略

**多级缓存**:
```python
# 1. 内存缓存（热点查询）
from cachetools import TTLCache
query_cache = TTLCache(maxsize=1000, ttl=3600)

# 2. 向量缓存（计算结果）
embedding_cache = {}

# 3. 结果缓存（最终结果）
@lru_cache(maxsize=500)
def cached_search(query_hash: str) -> List[Dict]:
    # 缓存搜索结果
    pass
```

---

## 🔐 安全架构

### 1. 数据安全

**敏感信息保护**:
- 数据脱敏处理
- 访问权限控制
- 传输加密（HTTPS）
- 存储加密

**配置安全**:
```python
# 环境变量管理
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = os.getenv("API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
```

### 2. API安全

**请求限制**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/search")
@limiter.limit("100/minute")  # 每分钟最多100次请求
async def search_endpoint():
    pass
```

---

## 📈 监控和日志

### 1. 系统监控

**性能指标**:
- API响应时间
- 模型推理耗时
- 系统资源使用率
- 错误率和成功率

**监控代码**:
```python
import time
import psutil
from prometheus_client import Counter, Histogram

# 指标定义
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request latency')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(process_time)
    
    return response
```

### 2. 日志系统

**日志配置**:
```python
from loguru import logger

logger.add(
    "logs/api.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    compression="zip"
)

# 使用示例
logger.info("用户查询: {}", query)
logger.error("模型加载失败: {}", error)
```

---

## 🔧 部署架构

### 1. 容器化部署

**Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose**:
```yaml
version: '3.8'
services:
  legal-ai:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - legal-ai
```

### 2. 扩展部署

**负载均衡**:
- Nginx反向代理
- 多实例部署
- 健康检查机制

**自动扩缩容**:
- 基于CPU/内存使用率
- 基于请求队列长度
- Kubernetes HPA

---

## 📋 开发路线图

### 阶段1: 基础架构 ✅
- [x] 项目结构搭建
- [x] 配置管理系统
- [x] 基础API框架
- [x] 数据处理管道

### 阶段2: 核心功能 🔄
- [ ] 预训练模型集成
- [ ] 向量检索引擎
- [ ] API接口实现
- [ ] 基础性能测试

### 阶段3: 模型优化 📋
- [ ] 领域数据构建
- [ ] 模型精调训练
- [ ] 性能评估体系
- [ ] 混合排序算法

### 阶段4: 功能增强 📋
- [ ] 知识图谱构建
- [ ] 智能解释功能
- [ ] 高级过滤器
- [ ] 用户界面开发

### 阶段5: 生产就绪 📋
- [ ] 性能优化
- [ ] 安全加固
- [ ] 监控告警
- [ ] 文档完善

---

## 🎯 架构优势

1. **可扩展性**: 模块化设计，易于功能扩展
2. **高性能**: 向量检索 + 缓存优化
3. **可维护性**: 清晰的分层架构和代码规范
4. **灵活性**: 配置驱动，支持多种部署方式
5. **可靠性**: 完善的错误处理和监控体系

---

**📝 说明**: 本文档会随着系统开发进展持续更新，确保架构设计与实际实现保持一致。