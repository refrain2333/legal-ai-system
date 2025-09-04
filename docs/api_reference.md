# 法智导航 API 接口文档

## 📋 概述

法智导航系统提供RESTful API接口，支持智能法律文档检索和咨询服务。

**基础信息：**
- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: API Key（后续版本支持）
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 🔍 搜索接口

### 1. 文档搜索

**端点**: `POST /search`

**描述**: 根据用户查询返回相关的法律文档。

#### 请求参数

```json
{
    "query": "string",           // 必填，查询文本
    "top_k": 10,                // 可选，返回结果数量，默认10
    "include_laws": true,        // 可选，是否包含法律条文，默认true
    "include_cases": true,       // 可选，是否包含案例，默认true
    "filters": {                // 可选，过滤条件
        "law_category": ["合同法", "刑法"],
        "case_year": [2020, 2021, 2022]
    }
}
```

#### 响应格式

```json
{
    "status": "success",
    "message": "查询成功",
    "data": {
        "results": [
            {
                "id": "law_001",
                "type": "law",              // law | case
                "title": "合同法第一百零七条",
                "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                "score": 0.95,             // 相似度评分
                "category": "合同法",
                "source": "《中华人民共和国合同法》",
                "related_items": [         // 关联条目
                    {
                        "id": "case_001",
                        "title": "房屋租赁合同违约案",
                        "relation": "applicable_law"
                    }
                ]
            }
        ],
        "total": 10,
        "query_time": 0.23,              // 查询耗时（秒）
        "has_more": false
    }
}
```

#### 错误响应

```json
{
    "status": "error",
    "message": "查询文本不能为空",
    "error_code": "INVALID_QUERY",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. 相似文档推荐

**端点**: `GET /similar/{document_id}`

**描述**: 根据指定文档ID获取相似文档。

#### 路径参数
- `document_id` (string): 文档ID

#### 查询参数
- `top_k` (int, optional): 返回数量，默认5
- `same_type_only` (bool, optional): 是否只返回相同类型文档，默认false

#### 响应格式
```json
{
    "status": "success",
    "data": {
        "source_document": {
            "id": "law_001",
            "title": "合同法第一百零七条",
            "type": "law"
        },
        "similar_documents": [
            {
                "id": "law_002",
                "title": "合同法第一百零八条",
                "similarity": 0.89
            }
        ]
    }
}
```

---

## 📊 统计接口

### 1. 搜索统计

**端点**: `GET /stats/search`

**描述**: 获取系统搜索统计信息。

#### 响应格式
```json
{
    "status": "success",
    "data": {
        "total_queries": 1250,
        "today_queries": 45,
        "avg_response_time": 0.67,
        "popular_categories": [
            {"name": "合同法", "count": 320},
            {"name": "刑法", "count": 280}
        ]
    }
}
```

---

## 🔧 系统接口

### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查系统运行状态。

#### 响应格式
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
        "database": "online",
        "model": "loaded",
        "index": "ready"
    }
}
```

### 2. 系统信息

**端点**: `GET /info`

**描述**: 获取系统基本信息。

#### 响应格式
```json
{
    "name": "法智导航",
    "version": "1.0.0",
    "model_info": {
        "name": "shibing624/text2vec-base-chinese",
        "version": "1.0",
        "embedding_dim": 768
    },
    "data_statistics": {
        "total_laws": 5000,
        "total_cases": 15000,
        "last_update": "2024-01-15T00:00:00Z"
    }
}
```

---

## 📝 状态码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 参数格式错误或缺失 |
| 401 | 未授权 | API密钥无效或缺失 |
| 429 | 请求过多 | 超出API调用频率限制 |
| 500 | 服务器错误 | 系统内部错误 |
| 503 | 服务不可用 | 系统维护或过载 |

---

## 🚀 使用示例

### Python示例

```python
import requests

# 基础配置
BASE_URL = "http://localhost:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"  # 如果需要认证
}

# 搜索示例
def search_legal_documents(query: str, top_k: int = 10):
    url = f"{BASE_URL}/search"
    payload = {
        "query": query,
        "top_k": top_k,
        "include_laws": True,
        "include_cases": True
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["data"]["results"]
    else:
        raise Exception(f"API调用失败: {response.text}")

# 使用示例
results = search_legal_documents("房屋租赁合同违约")
for result in results:
    print(f"标题: {result['title']}")
    print(f"相似度: {result['score']}")
    print(f"内容: {result['content'][:100]}...")
    print("-" * 50)
```

### JavaScript示例

```javascript
// 搜索函数
async function searchLegalDocuments(query, topK = 10) {
    const url = 'http://localhost:8000/api/v1/search';
    const payload = {
        query: query,
        top_k: topK,
        include_laws: true,
        include_cases: true
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'Authorization': 'Bearer YOUR_API_KEY'  // 如果需要认证
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.data.results;
    } catch (error) {
        console.error('搜索失败:', error);
        throw error;
    }
}

// 使用示例
searchLegalDocuments("交通事故责任认定")
    .then(results => {
        results.forEach(result => {
            console.log(`标题: ${result.title}`);
            console.log(`相似度: ${result.score}`);
            console.log(`类型: ${result.type}`);
        });
    })
    .catch(error => console.error(error));
```

### cURL示例

```bash
# 搜索请求
curl -X POST "http://localhost:8000/api/v1/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "劳动合同解除赔偿",
       "top_k": 5,
       "include_laws": true,
       "include_cases": true
     }'

# 健康检查
curl -X GET "http://localhost:8000/api/v1/health"
```

---

## ⚠️ 注意事项

1. **查询文本限制**: 单次查询文本长度不超过500字符
2. **频率限制**: 每分钟最多100次请求（未来版本）
3. **结果数量**: top_k参数最大值为50
4. **超时时间**: API请求超时时间为30秒
5. **编码格式**: 所有文本数据使用UTF-8编码

---

## 🔄 版本更新

### v1.0.0 (当前版本)
- ✅ 基础搜索功能
- ✅ 文档相似度计算
- ✅ 系统健康检查

### v1.1.0 (计划中)
- 🔄 用户认证系统
- 🔄 搜索历史记录
- 🔄 高级过滤功能

### v2.0.0 (计划中)
- 🔄 智能问答功能
- 🔄 知识图谱可视化
- 🔄 个性化推荐

---

## 📞 技术支持

如有API使用问题，请联系技术支持团队或查看项目文档。