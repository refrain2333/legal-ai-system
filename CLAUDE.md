# 法智导航 - 刑事法律AI检索系统开发指南

## 🎯 项目状态
- **领域**: 仅刑事法律 (446条刑法条文 + 17,131个刑事案例)
- **技术**: sentence-transformers + 768维向量 + DDD架构
- **效果**: 相似度0.4-0.6，响应47ms
- **阶段**: MVP完成，需要精度优化

## 🏗️ 架构 (DDD分层)
```
src/
├── api/           # HTTP接口，数据验证
├── services/      # 业务逻辑编排
├── domains/       # 核心实体定义
├── infrastructure/# 向量搜索，数据存储
└── config/        # 环境设置
```
**依赖**: API→Services→Domains←Infrastructure (严禁反向)

## 📊 数据存储结构

### 分离式存储设计
```
data/processed/
├── criminal/      # 完整文本数据 (用于内容展示)
│   ├── criminal_articles.pkl    # 446条法条完整文本 (0.80MB)
│   └── criminal_cases.pkl       # 17,131案例完整文本 (24.05MB)
└── vectors/       # 向量数据 (用于快速检索)
    ├── criminal_articles_vectors.pkl  # 法条向量+元数据 (1.35MB)
    └── criminal_cases_vectors.pkl     # 案例向量+元数据 (51.87MB)
```

### 数据使用流程
1. **检索**: 查询编码 → vectors/目录相似度匹配 → 获得ID和基础信息
2. **展示**: 需要完整内容时 → 从criminal/目录加载详细数据

### 向量技术规格
- **模型**: shibing624/text2vec-base-chinese
- **维度**: 768维 float32 (未归一化)
- **相似度**: 必须使用cosine_similarity
- **性能**: 加载2-3秒，内存400MB

### 元数据结构
```python
# vectors/目录 - 轻量元数据
article_meta = {"id", "article_number", "title", "chapter", "content_length"}
case_meta = {"id", "case_id", "accusations", "relevant_articles", "sentence_months"}

# criminal/目录 - 完整数据
article_full = {"article_number", "title", "content", "full_text", "chapter", "related_cases"}
case_full = {"case_id", "fact", "accusations", "relevant_articles", "sentence_info", "criminals"}
```

## ⚡ 开发要点

### 启动
```bash
python app.py                    # 生产模式
python src/main.py              # 开发模式
conda activate legal-ai         # 环境: C:\Users\lenovo\Miniconda3\envs\legal-ai\
```

### 技术栈
- **AI**: sentence-transformers (shibing624/text2vec-base-chinese)
- **Web**: FastAPI + Uvicorn (端口5005)
- **向量**: numpy cosine_similarity (768维)
- **存储**: pickle + 异步加载

### 开发规范
1. **架构**: API→Services→Domains←Infrastructure (严禁反向依赖)
2. **异步**: 所有IO操作使用async/await
3. **编码**: Windows设置`PYTHONIOENCODING=utf-8`
4. **测试**: 新功能必须包含pytest测试

### 关键文件
```
src/
├── services/search_service.py           # 业务逻辑核心
├── infrastructure/search/vector_search_engine.py  # 向量检索引擎
├── domains/entities.py                  # 领域实体定义
└── api/routes.py                        # API路由

data/processed/
├── criminal/                            # 完整文本数据
│   ├── criminal_articles.pkl           # 446条法条 (0.80MB)
│   └── criminal_cases.pkl              # 17,131案例 (24.05MB)
└── vectors/                             # 向量数据
    ├── criminal_articles_vectors.pkl   # 法条向量 (1.35MB)
    └── criminal_cases_vectors.pkl      # 案例向量 (51.87MB)
```

### 数据使用
```python
# 1. 加载向量 (用于检索)
import pickle
from sklearn.metrics.pairwise import cosine_similarity

with open("data/processed/vectors/criminal_articles_vectors.pkl", "rb") as f:
    vectors_data = pickle.load(f)

# 2. 计算相似度 (向量未归一化)
similarities = cosine_similarity(query_vector, vectors_data['vectors'])

# 3. 获取完整内容 (用于展示)
with open("data/processed/criminal/criminal_articles.pkl", "rb") as f:
    full_data = pickle.load(f)
```

## 🎯 优化重点

**当前问题**: 相似度0.4-0.6偏低，需要提升精度
1. **领域微调**: 使用法条-案例映射训练专业模型
2. **Hard Negative**: 构建三元组训练数据
3. **NER抽取**: 标注犯罪要素
4. **LTR排序**: 训练LightGBM排序模型