# 评估系统使用说明

## 目录结构
```
evaluation/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── eval_settings.py   # 评估参数配置
├── core/                   # 核心评估逻辑
│   ├── __init__.py
│   ├── evaluator.py       # 主评估引擎
│   └── metrics.py         # 评估指标计算
├── data/                   # 数据处理模块
│   ├── __init__.py
│   ├── ground_truth.py    # 真实数据加载
│   └── test_generator.py  # 测试数据生成
├── reports/                # 报告生成模块
│   ├── __init__.py
│   └── reporter.py        # 评估报告生成器
├── results/                # 评估结果存储
│   ├── evaluation.log     # 评估日志
│   └── *.json/*.txt       # 评估报告和结果
└── run_evaluation.py      # 主程序入口
```

## 快速开始

### 基本用法
```bash
# 完整评估（约5-10分钟）
python evaluation/run_evaluation.py

# 快速评估（约2-3分钟）
python evaluation/run_evaluation.py --quick

# 指定样本数量
python evaluation/run_evaluation.py --samples 15
```

### 评估类型
1. **法条到案例搜索**：输入法条条文，评估能否找到相关案例
2. **案例到法条搜索**：输入案例描述，评估能否找到相关法条
3. **罪名一致性评估**：评估搜索结果中的罪名一致性

### 评估指标
- **Precision@K**：前K个结果的精确率
- **Recall@K**：前K个结果的召回率
- **F1-Score**：精确率和召回率的调和平均
- **MAP**：平均精度均值
- **NDCG**：归一化折扣累积增益
- **MRR**：平均倒数排名

## 配置说明

主要配置在 `config/eval_settings.py`：

```python
EVALUATION_CONFIG = {
    "test_sample_size": 30,              # 标准模式样本数
    "quick_test_sample_size": 20,        # 快速模式样本数
    "crime_consistency_sample_size": 32, # 罪名一致性样本数
    "default_top_k": 10,                 # 默认返回结果数
    "similarity_thresholds": [0.3, 0.4, 0.5, 0.6, 0.7],
    "default_threshold": 0.4             # 相似度阈值
}
```

## 结果解读

### 综合评估分数
- **优秀**：>80%
- **良好**：60-80%
- **中等**：40-60%
- **需要改进**：<40%

### 典型结果示例
```
综合得分: 28.17%
- 法条到案例: Precision@5=0.24, Recall@5=0.31
- 案例到法条: Precision@5=0.22, Recall@5=0.28
- 罪名一致性: 一致性率=0.35
```

## 故障排除

### 常见问题
1. **模型加载失败**：检查 `.env` 中的模型路径配置
2. **数据文件缺失**：确保 `data/processed/` 目录下有必要的数据文件
3. **内存不足**：使用 `--quick` 选项减少样本数量

### 依赖要求
- Python 3.8+
- torch, transformers, scikit-learn
- 激活 `legal-ai` conda环境

## 输出文件

每次评估会生成：
- `evaluation_results_YYYYMMDD_HHMMSS.json`：详细结果数据
- `evaluation_report_YYYYMMDD_HHMMSS.txt`：可读性报告
- `evaluation.log`：运行日志

结果文件保存在 `evaluation/results/` 目录下。