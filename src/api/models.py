"""
API数据模型定义模块

此模块定义了FastAPI接口的请求和响应数据模型，使用Pydantic进行数据验证和序列化。
所有模型都会自动生成OpenAPI文档。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any

class SearchRequest(BaseModel):
    """搜索请求模型
    
    用于接收前端发送的搜索请求参数
    """
    query: str = Field(..., description="搜索查询文本，支持自然语言查询")
    top_k: int = Field(10, description="返回结果数量，默认为10，最大不超过50", le=50)

class SearchResult(BaseModel):
    """单条搜索结果模型
    
    包含搜索结果的完整信息，统一处理法条和案例两种文档类型
    """
    id: str = Field(..., description="文档唯一标识符")
    title: str = Field(..., description="文档显示标题")
    content: str = Field(..., description="文档完整内容文本")
    similarity: float = Field(..., description="与查询的语义相似度分数，范围0-1")
    type: str = Field(..., description="文档类型：'article'（法条）或'case'（案例）")
    
    # 案例特有字段
    case_id: Optional[str] = Field(None, description="案例编号，仅案例类型有效")
    criminals: Optional[List[str]] = Field(None, description="犯罪嫌疑人列表，仅案例类型有效")
    accusations: Optional[List[str]] = Field(None, description="指控罪名列表，仅案例类型有效")
    relevant_articles: Optional[List[int]] = Field(None, description="相关法条编号列表，仅案例类型有效")
    punish_of_money: Optional[float] = Field(None, description="罚金数额（万元），仅案例类型有效")
    death_penalty: Optional[bool] = Field(None, description="是否判处死刑，仅案例类型有效")
    life_imprisonment: Optional[bool] = Field(None, description="是否判处无期徒刑，仅案例类型有效")
    imprisonment_months: Optional[int] = Field(None, description="有期徒刑月数，仅案例类型有效")
    
    # 法条特有字段
    article_number: Optional[int] = Field(None, description="法条编号，仅法条类型有效")
    chapter: Optional[str] = Field(None, description="所属章节名称，仅法条类型有效")

class SearchResponse(BaseModel):
    """搜索响应模型
    
    包含搜索请求的整体结果信息
    """
    success: bool = Field(True, description="搜索操作是否成功")
    results: List[SearchResult] = Field([], description="搜索结果列表")
    total: int = Field(0, description="匹配结果总数")
    query: str = Field("", description="原始查询文本")

class StatusResponse(BaseModel):
    """系统状态响应模型
    
    增强版，包含启动状态信息
    """
    status: str = Field("ok", description="系统状态：'ok'正常，'loading'加载中，'error'异常")
    ready: bool = Field(False, description="系统是否准备就绪，可以处理请求")
    total_documents: int = Field(0, description="系统中索引的文档总数")
    startup_info: Optional[dict] = Field(None, description="启动状态信息，包含加载进度等详细信息")
