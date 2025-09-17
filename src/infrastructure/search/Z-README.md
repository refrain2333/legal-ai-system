# Search 模块文档

## 概述
语义搜索引擎实现，提供基于向量的法律文档智能检索

## 文件结构
```
search/
├── vector_search_engine.py  # 增强语义搜索引擎
└── __init__.py              # 模块导出
```

## 核心组件

### EnhancedSemanticSearch - 搜索引擎
**职责**: 执行语义搜索和文档检索

```python
class EnhancedSemanticSearch:
    def search(self, query, top_k=10):          # 综合搜索
    def search_articles_only(self, query, top_k=10):  # 只搜法条
    def search_cases_only(self, query, top_k=10):     # 只搜案例
    def get_document_by_id(self, doc_id):       # 按ID获取文档
    def get_stats(self):                        # 获取统计信息
```

## 快速使用

### 基本搜索
```python
from src.infrastructure.search import get_enhanced_search_engine

# 获取搜索引擎
engine = get_enhanced_search_engine()

# 执行搜索
results = engine.search("盗窃罪量刑", top_k=5)
for result in results:
    print(f"{result['title']} - 相似度: {result['similarity']:.3f}")
```

### 特定类型搜索
```python
# 只搜索法条
articles = engine.search_articles_only("故意伤害", top_k=3)

# 只搜索案例  
cases = engine.search_cases_only("毒品犯罪", top_k=3)
```

### 获取单个文档
```python
# 获取特定文档
document = engine.get_document_by_id("article_264", include_content=True)
if document:
    print(f"标题: {document['title']}")
    print(f"内容: {document['content'][:200]}...")
```

## 搜索原理

### 1. 查询编码
- 使用 `shibing624/text2vec-base-chinese` 模型
- 将查询文本编码为768维向量

### 2. 相似度计算
- 使用余弦相似度算法
- 分别计算法条和案例的相似度

### 3. 结果合并
- 法条和案例分别取top-k/2结果
- 按相似度合并排序
- 返回最终top-k结果

## 性能指标
| 指标 | 典型值 | 说明 |
|------|--------|------|
| 搜索耗时 | 50-100ms | 单次搜索时间 |
| 内存使用 | 400-500MB | 向量数据内存 |
| 准确率 | >85% | 语义匹配准确率 |

## 数据源
- 法条向量: `data/processed/vectors/criminal_articles_vectors.pkl`
- 案例向量: `data/processed/vectors/criminal_cases_vectors.pkl`
- 原始数据: `data/processed/criminal/` 目录

## 常见问题

### Q: 搜索返回空结果？
A: 检查数据是否加载，查询是否过于特殊

### Q: 相似度分数低？
A: 尝试更具体的查询词，或检查模型加载

### Q: 内容加载失败？
A: 检查原始数据文件是否存在

---
**版本**: 1.0.0  
**更新**: 2025-09-16
