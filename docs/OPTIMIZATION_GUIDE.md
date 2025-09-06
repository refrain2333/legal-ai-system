# 法律检索系统优化技术文档

> **版本**: v1.0  
> **日期**: 2025-09-06  
> **目标**: 基于现有数据集进行系统性能优化和功能增强

## 📋 优化概述

### 当前系统状态
- **文档数量**: 3,519个 (法条2,729 + 案例790)
- **平均相关度**: 0.6802
- **成功率**: 100%
- **响应时间**: 51.1ms
- **质量评级**: B+级 (良好偏优秀)

### 优化目标
- **相关度提升**: 0.68 → 0.75+ (目标提升10%)
- **功能增强**: 增加可解释性和关联分析
- **用户体验**: 提供更智能的检索体验

### 数据资源优势
- **精确映射表**: 668个精确案例-法条对应关系
- **模糊映射表**: 1,364个语义关联关系
- **完整法律文档**: 覆盖多个法律领域

---

## 🎯 优化技术路线图

### 阶段一: 混合排序引擎 (优先级:🔥🔥🔥)
**目标**: 直接提升检索准确度  
**预期效果**: 相关度 0.68 → 0.75+  
**实施时间**: 1-2天  
**技术难度**: ⭐⭐

### 阶段二: 知识图谱关联分析 (优先级:🔥🔥)
**目标**: 增加可解释性和关联推荐  
**预期效果**: 用户体验显著提升  
**实施时间**: 2-3天  
**技术难度**: ⭐⭐⭐

### 阶段三: 对比学习模型优化 (优先级:🔥)
**目标**: 模型专业化训练  
**预期效果**: 相关度质的飞跃  
**实施时间**: 3-5天  
**技术难度**: ⭐⭐⭐⭐

---

## 🔧 阶段一: 混合排序引擎实现

### 1.1 技术原理

现有系统只使用语义检索，新的混合排序引擎将结合三种信号：
1. **语义相似度** (70%权重) - 现有功能
2. **映射关系加权** (20%权重) - 基于精确映射表
3. **关键词匹配** (10%权重) - 传统文本匹配

### 1.2 实现步骤

#### 步骤1: 创建混合排序服务
```bash
# 创建新文件
touch src/services/hybrid_ranking_service.py
```

#### 步骤2: 实现核心代码

**文件**: `src/services/hybrid_ranking_service.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
混合排序引擎 - 多信号融合检索优化
基于映射表数据进行检索结果重新排序
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
import re

class HybridRankingService:
    """混合排序服务"""
    
    def __init__(self):
        self.mapping_data = self._load_mapping_data()
        self.precise_mappings = self._build_precise_mapping_index()
        self.fuzzy_mappings = self._build_fuzzy_mapping_index()
        
    def _load_mapping_data(self) -> Dict:
        """加载映射表数据"""
        try:
            precise_df = pd.read_csv('data/raw/精确映射表.csv')
            fuzzy_df = pd.read_csv('data/raw/精确+模糊匹配映射表.csv')
            
            return {
                'precise': precise_df,
                'fuzzy': fuzzy_df,
                'precise_count': len(precise_df),
                'fuzzy_count': len(fuzzy_df)
            }
        except Exception as e:
            print(f"Warning: 映射表加载失败 - {e}")
            return {'precise': pd.DataFrame(), 'fuzzy': pd.DataFrame()}
    
    def _build_precise_mapping_index(self) -> Dict:
        """构建精确映射索引"""
        index = {}
        if not self.mapping_data['precise'].empty:
            for _, row in self.mapping_data['precise'].iterrows():
                law_id = row['律法ID']
                case_id = row['案例ID']
                
                # 双向索引
                if law_id not in index:
                    index[law_id] = []
                if case_id not in index:
                    index[case_id] = []
                    
                index[law_id].append({
                    'related_id': case_id,
                    'type': 'case',
                    'relation': 'precise',
                    'description': row.get('适用说明', '')
                })
                
                index[case_id].append({
                    'related_id': law_id,
                    'type': 'law',
                    'relation': 'precise', 
                    'description': row.get('适用说明', '')
                })
        
        return index
    
    def _build_fuzzy_mapping_index(self) -> Dict:
        """构建模糊映射索引"""
        index = {}
        if not self.mapping_data['fuzzy'].empty:
            for _, row in self.mapping_data['fuzzy'].iterrows():
                law_id = row['律法ID']
                case_id = row['案例ID']
                is_precise = row.get('主要适用', '否') == '是'
                
                # 跳过已在精确映射中的关系
                if not is_precise:
                    if law_id not in index:
                        index[law_id] = []
                    if case_id not in index:
                        index[case_id] = []
                        
                    index[law_id].append({
                        'related_id': case_id,
                        'type': 'case',
                        'relation': 'fuzzy',
                        'description': row.get('适用说明', '')
                    })
                    
                    index[case_id].append({
                        'related_id': law_id,
                        'type': 'law',
                        'relation': 'fuzzy',
                        'description': row.get('适用说明', '')
                    })
        
        return index
    
    def enhance_search_results(self, query: str, original_results: List[Dict]) -> List[Dict]:
        """增强检索结果"""
        if not original_results:
            return original_results
        
        enhanced_results = []
        
        for result in original_results:
            enhanced_result = result.copy()
            doc_id = result.get('id', '')
            
            # 1. 计算映射关系权重
            mapping_boost = self._calculate_mapping_boost(doc_id)
            
            # 2. 计算关键词匹配权重  
            keyword_boost = self._calculate_keyword_boost(query, result)
            
            # 3. 融合最终分数
            original_score = result.get('score', 0)
            enhanced_score = (
                original_score * 0.7 +           # 语义相似度 70%
                mapping_boost * 0.2 +            # 映射关系 20%
                keyword_boost * 0.1              # 关键词匹配 10%
            )
            
            enhanced_result['original_score'] = original_score
            enhanced_result['mapping_boost'] = mapping_boost
            enhanced_result['keyword_boost'] = keyword_boost
            enhanced_result['score'] = enhanced_score
            enhanced_result['boost_applied'] = True
            
            # 4. 添加关联信息
            enhanced_result['related_docs'] = self._get_related_documents(doc_id)
            
            enhanced_results.append(enhanced_result)
        
        # 重新排序
        enhanced_results.sort(key=lambda x: x['score'], reverse=True)
        
        return enhanced_results
    
    def _calculate_mapping_boost(self, doc_id: str) -> float:
        """计算映射关系加权分数"""
        boost_score = 0.0
        
        # 精确映射加权更高
        if doc_id in self.precise_mappings:
            boost_score += 0.8  # 精确映射基础分
            boost_score += min(len(self.precise_mappings[doc_id]) * 0.1, 0.2)  # 关联数量加权
        
        # 模糊映射加权较低
        elif doc_id in self.fuzzy_mappings:
            boost_score += 0.5  # 模糊映射基础分
            boost_score += min(len(self.fuzzy_mappings[doc_id]) * 0.05, 0.1)  # 关联数量加权
        
        return min(boost_score, 1.0)
    
    def _calculate_keyword_boost(self, query: str, result: Dict) -> float:
        """计算关键词匹配加权分数"""
        title = result.get('title', '')
        content_preview = result.get('content_preview', '')
        
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        
        if not query_keywords:
            return 0.5  # 默认分数
        
        # 计算匹配度
        title_matches = sum(1 for kw in query_keywords if kw in title)
        content_matches = sum(1 for kw in query_keywords if kw in content_preview)
        
        # 标题匹配权重更高
        match_score = (title_matches * 0.6 + content_matches * 0.4) / len(query_keywords)
        
        return min(match_score, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        legal_keywords = [
            '合同', '违约', '赔偿', '责任', '法律', '条款', '诉讼', '法院',
            '判决', '损害', '故意', '过失', '刑法', '民法', '行政', '程序',
            '证据', '执行', '上诉', '仲裁', '调解', '和解'
        ]
        
        found_keywords = []
        for keyword in legal_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _get_related_documents(self, doc_id: str) -> List[Dict]:
        """获取相关文档信息"""
        related = []
        
        # 精确关联
        if doc_id in self.precise_mappings:
            for rel in self.precise_mappings[doc_id][:3]:  # 最多3个
                related.append({
                    'id': rel['related_id'],
                    'type': rel['type'],
                    'relation': 'precise',
                    'description': rel['description']
                })
        
        # 模糊关联 (如果精确关联不足)
        if len(related) < 3 and doc_id in self.fuzzy_mappings:
            remaining = 3 - len(related)
            for rel in self.fuzzy_mappings[doc_id][:remaining]:
                related.append({
                    'id': rel['related_id'],
                    'type': rel['type'],
                    'relation': 'fuzzy',
                    'description': rel['description']
                })
        
        return related
    
    def get_optimization_stats(self) -> Dict:
        """获取优化统计信息"""
        return {
            'precise_mappings_count': len(self.precise_mappings),
            'fuzzy_mappings_count': len(self.fuzzy_mappings),
            'total_relations': self.mapping_data.get('precise_count', 0) + 
                             self.mapping_data.get('fuzzy_count', 0),
            'optimization_enabled': True
        }
```

#### 步骤3: 集成到现有检索服务

**文件**: `src/services/retrieval_service.py` (修改现有文件)

在现有的 `RetrievalService` 类中添加：

```python
# 在 __init__ 方法中添加
def __init__(self, index_file: str = "data/indices/complete_semantic_index.pkl"):
    # ... 现有代码 ...
    
    # 新增：初始化混合排序服务
    try:
        from .hybrid_ranking_service import HybridRankingService
        self.hybrid_ranker = HybridRankingService()
        print("Hybrid ranking service initialized successfully!")
    except Exception as e:
        print(f"Warning: Hybrid ranking initialization failed - {e}")
        self.hybrid_ranker = None

# 修改 search 方法
async def search(self, query: str, top_k: int = 10, 
                enable_hybrid: bool = True) -> Dict[str, Any]:
    """增强版搜索方法"""
    
    # ... 现有搜索逻辑 ...
    
    # 新增：应用混合排序优化
    if enable_hybrid and self.hybrid_ranker:
        try:
            results = self.hybrid_ranker.enhance_search_results(query, results)
            print(f"Hybrid ranking applied to {len(results)} results")
        except Exception as e:
            print(f"Warning: Hybrid ranking failed - {e}")
    
    return {
        'query': query,
        'results': results[:top_k],
        'total': len(results),
        'search_time': search_time,
        'hybrid_enabled': enable_hybrid and self.hybrid_ranker is not None
    }
```

#### 步骤4: 测试优化效果

**创建测试脚本**: `test_hybrid_optimization.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
混合排序优化效果测试
"""

import sys
from pathlib import Path
import asyncio

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_hybrid_optimization():
    """测试混合排序优化效果"""
    from src.services.retrieval_service import get_retrieval_service
    
    service = await get_retrieval_service()
    
    test_queries = [
        "合同违约责任",
        "交通事故赔偿",
        "故意伤害罪",
        "劳动合同纠纷",
        "离婚财产分割"
    ]
    
    print("="*80)
    print("混合排序优化效果测试")
    print("="*80)
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        
        # 不使用混合排序
        result_original = await service.search(query, top_k=3, enable_hybrid=False)
        
        # 使用混合排序
        result_hybrid = await service.search(query, top_k=3, enable_hybrid=True)
        
        print("原始结果:")
        for i, doc in enumerate(result_original['results']):
            print(f"  {i+1}. 分数: {doc['score']:.4f} - {doc.get('title', '')[:50]}...")
            
        print("优化结果:")
        for i, doc in enumerate(result_hybrid['results']):
            original_score = doc.get('original_score', doc['score'])
            mapping_boost = doc.get('mapping_boost', 0)
            keyword_boost = doc.get('keyword_boost', 0)
            
            print(f"  {i+1}. 分数: {doc['score']:.4f} "
                  f"(原{original_score:.4f}+映射{mapping_boost:.2f}+关键词{keyword_boost:.2f}) "
                  f"- {doc.get('title', '')[:40]}...")
            
            if doc.get('related_docs'):
                print(f"      关联: {len(doc['related_docs'])}个相关文档")

if __name__ == "__main__":
    asyncio.run(test_hybrid_optimization())
```

### 1.3 使用命令

```bash
# 运行测试
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" test_hybrid_optimization.py

# 正常启动系统 (自动启用混合排序)
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" app.py
```

### 1.4 预期效果

- **相关度提升**: 从 0.68 提升到 0.75+
- **结果质量**: 有映射关系的文档排序靠前
- **用户体验**: 检索结果更准确，更符合预期

---

## 🕸️ 阶段二: 知识图谱关联分析

### 2.1 技术原理

基于1,364个映射关系构建法律知识图谱，实现：
- 文档间关联关系可视化
- 相关推荐功能
- 可解释的检索结果

### 2.2 实现步骤

#### 步骤1: 安装依赖
```bash
pip install networkx matplotlib
```

#### 步骤2: 创建知识图谱服务

**文件**: `src/services/legal_knowledge_graph.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律知识图谱服务
基于映射表构建文档关联关系图谱
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Tuple
import pickle
from pathlib import Path

class LegalKnowledgeGraph:
    """法律知识图谱"""
    
    def __init__(self, rebuild_graph: bool = False):
        self.graph_file = Path("data/indices/legal_knowledge_graph.pkl")
        
        if rebuild_graph or not self.graph_file.exists():
            self.graph = self._build_graph_from_mappings()
            self._save_graph()
        else:
            self.graph = self._load_graph()
        
        self.stats = self._calculate_graph_stats()
    
    def _build_graph_from_mappings(self) -> nx.Graph:
        """从映射表构建知识图谱"""
        print("Building legal knowledge graph from mapping tables...")
        
        G = nx.Graph()
        
        # 加载映射数据
        try:
            precise_df = pd.read_csv('data/raw/精确映射表.csv')
            fuzzy_df = pd.read_csv('data/raw/精确+模糊匹配映射表.csv')
        except Exception as e:
            print(f"Error loading mapping tables: {e}")
            return G
        
        # 添加精确映射关系
        for _, row in precise_df.iterrows():
            law_id = row['律法ID']
            case_id = row['案例ID']
            description = row.get('适用说明', '')
            
            G.add_edge(law_id, case_id,
                      relation_type='precise',
                      description=description,
                      weight=1.0,
                      mapping_id=row.get('映射ID', ''))
        
        # 添加模糊映射关系 (排除已有的精确关系)
        for _, row in fuzzy_df.iterrows():
            law_id = row['律法ID']
            case_id = row['案例ID']
            is_precise = row.get('主要适用', '否') == '是'
            description = row.get('适用说明', '')
            
            # 如果不是精确关系且不存在边，则添加
            if not is_precise and not G.has_edge(law_id, case_id):
                G.add_edge(law_id, case_id,
                          relation_type='fuzzy',
                          description=description,
                          weight=0.6,
                          mapping_id=row.get('映射ID', ''))
        
        print(f"Knowledge graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def _save_graph(self):
        """保存图谱到文件"""
        try:
            with open(self.graph_file, 'wb') as f:
                pickle.dump(self.graph, f)
            print(f"Knowledge graph saved to {self.graph_file}")
        except Exception as e:
            print(f"Error saving graph: {e}")
    
    def _load_graph(self) -> nx.Graph:
        """从文件加载图谱"""
        try:
            with open(self.graph_file, 'rb') as f:
                graph = pickle.load(f)
            print(f"Knowledge graph loaded from {self.graph_file}")
            return graph
        except Exception as e:
            print(f"Error loading graph: {e}")
            return nx.Graph()
    
    def get_related_documents(self, doc_id: str, max_results: int = 5) -> List[Dict]:
        """获取相关文档"""
        if doc_id not in self.graph:
            return []
        
        related_docs = []
        neighbors = list(self.graph.neighbors(doc_id))
        
        # 按关系权重排序
        neighbor_weights = []
        for neighbor in neighbors:
            edge_data = self.graph[doc_id][neighbor]
            weight = edge_data.get('weight', 0.5)
            relation_type = edge_data.get('relation_type', 'unknown')
            description = edge_data.get('description', '')
            
            neighbor_weights.append({
                'doc_id': neighbor,
                'weight': weight,
                'relation_type': relation_type,
                'description': description
            })
        
        # 排序并返回
        neighbor_weights.sort(key=lambda x: x['weight'], reverse=True)
        
        return neighbor_weights[:max_results]
    
    def get_document_centrality(self, doc_id: str) -> Dict[str, float]:
        """获取文档在图谱中的重要性指标"""
        if doc_id not in self.graph:
            return {}
        
        # 计算各种中心性指标
        degree_centrality = nx.degree_centrality(self.graph).get(doc_id, 0)
        try:
            betweenness_centrality = nx.betweenness_centrality(self.graph, k=min(100, self.graph.number_of_nodes())).get(doc_id, 0)
        except:
            betweenness_centrality = 0
        
        return {
            'degree_centrality': degree_centrality,
            'betweenness_centrality': betweenness_centrality,
            'neighbor_count': len(list(self.graph.neighbors(doc_id)))
        }
    
    def find_shortest_path(self, doc_id1: str, doc_id2: str) -> List[str]:
        """查找两个文档间的最短路径"""
        try:
            if doc_id1 in self.graph and doc_id2 in self.graph:
                return nx.shortest_path(self.graph, doc_id1, doc_id2)
        except nx.NetworkXNoPath:
            pass
        return []
    
    def get_subgraph_around_document(self, doc_id: str, radius: int = 2) -> nx.Graph:
        """获取文档周围的子图"""
        if doc_id not in self.graph:
            return nx.Graph()
        
        # 获取指定半径内的所有节点
        nodes_in_radius = set([doc_id])
        current_nodes = set([doc_id])
        
        for _ in range(radius):
            next_nodes = set()
            for node in current_nodes:
                next_nodes.update(self.graph.neighbors(node))
            current_nodes = next_nodes - nodes_in_radius
            nodes_in_radius.update(current_nodes)
        
        return self.graph.subgraph(nodes_in_radius)
    
    def _calculate_graph_stats(self) -> Dict:
        """计算图谱统计信息"""
        if self.graph.number_of_nodes() == 0:
            return {}
        
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'density': nx.density(self.graph),
            'connected_components': nx.number_connected_components(self.graph)
        }
        
        # 边类型统计
        edge_types = {}
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get('relation_type', 'unknown')
            edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
        
        stats['edge_types'] = edge_types
        
        return stats
    
    def get_graph_stats(self) -> Dict:
        """获取图谱统计信息"""
        return self.stats
    
    def export_graph_for_visualization(self, output_file: str = "legal_graph.gexf"):
        """导出图谱用于可视化"""
        try:
            nx.write_gexf(self.graph, output_file)
            print(f"Graph exported to {output_file}")
        except Exception as e:
            print(f"Error exporting graph: {e}")
```

#### 步骤3: 集成到检索服务

在 `src/services/retrieval_service.py` 中添加：

```python
# 在 __init__ 方法中添加
try:
    from .legal_knowledge_graph import LegalKnowledgeGraph
    self.knowledge_graph = LegalKnowledgeGraph()
    print("Knowledge graph service initialized successfully!")
except Exception as e:
    print(f"Warning: Knowledge graph initialization failed - {e}")
    self.knowledge_graph = None

# 在 search 方法中添加关联信息
if self.knowledge_graph:
    for result in results:
        doc_id = result.get('id', '')
        
        # 添加关联文档
        related_docs = self.knowledge_graph.get_related_documents(doc_id, max_results=3)
        result['knowledge_graph_relations'] = related_docs
        
        # 添加重要性指标
        centrality = self.knowledge_graph.get_document_centrality(doc_id)
        result['document_importance'] = centrality
```

### 2.3 使用说明

创建测试脚本测试知识图谱功能：

```python
# test_knowledge_graph.py
import asyncio
from src.services.legal_knowledge_graph import LegalKnowledgeGraph

async def test_knowledge_graph():
    kg = LegalKnowledgeGraph(rebuild_graph=True)
    
    print("图谱统计:", kg.get_graph_stats())
    
    # 测试关联查询
    test_doc = "law2023"  # 替换为实际存在的文档ID
    related = kg.get_related_documents(test_doc)
    print(f"\n{test_doc} 的关联文档:", related)

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())
```

---

## 🤖 阶段三: 对比学习模型优化

### 3.1 技术原理

利用668个精确映射关系进行对比学习训练，让模型专门学习法律文档的语义关系。

### 3.2 实现步骤

#### 步骤1: 安装训练依赖
```bash
pip install sentence-transformers torch scikit-learn
```

#### 步骤2: 创建训练数据构建器

**文件**: `src/models/contrastive_training.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对比学习训练模块
基于精确映射表进行模型优化
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import random
from typing import List, Tuple, Dict
from pathlib import Path

class ContrastiveLegalTrainer:
    """法律领域对比学习训练器"""
    
    def __init__(self, base_model_name: str = 'shibing624/text2vec-base-chinese'):
        self.base_model_name = base_model_name
        self.model = SentenceTransformer(base_model_name)
        
        # 加载原始文档数据
        self.laws_data = self._load_laws_data()
        self.cases_data = self._load_cases_data()
        self.mappings = self._load_mappings()
        
    def _load_laws_data(self) -> Dict:
        """加载法条数据"""
        try:
            with open('data/processed/full_dataset.pkl', 'rb') as f:
                import pickle
                full_data = pickle.load(f)
                
            laws_dict = {}
            for item in full_data:
                if item.get('type') == 'law':
                    laws_dict[item['id']] = {
                        'title': item.get('title', ''),
                        'content': item.get('content', '')
                    }
            return laws_dict
        except Exception as e:
            print(f"Error loading laws data: {e}")
            return {}
    
    def _load_cases_data(self) -> Dict:
        """加载案例数据"""
        try:
            with open('data/processed/full_dataset.pkl', 'rb') as f:
                import pickle
                full_data = pickle.load(f)
                
            cases_dict = {}
            for item in full_data:
                if item.get('type') == 'case':
                    cases_dict[item['id']] = {
                        'title': item.get('title', ''),
                        'content': item.get('content', '')
                    }
            return cases_dict
        except Exception as e:
            print(f"Error loading cases data: {e}")
            return {}
    
    def _load_mappings(self) -> pd.DataFrame:
        """加载精确映射表"""
        try:
            return pd.read_csv('data/raw/精确映射表.csv')
        except Exception as e:
            print(f"Error loading mappings: {e}")
            return pd.DataFrame()
    
    def create_training_examples(self, test_ratio: float = 0.2) -> Tuple[List, List]:
        """创建训练样本"""
        print("Creating training examples from precise mappings...")
        
        train_examples = []
        test_examples = []
        
        # 从精确映射创建正样本对
        positive_pairs = []
        for _, row in self.mappings.iterrows():
            law_id = row['律法ID']
            case_id = row['案例ID']
            
            # 获取文本内容
            law_text = self._get_document_text(law_id, 'law')
            case_text = self._get_document_text(case_id, 'case')
            
            if law_text and case_text:
                positive_pairs.append((case_text, law_text, 1.0))
        
        print(f"Created {len(positive_pairs)} positive pairs")
        
        # 创建负样本对
        negative_pairs = []
        law_ids = list(self.laws_data.keys())
        case_ids = list(self.cases_data.keys())
        
        # 获取已有的正样本对
        positive_law_case_pairs = set()
        for _, row in self.mappings.iterrows():
            positive_law_case_pairs.add((row['律法ID'], row['案例ID']))
        
        # 生成负样本（随机配对，但排除正样本）
        negative_count = min(len(positive_pairs), 1000)  # 限制负样本数量
        attempts = 0
        max_attempts = negative_count * 10
        
        while len(negative_pairs) < negative_count and attempts < max_attempts:
            law_id = random.choice(law_ids)
            case_id = random.choice(case_ids)
            
            if (law_id, case_id) not in positive_law_case_pairs:
                law_text = self._get_document_text(law_id, 'law')
                case_text = self._get_document_text(case_id, 'case')
                
                if law_text and case_text:
                    negative_pairs.append((case_text, law_text, 0.0))
            
            attempts += 1
        
        print(f"Created {len(negative_pairs)} negative pairs")
        
        # 合并所有样本
        all_pairs = positive_pairs + negative_pairs
        random.shuffle(all_pairs)
        
        # 分割训练集和测试集
        split_index = int(len(all_pairs) * (1 - test_ratio))
        train_pairs = all_pairs[:split_index]
        test_pairs = all_pairs[split_index:]
        
        # 转换为SentenceTransformers格式
        train_examples = [
            InputExample(texts=[pair[0], pair[1]], label=pair[2])
            for pair in train_pairs
        ]
        
        test_examples = [
            InputExample(texts=[pair[0], pair[1]], label=pair[2])
            for pair in test_pairs
        ]
        
        print(f"Training examples: {len(train_examples)}")
        print(f"Test examples: {len(test_examples)}")
        
        return train_examples, test_examples
    
    def _get_document_text(self, doc_id: str, doc_type: str) -> str:
        """获取文档文本"""
        if doc_type == 'law' and doc_id in self.laws_data:
            doc = self.laws_data[doc_id]
            return f"{doc['title']} {doc['content']}"[:512]  # 限制长度
        elif doc_type == 'case' and doc_id in self.cases_data:
            doc = self.cases_data[doc_id]
            return f"{doc['title']} {doc['content']}"[:512]  # 限制长度
        return ""
    
    def train_model(self, output_path: str = 'models/legal_model_optimized', 
                   epochs: int = 3, batch_size: int = 16):
        """训练模型"""
        print(f"Starting contrastive learning training...")
        print(f"Base model: {self.base_model_name}")
        
        # 创建训练数据
        train_examples, test_examples = self.create_training_examples()
        
        if not train_examples:
            print("No training examples created. Aborting training.")
            return None
        
        # 创建数据加载器
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
        
        # 创建评估器
        evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
            test_examples, name='legal-eval'
        )
        
        # 设置损失函数
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # 训练参数
        warmup_steps = int(len(train_dataloader) * epochs * 0.1)
        
        print(f"Training parameters:")
        print(f"  Epochs: {epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  Warmup steps: {warmup_steps}")
        print(f"  Training batches per epoch: {len(train_dataloader)}")
        
        # 开始训练
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            evaluation_steps=len(train_dataloader) // 2,  # 每半个epoch评估一次
            warmup_steps=warmup_steps,
            output_path=output_path,
            save_best_model=True,
            show_progress_bar=True
        )
        
        print(f"Training completed! Model saved to: {output_path}")
        return output_path
    
    def evaluate_model(self, model_path: str):
        """评估模型性能"""
        print("Evaluating model performance...")
        
        # 加载训练后的模型
        optimized_model = SentenceTransformer(model_path)
        
        # 创建测试样本
        _, test_examples = self.create_training_examples()
        
        if not test_examples:
            print("No test examples available.")
            return
        
        # 计算相似度
        correct_predictions = 0
        total_predictions = len(test_examples)
        
        for example in test_examples[:100]:  # 限制测试数量
            text1, text2 = example.texts
            expected_label = example.label
            
            # 计算相似度
            embeddings = optimized_model.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # 简单阈值分类
            predicted_label = 1.0 if similarity > 0.5 else 0.0
            
            if abs(predicted_label - expected_label) < 0.5:
                correct_predictions += 1
        
        accuracy = correct_predictions / min(total_predictions, 100)
        print(f"Model accuracy on test set: {accuracy:.4f}")
        
        return accuracy
```

#### 步骤3: 创建训练脚本

**文件**: `train_legal_model.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律模型训练脚本
"""

import sys
from pathlib import Path
import os

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主训练函数"""
    from src.models.contrastive_training import ContrastiveLegalTrainer
    
    print("="*80)
    print("法律领域对比学习模型训练")
    print("="*80)
    
    # 初始化训练器
    trainer = ContrastiveLegalTrainer()
    
    # 检查数据可用性
    print(f"法条数据: {len(trainer.laws_data)} 个")
    print(f"案例数据: {len(trainer.cases_data)} 个")  
    print(f"映射关系: {len(trainer.mappings)} 个")
    
    if len(trainer.mappings) == 0:
        print("错误: 没有找到映射数据，无法进行训练")
        return
    
    # 创建输出目录
    output_dir = Path("models/legal_model_optimized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 开始训练
    try:
        model_path = trainer.train_model(
            output_path=str(output_dir),
            epochs=3,
            batch_size=16
        )
        
        if model_path:
            print(f"\n训练完成! 模型保存在: {model_path}")
            
            # 评估模型
            trainer.evaluate_model(model_path)
            
            print(f"\n使用新模型重建索引:")
            print(f"1. 将新模型路径更新到 src/config/settings.py")
            print(f"2. 运行向量化脚本重建索引")
            print(f"3. 重启系统使用优化模型")
            
        else:
            print("训练失败!")
            
    except Exception as e:
        print(f"训练过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

### 3.3 使用步骤

```bash
# 1. 开始训练
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" train_legal_model.py

# 2. 训练完成后，更新配置使用新模型
# 编辑 src/config/settings.py，修改模型路径

# 3. 重建向量索引
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" tools/full_vectorization_executor.py

# 4. 重启系统
"C:\Users\lenovo\Miniconda3\envs\legal-ai\python.exe" app.py
```

---

## 📊 优化效果监控

### 创建效果对比测试

**文件**: `optimization_comparison.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化效果对比测试
"""

import sys
import asyncio
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def comprehensive_comparison():
    """全面对比优化前后效果"""
    from src.services.retrieval_service import get_retrieval_service
    
    service = await get_retrieval_service()
    
    test_cases = [
        "合同违约的法律责任",
        "交通事故赔偿标准",
        "劳动争议处理程序", 
        "故意伤害罪构成要件",
        "离婚财产分割原则"
    ]
    
    print("="*80)
    print("优化效果全面对比测试")
    print("="*80)
    
    results_summary = []
    
    for query in test_cases:
        print(f"\n测试查询: {query}")
        
        # 测试各种配置
        configs = [
            {"enable_hybrid": False, "label": "原始"},
            {"enable_hybrid": True, "label": "混合排序"},
        ]
        
        query_results = {"query": query, "configs": {}}
        
        for config in configs:
            start_time = time.time()
            result = await service.search(query, top_k=5, **config)
            end_time = time.time()
            
            # 计算平均相关度
            scores = [r.get('score', 0) for r in result['results']]
            avg_score = sum(scores) / len(scores) if scores else 0
            response_time = (end_time - start_time) * 1000
            
            query_results["configs"][config["label"]] = {
                "avg_score": avg_score,
                "response_time": response_time,
                "results_count": len(result['results'])
            }
            
            print(f"  {config['label']}: 平均相关度 {avg_score:.4f}, 响应时间 {response_time:.1f}ms")
        
        results_summary.append(query_results)
    
    # 总体统计
    print(f"\n" + "="*50)
    print("总体效果对比")
    print("="*50)
    
    for config_name in ["原始", "混合排序"]:
        scores = []
        times = []
        
        for result in results_summary:
            if config_name in result["configs"]:
                config_data = result["configs"][config_name]
                scores.append(config_data["avg_score"])
                times.append(config_data["response_time"])
        
        if scores:
            avg_score = sum(scores) / len(scores)
            avg_time = sum(times) / len(times)
            print(f"\n{config_name}配置:")
            print(f"  平均相关度: {avg_score:.4f}")
            print(f"  平均响应时间: {avg_time:.1f}ms")
    
    return results_summary

if __name__ == "__main__":
    results = asyncio.run(comprehensive_comparison())
```

---

## 📋 优化实施检查清单

### 阶段一检查清单
- [ ] 创建 `src/services/hybrid_ranking_service.py`
- [ ] 修改 `src/services/retrieval_service.py` 集成混合排序
- [ ] 创建并运行测试脚本验证效果
- [ ] 确认相关度提升 (目标: 0.68 → 0.75+)

### 阶段二检查清单  
- [ ] 安装 networkx 依赖
- [ ] 创建 `src/services/legal_knowledge_graph.py`
- [ ] 集成知识图谱到检索服务
- [ ] 测试关联关系功能
- [ ] 验证可解释性增强

### 阶段三检查清单
- [ ] 安装训练相关依赖
- [ ] 创建 `src/models/contrastive_training.py`
- [ ] 运行训练脚本生成优化模型
- [ ] 使用新模型重建向量索引
- [ ] 对比训练前后效果

### 最终验收清单
- [ ] 运行完整的效果对比测试
- [ ] 确认所有优化功能正常工作
- [ ] 更新系统文档和API说明
- [ ] 准备优化成果报告

---

## 🔧 故障排除

### 常见问题及解决方案

1. **映射表加载失败**
   - 检查文件路径是否正确
   - 确认CSV文件格式和编码
   
2. **训练内存不足**
   - 减小batch_size参数
   - 限制训练样本数量

3. **模型加载错误**
   - 确认模型文件完整性
   - 检查依赖版本兼容性

4. **性能没有提升**
   - 检查映射数据质量
   - 调整权重参数
   - 验证测试用例

---

这个优化技术文档为你提供了完整的实施路径。建议先从阶段一的混合排序开始，因为它能快速看到效果。每个阶段完成后都可以进行测试验证，确保优化效果符合预期。