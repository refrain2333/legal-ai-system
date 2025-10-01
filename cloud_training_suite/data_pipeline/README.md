# 数据处理流水线说明

本目录的脚本和文档，旨在说明一个完整的数据处理流水线，其最终目标是将**非结构化的原始法律文本**（如Markdown、JSON文件），转化为AI模型可以理解和使用的**结构化向量数据**。

## 工作流程详解

整个流程通过 `pipeline_example.py` 中的示例代码进行展示，主要分为以下四步：

### 步骤 1: 初始化工具

在开始任何处理之前，需要准备好两个核心工具：一个数据处理器和一个AI模型封装器（Embedder）。

*   **`LegalDataProcessor`**: 负责读取、解析和清洗原始文件。
*   **`LawformerEmbedder`**: 负责加载预训练的 `Lawformer` 模型，用于后续的向量化步骤。

```python
# from: pipeline_example.py

# 1. 定义核心类骨架
class LegalDataProcessor:
    # ...
    def process_criminal_law(self, file_path):
        # ...
        pass

class LawformerEmbedder:
    # ...
    def encode(self, texts: list, batch_size: int = 32):
        # ...
        pass

# 2. 在主函数中初始化
processor = LegalDataProcessor()
embedder = LawformerEmbedder()
```

### 步骤 2: 处理原始文本

调用 `LegalDataProcessor`，将磁盘上的原始文件（如`刑法.md`）解析成结构化的Python对象列表。这一步是典型的ETL（提取、转换、加载）过程。

```python
# from: pipeline_example.py

processed_laws = processor.process_criminal_law("raw_data/刑法.md")

# 处理完后，通常会用pickle等工具将结果保存，避免重复劳动
processor.save_to_pickle("processed_data/")
```

### 步骤 3: 文本向量化

这是将文本“AI化”的关键一步。我们调用 `LawformerEmbedder` 的 `encode` 方法，将干净的文本内容批量送入AI模型，模型会为每一段文本输出一个768维的向量。

```python
# from: pipeline_example.py

# 提取需要向量化的文本内容
law_contents = [item["content"] for item in processed_laws]

# 批量进行向量化，效率高
law_vectors = embedder.encode(law_contents, batch_size=64)
```

### 步骤 4: 保存向量结果

最后，将上一步生成的向量，连同它们的元数据（ID、标题等）打包成一个字典，并保存为文件。这个文件就是流水线的最终产物，可以直接用于后续的模型训练或信息检索任务。

```python
# from: pipeline_example.py

vector_package = {
    'vectors': law_vectors,
    'metadata': [{'id': item['id']} for item in processed_laws],
    'model_name': 'thunlp/Lawformer'
}

# with open("vectors/law_vectors.pkl", "wb") as f:
#     pickle.dump(vector_package, f)
print(f"向量包已保存，包含 {law_vectors.shape[0]} 个向量。")
```
