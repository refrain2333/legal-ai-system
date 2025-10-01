# 向量数据说明文档

> **目录作用**：集中存放"刑法条文向量 & 刑事案例向量"，供后续相似度检索、语义搜索、知识图谱嵌入与机器学习/LLM微调使用。
>
> **数据来源**: 此目录中的向量数据由 `tools/data_processing/criminal_data_vectorizer.py` 处理 `data/processed/criminal/` 目录中的原始数据生成。使用 `thunlp/Lawformer` 模型，嵌入维度为 **768**。

## 文件概览

| 文件名 | 大小 (MB) | 向量条数 | 数据类型 | 描述 |
| --- | --- | --- | --- | --- |
| **criminal_articles_vectors.pkl** | 1.35 | 446 | criminal_articles | 刑法条文文本向量及元数据 |
| **criminal_cases_vectors.pkl** | 51.87 | 17,131 | criminal_cases | 刑事案例文本向量及元数据 |

> **重要说明**：
> 1. 向量为 `float32` 类型，**未做 L2 归一化**（保持 SentenceTransformer 输出原始值）
> 2. 如需余弦相似度检索，可在加载后调用 `sklearn.preprocessing.normalize` 做单位化处理
> 3. 这些向量文件被简化版法智导航系统直接使用，支持语义搜索功能
> 4. 元数据中不包含完整文本内容，完整内容需从 `data/processed/criminal/` 获取

## 数据文件结构

每个向量文件（.pkl）包含以下键值对：

| 键名 | 类型 | 说明 |
| --- | --- | --- |
| `vectors` | `np.ndarray` | 向量矩阵，形状 `(total_count, 768)`，数据类型 `float32` |
| `metadata` | `list[dict]` | 与向量一一对应的元数据列表 |
| `model_name` | `str` | 生成向量所用模型名称: `thunlp/Lawformer` |
| `embedding_dim` | `int` | 嵌入维度，固定为 768 |
| `total_count` | `int` | 向量条数，与 `vectors.shape[0]` 一致 |
| `data_type` | `str` | `criminal_articles` 或 `criminal_cases` |
| `created_time` | `str` | 生成时间，格式 `YYYY-MM-DD HH:MM:SS` |
| `statistics` | `dict` | 向量统计信息（均值范数、标准差等） |

### 向量统计信息示例
```json
{
  "vector_shape": [446, 768],
  "vector_dtype": "float32", 
  "mean_norm": 15.135,
  "std_norm": 0.662
}
```

## 元数据结构详解

### 1. criminal_articles_vectors.pkl 元数据
每个法条向量对应的元数据结构：
```json
{
  "id": "article_1",                    # 文档唯一标识
  "index": 0,                           # 在向量矩阵中的索引位置
  "article_number": 1,                  # 法条编号
  "title": "中华人民共和国刑法 第1条",   # 法条标题
  "chapter": "第一章 刑法的任务、基本原则和适用范围",  # 所属章节
  "section": null,                      # 所属节次（可能为空）
  "content_length": 43,                 # 原文内容长度（字符数）
  "type": "criminal_article"            # 数据类型标识
}
```

### 2. criminal_cases_vectors.pkl 元数据
每个案例向量对应的元数据结构：
```json
{
  "id": "case_case_000001",             # 案例唯一标识
  "index": 0,                           # 在向量矩阵中的索引位置
  "case_id": "case_000001",             # 案例编号
  "accusations": ["盗窃"],               # 罪名列表
  "relevant_articles": [264],           # 相关法条编号列表
  "sentence_months": 2,                 # 判决刑期（月）
  "fine_amount": 0,                     # 罚金金额（元）
  "fact_length": 98,                    # 案件事实描述长度（字符数）
  "type": "criminal_case"               # 数据类型标识
}
```

## 基本使用示例

### 1. 加载向量数据
```python
import pickle
import numpy as np
from pathlib import Path

# 加载法条向量
vectors_dir = Path("data/processed/vectors")
with open(vectors_dir / "criminal_articles_vectors.pkl", "rb") as f:
    articles_data = pickle.load(f)

print(f"加载法条向量: {articles_data['vectors'].shape}")
print(f"模型名称: {articles_data['model_name']}")
print(f"向量维度: {articles_data['embedding_dim']}")

# 加载案例向量  
with open(vectors_dir / "criminal_cases_vectors.pkl", "rb") as f:
    cases_data = pickle.load(f)

print(f"加载案例向量: {cases_data['vectors'].shape}")
```

### 2. 向量相似度计算
```python
from sklearn.metrics.pairwise import cosine_similarity

# 计算法条间的相似度
article_vectors = articles_data['vectors']
similarities = cosine_similarity(article_vectors)

# 找到与第一条法条最相似的top5
query_idx = 0
sim_scores = similarities[query_idx]
top5_indices = sim_scores.argsort()[-6:-1][::-1]  # 排除自身

print(f"与第{query_idx+1}条最相似的法条：")
for idx in top5_indices:
    meta = articles_data['metadata'][idx]
    print(f"  相似度 {sim_scores[idx]:.3f}: {meta['title']}")
```

### 3. 语义检索示例
```python
from src.infrastructure.storage.lawformer_embedder import LawformerEmbedder

# 加载相同的模型进行查询编码
model = LawformerEmbedder(model_name='thunlp/Lawformer')

# 查询示例
query = "被告人秘密窃取他人财物，价值较大"
query_vector = model.encode([query])

# 在案例向量中搜索
case_vectors = cases_data['vectors'] 
similarities = cosine_similarity(query_vector, case_vectors)[0]

# 获取最相关的top5案例
top5_indices = similarities.argsort()[-5:][::-1]

print("最相关的案例：")
for idx in top5_indices:
    meta = cases_data['metadata'][idx]
    print(f"相似度 {similarities[idx]:.3f}: 案例{meta['case_id']} - {', '.join(meta['accusations'])}")
```

## 高级使用场景

### 1. 构建FAISS索引加速检索
```python
import faiss

# 构建法条向量的FAISS索引
article_vectors = articles_data['vectors'].astype('float32')
dimension = article_vectors.shape[1]

# 创建索引
index = faiss.IndexFlatIP(dimension)  # 内积索引（需先归一化做余弦相似度）

# 归一化向量
faiss.normalize_L2(article_vectors)
index.add(article_vectors)

# 快速检索
query_vector = model.encode(["盗窃罪的构成要件"])
faiss.normalize_L2(query_vector)

distances, indices = index.search(query_vector, k=5)
print("FAISS检索结果：")
for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
    meta = articles_data['metadata'][idx]
    print(f"{i+1}. 相似度{dist:.3f}: {meta['title']}")
```

### 2. 批量相似度计算
```python
# 计算多个查询的批量相似度
queries = [
    "盗窃他人财物",
    "故意伤害他人身体", 
    "诈骗他人钱财"
]

query_vectors = model.encode(queries)
case_vectors = cases_data['vectors']

# 批量计算相似度
batch_similarities = cosine_similarity(query_vectors, case_vectors)

for i, query in enumerate(queries):
    print(f"\n查询: {query}")
    top3_indices = batch_similarities[i].argsort()[-3:][::-1]
    
    for idx in top3_indices:
        meta = cases_data['metadata'][idx]
        score = batch_similarities[i][idx]
        print(f"  相似度{score:.3f}: {meta['case_id']} - {', '.join(meta['accusations'])}")
```

### 3. 向量聚类分析
```python
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 对法条向量进行聚类
n_clusters = 10
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(articles_data['vectors'])

# 分析聚类结果
for cluster_id in range(n_clusters):
    cluster_indices = np.where(clusters == cluster_id)[0]
    print(f"\n聚类 {cluster_id} ({len(cluster_indices)} 个法条):")
    
    for idx in cluster_indices[:5]:  # 显示前5个
        meta = articles_data['metadata'][idx]
        print(f"  第{meta['article_number']}条: {meta['title'][:50]}...")
```

## 与简化版系统的集成

### 当前系统使用方式
此向量数据被简化版法智导航系统（`src/engines/search_engine.py`）直接使用：

1. **数据加载**: 系统启动时自动加载两个向量文件
2. **语义搜索**: 用户查询被编码后与向量库进行相似度计算  
3. **结果返回**: 返回最相关的法条和案例，包含标题和基本信息
4. **内容补充**: 当需要完整内容时，可从 `data/processed/criminal/` 获取

### 系统架构优势
- **快速启动**: 预计算向量，避免实时编码延迟
- **高效检索**: 基于numpy的向量运算，支持毫秒级响应
- **灵活扩展**: 标准向量格式，易于集成其他检索算法

## 数据更新和维护

### 重新生成向量
如果原始数据更新，重新生成向量：
```bash
cd /path/to/legal-ai
python tools/data_processing/criminal_data_vectorizer.py
```

### 向量文件验证
```python
# 验证向量文件完整性
def validate_vector_file(filepath):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    
    required_keys = ['vectors', 'metadata', 'model_name', 'embedding_dim', 'total_count']
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        print(f"缺少键: {missing_keys}")
        return False
    
    if data['vectors'].shape[0] != len(data['metadata']):
        print("向量数量与元数据数量不匹配")
        return False
        
    print(f"文件验证通过: {data['total_count']} 个向量")
    return True

# 验证两个向量文件
validate_vector_file("data/processed/vectors/criminal_articles_vectors.pkl")
validate_vector_file("data/processed/vectors/criminal_cases_vectors.pkl")
```

## 技术规格

- **向量模型**: thunlp/Lawformer
- **向量维度**: 768维
- **数据精度**: float32
- **存储格式**: pickle序列化
- **索引方式**: 序列索引（与元数据一一对应）
- **相似度算法**: 余弦相似度（需要归一化）或点积相似度

## 性能参考

基于测试环境的性能数据：
- **加载时间**: ~2-3秒（两个向量文件）
- **内存占用**: ~400MB（17,577个768维向量）
- **查询速度**: ~50-100ms（单次语义检索，包含排序）
- **并发能力**: 支持多线程并发查询

---

*此文档最后更新: 2025-09-11*  
*向量数据版本: v1.0*  
*总向量数: 17,577 (446条法条 + 17,131个案例)*  
*生成模型: thunlp/Lawformer*
