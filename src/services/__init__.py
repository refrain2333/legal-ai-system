#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务层 (Service Layer)
封装核心业务逻辑，协调领域对象和基础设施
"""

from .search_service import SearchService

__all__ = ['SearchService']