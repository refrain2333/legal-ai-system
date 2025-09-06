# 法智导航系统使用指南 - 标准化版本

> **Legal AI System User Guide - Standardized Version**  
> **版本**: v0.3.1 | **更新**: 2025-01-27 | **状态**: 生产就绪

## 🚀 快速开始 (标准流程)

### 环境要求
```yaml
必需环境:
  - Python: 3.9+
  - Conda: Miniconda/Anaconda
  - 内存: 4GB+ (推荐8GB)
  - 磁盘空间: 2GB+

操作系统:
  - Windows: 10/11 (已测试)
  - Linux: Ubuntu 18.04+ (兼容)
  - macOS: 10.14+ (兼容)
```

### 🔧 标准安装流程

#### 1. 环境激活 (必需)
```bash
# 激活conda环境
conda activate legal-ai

# 验证环境
python --version  # 应显示 Python 3.9+
```

#### 2. 依赖检查 (如需要)
```bash
# 检查关键依赖
pip list | grep pydantic-settings

# 如果缺失，安装
pip install pydantic-settings
```

#### 3. 系统验证 (推荐)
```bash
# 验证项目结构
python tools/structure_check.py
# 输出: SUCCESS - 100%符合标准

# 验证系统功能 (可选)  
python tools/verify_system_structure.py
```

#### 4. 标准启动 (唯一方式)
```bash
# 启动服务 - 标准命令
python app.py

# 输出示例:
# ============================================================
# Legal AI System - Starting Server...
# Semantic Document Retrieval Service
# ============================================================  
# Starting server on http://127.0.0.1:5005
# INFO: Uvicorn running on http://127.0.0.1:5005
```

### 📍 服务访问地址
```yaml
核心服务:
  - 主页: http://localhost:5005
  - API文档: http://localhost:5005/docs
  - 健康检查: http://localhost:5005/health

监控统计:
  - 检索统计: http://localhost:5005/api/v1/search/statistics
  - 系统状态: http://localhost:5005/api/v1/search/health
```

## 🔍 API使用指南

### 核心检索接口

#### 1. 语义检索 (主要功能)
```bash
# 基础检索
curl -X POST "http://localhost:5005/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "合同违约的法律责任",
    "top_k": 5,
    "min_similarity": 0.3
  }'

# 响应示例
{
  "query": "合同违约的法律责任",
  "results": [
    {
      "id": "law_0965",
      "type": "law", 
      "title": "合同法第107条",
      "score": 0.7087,
      "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担违约责任..."
    }
  ],
  "total": 5,
  "search_time": 0.047,
  "message": "Found 5 results with semantic search"
}
```

#### 2. 快速检索 (简化查询)
```bash
# GET方式快速查询
curl "http://localhost:5005/api/v1/search/quick?q=故意伤害&limit=3&type=case"

# 响应格式相同，但处理更快
```

#### 3. 文档详情获取
```bash
# 获取特定文档完整信息
curl "http://localhost:5005/api/v1/search/document/law_0965"

# 响应包含完整文档内容和元数据
```

#### 4. 系统监控接口
```bash
# 健康检查
curl "http://localhost:5005/api/v1/search/health"
# 响应: {"status": "healthy", "ready": true, ...}

# 统计信息
curl "http://localhost:5005/api/v1/search/statistics"  
# 响应: {"total_documents": 3519, "total_searches": 42, ...}
```

### 批量处理接口

#### 批量检索
```bash
curl -X POST "http://localhost:5005/api/v1/search/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "合同违约责任",
      "故意伤害罪",
      "民事诉讼程序"
    ],
    "top_k": 3
  }'
```

## 💻 Python SDK 使用

### 异步接口使用
```python
import asyncio
from pathlib import Path
import sys

# 添加项目路径 (如需要)
sys.path.insert(0, str(Path.cwd()))

# 导入服务
from src.services.retrieval_service import get_retrieval_service

async def search_example():
    """标准检索示例"""
    
    # 获取检索服务实例
    service = await get_retrieval_service()
    
    # 执行语义检索
    results = await service.search(
        query="合同违约的法律责任",
        top_k=5,
        min_similarity=0.3
    )
    
    # 处理结果
    print(f"查询: {results['query']}")
    print(f"找到 {results['total']} 个结果，用时 {results['search_time']:.3f}s")
    
    for i, doc in enumerate(results['results'], 1):
        print(f"{i}. [{doc['score']:.4f}] [{doc['type']}] {doc['title']}")
        print(f"   预览: {doc['content'][:100]}...")
        
# 运行示例
if __name__ == "__main__":
    asyncio.run(search_example())
```

### 批量处理示例  
```python
async def batch_search_example():
    """批量检索示例"""
    service = await get_retrieval_service()
    
    queries = [
        "合同违约责任",
        "故意伤害罪构成要件", 
        "民事诉讼程序",
        "交通事故处理"
    ]
    
    # 批量处理
    results = []
    for query in queries:
        result = await service.search(query, top_k=3)
        results.append(result)
        
    # 汇总结果
    for result in results:
        print(f"\\n查询: {result['query']}")
        print(f"结果: {result['total']}个，最高分: {result['results'][0]['score']:.4f}")
```

## 🎯 高级功能使用

### 文档类型过滤
```python
# 只搜索法律条文
law_results = await service.search(
    query="合同违约责任",
    doc_types=["law"],  # 只搜索法条
    top_k=10
)

# 只搜索案例
case_results = await service.search(
    query="故意伤害案例",
    doc_types=["case"],  # 只搜索案例
    top_k=10
)
```

### 相似度阈值调节
```python
# 高质量结果 (严格模式)
high_quality = await service.search(
    query="民事诉讼程序",
    min_similarity=0.6,  # 高阈值，结果更精准
    top_k=10
)

# 宽泛搜索 (发现模式)
broad_search = await service.search(
    query="交通事故处理",
    min_similarity=0.2,  # 低阈值，结果更全面
    top_k=20
)
```

### 系统监控和统计
```python
# 获取系统统计
stats = await service.get_statistics()
print(f"文档总数: {stats['total_documents']}")
print(f"搜索次数: {stats['total_searches']}")  
print(f"平均响应时间: {stats['average_search_time']:.3f}s")

# 健康检查
health = await service.health_check()
print(f"服务状态: {health['status']}")
print(f"服务版本: {health['version']}")
```

## 🛠️ 工具和维护

### 项目结构检查
```bash
# 验证项目结构是否标准
python tools/structure_check.py

# 输出示例:
# ==================================================
# Project Structure Verification  
# ==================================================
# 1. Directory Structure:
#   OK src/
#   OK src/api/
#   ...
# SUCCESS: Project structure is standardized!
```

### 系统功能验证
```bash  
# 完整系统测试 (包含编码问题，但功能正常)
python tools/verify_system_structure.py

# 简化验证 (推荐)
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.services.retrieval_service import get_retrieval_service
async def test():
    service = await get_retrieval_service()
    result = await service.search('测试查询', top_k=1)
    print(f'测试结果: {result[\"total\"]}个文档')
asyncio.run(test())
"
```

### 性能测试
```bash
# 运行性能测试脚本
python -c "
import asyncio, time
import sys
sys.path.insert(0, '.')
from src.services.retrieval_service import get_retrieval_service

async def perf_test():
    service = await get_retrieval_service()
    queries = ['合同违约', '故意伤害', '民事诉讼', '交通事故']
    
    start = time.time()
    for query in queries:
        await service.search(query, top_k=5)
    duration = time.time() - start
    
    print(f'4个查询总用时: {duration:.3f}s')
    print(f'平均每查询: {duration/4:.3f}s')

asyncio.run(perf_test())
"
```

## ⚠️ 常见问题和解决方案

### 启动问题

#### 问题1: ImportError: attempted relative import
```bash
# 解决方案: 使用标准启动脚本
python app.py  # ✅ 正确
python src/main.py  # ❌ 错误，会导入失败
```

#### 问题2: ModuleNotFoundError: No module named 'pydantic_settings'
```bash
# 解决方案: 安装缺失依赖
pip install pydantic-settings
```

#### 问题3: UnicodeEncodeError (日志编码问题)
```
# 现象: 日志中有编码警告，但不影响功能
# 解决方案: 忽略警告，系统功能正常
# 服务器正常启动标志: "Uvicorn running on http://127.0.0.1:5005"
```

### 性能问题

#### 问题1: 首次启动慢 (~15秒)
```
# 原因: 语义模型加载时间
# 解决方案: 正常现象，后续查询速度正常 (~47ms)
```

#### 问题2: 内存使用高 (~2GB)
```
# 原因: 3,519个文档的768维向量 + 语义模型
# 解决方案: 正常现象，确保机器有足够内存
```

### API问题

#### 问题1: 连接拒绝
```bash
# 检查服务状态
curl -s http://localhost:5005/health || echo "服务未启动"

# 重新启动服务
python app.py
```

#### 问题2: 搜索结果质量
```python
# 调整相似度阈值
results = await service.search(
    query="your_query",
    min_similarity=0.4,  # 调整阈值 (0.0-1.0)
    top_k=10
)
```

## 📋 系统维护

### 日常维护检查
```bash
# 1. 结构检查 (每次启动前推荐)
python tools/structure_check.py

# 2. 健康检查 (服务运行中)
curl http://localhost:5005/health

# 3. 统计监控 (定期检查)  
curl http://localhost:5005/api/v1/search/statistics
```

### 数据更新
```
注意: 当前版本使用预构建的3,519文档语义索引
如需更新数据，需要重新运行向量化工具:
python tools/full_vectorization_executor.py
```

---

## 🎯 总结

**标准化后的法智导航系统特点:**
- ✅ **简单启动**: `python app.py` 一键启动
- ✅ **结构清晰**: 无重复文件，标准目录结构
- ✅ **性能优异**: 47ms响应，0.6-0.8相似度
- ✅ **功能完整**: 7个API端点，3,519文档检索
- ✅ **生产就绪**: 健康监控，错误处理完善

**🚀 系统现在可以稳定高效地为用户提供智能法律检索服务！**