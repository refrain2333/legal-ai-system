# 基础设施层模块文档

## 模块概述

`src/infrastructure/` 是法智导航系统的**技术实现层**，负责提供所有技术细节的具体实现，将领域层的抽象接口转化为实际可运行的技术方案。

## 文件结构

```
src/infrastructure/
├── __init__.py              # 模块导出
├── repositories.py          # 存储库具体实现 (核心)
├── search/                  # 搜索引擎技术实现
│   ├── __init__.py         # 搜索子包导出
│   └── vector_search_engine.py  # 增强语义搜索引擎
└── storage/                 # 数据存储技术实现
    ├── __init__.py         # 存储子包导出
    ├── data_loader.py      # 统一数据加载管理器
    └── legacy_compatibility.py  # 旧数据兼容性处理
```

## 核心组件

### 1. LegalDocumentRepository - 存储库实现
**职责**: 实现领域层的 `ILegalDocumentRepository` 接口

```python
class LegalDocumentRepository(ILegalDocumentRepository):
    """法律文档存储库具体实现"""
    
    def __init__(self):
        self.search_engine = EnhancedSemanticSearch()  # 搜索引擎
        self.data_loader = get_data_loader()           # 数据加载器
```

**主要方法**:
- `search_documents()`: 执行搜索并返回领域对象
- `get_document_by_id()`: 根据ID获取单个文档
- `get_documents_by_ids()`: 批量获取文档
- `get_total_document_count()`: 获取文档统计
- `is_ready()`: 检查存储库是否就绪

### 2. EnhancedSemanticSearch - 搜索引擎
**职责**: 提供语义搜索的技术实现

```python
class EnhancedSemanticSearch:
    """增强的语义搜索引擎"""
    
    def search(self, query: str, top_k: int = 10):
        # 编码查询文本 -> 计算相似度 -> 返回排序结果
```

**核心功能**:
- 向量编码和余弦相似度计算
- 法条和案例分别搜索再合并
- 内容延迟加载和元数据丰富
- 性能统计和状态监控

### 3. DataLoader - 数据加载器
**职责**: 统一管理所有数据加载和缓存

```python
class DataLoader:
    """统一数据加载管理器"""
    
    def load_vectors(self):        # 加载向量数据
    def load_original_data(self):  # 加载原始数据  
    def load_model(self):          # 加载语义模型
    def get_article_content(self): # 获取法条内容
    def get_case_content(self):    # 获取案例内容
```

**数据管理**:
- 向量数据 (`criminal_articles_vectors.pkl`, `criminal_cases_vectors.pkl`)
- 原始数据 (`criminal_articles.pkl`, `criminal_cases.pkl`)
- 语义模型 (`shibing624/text2vec-base-chinese`)
- 内容缓存和内存管理

## 使用方法

### 基本使用
```python
from src.infrastructure import get_legal_document_repository

# 获取存储库实例
repository = get_legal_document_repository()

# 执行搜索
from src.domains.value_objects import SearchQuery
query = SearchQuery(query_text="盗窃罪量刑")
results, context = await repository.search_documents(query)

# 获取单个文档
document = await repository.get_document_by_id("article_264")
```

### 直接使用技术组件
```python
from src.infrastructure.search import get_enhanced_search_engine
from src.infrastructure.storage import get_data_loader

# 使用搜索引擎
engine = get_enhanced_search_engine()
raw_results = engine.search("故意伤害", top_k=5)

# 使用数据加载器
loader = get_data_loader()
content = loader.get_case_content("case_000001")
```

### 初始化数据
```python
# 手动初始化所有数据
loader = get_data_loader()
stats = loader.load_all()
print(f"加载完成: {stats['total_documents']} 个文档")

# 检查系统状态
repository = get_legal_document_repository()
if repository.is_ready():
    print("系统准备就绪")
else:
    print("系统未就绪，需要初始化")
```

## 配置和路径

### 数据文件路径
```python
# 默认数据路径 (相对于项目根目录)
data/processed/vectors/criminal_articles_vectors.pkl
data/processed/vectors/criminal_cases_vectors.pkl
data/processed/criminal/criminal_articles.pkl  
data/processed/criminal/criminal_cases.pkl
```

### 模型配置
- 默认模型: `shibing624/text2vec-base-chinese`
- 向量维度: 768
- 自动下载和缓存

## 设计理念

### 1. 依赖倒置原则
```python
# 基础设施层依赖领域层接口
from ..domains.repositories import ILegalDocumentRepository

class LegalDocumentRepository(ILegalDocumentRepository):  # 实现接口
    pass
```

### 2. 技术细节封装
- 所有文件IO操作集中处理
- 向量计算和模型推理统一管理
- 错误处理和日志记录标准化

### 3. 性能优化
- **内容缓存**: 减少重复IO操作
- **懒加载**: 按需加载数据，节省内存
- **线程安全**: 使用锁确保并发安全

### 4. 兼容性处理
- 处理旧版pickle文件格式
- 支持多种ID命名约定
- 向后兼容性保障

## 扩展和定制

### 更换数据源
```python
# 实现新的存储库
class DatabaseRepository(ILegalDocumentRepository):
    def __init__(self):
        self.db_connection = create_db_connection()
    
    async def search_documents(self, query):
        # 使用数据库实现搜索
        return database_search_results
```

### 自定义搜索引擎
```python
# 实现新的搜索引擎
class CustomSearchEngine:
    def search(self, query, top_k):
        # 自定义搜索算法
        return custom_results
```

## 故障排除

### 常见问题
1. **数据文件不存在**: 检查 `data/processed/` 目录文件
2. **模型加载失败**: 检查网络连接和模型名称
3. **内存不足**: 调整缓存大小或使用懒加载

### 调试方法
```python
# 获取详细状态信息
loader = get_data_loader()
stats = loader.get_stats()
print(f"内存使用: {stats['memory_usage_mb']}MB")
print(f"缓存内容: {stats['cached_contents']} 项")

# 清空缓存
loader.clear_cache()
```

## 性能指标

| 指标 | 典型值 | 说明 |
|------|--------|------|
| 模型加载时间 | 2-5秒 | 首次加载语义模型 |
| 向量加载时间 | 1-3秒 | 加载预计算向量 |
| 搜索响应时间 | 50-200ms | 单次搜索耗时 |
| 内存使用 | 500-800MB | 模型+向量数据内存 |
| 缓存命中率 | >80% | 内容缓存效率 |

---

**版本**: 1.0.0  
**最后更新**: 2025-09-16
