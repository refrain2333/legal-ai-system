#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心业务实体 (Entities)
定义法律文档领域的核心业务对象
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass


@dataclass
class LegalDocument(ABC):
    """法律文档基类 - 核心业务实体"""
    
    id: str
    title: str
    content: str
    document_type: str
    
    @abstractmethod
    def get_searchable_text(self) -> str:
        """获取用于搜索的文本内容"""
        pass
    
    @abstractmethod
    def get_display_title(self) -> str:
        """获取显示标题"""
        pass


@dataclass
class Article(LegalDocument):
    """法条实体"""
    
    article_number: Optional[int] = None
    chapter: Optional[str] = None
    law_name: Optional[str] = None
    
    def __post_init__(self):
        self.document_type = "article"
    
    def get_searchable_text(self) -> str:
        """返回用于搜索的完整文本"""
        text_parts = [self.title or '', self.content or '']
        if self.chapter:
            text_parts.append(self.chapter)
        if self.law_name:
            text_parts.append(self.law_name)
        return ' '.join(filter(None, text_parts))
    
    def get_display_title(self) -> str:
        """返回显示标题"""
        if self.article_number:
            return f"第{self.article_number}条 {self.title or ''}"
        return self.title or f"法条 {self.id}"


@dataclass  
class Case(LegalDocument):
    """案例实体"""
    
    case_id: Optional[str] = None
    criminals: Optional[List[str]] = None
    accusations: Optional[List[str]] = None
    relevant_articles: Optional[List[int]] = None
    
    # 量刑信息
    punish_of_money: Optional[float] = None
    death_penalty: Optional[bool] = None
    life_imprisonment: Optional[bool] = None
    imprisonment_months: Optional[int] = None
    
    def __post_init__(self):
        self.document_type = "case"
        if self.case_id is None:
            self.case_id = self.id
    
    def get_searchable_text(self) -> str:
        """返回用于搜索的完整文本"""
        text_parts = [self.title or '', self.content or '']
        
        if self.criminals:
            text_parts.append(' '.join(self.criminals))
        if self.accusations:
            text_parts.append(' '.join(self.accusations))
            
        return ' '.join(filter(None, text_parts))
    
    def get_display_title(self) -> str:
        """返回显示标题"""
        if self.criminals and len(self.criminals) > 0:
            main_criminal = self.criminals[0]
            if self.accusations and len(self.accusations) > 0:
                main_charge = self.accusations[0]
                return f"{main_criminal}{main_charge}案"
        return self.title or f"案例 {self.case_id}"
    
    def has_severe_punishment(self) -> bool:
        """判断是否为重刑案例"""
        return (self.death_penalty is True or 
                self.life_imprisonment is True or 
                (self.imprisonment_months is not None and self.imprisonment_months >= 120))  # 10年以上