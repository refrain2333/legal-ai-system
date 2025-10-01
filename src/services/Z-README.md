# 服务层模块文档

## 模块概述

`src/services/` 是法智导航系统的业务服务层，负责封装核心业务逻辑，协调领域对象和基础设施组件，提供完整的业务流程管理。

## 文件结构

```
src/services/
├── __init__.py      # 模块导出
├── search_service.py # 搜索业务服务
└── README.md        # 本文档
```

## 核心服务

### SearchService - 搜索业务服务

**主要功能:**
- 执行完整的法律文档搜索业务流程
- 文档获取和管理
- 业务异常处理和日志记录

**关键方法:**

```python
async def search_documents(query_text: str, max_results: int = 10) -> dict:
    """搜索法律文档 - 完整业务流程"""
    
async def get_document_by_id(document_id: str) -> Optional[dict]:
    """根据ID获取单个文档"""
```

## 业务流程

### 搜索业务流程
1. **查询验证** - 验证查询文本有效性
2. **查询构建** - 创建SearchQuery值对象
3. **搜索执行** - 调用存储库执行搜索
4. **结果转换** - 领域对象转换为API格式
5. **响应构建** - 构建完整的API响应

### 错误处理流程
- 统一的业务异常处理
- 详细的错误日志记录
- 友好的错误信息返回

## 设计特点

### 1. 依赖注入
```python
def __init__(self, repository: ILegalDocumentRepository):
    self.repository = repository  # 通过接口依赖
```

### 2. 业务逻辑集中
- 所有搜索相关业务在一个服务中
- 避免业务逻辑分散

### 3. 数据转换
- 领域对象 ↔ API响应格式转换
- 处理数据结构差异

### 4. 易于测试
```python
# 测试示例
mock_repo = MockRepository()
service = SearchService(mock_repo)
result = await service.search_documents("盗窃罪")
```

## 在架构中的位置

```
API层 (HTTP接口) 
    ↓ 调用
服务层 (业务编排) ← 本模块
    ↓ 使用  
领域层 (业务概念)
    ↑ 实现
基础设施层 (技术实现)
```

## 使用示例

### 基本使用
```python
from src.services import SearchService
from src.infrastructure import LegalDocumentRepository

# 创建服务实例
repository = LegalDocumentRepository()
service = SearchService(repository)

# 执行搜索
result = await service.search_documents("故意伤害罪", max_results=5)
```

### API层调用
```python
# 在API路由中调用服务
@router.post("/search")
async def search_endpoint(request: SearchRequest):
    service = get_search_service()  # 依赖注入
    result = await service.search_documents(
        request.query, 
        request.top_k
    )
    return result
```

## 扩展说明

- 添加新业务服务: 创建新的服务类
- 扩展搜索功能: 修改SearchService方法
- 支持新文档类型: 更新数据转换逻辑

---

**版本**: 1.0.0  
**最后更新**: 2025-09-16
