# Repositories 模块

## 📁 结构说明

这个模块实现了领域层定义的存储库接口，提供具体的数据访问实现。

### 文件结构
```
repositories/
├── __init__.py                    # 模块导出
├── legal_document_repository.py   # 法律文档存储库实现
└── Z-README.md                   # 本说明文档
```

## 🎯 职责

### LegalDocumentRepository
- 实现 `ILegalDocumentRepository` 接口
- 组合搜索引擎和数据加载器
- 提供统一的文档访问接口
- 负责数据格式转换和错误处理

## 🔄 依赖关系

```
LegalDocumentRepository
├── 依赖 → EnhancedSemanticSearch    (搜索引擎)
├── 依赖 → DataLoader               (数据加载器)
└── 实现 → ILegalDocumentRepository  (领域接口)
```

## 📋 主要功能

1. **文档搜索** - `search_documents()`
2. **ID查询** - `get_document_by_id()`
3. **批量查询** - `get_documents_by_ids()`
4. **统计信息** - `get_total_document_count()`
5. **状态检查** - `is_ready()`

## 🚀 使用方式

```python
from ..infrastructure.repositories import get_legal_document_repository

# 获取存储库实例
repo = get_legal_document_repository()

# 检查就绪状态
if repo.is_ready():
    # 执行搜索
    results, context = await repo.search_documents(query)
```