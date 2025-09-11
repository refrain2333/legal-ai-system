from pydantic import BaseModel, Field
from typing import List, Optional, Any

class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(10, description="返回结果数量", le=50)

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    type: str
    
    # 案例特有字段
    case_id: Optional[str] = None
    criminals: Optional[List[str]] = None
    accusations: Optional[List[str]] = None
    relevant_articles: Optional[List[int]] = None
    punish_of_money: Optional[float] = None
    death_penalty: Optional[bool] = None
    life_imprisonment: Optional[bool] = None
    imprisonment_months: Optional[int] = None
    
    # 法条特有字段
    article_number: Optional[int] = None
    chapter: Optional[str] = None

class SearchResponse(BaseModel):
    success: bool = True
    results: List[SearchResult] = []
    total: int = 0
    query: str = ""

class StatusResponse(BaseModel):
    status: str = "ok"
    ready: bool = False
    total_documents: int = 0
