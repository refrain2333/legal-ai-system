# 系统架构设计文档

## 🏗️ 整体架构

### 1. 系统架构图 (Mermaid)

```mermaid
graph TB
    subgraph "前端层 Frontend Layer"
        UI[Web界面]
        WS[WebSocket连接]
    end

    subgraph "API网关层 API Gateway"
        ROUTER[路由分发器]
        AUTH[认证中间件]
        CORS[跨域处理]
    end

    subgraph "业务服务层 Business Service"
        SEARCH[搜索服务]
        KG[知识图谱服务]
        DEBUG[调试服务]
    end

    subgraph "领域层 Domain Layer"
        ENTITY[实体模型]
        REPO[存储接口]
        VALUE[值对象]
    end

    subgraph "基础设施层 Infrastructure"
        VECTOR[向量搜索引擎]
        LLM[LLM集成]
        STORAGE[数据存储]
        CACHE[缓存服务]
    end

    subgraph "数据层 Data Layer"
        PICKLE[(Pickle文件)]
        VECTORS[(向量数据库)]
        FILES[(静态文件)]
    end

    UI --> ROUTER
    WS --> ROUTER
    ROUTER --> AUTH
    AUTH --> SEARCH
    AUTH --> KG
    AUTH --> DEBUG

    SEARCH --> ENTITY
    KG --> ENTITY
    DEBUG --> ENTITY

    ENTITY --> REPO
    REPO --> VECTOR
    REPO --> STORAGE

    VECTOR --> VECTORS
    STORAGE --> PICKLE
    LLM --> CACHE

    style UI fill:#e1f5fe
    style SEARCH fill:#f3e5f5
    style VECTOR fill:#fff3e0
    style VECTORS fill:#e8f5e8
```

### 2. DDD分层架构

```mermaid
graph LR
    subgraph "接口层 Interface"
        API[API Routes]
        WEB[Web UI]
        WS[WebSocket]
    end

    subgraph "应用层 Application"
        SERVICE[Search Service]
        PIPELINE[AI Pipeline]
    end

    subgraph "领域层 Domain"
        ENTITY[Entities]
        AGGREGATE[Aggregates]
        REPOSITORY[Repository Interface]
    end

    subgraph "基础设施层 Infrastructure"
        REPO_IMPL[Repository Implementation]
        VECTOR_ENGINE[Vector Search Engine]
        LLM_CLIENT[LLM Client]
        DATA_STORAGE[Data Storage]
    end

    API --> SERVICE
    WEB --> SERVICE
    WS --> SERVICE

    SERVICE --> ENTITY
    SERVICE --> REPOSITORY
    PIPELINE --> ENTITY

    REPOSITORY --> REPO_IMPL
    REPO_IMPL --> VECTOR_ENGINE
    REPO_IMPL --> DATA_STORAGE
    SERVICE --> LLM_CLIENT

    style API fill:#bbdefb
    style SERVICE fill:#c8e6c9
    style ENTITY fill:#ffe0b2
    style REPO_IMPL fill:#f8bbd9
```

### 3. 数据流架构

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端界面
    participant API as API网关
    participant Service as 搜索服务
    participant Vector as 向量引擎
    participant LLM as LLM服务
    participant Storage as 数据存储

    User->>Frontend: 输入查询
    Frontend->>API: POST /api/search
    API->>Service: 调用搜索服务

    Service->>LLM: 查询分析增强
    LLM-->>Service: 增强后查询

    Service->>Vector: 向量相似度计算
    Vector->>Storage: 获取向量数据
    Storage-->>Vector: 返回向量结果
    Vector-->>Service: 相似文档ID列表

    Service->>Storage: 获取完整文档内容
    Storage-->>Service: 文档详细信息

    Service-->>API: 搜索结果
    API-->>Frontend: JSON响应
    Frontend-->>User: 展示结果

    Note over Service,LLM: 支持多提供商备选
    Note over Vector,Storage: 分离式存储设计
```

## 🔧 技术栈架构

### 核心技术组件

```mermaid
mindmap
  root((法智导航))
    前端技术
      HTML5
      CSS3
      JavaScript ES6+
      WebSocket
      响应式设计
    后端框架
      FastAPI
      Uvicorn
      Pydantic
      AsyncIO
      依赖注入
    AI模型
      Lawformer
      768维向量
      Cosine相似度
      多提供商LLM
    数据存储
      Pickle序列化
      向量索引
      分离式存储
      异步加载
    基础设施
      Docker支持
      日志系统
      性能监控
      错误处理
```

## 📊 性能架构

### 响应时间分布

```mermaid
pie title 系统响应时间分布
    "向量检索" : 35
    "文档加载" : 25
    "LLM处理" : 30
    "结果格式化" : 10
```

### 并发处理能力

```mermaid
graph LR
    subgraph "负载均衡"
        LB[Load Balancer]
    end

    subgraph "应用实例"
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance N]
    end

    subgraph "共享资源"
        CACHE[Redis Cache]
        STORAGE[Shared Storage]
        MODEL[Model Cache]
    end

    LB --> APP1
    LB --> APP2
    LB --> APP3

    APP1 --> CACHE
    APP2 --> CACHE
    APP3 --> CACHE

    APP1 --> STORAGE
    APP2 --> STORAGE
    APP3 --> STORAGE

    APP1 --> MODEL
    APP2 --> MODEL
    APP3 --> MODEL
```

## 🛡️ 安全架构

### 安全层级设计

```mermaid
graph TD
    subgraph "网络安全"
        FIREWALL[防火墙]
        HTTPS[HTTPS/TLS]
        CORS[CORS策略]
    end

    subgraph "应用安全"
        AUTH[身份认证]
        VALID[输入验证]
        RATE[速率限制]
    end

    subgraph "数据安全"
        ENCRYPT[数据加密]
        BACKUP[备份策略]
        ACCESS[访问控制]
    end

    FIREWALL --> AUTH
    HTTPS --> VALID
    CORS --> RATE

    AUTH --> ENCRYPT
    VALID --> BACKUP
    RATE --> ACCESS

    style FIREWALL fill:#ffcdd2
    style AUTH fill:#f8bbd9
    style ENCRYPT fill:#e1f5fe
```

## 🔄 部署架构

### 容器化部署

```mermaid
graph TB
    subgraph "开发环境"
        DEV[开发容器]
        DEV_DB[开发数据]
    end

    subgraph "测试环境"
        TEST[测试容器]
        TEST_DB[测试数据]
        CI[CI/CD Pipeline]
    end

    subgraph "生产环境"
        PROD1[生产容器1]
        PROD2[生产容器2]
        PROD_DB[生产数据]
        MONITOR[监控服务]
    end

    DEV --> CI
    TEST --> CI
    CI --> PROD1
    CI --> PROD2

    PROD1 --> PROD_DB
    PROD2 --> PROD_DB
    PROD1 --> MONITOR
    PROD2 --> MONITOR

    style DEV fill:#e8f5e8
    style TEST fill:#fff3e0
    style PROD1 fill:#ffebee
    style PROD2 fill:#ffebee
```

---

*本架构文档基于DDD设计原则，确保系统的可维护性、可扩展性和高性能。*