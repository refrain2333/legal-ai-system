# AI驱动刑法智能检索管道 - 流程图

基于Mermaid图表语法的完整数据流程可视化

---

## 🔄 完整流程图

```mermaid
flowchart TD
    A[用户查询: 打架致人轻伤怎么判？] --> B{阶段1: LLM问题分类器}

    B -->|刑法相关| C[阶段2: 结构化信息提取器]
    B -->|非刑法| Z[普通AI模式<br/>基于提示词回答]

    C --> D[阶段3: 智能路由决策]

    D --> E1[知识图谱搜索<br/>基于识别罪名]
    D --> E2[LLM增强搜索<br/>Query2doc + HyDE]
    D --> E3[BM25混合搜索<br/>AI生成关键词]
    D --> E4[基础语义搜索<br/>备用降级路径]

    E1 --> F[阶段4: 智能融合引擎]
    E2 --> F
    E3 --> F
    E4 --> F

    F --> G[阶段5: AI辅助回答生成]
    G --> H[返回专业法律回答]
    Z --> Y[返回通用AI回答]

    classDef llmStage fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef searchStage fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef fusionStage fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef generalStage fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class B,C,G llmStage
    class E1,E2,E3,E4 searchStage
    class D,F fusionStage
    class Z,Y generalStage
```

---

## 📊 详细阶段流程图

### 阶段1: LLM问题分类

```mermaid
flowchart LR
    A[用户查询] --> B[LLM分类器]
    B --> C{是否刑法相关?}
    C -->|是<br/>confidence > 0.7| D[启用完整搜索管道]
    C -->|否<br/>confidence < 0.7| E[普通AI助手模式<br/>基于提示词回答]

    classDef process fill:#e1f5fe,stroke:#01579b
    classDef decision fill:#fff3e0,stroke:#e65100
    classDef criminal fill:#e8f5e8,stroke:#1b5e20
    classDef general fill:#e3f2fd,stroke:#1976d2

    class A,B process
    class C decision
    class D criminal
    class E general
```

### 阶段2: 结构化信息提取

```mermaid
flowchart TD
    A[用户查询] --> B[LLM结构化提取器]
    B --> C[crimes_list.txt<br/>45种罪名匹配]
    B --> D[Query2doc增强器]
    B --> E[HyDE增强器]
    B --> F[BM25关键词生成器]

    C --> G[JSON输出]
    D --> G
    E --> G
    F --> G

    G --> H[结构化数据<br/>罪名+增强查询+关键词]

    classDef input fill:#e1f5fe,stroke:#01579b
    classDef process fill:#f3e5f5,stroke:#4a148c
    classDef output fill:#e8f5e8,stroke:#1b5e20

    class A input
    class B,C,D,E,F process
    class G,H output
```

### 阶段3: 智能路由决策

```mermaid
flowchart TD
    A[结构化提取结果] --> B{智能路由器}

    B -->|有识别罪名| C[启用知识图谱搜索]
    B -->|有增强查询| D[启用LLM增强搜索]
    B -->|有BM25关键词| E[启用混合搜索]
    B -->|降级策略| F[启用基础搜索]

    C --> G[并行执行 asyncio.gather]
    D --> G
    E --> G
    F --> G

    G --> H[收集多路搜索结果]

    classDef router fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef search fill:#f3e5f5,stroke:#4a148c
    classDef parallel fill:#e8f5e8,stroke:#1b5e20

    class A,B router
    class C,D,E,F search
    class G,H parallel
```

### 阶段4: 智能融合引擎

```mermaid
flowchart TD
    A[多路搜索结果] --> B[结果标准化处理]
    B --> C[RRF融合算法<br/>k=60]
    B --> D[多路验证置信度]
    B --> E[排名一致性评分]
    B --> F[知识图谱增强加成]

    C --> G[综合评分计算]
    D --> G
    E --> G
    F --> G

    G --> H[最终排序结果]
    H --> I[融合结果数据<br/>分数+置信度+推理]

    classDef input fill:#f3e5f5,stroke:#4a148c
    classDef algorithm fill:#fff3e0,stroke:#e65100
    classDef fusion fill:#e8f5e8,stroke:#1b5e20

    class A,B input
    class C,D,E,F algorithm
    class G,H,I fusion
```

### 阶段5: AI辅助回答生成

```mermaid
flowchart LR
    A[融合搜索结果] --> B[AI回答生成器]
    A2[用户原始查询] --> B

    B --> C[生成专业法律分析]
    B --> D[提供量刑参考依据]
    B --> E[标注信息来源可信度]

    C --> F[完整API响应]
    D --> F
    E --> F

    F --> G[返回给用户]

    classDef input fill:#e1f5fe,stroke:#01579b
    classDef generator fill:#f3e5f5,stroke:#4a148c
    classDef output fill:#e8f5e8,stroke:#1b5e20

    class A,A2 input
    class B,C,D,E generator
    class F,G output
```

---

## 🔍 模块状态流程图

```mermaid
flowchart TD
    A[智能路由器] --> B{检查各模块状态}

    B --> C1[知识图谱搜索]
    B --> C2[LLM增强搜索]
    B --> C3[BM25混合搜索]
    B --> C4[基础语义搜索]

    C1 --> S1{引擎已初始化?}
    C2 --> S2{代码bug已修复?}
    C3 --> S3{BM25索引可用?}
    C4 --> S4[✅ 完全可用]

    S1 -->|否| F1[❌ 降级到其他搜索]
    S1 -->|是| OK1[✅ 执行KG搜索]

    S2 -->|否| F2[❌ 降级到混合搜索]
    S2 -->|是| OK2[✅ 执行LLM增强]

    S3 -->|否| F3[⚠️ 降级到纯语义]
    S3 -->|是| OK3[✅ 执行混合搜索]

    OK1 --> R[收集结果]
    OK2 --> R
    OK3 --> R
    S4 --> R
    F1 --> R
    F2 --> R
    F3 --> R

    classDef available fill:#e8f5e8,stroke:#1b5e20
    classDef warning fill:#fff3e0,stroke:#e65100
    classDef error fill:#ffebee,stroke:#b71c1c
    classDef router fill:#e1f5fe,stroke:#01579b

    class OK1,OK2,OK3,S4 available
    class F3 warning
    class F1,F2 error
    class A,B,R router
```

---

## 🏗️ 技术架构流程图

```mermaid
flowchart TB
    subgraph API ["API 层"]
        A1[POST /api/search/intelligent]
    end

    subgraph Service ["业务服务层"]
        B1[IntelligentSearchService]
        B2[LLMClassifier]
        B3[StructuredExtractor]
    end

    subgraph Search ["搜索引擎层"]
        C1[KnowledgeEnhancedEngine]
        C2[MultiRetrievalEngine]
        C3[VectorSearchEngine]
        C4[SearchCoordinator]
    end

    subgraph Infrastructure ["基础设施层"]
        D1[LegalKnowledgeGraph]
        D2[LLMClient]
        D3[DataLoader]
        D4[VectorCalculator]
    end

    A1 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> C1
    B1 --> C2
    B1 --> C3

    C1 --> D1
    C2 --> D2
    C3 --> D3
    C4 --> D4

    classDef api fill:#e3f2fd,stroke:#0d47a1
    classDef service fill:#f3e5f5,stroke:#4a148c
    classDef search fill:#e8f5e8,stroke:#1b5e20
    classDef infra fill:#fff3e0,stroke:#e65100

    class A1 api
    class B1,B2,B3 service
    class C1,C2,C3,C4 search
    class D1,D2,D3,D4 infra
```

---

## 🎯 数据流转图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API网关
    participant LLM as LLM分类器
    participant EXT as 提取器
    participant RT as 路由器
    participant KG as 知识图谱
    participant ENH as LLM增强
    participant HYB as 混合搜索
    participant FUS as 融合引擎
    participant GEN as 回答生成器

    U->>API: 查询请求
    API->>LLM: 问题分类

    alt 刑法相关问题
        LLM-->>API: 刑法相关(confidence: 0.95)
        API->>EXT: 结构化提取
        EXT-->>API: 罪名+Query2doc+HyDE+BM25词
        API->>RT: 智能路由

        par 并行搜索
            RT->>KG: 基于"故意伤害"搜索
            KG-->>RT: KG结果
        and
            RT->>ENH: Query2doc+HyDE搜索
            ENH-->>RT: 增强结果
        and
            RT->>HYB: BM25混合搜索
            HYB-->>RT: 混合结果
        end

        RT->>FUS: 多路结果融合
        FUS-->>RT: 排序结果
        RT->>GEN: 生成专业回答
        GEN-->>RT: 完整分析
        RT-->>API: 专业法律回答

    else 非刑法问题
        LLM-->>API: 非刑法(confidence: 0.3)
        API->>GEN: 普通AI助手模式
        Note right of GEN: 基于通用提示词<br/>不启用任何搜索功能
        GEN-->>API: 通用助手回答
    end

    API-->>U: 最终回答
```

---

## 📈 性能优化流程图

```mermaid
flowchart TD
    A[用户查询] --> B{缓存检查}
    B -->|命中| C[返回缓存结果]
    B -->|未命中| D[执行完整管道]

    D --> E[并行搜索执行]
    E --> F{结果质量检查}
    F -->|高质量| G[返回结果并缓存]
    F -->|低质量| H[触发降级策略]

    H --> I[使用更可靠的搜索路径]
    I --> J[返回降级结果]

    G --> K[用户响应]
    C --> K
    J --> K

    classDef cache fill:#e8f5e8,stroke:#1b5e20
    classDef process fill:#f3e5f5,stroke:#4a148c
    classDef fallback fill:#fff3e0,stroke:#e65100

    class B,C,G cache
    class A,D,E,K process
    class F,H,I,J fallback
```