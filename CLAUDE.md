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
**核心技术**：FastAPI + PyTorch + Transformers + Faiss
**架构模式**：分层架构 (API → Services → AI Models → Data)

## 关键开发命令

```bash
# 环境准备（仅首次）
python scripts/init/step1_env_check.py && \
python scripts/init/step2_project_setup.py && \
python scripts/init/step3_final_check.py

# 虚拟环境管理
conda activate legal-ai  # 激活conda环境
conda env update -f environment.yml  # 更新环境

# 开发服务器
python src/main.py  # http://localhost:5005

# 单独测试运行
pytest tests/test_specific.py -v  # 运行特定测试
pytest -k "test_embedding" -v     # 运行特定模式测试

# 代码质量检查
black src/ tests/ --line-length=100  # 格式化代码
pylint src/ --rcfile=.pylintrc        # 代码检查
pytest tests/ -v --cov=src           # 测试+覆盖率
```

## AI模型架构

### 向量检索流水线
1. **文本向量化**: shibing624/text2vec-base-chinese (768维)
2. **索引构建**: Faiss IndexFlatIP (内积搜索)
3. **混合排序**: 语义相似度(70%) + 关键词匹配(30%)

### 关键配置
```python
# src/config/settings.py
MODEL_NAME = "shibing624/text2vec-base-chinese"
EMBEDDING_DIM = 768
MAX_SEQUENCE_LENGTH = 512
SIMILARITY_WEIGHT = 0.7  # 语义相似度权重
```

### 数据模型
```python
# 统一法律文档结构
@dataclass
class LegalDocument:
    id: str
    type: str  # "law" | "case"  
    title: str
    content: str
    embedding: np.ndarray
    related_ids: List[str]
```

## 代码架构

### 关键目录
- `src/models/`: AI模型实现 (待开发重点)
- `src/services/`: 业务逻辑，调用AI模型
- `src/api/`: FastAPI路由，调用services
- `src/config/`: Pydantic配置管理

### FastAPI关键约定
- 全异步处理：`async def`
- Pydantic请求/响应模型
- 中间件：CORS, 异常处理, 日志记录
- 健康检查：`GET /health`

## 开发约定

### 代码风格
- Black格式化 (100字符行长度)
- Type hints必需
- Docstring使用Google风格
- 异步优先：`async/await`

### 测试要求
- 单元测试：每个模型/服务类
- API测试：每个端点
- 集成测试：端到端流程
- 覆盖率目标：>80%

### 依赖管理
- **主要依赖文件**: `environment.yml` (conda环境) + `requirements_fixed.txt` (pip备选)
- **模型存储**: `./models/pretrained/` (自动下载shibing624/text2vec-base-chinese)
- **新依赖添加**: 先在environment.yml中添加，然后`conda env update`
- **版本固定**: Pydantic<2.0.0 (兼容性要求)

### 环境变量配置
```bash
# 关键环境变量 (.env文件)
APP_ENV=development
DEBUG=true
MODEL_CACHE_DIR=./models/pretrained
DATA_RAW_PATH=./data/raw
LOG_LEVEL=INFO
```

## 任务管理流程

### 必需步骤
1. **开始任务**: 使用TodoWrite工具创建任务列表
2. **进度跟踪**: 每完成子任务立即标记完成
3. **文档同步**: 重要变更更新CHANGELOG.md
4. **代码审查**: 完成后运行所有质量检查

### 文档位置
- 任务跟踪：`docs/tasks/CURRENT_TASKS.md`
- 变更日志：`CHANGELOG.md`
- 临时文件：`temp_YYYY-MM-DD_purpose_lifecycle.*`

## 开发状态

**已完成**: 项目架构、FastAPI框架、配置管理、数据准备、初始化脚本
**当前重点**: AI模型层实现 (src/models/)
**数据就绪**: 法律条文1.3MB + 案例16.5MB + 映射表
**环境配置**: Conda环境配置文件和pip依赖已就绪

## 数据文件说明

**位置**: `./data/raw/`
- `raw_laws(1).csv` - 法律条文 (1.3MB)
- `raw_cases(1).csv` - 案例数据 (16.5MB)  
- `精确映射表.csv` - 法条案例精确映射 (73KB)
- `精确+模糊匹配映射表.csv` - 扩展映射关系 (116KB)

## 关键注意事项

- **虚拟环境必需**：避免依赖冲突
- **异步优先**：所有IO操作使用async
- **类型安全**：全面使用类型提示
- **测试驱动**：先写测试，再实现功能
- **配置驱动**：硬编码值移至settings.py