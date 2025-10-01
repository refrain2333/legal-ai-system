# 领域层模块文档

## 模块概述

`src/domains/` 是法智导航系统的核心业务领域层，采用领域驱动设计(DDD)模式，定义了法律文档搜索领域的核心业务概念、规则和接口。

## 文件结构

```
src/domains/
├── __init__.py      # 模块导出
├── entities.py      # 核心业务实体
├── value_objects.py # 值对象定义  
├── repositories.py  # 存储库接口
└── README.md        # 本文档
```

## 核心概念

### 1. 业务实体 (Entities)
- `LegalDocument`: 法律文档基类
- `Article`: 法条实体，包含条文号、章节等信息
- `Case`: 案例实体，包含罪名、量刑等信息

### 2. 值对象 (Value Objects)  
- `SearchQuery`: 搜索查询参数
- `SearchResult`: 搜索结果
- `SearchContext`: 搜索上下文信息

### 3. 存储库接口 (Repositories)
- `ILegalDocumentRepository`: 主存储库接口
- `IArticleRepository`: 法条专用接口
- `ICaseRepository`: 案例专用接口

## 使用方法

### 导入领域对象
```python
from src.domains import Article, Case, SearchQuery, SearchResult

# 创建法条对象
article = Article(
    id="article_264",
    title="盗窃罪",
    content="盗窃公私财物，数额较大的...",
    article_number=264
)

# 创建搜索查询
query = SearchQuery(query_text="盗窃罪的量刑标准", max_results=10)
```

### 使用存储库接口
```python
from src.domains import ILegalDocumentRepository

class MyService:
    def __init__(self, repository: ILegalDocumentRepository):
        self.repository = repository
    
    async def search(self, query_text: str):
        query = SearchQuery(query_text=query_text)
        results, context = await self.repository.search_documents(query)
        return results
```

## 设计原则

1. **领域隔离**: 业务逻辑与基础设施分离
2. **接口契约**: 定义清晰的存储库接口
3. **不可变性**: 值对象确保线程安全
4. **类型安全**: 完整的类型注解

## 扩展说明

- 添加新的文档类型: 继承 `LegalDocument`
- 扩展搜索功能: 修改 `SearchQuery` 和 `SearchResult`
- 实现新的存储库: 实现对应的接口

---

**版本**: 1.0.0  
**最后更新**: 2025-09-16
