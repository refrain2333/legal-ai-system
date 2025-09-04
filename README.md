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

1. **克隆项目**
```bash
git clone <repository-url>
cd legal-navigation-ai
```

2. **创建虚拟环境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件设置必要的环境变量
```

5. **准备数据**
```bash
# 将数据文件放入 data/raw/ 目录
# - raw_laws(1).csv
# - raw_cases(1).csv  
# - 精确映射表.csv
```

6. **启动服务**
```bash
python src/main.py
```

服务启动后访问: http://localhost:8000

## 🏗️ 项目架构

```
legal-navigation-ai/
├── src/                    # 核心源代码
│   ├── api/               # API接口层
│   ├── models/            # AI模型层
│   ├── services/          # 业务逻辑层
│   └── utils/             # 工具函数
├── data/                  # 数据存储
├── models/                # AI模型文件
├── config/                # 配置管理
├── docs/                  # 项目文档
├── tests/                 # 测试代码
└── scripts/               # 工具脚本
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