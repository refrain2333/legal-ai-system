# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CLAUDE.md编写规则

**重要：此文件仅包含AI开发指导的关键信息，禁止添加以下内容**：
- 详细的安装步骤（应在README.md中）
- 完整的API文档（应在docs/api/中）
- 项目介绍和背景（应在README.md中）
- 用户手册内容（应在docs/user/中）

**此文件专注于**：
- 核心架构和技术决策
- AI开发的关键指导
- 代码约定和最佳实践
- 开发工作流程

---

## 项目核心

**法智导航** - 智能法律检索系统
**核心技术**：FastAPI + sentence-transformers + numpy + asyncio
**架构模式**：分层架构 (API → Services → AI Models → Data)
**当前版本**：v0.3.1 (第二阶段完成)

## 关键开发命令

```bash
# 环境准备（仅首次）
conda activate legal-ai  # 激活conda环境
pip install -r requirements_fixed.txt  # 安装依赖

# 系统验证
python verify_system_structure.py  # 验证系统结构

# 开发服务器
python src/main.py  # http://localhost:5005

# 代码质量
black src/ tests/ && pylint src/ && pytest
```

## AI模型架构

### 语义检索流水线 (v0.3.1)
1. **文本向量化**: shibing624/text2vec-base-chinese (768维语义向量)
2. **索引构建**: numpy向量数组 + 内积相似度计算
3. **检索排序**: 纯语义相似度排序

### 关键配置
```python
# src/models/semantic_embedding.py
MODEL_NAME = "shibing624/text2vec-base-chinese"
EMBEDDING_DIM = 768
MAX_SEQUENCE_LENGTH = 128  # 优化后长度
BATCH_SIZE = 32  # 批处理大小
```

### 数据模型
```python
# 完整语义索引结构
{
    'vectors': np.ndarray,  # (3519, 768) 语义向量矩阵
    'metadata': List[Dict],  # 文档元数据
    'model_info': Dict      # 模型信息
}
```

## 代码架构

### 关键目录 (第二阶段完成)
- `src/models/`: **semantic_embedding.py** (768维语义模型)
- `src/data/`: **full_dataset_processor.py** (3,519文档处理)
- `src/services/`: **retrieval_service.py** (v0.3.0语义服务)
- `src/api/`: FastAPI路由 (向后兼容)
- `src/config/`: Pydantic配置管理

### 项目结构规范
- **相对导入**: 使用 `from ..models.semantic_embedding import SemanticTextEmbedding`
- **模块分离**: models/data/services/api 功能清晰分离
- **无sys.path**: 禁止使用 `sys.path.append()` 硬编码路径

## 开发状态

**✅ 第二阶段已完成 (v0.3.1)**:
- 大规模数据处理 (3,519个文档)
- 语义向量检索系统 (sentence-transformers)
- 高性能服务 (47ms平均响应时间)
- 项目结构优化 (标准导入路径)
- 向后兼容API (完全兼容v0.2.0)

**📊 关键指标**:
- 文档数量: **3,519个** (法条+案例)
- 相似度质量: **0.6-0.8** (vs 原0.1-0.2)
- 响应时间: **47ms平均**
- 向量维度: **768维标准**

**🎯 生产就绪**: 系统已达到生产级别性能和稳定性

## 数据文件说明

**处理完成的数据** (v0.3.1):
- `data/processed/full_dataset.pkl` - 3,519个文档 (1.9MB)
- `data/indices/complete_semantic_index.pkl` - 语义索引 (11.2MB)

**原始数据** (`./data/raw/`):
- `raw_laws(1).csv` - 法律条文 (1.3MB)
- `raw_cases(1).csv` - 案例数据 (16.5MB)

## 关键注意事项

- **环境**: conda环境 `legal-ai` 必需
- **内存需求**: ~2GB (模型加载)
- **导入规范**: 使用相对导入，避免sys.path
- **异步优先**: 所有IO操作使用async
- **版本兼容**: 完全向后兼容API接口