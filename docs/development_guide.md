# 法智导航项目 - 开发规范与工作流程

## 📋 总体原则

### 开发理念
- **质量优先**: 代码质量胜过开发速度
- **渐进式开发**: 小步快跑，持续迭代
- **文档驱动**: 先写文档，再写代码
- **测试驱动**: 核心功能必须有测试覆盖

### 协作原则
- **透明沟通**: 所有重要决定都要记录
- **代码审查**: 关键代码必须经过审查
- **知识共享**: 及时分享技术心得和踩坑经验

## 🔧 开发环境规范

### Python环境管理
```bash
# 使用虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 开发工具安装
pip install pre-commit
pre-commit install
```

### IDE配置推荐
- **VSCode**: 推荐插件
  - Python
  - Pylance
  - Black Formatter
  - GitLens
  - Python Docstring Generator

## 📝 代码编写规范

### 命名规范
```python
# 变量和函数: snake_case
user_query = "房屋租赁纠纷"
def process_legal_text(text: str) -> str:
    pass

# 类名: PascalCase
class LegalEmbedder:
    pass

# 常量: UPPER_SNAKE_CASE
MAX_SEQUENCE_LENGTH = 512
MODEL_CACHE_DIR = "./models/cache"

# 私有成员: 单下划线前缀
class APIService:
    def _validate_input(self, data):
        pass
```

### 文档字符串规范
```python
def search_legal_documents(
    query: str, 
    top_k: int = 10,
    include_cases: bool = True
) -> List[Dict]:
    """
    搜索相关的法律文档。
    
    Args:
        query (str): 用户查询文本
        top_k (int, optional): 返回结果数量. Defaults to 10.
        include_cases (bool, optional): 是否包含案例. Defaults to True.
    
    Returns:
        List[Dict]: 搜索结果列表，每个结果包含id, title, content, score等字段
        
    Raises:
        ValueError: 当query为空字符串时
        RuntimeError: 当模型未正确加载时
        
    Example:
        >>> results = search_legal_documents("合同违约", top_k=5)
        >>> len(results) <= 5
        True
    """
    pass
```

### 类型注解规范
```python
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
import numpy as np

# 函数注解
def load_legal_data(file_path: str) -> pd.DataFrame:
    pass

def build_embeddings(texts: List[str]) -> np.ndarray:
    pass

def search_similar(
    query_embedding: np.ndarray,
    index: 'faiss.Index'
) -> Tuple[np.ndarray, np.ndarray]:
    pass

# 类属性注解
class LegalRetriever:
    model_name: str
    embedding_dim: int
    index: Optional['faiss.Index'] = None
```

## 🔍 代码质量检查

### Pre-commit Hook设置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.8.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
```

### 代码检查命令
```bash
# 格式化代码
black src/ tests/

# 导入排序
isort src/ tests/ --profile black

# 代码检查
pylint src/
flake8 src/

# 类型检查（可选）
mypy src/ --ignore-missing-imports
```

## 🧪 测试规范

### 测试结构
```
tests/
├── unit/              # 单元测试
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_api.py
├── integration/       # 集成测试
│   ├── test_full_pipeline.py
│   └── test_api_integration.py
├── fixtures/          # 测试数据
│   └── sample_data.py
└── conftest.py        # pytest配置
```

### 测试编写规范
```python
import pytest
from unittest.mock import Mock, patch
from src.models.embedder import LegalEmbedder

class TestLegalEmbedder:
    """测试法律文本嵌入器"""
    
    @pytest.fixture
    def embedder(self):
        """创建测试用的嵌入器实例"""
        return LegalEmbedder(model_name="test-model")
    
    def test_embed_text_normal(self, embedder):
        """测试正常文本嵌入"""
        text = "这是一个测试文本"
        embedding = embedder.embed_text(text)
        
        assert embedding is not None
        assert len(embedding.shape) == 2
        assert embedding.shape[0] == 1
    
    def test_embed_text_empty(self, embedder):
        """测试空文本处理"""
        with pytest.raises(ValueError):
            embedder.embed_text("")
    
    @patch('src.models.embedder.torch.cuda.is_available')
    def test_device_selection(self, mock_cuda, embedder):
        """测试设备选择逻辑"""
        mock_cuda.return_value = False
        device = embedder._get_device()
        assert device == "cpu"
```

### 测试运行
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_models.py

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行测试并显示详细输出
pytest -v -s
```

## 📊 性能测试规范

### 基准测试
```python
import time
import statistics
from typing import List

def benchmark_search_speed(search_func, queries: List[str], iterations: int = 10):
    """基准测试搜索速度"""
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        for query in queries:
            search_func(query)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'mean_time': statistics.mean(times),
        'std_time': statistics.stdev(times),
        'min_time': min(times),
        'max_time': max(times)
    }
```

## 📁 文件组织规范

### 导入顺序
```python
# 1. 标准库导入
import os
import sys
from typing import List, Dict

# 2. 第三方库导入
import pandas as pd
import numpy as np
import torch
from transformers import AutoModel

# 3. 本地导入
from src.utils.config import Config
from src.models.base import BaseModel
```

### 模块结构
```python
"""
模块文档字符串：描述模块功能和主要类/函数
"""

# 常量定义
DEFAULT_MODEL_NAME = "shibing624/text2vec-base-chinese"
MAX_BATCH_SIZE = 32

# 类定义
class MainClass:
    pass

# 函数定义
def main_function():
    pass

# 主程序入口
if __name__ == "__main__":
    main_function()
```

## 🚀 部署规范

### Docker文件规范
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量管理
```bash
# .env 文件示例
MODEL_PATH=/app/models
LOG_LEVEL=INFO
API_PORT=8000
REDIS_URL=redis://localhost:6379
```

## 📋 提交规范

### Commit Message格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type类型
- **feat**: 新功能
- **fix**: Bug修复
- **docs**: 文档更改
- **style**: 代码格式化
- **refactor**: 重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

#### 示例
```
feat(api): 添加法律文档搜索接口

- 实现基于向量检索的搜索功能
- 支持多种文档类型过滤
- 添加搜索结果相关性排序

Closes #123
```

## 🔐 安全规范

### 敏感信息处理
- 使用环境变量存储API密钥
- 不在代码中硬编码密码或令牌
- 敏感配置文件添加到.gitignore

### 数据安全
- 法律数据不得外传
- 用户查询日志脱敏处理
- 定期清理临时文件

## 📈 监控规范

### 日志规范
```python
from loguru import logger

# 配置日志
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

# 使用示例
logger.info("开始处理用户查询: {}", query)
logger.error("模型加载失败: {}", error_msg)
logger.debug("搜索结果: {} 条", len(results))
```

### 性能监控
```python
import time
from functools import wraps

def monitor_time(func):
    """监控函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} 执行时间: {end-start:.2f}秒")
        return result
    return wrapper
```

---

**⚠️ 重要提醒**: 
- 本规范是项目质量的底线，不是上限
- 遇到特殊情况可以申请例外，但需要充分说明理由
- 规范会随项目发展持续更新，请及时关注变化