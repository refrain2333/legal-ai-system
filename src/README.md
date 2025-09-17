# src目录架构概述

## 📁 DDD分层架构

```
src/
├── api/           # API层 - HTTP接口
├── services/      # 服务层 - 业务编排
├── domains/       # 领域层 - 核心概念
├── infrastructure/# 基础设施层 - 技术实现
└── config/        # 配置层
```

**依赖关系**: `api → services → domains ← infrastructure`

## 🎯 当前实现

### API层
- 4个端点: 搜索、状态、文档获取、健康检查
- FastAPI + Pydantic数据验证

### 服务层
- 搜索业务服务: 查询验证 → 搜索执行 → 结果转换

### 领域层
- 实体: `Article`(法条), `Case`(案例)
- 值对象: `SearchQuery`, `SearchResult`
- 接口: `ILegalDocumentRepository`

### 基础设施层
- 向量搜索引擎 (sentence-transformers)
- 数据加载器 (分离式存储: vectors/ + criminal/)
- 存储库实现

### 配置层
- Pydantic配置管理，支持.env文件

## 🔧 核心特性
- 刑事法律检索 (446条法条 + 17,131案例)
- 768维语义向量搜索
- 异步处理 + 依赖注入
- 相似度0.4-0.6，响应47ms
