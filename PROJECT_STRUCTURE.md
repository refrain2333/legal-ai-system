# 法智导航项目标准结构

## 项目目录标准

```
法律/ (项目根目录)
├── 📁 src/                    # 源代码 (核心业务逻辑)
│   ├── 📁 api/               # API层
│   │   ├── __init__.py
│   │   ├── app.py           # FastAPI应用
│   │   └── search_routes.py # 搜索路由
│   ├── 📁 models/            # AI模型层
│   │   ├── __init__.py
│   │   └── semantic_embedding.py # 语义向量模型
│   ├── 📁 services/          # 业务服务层
│   │   ├── __init__.py
│   │   └── retrieval_service.py # 检索服务
│   ├── 📁 data/              # 数据处理模块
│   │   ├── __init__.py
│   │   └── full_dataset_processor.py # 数据处理器
│   ├── 📁 config/            # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py      # 设置文件
│   ├── 📁 utils/             # 工具函数
│   │   ├── __init__.py
│   │   └── logger.py        # 日志工具
│   ├── __init__.py
│   └── main.py              # 主入口文件
├── 📁 tests/                  # 测试代码 (唯一测试目录)
│   ├── __init__.py
│   ├── conftest.py          # pytest配置
│   ├── test_core_functionality.py # 核心功能测试
│   ├── 📁 unit/             # 单元测试
│   ├── 📁 integration/      # 集成测试
│   └── 📁 fixtures/         # 测试固件
├── 📁 data/                   # 数据文件
│   ├── 📁 raw/              # 原始数据
│   ├── 📁 processed/        # 处理后数据
│   └── 📁 indices/          # 向量索引
├── 📁 docs/                   # 项目文档
│   ├── 📁 tasks/            # 任务文档
│   └── 📁 api/              # API文档
├── 📁 tools/                  # 工具脚本 (独立运行的脚本)
│   ├── verify_system_structure.py # 系统验证
│   └── full_vectorization_executor.py # 向量化工具
├── 📁 scripts/                # 项目脚本 (设置和初始化)
│   ├── validate_data.py     # 数据验证
│   └── 📁 init/             # 初始化脚本
│       ├── step1_env_check.py
│       ├── step2_project_setup.py
│       └── step3_final_check.py
├── start_server.py           # 服务启动脚本 (唯一启动脚本)
├── requirements_fixed.txt    # Python依赖
├── CHANGELOG.md             # 变更日志
├── README.md                # 项目说明
└── CLAUDE.md                # AI开发指导
```

## 文件命名规范

### Python模块命名
- **小写下划线**: `semantic_embedding.py`, `retrieval_service.py`
- **描述性名称**: `full_dataset_processor.py` 而不是 `processor.py`

### 类命名
- **驼峰命名**: `SemanticTextEmbedding`, `RetrievalService`
- **描述性名称**: 清楚表达功能

### 目录功能定义
- `src/`: 业务逻辑核心代码
- `tests/`: 所有测试相关代码
- `tools/`: 独立运行的工具脚本
- `scripts/`: 项目设置和初始化脚本
- `data/`: 数据文件存储
- `docs/`: 项目文档

## 禁止的结构
- ❌ 根目录散乱的.py文件
- ❌ 重复的测试目录 (src/tests/ + tests/)
- ❌ 功能重复的文件
- ❌ 临时文件混入版本控制