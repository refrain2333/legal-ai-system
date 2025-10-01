# 配置模块文档

## 模块概述

`src/config/` 模块负责管理应用的所有配置项，基于 Pydantic 提供类型安全的配置管理。

## 文件结构

```
src/config/
├── __init__.py      # 导出配置实例
├── settings.py      # 配置类定义
└── README.md        # 本文档
```

## 配置说明

### 主要配置项

**应用配置:**
- `APP_NAME`: 应用名称 (默认: "Legal Navigation AI")
- `APP_VERSION`: 版本号
- `APP_ENV`: 运行环境
- `DEBUG`: 调试模式

**服务器配置:**
- `HOST`: 服务器地址 (默认: 127.0.0.1)
- `PORT`: 服务端口 (默认: 5005)

**模型配置:**
- `MODEL_NAME`: 文本向量化模型
- `EMBEDDING_DIM`: 向量维度 (768)

**其他配置:**
- `CORS_ORIGINS`: CORS允许的源
- `SECRET_KEY`: 加密密钥
- 日志、缓存、文件路径等配置

## 使用方法

### 导入配置
```python
from src.config import settings

print(f"服务运行在: {settings.HOST}:{settings.PORT}")
print(f"调试模式: {settings.DEBUG}")
```

### 环境变量配置
```bash
# 设置环境变量
export PORT=8000
export DEBUG=false
```

### .env 文件配置
创建 `.env` 文件：
```env
PORT=8000
DEBUG=false
MODEL_NAME=shibing624/text2vec-base-chinese
```

## 配置优先级

1. 环境变量 (最高)
2. .env 文件  
3. 默认值 (最低)

## 默认值参考

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| PORT | 5005 | 服务端口 |
| HOST | 127.0.0.1 | 服务器地址 |
| DEBUG | True | 调试模式 |
| LOG_LEVEL | INFO | 日志级别 |

---

**版本**: 1.0.0  
**最后更新**: 2025-09-16
