# Storage 模块文档

## 概述
统一数据加载和管理中心，负责所有法律数据的加载、缓存和提供

## 文件结构
```
storage/
├── data_loader.py          # 核心数据加载管理器
├── legacy_compatibility.py  # 旧数据兼容性处理
└── __init__.py             # 模块导出
```

## 核心组件

### 1. DataLoader - 数据加载器
**职责**: 统一管理数据加载、缓存和错误处理

```python
class DataLoader:
    def load_vectors(self):        # 加载向量数据
    def load_original_data(self):  # 加载原始数据  
    def load_model(self):          # 加载语义模型
    def get_article_content(self): # 获取法条内容
    def get_case_content(self):    # 获取案例内容
```

### 2. LegacyCompatibilityHandler - 兼容性处理
**职责**: 确保新旧数据格式兼容

```python
class LegacyCompatibilityHandler:
    def convert_legacy_format(self):  # 转换旧格式数据
    def validate_data_integrity(self):  # 验证数据完整性
```

## 快速使用

### 基本使用
```python
from src.infrastructure.storage.data_loader import get_data_loader

# 获取数据加载器
loader = get_data_loader()

# 加载所有数据
stats = loader.load_all()
print(f"加载完成: {stats['total_documents']} 个文档")

# 获取法条内容
content = loader.get_article_content("article_264")
```

### 兼容性处理
```python
from src.infrastructure.storage.legacy_compatibility import LegacyCompatibilityHandler

handler = LegacyCompatibilityHandler()
result = handler.convert_legacy_format(old_data)
```

## 数据文件路径
- 法条向量: `data/processed/vectors/criminal_articles_vectors.pkl`
- 案例向量: `data/processed/vectors/criminal_cases_vectors.pkl`
- 法条数据: `data/processed/criminal/criminal_articles.pkl`
- 案例数据: `data/processed/criminal/criminal_cases.pkl`

## 性能指标
| 指标 | 典型值 | 说明 |
|------|--------|------|
| 加载时间 | 3-5秒 | 完整数据加载 |
| 内存使用 | 400-500MB | 向量+模型 |
| 搜索耗时 | 50-100ms | 单次搜索 |

## 常见问题

### Q: 数据加载失败？
A: 检查数据文件是否存在，路径是否正确

### Q: 内存占用高？
A: 调整缓存大小或启用懒加载

### Q: 格式不兼容？
A: 使用兼容性处理器转换

---
**版本**: 1.0.0  
**更新**: 2025-09-16
