# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

法智导航是一个基于AI技术的智能法律文档检索系统，采用语义向量化技术，支持自然语言查询，提供法律条文和案例的高精度匹配服务。

## 核心架构

### 分层架构
```
FastAPI应用层 (src/api/)
├── app.py - FastAPI应用入口和配置
├── routes.py - API路由定义
└── models.py - Pydantic数据模型

业务引擎层 (src/engines/)
└── enhanced_search_engine.py - 增强的语义搜索引擎

核心服务层 (src/core/)
├── data_loader.py - 统一数据加载器
└── legacy_compatibility.py - 向后兼容支持

配置层 (src/config/)
└── settings.py - 应用配置管理
```

### 数据架构
- **原始数据**: data/laws/ (分类法律条文), data/cases/ (法律案例)
- **处理数据**: data/processed/ (向量化数据)
- **索引文件**: data/indices/ (向量索引和元数据)

## 开发命令

### 启动服务
```bash
# 主启动脚本
python app.py

# 开发模式启动
python src/main.py
```

### 测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/conftest.py

# 异步测试
pytest-asyncio
```

### 代码质量
```bash
# 代码格式化
black src/ tests/

# 代码检查
pylint src/

# 导入排序
isort src/ tests/
```

### 依赖管理
```bash
# 安装依赖
pip install -r requirements.txt

# 创建conda环境
conda activate legal-ai
```

## 技术栈要点

### AI/ML 组件
- **向量化模型**: sentence-transformers (shibing624/text2vec-base-chinese)
- **向量检索**: cosine similarity + numpy
- **维度**: 768维语义向量
- **数据处理**: pandas + faiss-cpu

### Web 框架
- **FastAPI**: 异步API框架
- **Uvicorn**: ASGI服务器
- **CORS**: 跨域中间件配置
- **静态文件**: 前端页面服务

### 配置管理
- **环境配置**: .env文件 + pydantic-settings
- **默认端口**: 5005
- **调试模式**: settings.DEBUG控制

## 项目特定规则

### 数据处理
1. 所有文本处理必须支持UTF-8编码
2. 向量数据延迟加载以节省内存
3. 内容数据按需加载(include_content参数)

### API设计
1. 所有搜索接口返回SearchResponse格式
2. 支持articles和cases两种数据类型
3. 相似度阈值过滤低质量结果

### 路径约定
- 项目根目录自动加入Python路径
- 相对路径基于项目根目录
- 配置文件优先级: .env > 默认设置

### 性能要求
- 平均检索响应时间: <50ms
- 支持3000+文档检索
- 内存使用控制在2GB以内

## 重要文件

### 核心入口文件
- `app.py` - 主启动脚本(简化版)
- `src/api/app.py` - FastAPI应用定义
- `src/engines/enhanced_search_engine.py` - 搜索引擎核心

### 配置文件  
- `src/config/settings.py` - 应用配置类
- `requirements.txt` - Python依赖
- `pytest.ini` - 测试配置

### 数据相关
- `src/core/data_loader.py` - 数据加载器
- `tests/conftest.py` - 测试fixtures

## 开发注意事项

1. **编码问题**: Windows环境需设置PYTHONIOENCODING=utf-8
2. **异步模式**: 所有IO操作使用async/await模式
3. **错误处理**: API层统一异常处理和HTTP状态码
4. **日志管理**: 使用loguru进行结构化日志记录
5. **测试覆盖**: 所有新功能需编写对应pytest测试

## 前端集成

- 前端文件位置: `frontend/`
- Web访问: http://localhost:5005/ui/
- API文档: http://localhost:5005/docs
- 健康检查: http://localhost:5005/health