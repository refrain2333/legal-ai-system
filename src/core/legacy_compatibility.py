#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容旧数据结构的类定义
用于加载旧版本序列化的数据
"""

class DummyClass:
    """用于兼容旧数据的虚拟类"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class CriminalArticle:
    """法条数据类 - 兼容旧版本"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class CriminalLawArticle:
    """法条数据类 - 兼容旧版本"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class CriminalCase:
    """案例数据类 - 兼容旧版本"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class CriminalMapping:
    """法条案例映射类 - 兼容旧版本"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# 创建虚拟的模块类
class VirtualModule:
    def __init__(self):
        self.DummyClass = DummyClass
        self.CriminalArticle = CriminalArticle
        self.CriminalLawArticle = CriminalLawArticle  # 添加缺失的类
        self.CriminalCase = CriminalCase
        self.CriminalMapping = CriminalMapping
        
        # 添加可能需要的其他类
        self.CriminalLawProcessor = DummyClass
        self.MarkdownProcessor = DummyClass
        self.DataProcessor = DummyClass
        
        # 添加可能的函数
        self.process_data = lambda x: x
        self.load_data = lambda x: x

# 创建包结构
class VirtualPackage:
    def __init__(self):
        # 子模块
        self.criminal_data_processor = VirtualModule()
        self.criminal_law_processor = VirtualModule()
        self.markdown_processor = VirtualModule()
        self.unified_dataset_processor = VirtualModule()
        self.cases_processor = VirtualModule()
        self.sqlite_processor = VirtualModule()
        
        # 直接的类
        self.DummyClass = DummyClass
        self.CriminalArticle = CriminalArticle
        self.CriminalLawArticle = CriminalLawArticle  # 添加缺失的类
        self.CriminalCase = CriminalCase
        self.CriminalMapping = CriminalMapping

# 为了兼容旧的导入路径，我们需要在sys.modules中注册
import sys

# 创建完整的模块层次结构
src_data_package = VirtualPackage()

# 注册所有可能的模块路径
module_mappings = {
    'src': VirtualModule(),
    'src.data': src_data_package,
    'src.data.criminal_data_processor': VirtualModule(),
    'src.data.criminal_law_processor': VirtualModule(),
    'src.data.markdown_processor': VirtualModule(),
    'src.data.unified_dataset_processor': VirtualModule(),
    'src.data.cases_processor': VirtualModule(),
    'src.data.sqlite_processor': VirtualModule(),
    'src.data.full_dataset_processor': VirtualModule(),
    
    # 没有src前缀的版本
    'data': src_data_package,
    'criminal_data_processor': VirtualModule(),
    'criminal_law_processor': VirtualModule(), 
    'markdown_processor': VirtualModule(),
    'unified_dataset_processor': VirtualModule(),
    'cases_processor': VirtualModule(),
    'sqlite_processor': VirtualModule(),
}

# 批量注册模块
for module_name, module_obj in module_mappings.items():
    sys.modules[module_name] = module_obj

print("Legacy compatibility module loaded - ready to handle old pickle files")