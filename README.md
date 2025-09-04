# 法智导航 - 智能法律匹配与咨询系统

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 项目简介

法智导航（Legal Navigation AI）是一个基于深度学习的智能法律检索系统，能够理解用户的自然语言查询，并精准匹配相关的法律条文和案例，提供专业的法律咨询服务。

### ✨ 核心功能
- 🔍 **智能语义检索**: 支持自然语言查询，理解用户真实意图
- ⚖️ **精准法律匹配**: 基于法律领域精调模型，提供高准确度匹配
- 🕸️ **知识图谱关联**: 展示法条与案例间的关联关系
- 🤖 **智能解释**: 将复杂法条转换为通俗易懂的解释

### 🚀 技术特色
- **语义向量检索**: 使用sentence-transformers进行文本向量化
- **领域模型精调**: 基于法律数据的专业模型训练
- **混合排序算法**: 语义相似度 + 关键词匹配
- **可解释AI**: 提供检索结果的解释和关联分析

## 📦 快速开始

### 环境要求
- Python 3.9+
- 8GB+ 内存推荐
- （可选）NVIDIA GPU用于模型训练

### 安装步骤

1. **进入项目目录**
```bash
cd "C:\Users\lenovo\Desktop\法律"
# 项目已经准备就绪
```

2. **环境检查 (重要!)**
```bash
# 检查当前环境状态
python scripts/env_check.py
```

3. **创建虚拟环境 (强烈推荐)**

**方案一：Conda环境 (推荐，您已有Miniconda)**
```bash
# 创建专用环境
conda create -n legal-ai python=3.9 -y

# 激活环境
conda activate legal-ai
```

**方案二：Python venv环境**
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境 (Windows)
venv\Scripts\activate

# 激活环境 (Linux/Mac)
source venv/bin/activate
```

4. **安装依赖 (在虚拟环境中)**
```bash
pip install -r requirements.txt
```

5. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件设置必要的环境变量
```

6. **数据已准备就绪**
```bash
# 数据文件已在 data/raw/ 目录中：
# ✓ raw_laws(1).csv        - 法律条文数据 (1.3MB)
# ✓ raw_cases(1).csv       - 案例数据 (16.5MB)  
# ✓ 精确映射表.csv          - 精确映射关系 (73KB)
# ✓ 精确+模糊匹配映射表.csv  - 扩展映射关系 (116KB)
```

7. **环境验证**
```bash
# 验证虚拟环境和依赖
python scripts/env_check.py

# 项目初始化检查
python scripts/simple_init.py
```

8. **启动服务**
```bash
python src/main.py
```

服务启动后访问: http://localhost:5005

## 🏗️ 项目架构

```
法律/ (项目根目录)
├── src/                    # 核心源代码
│   ├── api/               # API接口层
│   ├── models/            # AI模型层
│   ├── services/          # 业务逻辑层
│   ├── utils/             # 工具函数
│   └── config/            # 配置管理
├── data/                  # 数据存储  
│   └── raw/               # ✓ 原始数据已就绪
├── models/                # AI模型文件
├── docs/                  # 项目文档
├── tests/                 # 测试代码
└── scripts/               # ✓ 工具脚本 (初始化/验证)
```

## 🔧 开发指南

### 代码规范
```bash
# 代码格式化
black src/ tests/

# 代码检查
pylint src/

# 运行测试
pytest
```

### 提交规范
```bash
git commit -m "feat(api): 添加搜索接口"
git commit -m "fix(model): 修复向量化bug"
git commit -m "docs: 更新API文档"
```

## 📊 开发路线图

- [x] **阶段1**: 项目初始化和基础架构
- [ ] **阶段2**: 核心检索功能实现  
- [ ] **阶段3**: 模型精调和优化
- [ ] **阶段4**: 系统集成和部署

## 📚 文档

- [API参考](docs/api/README.md)
- [架构设计](docs/architecture/README.md)
- [开发指南](docs/development/README.md)
- [部署文档](docs/deployment/README.md)
- [用户手册](docs/user/README.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系我们

- 📧 Email: contact@legal-navigation-ai.com
- 💬 讨论群: [技术交流群链接]
- 🐛 Bug报告: [GitHub Issues](https://github.com/legal-navigation-ai/issues)

---

**⚠️ 免责声明**: 本系统提供的法律信息仅供参考，不构成正式的法律建议。具体法律问题请咨询专业律师。