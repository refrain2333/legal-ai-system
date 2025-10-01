#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新的模块化路由入口
替换原有的单体routes.py，使用模块化结构
"""

# 直接从routes目录导入已创建的router
from .routes import router

__all__ = ["router"]