# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目核心

**法智导航** - 智能法律检索系统 v0.4.0 (增强评分版)
**核心技术**：FastAPI + sentence-transformers + numpy + asyncio + jieba
**架构模式**：分层异步架构 (API → Services → AI Models → Data)
**数据规模**：3,519个法律文档，768维语义向量，~40ms平均响应
**新增特性**：智能关键词提取 + 分数校准 + 多算法融合

## 关键开发命令

```bash
# 环境激活 (必需)
conda activate legal-ai

# 依赖安装
pip install -r requirements_fixed.txt  # 推荐使用
pip install pydantic-settings  # 如果单独缺失
pip install jieba  # 中文分词和关键词提取 (v0.4.0新增)

# 标准启动 (正确路径)
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" app.py  # http://127.0.0.1:5005
# 或使用conda环境
conda activate legal-ai && python app.py

# 结构验证
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/structure_check.py
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/verify_system_structure.py
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/verify_project_structure.py

# 完整向量化 (重建索引)
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/full_vectorization_executor.py

# 动态法律词典生成 (v0.4.0新增)
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/generate_dynamic_legal_dictionary.py

# 测试
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tests/test_core_functionality.py  # 核心功能测试
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" -m pytest tests/  # 完整测试套件
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" -m pytest tests/unit/  # 单元测试
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" -m pytest tests/integration/  # 集成测试

# 代码质量检查
pylint src/  # 代码质量分析
black src/  # 代码格式化
isort src/  # import排序
```

## AI模型架构

### 语义检索流水线 (已实现)
1. **文本向量化**: sentence-transformers/shibing624/text2vec-base-chinese
2. **向量存储**: numpy arrays (3519, 768) + pickle序列化
3. **相似度计算**: dot product similarity (已归一化)
4. **结果排序**: numpy argsort，支持type/similarity过滤

### 增强评分系统 (v0.4.0新增)
1. **分数校准**: 三段式映射，解决分数过高问题 (0.6-0.8 → 0.1-0.9)
2. **智能关键词提取**: TF-IDF + TextRank + KeyBERT + 动态法律词典
3. **多算法融合**: 语义(70%) + 关键词(20%) + 类型相关性(10%)
4. **动态权重调整**: semantic_focused/keyword_focused/balanced 三种模式

### 关键模型配置
```python
# src/config/settings.py
MODEL_NAME = "shibing624/text2vec-base-chinese"
EMBEDDING_DIM = 768  # 固定维度
MAX_SEQUENCE_LENGTH = 512
DEFAULT_TOP_K = 10
```

### 核心数据结构
```python
# 索引数据格式 (complete_semantic_index.pkl)
{
    'vectors': np.ndarray(3519, 768),  # 语义向量矩阵
    'metadata': List[Dict]  # 文档元数据
}

# 文档元数据结构
{
    'id': 'law_0001',
    'type': 'law',  # 'law' | 'case'
    'title': str,
    'content_preview': str,
    'source': str
}
```

## 代码架构 (标准化后)

### 核心模块职责
- `src/models/semantic_embedding.py`: sentence-transformers语义向量化
- `src/services/retrieval_service.py`: 检索服务单例，向后兼容API
- `src/services/enhanced_scoring_service.py`: 增强评分服务 (v0.4.0新增)
- `src/services/smart_keyword_extractor.py`: 智能关键词提取器 (v0.4.0新增)
- `src/api/search_routes.py`: 7个RESTful端点
- `src/data/full_dataset_processor.py`: 3,519文档处理流水线

### 关键导入模式
```python
# 正确的相对导入 (已修复)
from ..models.semantic_embedding import SemanticTextEmbedding
from ..services.retrieval_service import get_retrieval_service
from ..services.enhanced_scoring_service import get_enhanced_scoring_service  # v0.4.0新增
from ..services.smart_keyword_extractor import get_smart_keyword_extractor  # v0.4.0新增

# 避免sys.path.append() - 已全部清理
```

### API端点架构
```python
# 7个生产级端点
POST /api/v1/search/          # 完整语义检索
GET  /api/v1/search/quick     # 快速检索 
GET  /api/v1/search/document/{id}  # 文档详情
GET  /api/v1/search/statistics     # 系统统计
GET  /api/v1/search/health         # 健康检查
POST /api/v1/search/batch          # 批量检索
POST /api/v1/search/rebuild        # 索引重建
```

## 启动和部署

### 标准启动流程
```python
# app.py - 唯一启动脚本
def main():
    # 路径设置
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # 应用创建
    from src.api.app import create_app
    app = create_app()
    
    # 服务器启动
    uvicorn.run(app, host="127.0.0.1", port=5005, reload=False)
```

### 性能特征
- **首次启动**: ~15秒 (模型加载)
- **内存使用**: ~2GB (合理范围)
- **查询性能**: 47ms平均响应
- **相似度质量**: 0.6-0.8 (vs 原0.1-0.2)

## 开发约定

### 代码风格
- **异步优先**: 所有IO使用async/await + ThreadPoolExecutor
- **类型安全**: 完整type hints + Pydantic
- **相对导入**: from ..module import (已标准化)
- **单例模式**: get_retrieval_service()全局实例

### 文件组织规则
- **启动脚本**: 仅`app.py` (其他已清理)
- **工具脚本**: 统一放置`tools/`目录
- **测试文件**: 统一`tests/`目录 (不在src/tests/)
- **临时文件**: `temp_YYYY-MM-DD_*` 命名规范

### 依赖管理
```bash
# requirements_fixed.txt (生产依赖)
sentence-transformers>=2.2.2  # 语义模型核心
pydantic-settings>=2.0.0      # 配置管理 (必需)
numpy>=1.21.0                 # 向量计算
fastapi>=0.100.0              # API框架
uvicorn[standard]>=0.18.0     # ASGI服务器
torch>=1.13.0                 # 深度学习框架
transformers>=4.21.0          # Transformer模型

# 开发工具依赖
pytest>=7.1.0                 # 测试框架
pytest-asyncio>=0.19.0        # 异步测试
pylint>=2.15.0               # 代码质量
black>=22.8.0                # 代码格式化
isort>=5.10.0                # import排序
```

## 数据和索引

### 数据位置
```
data/
├── raw/                      # 原始CSV文件
│   ├── 法律条文.csv         # 2,729个法条
│   └── 案例.csv             # 790个案例
├── processed/               # 处理后数据
│   ├── full_dataset.pkl    # 结构化数据 1.9MB
│   └── dynamic_legal_dictionary.pkl  # 动态法律词典 (v0.4.0新增)
└── indices/                # 向量索引
    └── complete_semantic_index.pkl  # 语义索引 11.2MB
```

### 索引重建
```bash
# 完整重建流程 (3-5分钟)
python tools/full_vectorization_executor.py
# 输出: 处理3,519文档 -> 11.2MB索引

# 动态法律词典重建 (v0.4.0新增)
python tools/generate_dynamic_legal_dictionary.py
# 输出: 从3,519文档提取127个专业法律词汇
```

## 测试和验证

### 测试架构
```bash
# 测试结构
tests/
├── conftest.py              # pytest配置和fixtures
├── fixtures/                # 测试数据fixtures
├── unit/                    # 单元测试
├── integration/             # 集成测试
└── test_core_functionality.py  # 核心功能测试套件

# 运行测试
python tests/test_core_functionality.py  # 快速核心测试
pytest tests/unit/                       # 单元测试
pytest tests/integration/               # 集成测试
pytest tests/ -v                        # 详细输出全部测试
pytest tests/ --asyncio-mode=auto       # 异步测试模式
```

### 验证工具
```bash
# 结构检查 (建议每次开发前运行)
python tools/structure_check.py           # 验证标准化结构
python tools/verify_system_structure.py   # 导入+功能测试
python tools/verify_project_structure.py  # 项目结构验证

# 工具脚本说明
tools/
├── structure_check.py                     # 项目结构标准化检查
├── verify_system_structure.py            # 系统结构和导入验证
├── verify_project_structure.py           # 项目整体结构验证
├── full_vectorization_executor.py        # 完整向量化重建工具
└── generate_dynamic_legal_dictionary.py  # 动态法律词典生成器 (v0.4.0新增)
```

## 常见问题解决

### 启动问题
```bash
# ImportError: attempted relative import
python app.py  # ✅ 正确 (标准启动脚本)
python src/main.py  # ❌ 错误 (相对导入失败)

# ModuleNotFoundError: pydantic_settings  
pip install pydantic-settings  # ✅ 解决方案
```

### 性能问题
```python
# 首次启动慢 (~15秒): 正常现象，模型加载
# 后续查询快 (~40ms): 模型已缓存 + 增强评分优化
# 内存使用高 (~2GB): 3,519文档向量 + 模型权重
# 关键词匹配0分: 需要先运行动态词典生成工具 (v0.4.0)
```

## 架构升级记录

### v0.4.0 (增强评分版) - 2025-01-27
- ✅ **分数校准系统**: 解决分数过高问题，0.6-0.8 → 0.1-0.9区间重分布
- ✅ **智能关键词提取**: TF-IDF + TextRank + KeyBERT多算法融合
- ✅ **动态法律词典**: 从3,519文档自动提取127个专业词汇
- ✅ **多信号评分**: 语义+关键词+类型相关性融合，动态权重调整
- ✅ **噪声检测**: 无关查询分数从0.8→0.1，显著提升准确性
- ✅ **向后兼容**: 可选启用`enable_enhanced_scoring=True`
- ✅ **缓存优化**: 关键词提取结果缓存，提升响应速度

### v0.3.1 (语义检索版)
- ✅ 语义检索: TF-IDF → sentence-transformers
- ✅ 数据规模: 150 → 3,519文档 (+2,346%)  
- ✅ 检索质量: 0.1-0.2 → 0.6-0.8相似度 (+400%)
- ✅ 项目结构: 标准化，清理9个重复文件
- ✅ 向后兼容: 100%保持原有API

### 关键技术决策
- **模型选择**: shibing624/text2vec-base-chinese (中文优化)
- **存储格式**: pickle (性能) vs JSON (可读性)
- **异步架构**: asyncio + ThreadPoolExecutor (CPU密集计算)
- **单例服务**: 内存共享，避免重复加载
- **关键词算法**: jieba分词 + TF-IDF/TextRank双重提取 (v0.4.0)
- **评分策略**: 校准+融合+动态权重，解决分数虚高 (v0.4.0)