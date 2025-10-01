# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 法智导航 - 刑事法律AI检索系统开发指南

## 🎯 项目状态
- **领域**: 仅刑事法律 (416条刑法条文 + 17,131个刑事案例)
- **技术**: thunlp/Lawformer + 768维向量 + DDD架构
- **效果**: 相似度0.4-0.6，响应47ms
- **阶段**: 模型已升级到Lawformer，精度优化中

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
- **模型**: thunlp/Lawformer
- **维度**: 768维 float32 (未归一化)
- **相似度**: 必须使用cosine_similarity
- **性能**: 加载2-3秒，内存500MB

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

### 必需开发命令
```bash
# ⚠️ 关键：确保激活正确的Python环境
conda activate legal-ai         # 激活位于C:\Users\lenovo\Miniconda3\envs\legal-ai\的环境

# 安装依赖
pip install -r requirements.txt # 核心依赖包
conda install scikit-learn      # 确保向量计算库正确安装

# 启动服务
python app.py                    # 生产模式启动
uvicorn src.api.app:create_app --host 127.0.0.1 --port 5006 --reload  # 开发模式(推荐)

# 代码质量保证 (必运行)
black src/ --line-length=100    # 代码格式化
isort src/ --profile black --line-length 100  # 导入排序
pylint src/ --rcfile=.pylintrc  # 代码规范检查
flake8 src/ --max-line-length=100 --extend-ignore=E203,W503  # 语法检查

# 测试
pytest -v                       # 运行所有测试(详细模式)
pytest tests/ -k "test_search"  # 运行特定测试
pytest --tb=line               # 错误追踪简化

# Git提交前检查
pre-commit run --all-files     # 运行代码质量检查
```

## ⚠️ 环境和依赖要求
- **Python环境**: `C:\Users\lenovo\Miniconda3\envs\legal-ai\` (必须激活: `conda activate legal-ai`)
- **核心依赖**: torch>=1.13.0, transformers>=4.21.0, faiss-cpu>=1.7.2, scikit-learn
- **模型路径**: Lawformer模型缓存在 `./.cache/transformers/`
- **Windows编码**: 设置 `PYTHONIOENCODING=utf-8` 避免中文乱码

### 技术栈
- **AI**: thunlp/Lawformer (专业法律领域模型)
- **Web**: FastAPI + Uvicorn (端口5006)
- **向量**: numpy cosine_similarity (768维)
- **存储**: pickle + 异步加载

### 开发规范
1. **架构**: API→Services→Domains←Infrastructure (严禁反向依赖)
2. **异步**: 所有IO操作使用async/await模式
3. **向量计算**: 必须使用cosine_similarity，向量未归一化
4. **数据加载**: 使用pickle格式，分离vectors/和criminal/目录
5. **临时文件**: 创建临时测试文件时必须命名为*_temp.py，完成后删除
6. **Git提交**: 重大功能更新前必须运行pre-commit检查

### 关键文件和架构理解
```
src/
├── api/
│   ├── app.py                          # FastAPI应用创建，启动管理，前端服务
│   ├── routes.py                       # API路由定义
│   └── models.py                       # API数据模型
├── services/
│   └── search_service.py               # 搜索业务逻辑核心，封装API与基础设施层
├── domains/
│   ├── entities.py                     # 核心实体(LegalDocument, Article, Case)
│   ├── repositories.py                 # 存储库接口定义
│   └── value_objects.py                # 值对象(SearchQuery, SearchResult)
├── infrastructure/
│   ├── search/
│   │   ├── vector_search_engine.py     # 增强语义搜索引擎入口
│   │   ├── core/search_coordinator.py  # 搜索协调器，统一管理搜索流程
│   │   └── storage/data_loader.py      # 数据加载管理
│   └── repositories/
│       └── legal_document_repository.py # 文档存储库实现
└── config/
    └── settings.py                     # 配置管理

data/processed/                         # 双层数据存储架构
├── criminal/                           # 完整文本数据 (展示用)
│   ├── criminal_articles.pkl          # 446条法条 (0.80MB)
│   └── criminal_cases.pkl             # 17,131案例 (24.05MB)
└── vectors/                            # 向量数据 (检索用)
    ├── criminal_articles_vectors.pkl   # 法条向量 (1.35MB)
    └── criminal_cases_vectors.pkl      # 案例向量 (51.87MB)
```

### 搜索流程理解
1. **请求路径**: API Routes → Search Service → Legal Document Repository → Vector Search Engine
2. **数据流**: 查询文本 → Lawformer编码 → 向量相似度计算 → 结果排序 → 完整内容加载
3. **核心组件**:
   - `SearchCoordinator`: 统一搜索协调，管理法条和案例的混合搜索
   - `SearchService`: 业务逻辑封装，处理查询验证和结果转换
   - `VectorSearchEngine`: 语义搜索引擎，负责底层相似度计算
   - `MultiRetrievalEngine`: 多路召回引擎，支持Query2Doc+HyDE增强
   - `KnowledgeEnhancedEngine`: 知识图谱增强搜索引擎

### 调试和开发工具
- **调试接口**: `src/types/debug_interfaces.py` 提供模块追踪功能
- **知识图谱**: 支持法条-案例关系推理 (`src/infrastructure/knowledge/`)
- **LLM增强**: 支持Query2Doc和HyDE查询扩展 (`src/infrastructure/llm/`)

### 环境和前端访问
- **Python环境路径**: `C:\Users\lenovo\Miniconda3\envs\legal-ai\` ⚠️ 关键环境位置
- **环境激活**: `conda activate legal-ai`
- **服务端口**: 5006 (http://127.0.0.1:5006)
- **前端界面**: http://127.0.0.1:5006/ui/ 或直接打开 frontend/index.html
- **API文档**: http://127.0.0.1:5006/docs (Swagger自动生成)
- **健康检查**: http://127.0.0.1:5006/health

### 重要配置文件
- **.env**: 环境变量配置 (模型路径、端口设置、LLM提供商配置等)
- **.pre-commit-config.yaml**: Git提交前检查 (black, isort, flake8, bandit安全扫描)
- **pytest.ini**: 测试配置 (testpaths=tests, 告警过滤)
- **requirements.txt**: 依赖管理 (torch, transformers, faiss-cpu, fastapi等)

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

## 前端开发规则

### 界面设计要求
- **禁止使用emoji表情符号**: 前端界面和状态显示不使用emoji，改用文字或图标字体
- **状态指示器**: 使用CSS样式或Font Awesome图标替代emoji
- **文字描述**: 优先使用清晰的中文文字描述状态和功能
- **专业性**: 保持界面的专业性和严肃性，符合法律系统的特性