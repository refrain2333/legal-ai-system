# API 模块文档

## 模块概述

`src/api/` 模块是法智导航系统的HTTP接口层，基于FastAPI框架实现，负责处理所有外部请求和响应。本模块遵循DDD分层架构原则，仅负责HTTP层面的处理，所有业务逻辑委托给服务层。

## 文件结构

```
src/api/
├── __init__.py      # 模块初始化，导出create_app函数
├── app.py           # FastAPI应用配置和创建
├── models.py        # Pydantic数据模型定义
└── routes.py        # API路由实现
```

## API端点

### 1. 搜索接口

**端点**: `POST /api/search`

**功能**: 执行语义搜索，返回相关的法律条文和案例

**请求体**:
```json
{
  "query": "盗窃罪的量刑标准",
  "top_k": 10
}
```

**响应**:
```json
{
  "success": true,
  "results": [
    {
      "id": "article_264",
      "title": "刑法第二百六十四条",
      "content": "盗窃公私财物，数额较大的...",
      "similarity": 0.85,
      "type": "article",
      "article_number": 264,
      "chapter": "侵犯财产罪"
    }
  ],
  "total": 1,
  "query": "盗窃罪的量刑标准"
}
```

### 2. 系统状态接口

**端点**: `GET /api/status`

**功能**: 获取系统运行状态和文档统计信息

**响应**:
```json
{
  "status": "ok",
  "ready": true,
  "total_documents": 17577
}
```

### 3. 文档获取接口

**端点**: `GET /api/document/{document_id}`

**功能**: 根据ID获取单个文档的详细信息

**参数**:
- `document_id`: 文档唯一标识符

### 4. 健康检查接口

**端点**: `GET /health`

**功能**: 简单的健康检查，用于监控系统状态

**响应**:
```json
{
  "status": "healthy",
  "message": "法智导航 API 运行正常"
}
```

## 数据模型

### SearchRequest 模型
```python
class SearchRequest(BaseModel):
    query: str  # 搜索查询文本
    top_k: int = 10  # 返回结果数量，最大50
```

### SearchResult 模型
```python
class SearchResult(BaseModel):
    # 通用字段
    id: str           # 文档唯一标识符
    title: str        # 文档标题
    content: str      # 文档内容
    similarity: float # 相似度分数(0-1)
    type: str         # 文档类型: article/case
    
    # 案例特有字段
    case_id: Optional[str]
    criminals: Optional[List[str]]
    accusations: Optional[List[str]]
    # ... 其他刑罚相关字段
    
    # 法条特有字段
    article_number: Optional[int]
    chapter: Optional[str]
```

### SearchResponse 模型
```python
class SearchResponse(BaseModel):
    success: bool              # 操作是否成功
    results: List[SearchResult] # 搜索结果列表
    total: int                 # 匹配结果总数
    query: str                 # 原始查询文本
```

## 技术特性

### 1. 依赖注入设计
```python
def get_search_service() -> SearchService:
    """依赖注入：获取搜索服务实例"""
    repository = get_legal_document_repository()
    return SearchService(repository)
```

### 2. 错误处理机制
- HTTP异常的统一处理
- 服务层错误的适当转换
- 优雅的降级处理

### 3. CORS支持
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 静态文件服务
```python
# 挂载前端静态文件
frontend_path = Path(__file__).parent.parent.parent / "frontend"
app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True))
```

## 快速开始

### 启动服务
```bash
python app.py
```

### 访问前端
- Web服务器: http://localhost:5005/ui/
- 直接文件: 打开 `frontend/index.html`

### API测试
```bash
# 搜索测试
curl -X POST "http://localhost:5005/api/search" \
     -H "Content-Type: application/json" \
     -d '{"query":"故意伤害","top_k":5}'

# 状态检查
curl "http://localhost:5005/api/status"
```

## 开发规范

1. **分层原则**: API层只处理HTTP，业务逻辑在服务层
2. **数据验证**: 使用Pydantic进行严格的输入验证
3. **错误处理**: 统一错误响应格式
4. **文档化**: 所有接口自动生成OpenAPI文档

## 性能指标

- 平均响应时间: < 50ms
- 支持并发请求: 是
- 最大结果数: 50条
- 相似度阈值: 0.4-0.6

---

**版本**: 1.0.0  
**最后更新**: 2025-09-16  
**维护者**: 法智导航开发团队
