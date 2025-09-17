
"""
增强的Legacy兼容性模块
处理旧pickle文件中的模块引用、类定义和数据格式兼容问题
提供完整的向前兼容支持
"""

import sys
import logging
from types import SimpleNamespace
from typing import Any, Dict, Optional, List, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class LegacyDataObject:
    """通用的Legacy数据对象基类，支持动态属性设置"""
    
    def __init__(self, *args, **kwargs):
        """
        初始化Legacy数据对象
        
        Args:
            *args: 位置参数
            **kwargs: 任意键值对属性
        """
        # 处理所有可能的初始化方式
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                # 如果传入字典，设置所有属性
                for k, v in args[0].items():
                    setattr(self, k, v)
            else:
                # 其他情况，尝试逐个设置
                for i, arg in enumerate(args):
                    setattr(self, f'arg_{i}', arg)
        
        # 设置关键字参数
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # 确保基本属性存在
        if not hasattr(self, 'case_id'):
            self.case_id = None
        if not hasattr(self, 'fact'):
            self.fact = ""
        if not hasattr(self, 'accusations'):
            self.accusations = []
        if not hasattr(self, 'relevant_articles'):
            self.relevant_articles = []
        if not hasattr(self, 'criminals'):
            self.criminals = []
    
    def __getattr__(self, name: str) -> Any:
        """处理缺失属性，返回合理的默认值"""
        if name.endswith('_list') or name.endswith('s'):
            return []
        elif name.endswith('_id') or name.endswith('_number'):
            return None
        elif name.endswith('_info') or name.endswith('_data'):
            return {}
        else:
            return None
    
    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性，支持动态添加"""
        super().__setattr__(name, value)
    
    def __getstate__(self):
        """支持pickle序列化"""
        return self.__dict__
    
    def __setstate__(self, state):
        """支持pickle反序列化"""
        self.__dict__.update(state)
    
    def __reduce__(self):
        """支持pickle协议"""
        return (self.__class__, (), self.__dict__)
    
    def __reduce_ex__(self, protocol):
        """支持pickle协议扩展"""
        return self.__reduce__()
    
    def __call__(self, *args, **kwargs):
        """如果被当作函数调用，返回self"""
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def __repr__(self) -> str:
        attrs = ', '.join(f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith('_'))
        return f"{self.__class__.__name__}({attrs})"


class LegacyCase(LegacyDataObject):
    """Legacy案例数据类，兼容多种历史格式"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 标准化字段映射
        self._normalize_fields()
    
    def _normalize_fields(self):
        """标准化不同历史版本的字段名"""
        # 处理case_id的不同命名
        if not hasattr(self, 'case_id') or self.case_id is None:
            for field_name in ['id', 'document_id', 'caseId', 'case_number']:
                if hasattr(self, field_name):
                    self.case_id = getattr(self, field_name)
                    break
        
        # 处理criminals字段
        if not hasattr(self, 'criminals') or self.criminals is None:
            self.criminals = []
        elif isinstance(self.criminals, str):
            # 如果是字符串，分割为列表
            self.criminals = [name.strip() for name in self.criminals.split(',') if name.strip()]
        
        # 处理accusations字段
        if not hasattr(self, 'accusations') or self.accusations is None:
            self.accusations = []
        elif isinstance(self.accusations, str):
            self.accusations = [acc.strip() for acc in self.accusations.split(',') if acc.strip()]
        
        # 处理relevant_articles字段
        if not hasattr(self, 'relevant_articles') or self.relevant_articles is None:
            self.relevant_articles = []
        elif isinstance(self.relevant_articles, str):
            # 尝试解析字符串形式的法条编号
            try:
                self.relevant_articles = [int(x.strip()) for x in self.relevant_articles.split(',') if x.strip().isdigit()]
            except (ValueError, AttributeError):
                self.relevant_articles = []
        
        # 处理fact字段 - 这是案例内容的关键字段！
        if not hasattr(self, 'fact') or self.fact is None:
            # 尝试从其他可能的字段获取案例事实
            for field_name in ['content', 'text', 'case_fact', 'case_description', 'description', 'body']:
                if hasattr(self, field_name) and getattr(self, field_name):
                    self.fact = getattr(self, field_name)
                    break
            
            # 如果还是没有内容，设置为空字符串
            if not hasattr(self, 'fact') or self.fact is None:
                self.fact = ""


class LegacyArticle(LegacyDataObject):
    """Legacy法条数据类，兼容多种历史格式"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 标准化字段映射
        self._normalize_fields()
    
    def _normalize_fields(self):
        """标准化不同历史版本的字段名"""
        # 处理article_number的不同命名
        if not hasattr(self, 'article_number') or self.article_number is None:
            for field_name in ['number', 'articleNumber', 'article_id', 'id']:
                if hasattr(self, field_name):
                    try:
                        self.article_number = int(getattr(self, field_name))
                        break
                    except (ValueError, TypeError):
                        continue
        
        # 处理title字段
        if not hasattr(self, 'title') or self.title is None:
            self.title = f"第{self.article_number}条" if self.article_number else "未知条文"
        
        # 处理chapter字段
        if not hasattr(self, 'chapter') or self.chapter is None:
            self.chapter = "未知章节"
        
        # 处理content字段 - 这是关键！
        if not hasattr(self, 'content') or self.content is None:
            # 尝试从其他可能的字段获取内容
            for field_name in ['text', 'body', 'description', 'article_text', 'law_text', 'full_text']:
                if hasattr(self, field_name) and getattr(self, field_name):
                    self.content = getattr(self, field_name)
                    break
            
            # 如果还是没有内容，设置为空字符串
            if not hasattr(self, 'content') or self.content is None:
                self.content = ""


class LegacyCompatibilityManager:
    """Legacy兼容性管理器，统一处理所有兼容性问题"""
    
    def __init__(self):
        self.registered_classes = {}
        self.module_mappings = {}
        self._setup_compatibility()
    
    def _setup_compatibility(self):
        """设置兼容性映射"""
        # 注册所有可能的类名别名
        class_mappings = {
            # 案例类的各种名称
            'CriminalCase': LegacyCase,
            'Case': LegacyCase,
            'LegalCase': LegacyCase,
            'CaseData': LegacyCase,
            
            # 法条类的各种名称  
            'CriminalArticle': LegacyArticle,
            'CriminalLawArticle': LegacyArticle,
            'Article': LegacyArticle,
            'LegalArticle': LegacyArticle,
            'LawArticle': LegacyArticle,
            'ArticleData': LegacyArticle,
        }
        
        self.registered_classes.update(class_mappings)
        
        # 创建兼容性模块结构
        self._create_module_structure()
    
    def _create_module_structure(self):
        """创建完整的模块兼容性结构"""
        # 创建根数据模块
        data_module = SimpleNamespace()
        data_module.__file__ = 'src.data'
        data_module.__path__ = ['src.data']
        
        # 添加所有类到根模块
        for class_name, class_obj in self.registered_classes.items():
            setattr(data_module, class_name, class_obj)
        
        # 创建子模块
        submodules = [
            'criminal_articles',
            'criminal_cases', 
            'criminal_law_processor',  # 这是pickle文件中真正需要的模块
            'data_processor',
            'legal_data'
        ]
        
        for submodule_name in submodules:
            submodule = SimpleNamespace()
            submodule.__file__ = f'src.data.{submodule_name}'
            
            # 在每个子模块中也注册所有类
            for class_name, class_obj in self.registered_classes.items():
                setattr(submodule, class_name, class_obj)
            
            setattr(data_module, submodule_name, submodule)
            
            # 在sys.modules中注册
            sys.modules[f'src.data.{submodule_name}'] = submodule
        
        # 在sys.modules中注册主模块 - 这个必须在最后
        sys.modules['src.data'] = data_module
        self.module_mappings['src.data'] = data_module
        
        logger.info(f"Registered {len(self.registered_classes)} legacy classes and {len(submodules)} modules")
    
    def register_class(self, class_name: str, class_obj: type):
        """动态注册新的Legacy类"""
        self.registered_classes[class_name] = class_obj
        
        # 更新所有已注册的模块
        for module in self.module_mappings.values():
            if hasattr(module, '__dict__'):
                setattr(module, class_name, class_obj)
    
    def get_class(self, class_name: str) -> Optional[type]:
        """获取注册的Legacy类"""
        return self.registered_classes.get(class_name)
    
    def validate_pickle_file(self, file_path: Union[str, Path]) -> bool:
        """验证pickle文件是否可以正常加载"""
        try:
            import pickle
            with open(file_path, 'rb') as f:
                # 只检查文件是否可读，不实际加载数据
                f.read(1)  # 读取一个字节来验证文件可访问
                f.seek(0)  # 重置文件指针
            return True
        except Exception as e:
            logger.warning(f"Pickle file validation failed for {file_path}: {e}")
            return False
    
    def safe_load_pickle(self, file_path: Union[str, Path]) -> Optional[Any]:
        """safe_load_pickle方法的别名，保持兼容性"""
        return self.safe_pickle_load(file_path)
    
    def safe_pickle_load(self, file_path: Union[str, Path]) -> Optional[Any]:
        """安全地加载pickle文件，处理兼容性问题"""
        try:
            import pickle
            import sys
            file_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                logger.error(f"Pickle file does not exist: {file_path}")
                return None
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.error(f"Pickle file is empty: {file_path}")
                return None
            
            logger.debug(f"Loading pickle file: {file_path} (size: {file_size} bytes)")
            
            # 创建自定义的Unpickler来处理兼容性问题
            manager = self  # 保存self引用给内部类使用
            
            class CompatibilityUnpickler(pickle.Unpickler):
                def find_class(self, module, name):
                    """处理模块和类名的兼容性映射"""
                    # 处理旧的模块路径
                    if module.startswith('src.data.'):
                        # 尝试从兼容性管理器获取类
                        if name in manager.registered_classes:
                            return manager.registered_classes[name]
                    
                    # 处理常见的类名映射
                    class_mappings = {
                        'CriminalCase': LegacyCase,
                        'Case': LegacyCase,
                        'CriminalArticle': LegacyArticle,
                        'Article': LegacyArticle,
                        'CriminalLawArticle': LegacyArticle,
                    }
                    
                    if name in class_mappings:
                        logger.debug(f"Mapping class {module}.{name} to {class_mappings[name]}")
                        return class_mappings[name]
                    
                    # 尝试默认加载
                    try:
                        return super().find_class(module, name)
                    except (ImportError, AttributeError) as e:
                        logger.warning(f"Could not find class {module}.{name}, using LegacyDataObject: {e}")
                        return LegacyDataObject
            
            with open(file_path, 'rb') as f:
                unpickler = CompatibilityUnpickler(f)
                data = unpickler.load()
            
            if data is None:
                logger.error(f"Pickle file loaded but data is None: {file_path}")
                return None
            
            data_length = len(data) if hasattr(data, '__len__') else 'unknown'
            logger.info(f"Successfully loaded pickle file: {file_path} (items: {data_length})")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load pickle file {file_path}: {type(e).__name__}: {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None


# 创建全局兼容性管理器实例
_compatibility_manager = LegacyCompatibilityManager()

# 为了保持向后兼容，保留原有的类定义
CriminalCase = LegacyCase
CriminalArticle = LegacyArticle  
CriminalLawArticle = LegacyArticle

# 导出便捷函数
def get_compatibility_manager() -> LegacyCompatibilityManager:
    """获取兼容性管理器实例"""
    return _compatibility_manager

def register_legacy_class(class_name: str, class_obj: type):
    """注册新的Legacy类"""
    _compatibility_manager.register_class(class_name, class_obj)

def safe_load_pickle(file_path: Union[str, Path]) -> Optional[Any]:
    """安全加载pickle文件的便捷函数"""
    return _compatibility_manager.safe_pickle_load(file_path)

def validate_data_file(file_path: Union[str, Path]) -> bool:
    """验证数据文件的便捷函数"""
    return _compatibility_manager.validate_pickle_file(file_path)

# 初始化时的日志
logger.info("Legacy compatibility module initialized successfully")