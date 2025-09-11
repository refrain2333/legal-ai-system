# 刑事数据集说明文档

> **目录作用**：集中存放"刑法条文、刑事案例及相关衍生数据"的**结构化与预处理结果**，供后续检索、语义匹配、知识图谱构建与模型训练使用。所有数据均来源于公开裁判文书与官方法律文本，经过脚本清洗、去噪、标准化处理。

> **使用场景**  
> • 后端 API 实时检索/相似度匹配的原始数据源  
> • 数据分析与可视化  
> • 机器学习模型训练与LLM微调  
> • 司法知识图谱构建  
> • 向量化处理的输入数据（配合tools/data_processing/criminal_data_vectorizer.py）

## 文件概览

| 文件名 | 大小 (MB) | 记录数 | 数据类型 | 描述 |
|---|---|---|---|---|
| **criminal_articles.pkl** | 0.80 | 446 | list[CriminalArticle] | **核心法条数据** - 包含完整内容 |
| **criminal_cases.pkl** | 24.05 | 17,131 | list[CriminalCase] | **核心案例数据** - 包含完整案情事实 |
| article_case_mappings.pkl | 0.05 | 183 | dict | 法条 ↔ 案例映射关系 |
| crime_type_analysis.pkl | 0.19 | 202 | dict | 罪名统计分析数据 |
| criminal_professional_dictionary.pkl | 0.00 | 8 | dict | 刑法专业词典 |
| criminal_law_summary.json | - | - | json | 数据集统计摘要 |
| criminal_professional_dictionary.json | - | - | json | 专业词典JSON版本 |

> **重要说明**：
> - `criminal_articles.pkl` 和 `criminal_cases.pkl` 是**核心数据文件**，包含完整的文本内容
> - 向量化处理工具会从这两个文件读取数据并生成 `data/processed/vectors/` 目录下的向量文件
> - 其他文件为分析和映射数据，用于增强搜索和统计功能

## 核心数据结构详解

### 1. criminal_articles.pkl - 刑法条文数据

**数据类型**: `list[CriminalArticle]`  
**记录数量**: 446 条法条  
**包含内容**: 中华人民共和国刑法及相关司法解释

#### 数据结构字段：
```python
class CriminalArticle:
    article_number: int        # 条文号码
    title: str                # 条文标题（完整）
    content: str              # 条文内容（完整文本）
    full_text: str            # 条文全文（格式化版本）
    chapter: str              # 所属章节
    section: str | None       # 所属节次（可能为空）
    related_cases: list       # 关联案例ID列表
    crime_types: list         # 相关罪名列表
    document_id: str          # 文档唯一标识符
```

#### 示例数据：
```python
# 第一条记录示例
article = criminal_articles[0]
print(f"条文号: {article.article_number}")      # 1
print(f"标题: {article.title}")                  # "中华人民共和国刑法 第1条"
print(f"内容: {article.content}")                # "为了惩罚犯罪，保护人民，根据宪法..."
print(f"章节: {article.chapter}")                # "第一章 刑法的任务、基本原则和适用范围"
```

### 2. criminal_cases.pkl - 刑事案例数据

**数据类型**: `list[CriminalCase]`  
**记录数量**: 17,131 个案例  
**包含内容**: 真实刑事案例的案情事实、罪名、量刑等信息

#### 数据结构字段：
```python
class CriminalCase:
    case_id: str                    # 案例唯一标识符
    fact: str                      # 案件事实（完整描述）
    accusations: list[str]         # 指控罪名列表
    relevant_articles: list[int]   # 相关法条编号
    sentence_info: dict           # 量刑信息
    criminals: list[str]          # 犯罪人员列表
    case_summary: str             # 案例摘要
    related_articles_docs: list   # 相关法条文档ID
```

#### 量刑信息结构：
```python
sentence_info = {
    'imprisonment_months': int,    # 有期徒刑月数
    'fine_amount': int,           # 罚金金额（元）
    'death_penalty': bool,        # 是否死刑
    'life_imprisonment': bool     # 是否无期徒刑
}
```

#### 示例数据：
```python
# 第一个案例示例
case = criminal_cases[0]
print(f"案例ID: {case.case_id}")                      # "case_000001"
print(f"罪名: {case.accusations}")                    # ["盗窃"]
print(f"相关法条: {case.relevant_articles}")          # [264]
print(f"案件事实: {case.fact[:100]}...")              # "公诉机关起诉指控，被告人张某某秘密窃取他人财物..."
print(f"量刑: {case.sentence_info}")                  # {'imprisonment_months': 2, 'fine_amount': 0, ...}
```

### 3. 辅助数据文件

#### article_case_mappings.pkl
- **用途**: 提供法条与案例的双向映射关系
- **结构**: `dict[int, CriminalMapping]` - 按法条编号索引
- **内容**: 每个法条对应的案例数量、典型案例、相关罪名等

#### crime_type_analysis.pkl  
- **用途**: 罪名统计和分析数据
- **结构**: `dict[str, dict]` - 按罪名索引
- **内容**: 每个罪名的案例数量、相关法条、平均刑期、刑期分布等

#### criminal_professional_dictionary.pkl
- **用途**: 刑法领域专业词汇词典
- **结构**: 包含同义词映射、专业术语分类等
- **内容**: 71个专业术语，分为sentence_terms、procedure_terms、concept_terms等类别

## 数据加载示例

### 基本加载方式
```python
import pickle
from pathlib import Path

# 设置数据目录
data_dir = Path("data/processed/criminal")

# 加载法条数据
with open(data_dir / "criminal_articles.pkl", "rb") as f:
    articles = pickle.load(f)
print(f"加载了 {len(articles)} 条法条")

# 加载案例数据  
with open(data_dir / "criminal_cases.pkl", "rb") as f:
    cases = pickle.load(f)
print(f"加载了 {len(cases)} 个案例")

# 访问具体数据
first_article = articles[0]
print(f"第一条法条: {first_article.title}")
print(f"内容: {first_article.content}")

first_case = cases[0]
print(f"第一个案例: {first_case.case_id}")  
print(f"罪名: {first_case.accusations}")
print(f"事实: {first_case.fact[:200]}...")
```

### 数据筛选示例
```python
# 查找特定罪名的案例
def find_cases_by_crime(cases, crime_name):
    return [case for case in cases if crime_name in case.accusations]

theft_cases = find_cases_by_crime(cases, "盗窃")
print(f"找到 {len(theft_cases)} 个盗窃案例")

# 查找特定法条相关案例
def find_cases_by_article(cases, article_number):
    return [case for case in cases if article_number in case.relevant_articles]

article_264_cases = find_cases_by_article(cases, 264)
print(f"与第264条相关的案例: {len(article_264_cases)} 个")
```

## 数据统计信息

### 整体统计
- **法条总数**: 446 条
- **案例总数**: 17,131 个  
- **覆盖罪名**: 202 种主要罪名
- **法条覆盖**: 44 个核心刑法条文
- **数据来源**: 公开裁判文书网 + 官方法律条文

### Top 10 高频罪名
1. 盗窃 - 995 案例
2. [走私、贩卖、运输、制造]毒品 - 883 案例
3. 故意伤害 - 639 案例  
4. 抢劫 - 472 案例
5. 诈骗 - 352 案例
6. 受贿 - 346 案例
7. 寻衅滋事 - 333 案例
8. 危险驾驶 - 287 案例
9. 合同诈骗 - 268 案例
10. [组织、强迫、引诱、容留、介绍]卖淫 - 264 案例

### Top 10 高引用法条
1. 第347条 - 1614 次引用（毒品犯罪）
2. 第264条 - 952 次引用（盗窃罪）  
3. 第383条 - 733 次引用（贪污罪）
4. 第234条 - 591 次引用（故意伤害罪）
5. 第133条 - 494 次引用（交通肇事罪）
6. 第280条 - 472 次引用（抢劫罪）
7. 第345条 - 413 次引用（滥伐林木罪）
8. 第266条 - 386 次引用（诈骗罪）
9. 第397条 - 380 次引用（滥用职权罪）
10. 第196条 - 370 次引用（信用卡诈骗罪）

## 与向量数据的关系

此目录中的原始数据是 `data/processed/vectors/` 向量数据的**源数据**：

1. **数据流向**: `criminal/*.pkl` → `tools/data_processing/criminal_data_vectorizer.py` → `vectors/*.pkl`
2. **向量化过程**: 提取 `article.content` 和 `case.fact` 字段进行文本向量化
3. **元数据保留**: 向量文件中的metadata来源于此目录的数据结构
4. **完整性**: 此目录包含完整文本内容，向量目录仅包含向量和基本元数据

## 使用建议

### 对于开发者
- 需要完整文本内容时，使用此目录的数据
- 需要快速相似度检索时，使用 `vectors/` 目录的向量数据
- 进行数据分析时，结合原始数据和向量数据

### 对于研究者  
- 可用于法律文本挖掘研究
- 支持刑法案例分析
- 适合司法大数据分析项目

### 数据更新
- 如需重新向量化，运行: `python tools/data_processing/criminal_data_vectorizer.py`
- 向量化大约需要3-5分钟，生成768维度向量
- 生成的向量文件将保存到 `data/processed/vectors/` 目录

---

*此文档最后更新: 2025-09-11*  
*数据版本: v1.0*  
*总数据量: 17,577 条记录 (446条法条 + 17,131个案例)*