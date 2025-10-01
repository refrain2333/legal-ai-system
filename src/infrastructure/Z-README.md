# 基础设施层文档

## 🏗️ 模块概述
基础设施层是系统的技术实现核心，负责将领域层的抽象概念转化为具体可运行的技术方案。

## 📁 文件结构
```
infrastructure/
├── repositories/            # 存储库实现
│   ├── legal_document_repository.py  # 法律文档存储库
│   └── __init__.py
├── search/                  # 搜索引擎
│   └── vector_search_engine.py      # 向量搜索引擎
├── startup/                 # 启动管理
│   └── startup_manager.py          # 启动管理器
└── storage/                 # 数据存储
    ├── data_loader.py              # 数据加载器
    └── legacy_compatibility.py     # 兼容性处理
```

## 🎯 核心功能

### 1. 数据存储 (Storage)
- **DataLoader**: 统一数据加载和管理
- **LegacyCompatibility**: 旧数据格式兼容处理

### 2. 搜索服务 (Search)  
- **EnhancedSemanticSearch**: 增强语义搜索引擎
- 支持法条和案例的向量搜索

### 3. 存储库 (Repositories)
- **LegalDocumentRepository**: 法律文档存储库实现
- 对接领域层接口

### 4. 启动管理 (Startup)
- **StartupManager**: 系统启动状态管理
- 实时进度监控和错误处理

## 🚀 快速开始

### 初始化系统
```python
from src.infrastructure.startup import get_startup_manager
from src.infrastructure.storage import get_data_loader

# 获取启动管理器和数据加载器
manager = get_startup_manager()
data_loader = get_data_loader()

# 启动系统
manager.start_system(data_loader)

# 监控启动进度
status = manager.get_status()
print(f"启动进度: {status.overall_progress}%")
```

### 使用搜索功能
```python
from src.infrastructure import get_legal_document_repository

# 获取存储库实例
repo = get_legal_document_repository()

# 执行搜索
results, context = await repo.search_documents("盗窃罪")

# 获取单个文档
document = await repo.get_document_by_id("article_264")
```

### 直接访问数据
```python
from src.infrastructure.storage import get_data_loader

# 获取数据加载器
loader = get_data_loader()

# 加载所有数据
stats = loader.load_all()
print(f"已加载 {stats['total_documents']} 个文档")

# 获取具体内容
content = loader.get_article_content("article_263")
```

## 🔧 配置说明

### 数据文件路径
```
data/processed/vectors/criminal_articles_vectors.pkl
data/processed/vectors/criminal_cases_vectors.pkl  
data/processed/criminal/criminal_articles.pkl
data/processed/criminal/criminal_cases.pkl
```

### 模型配置
- 默认模型: `shibing624/text2vec-base-chinese`
- 向量维度: 768
- 自动下载和缓存

## 📊 性能指标

| 项目 | 数值 | 说明 |
|------|------|------|
| 模型加载 | 2-5秒 | 首次加载时间 |
| 数据加载 | 1-3秒 | 向量数据加载 |
| 搜索响应 | <200ms | 单次搜索耗时 |
| 内存使用 | 500-800MB | 完整运行内存 |
| 启动时间 | 3-8秒 | 系统总启动时间 |

## 🛠️ 扩展开发

### 添加新的数据源
```python
class NewDataSourceRepository(ILegalDocumentRepository):
    def __init__(self):
        # 初始化新数据源连接
        
    async def search_documents(self, query):
        # 实现新数据源的搜索逻辑
```

### 自定义搜索引擎
```python
class CustomSearchEngine:
    def search(self, query, top_k=10):
        # 实现自定义搜索算法
        return search_results
```

## ❓ 常见问题

### Q: 数据加载失败？
A: 检查数据文件是否存在，路径是否正确配置

### Q: 内存占用过高？
A: 启用懒加载模式，调整缓存大小

### Q: 启动时间过长？
A: 检查网络连接，模型下载可能需要时间

### Q: 搜索效果不好？
A: 检查模型是否正确加载，数据是否完整

## 📝 使用建议

1. **首次运行**: 确保数据文件就位，系统会自动下载模型
2. **生产环境**: 建议预加载所有数据，提高响应速度
3. **开发调试**: 可以使用懒加载模式节省内存
4. **性能优化**: 适当调整缓存大小和搜索参数

---
**版本**: 2.0.0  
**更新日期**: 2025-09-17  
**维护团队**: 技术基础设施组
