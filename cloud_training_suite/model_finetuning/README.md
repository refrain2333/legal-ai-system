# 模型微调说明

本目录的脚本和文档，旨在说明如何通过“对比学习”的方法，对一个通用的预训练语言模型（如 `thunlp/Lawformer`）进行**微调（Fine-tuning）**，以获得一个在特定业务场景（如法律案例与法条匹配）下表现更优的专用模型。

## 工作流程详解

整个流程通过 `finetune_example.py` 中的示例代码进行展示，主要分为以下五步：

### 步骤 1: 加载配置

从 `config.yaml` 文件中加载所有超参数，如学习率、批大小、训练轮数等。将配置与代码分离是一个良好的工程实践。

```yaml
# from: config_example.yaml

training:
  learning_rate: 5e-5
  batch_size: 8
```

### 步骤 2: 准备“三元组”数据

对比学习的核心是“三元组（Triplet）”数据。我们需要准备一个包含大量三元组的数据集，每个三元组由锚点（Anchor）、正样本（Positive）和负样本（Negative）构成。

*   **目标**: 让模型学习到，Anchor和Positive在语义上应该“更近”，和Negative应该“更远”。

```python
# from: finetune_example.py

class TripletDataset(Dataset):
    def __init__(self, data_path):
        # ... 从jsonl文件中加载三元组数据 ...
        pass
```

### 步骤 3: 初始化模型、损失和优化器

*   **模型**: 定义 `LawformerContrastiveModel`，它在预训练模型之上增加了一个“投影头”，专门用于对比学习任务。
*   **损失函数**: 使用 `TripletLoss`，它的数学原理就是实现“拉近正样本，推远负样本”的目标。
*   **优化器**: 使用 `AdamW`，这是训练Transformer模型的主流选择。
*   **调度器**: 使用带“预热（Warmup）”的学习率调度器，有助于模型稳定训练。

```python
# from: finetune_example.py

model = LawformerContrastiveModel()
loss_fn = TripletLoss(margin=0.5)
optimizer = AdamW(model.parameters(), lr=...)
scheduler = get_linear_schedule_with_warmup(...)
```

### 步骤 4: 训练循环

这是微调的核心。程序会不断地从数据集中取出成批的三元组数据，执行一个标准的训练步骤：

1.  `optimizer.zero_grad()`: 清空上一轮的梯度。
2.  `model(...)`: 模型进行前向传播，计算出三元组的向量。
3.  `loss_fn(...)`: 计算损失值。
4.  `loss.backward()`: 根据损失，计算梯度。
5.  `optimizer.step()`: 更新模型权重。
6.  `scheduler.step()`: 更新学习率。

```python
# from: finetune_example.py

# for batch in dataloader:
#     optimizer.zero_grad()
#     anchor_vec = model(batch['anchor'])
#     ...
#     loss = loss_fn(anchor_vec, positive_vec, negative_vec)
#     loss.backward()
#     optimizer.step()
#     scheduler.step()
```

### 步骤 5: 保存模型

训练完成后，将优化后的模型权重（`state_dict`）保存到文件（如 `fine_tuned_model.pt`），以便后续的评估和部署。
