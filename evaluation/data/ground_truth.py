#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ground Truth数据加载器
加载和管理真实映射数据
"""

import pickle
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# 创建模块适配器来处理pickle加载时的模块路径问题
class ModuleAdapter:
    """模块适配器，用于处理pickle反序列化时的模块路径问题"""
    
    def __init__(self):
        self.fake_modules_created = False
        # 延迟创建假模块，只在需要时创建
    
    def create_fake_modules_if_needed(self):
        """只在需要加载pickle文件时创建假模块"""
        if not self.fake_modules_created:
            # 创建完整的假模块层次结构
            fake_modules = [
                'src',
                'src.data',
                'src.data.criminal_law_processor',
                'src.domains',
                'src.domains.entities',
                'data_processor'  # 添加缺失的data_processor模块
            ]
            
            for module_name in fake_modules:
                if module_name not in sys.modules:
                    # 创建最小化的假模块
                    fake_module = type(sys)(module_name)
                    sys.modules[module_name] = fake_module
                    logger.info(f"创建临时假模块 {module_name} 用于pickle加载")
            
            # 为了兼容pickle，创建所需的假类
            try:
                # 创建pickle文件需要的类
                fake_article_class = type('Article', (), {})
                fake_case_class = type('Case', (), {})
                fake_criminal_law_article_class = type('CriminalLawArticle', (), {})
                fake_criminal_case_class = type('CriminalCase', (), {})
                fake_simple_article_class = type('SimpleArticle', (), {})  # 添加SimpleArticle类
                fake_simple_case_class = type('SimpleCase', (), {})  # 添加SimpleCase类
                
                # 添加到相应的模块
                if 'src.domains.entities' in sys.modules:
                    setattr(sys.modules['src.domains.entities'], 'Article', fake_article_class)
                    setattr(sys.modules['src.domains.entities'], 'Case', fake_case_class)
                
                if 'src.data.criminal_law_processor' in sys.modules:
                    setattr(sys.modules['src.data.criminal_law_processor'], 'CriminalLawArticle', fake_criminal_law_article_class)
                    setattr(sys.modules['src.data.criminal_law_processor'], 'CriminalCase', fake_criminal_case_class)
                
                # 为data_processor模块添加所需的类
                if 'data_processor' in sys.modules:
                    setattr(sys.modules['data_processor'], 'Article', fake_article_class)
                    setattr(sys.modules['data_processor'], 'Case', fake_case_class)
                    setattr(sys.modules['data_processor'], 'SimpleArticle', fake_simple_article_class)
                    setattr(sys.modules['data_processor'], 'SimpleCase', fake_simple_case_class)
                
                # 添加到__main__模块以解决当前错误
                import __main__
                setattr(__main__, 'SimpleArticle', fake_simple_article_class)
                setattr(__main__, 'SimpleCase', fake_simple_case_class)
                setattr(__main__, 'Article', fake_article_class)
                setattr(__main__, 'Case', fake_case_class)
                
                # 为data_processor模块添加更多类
                if 'data_processor' in sys.modules:
                    setattr(sys.modules['data_processor'], 'CriminalLawArticle', fake_criminal_law_article_class)
                    setattr(sys.modules['data_processor'], 'CriminalCase', fake_criminal_case_class)
                    
                logger.info("创建临时假实体类用于pickle加载")
            except Exception as e:
                logger.debug(f"创建假实体类时出现警告: {e}")
                
            self.fake_modules_created = True
    
    def cleanup_fake_modules(self):
        """清理假模块"""
        if self.fake_modules_created:
            # 清理所有我们创建的假模块
            fake_modules = [
                'src.domains.entities',
                'src.domains', 
                'src.data.criminal_law_processor',
                'src.data',
                'src',
                'data_processor'  # 添加data_processor模块清理
            ]
            
            for module_name in fake_modules:
                if module_name in sys.modules:
                    # 只删除我们创建的假模块（没有__file__属性的）
                    fake_module = sys.modules[module_name]
                    if not hasattr(fake_module, '__file__'):  # 确认是假模块
                        del sys.modules[module_name]
                        logger.debug(f"清理临时假模块 {module_name}")
            
            self.fake_modules_created = False

# 全局模块适配器实例
_module_adapter = ModuleAdapter()


class GroundTruthLoader:
    """Ground Truth数据加载器"""
    
    def __init__(self):
        """初始化数据加载器"""
        # 使用项目实际的数据加载器
        try:
            # 添加项目路径
            project_root = Path(__file__).resolve().parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # 验证src目录存在
            src_dir = project_root / "src"
            if not src_dir.exists():
                raise ImportError(f"src目录不存在: {src_dir}")
            
            from src.infrastructure.storage.data_loader import DataLoader
            from src.config.settings import settings
            
            self.data_loader = DataLoader(config=settings, project_root=project_root)
            logger.info("使用项目实际的DataLoader")
        except ImportError as e:
            logger.warning(f"无法导入项目DataLoader: {e}，使用备用方案")
            self.data_loader = None
        
        self.article_case_mapping = {}
        self.case_article_mapping = {}
        self.articles_dict = {}
        self.cases_dict = {}
        
        self.loaded = False
    
    def load(self) -> bool:
        """
        加载所有Ground Truth数据
        
        Returns:
            是否成功加载
        """
        try:
            if self.data_loader:
                # 使用项目实际的数据加载器
                logger.info("使用项目DataLoader加载数据...")
                load_result = self.data_loader.load_all()
                
                if load_result.get('success'):
                    # 从项目数据加载器获取数据
                    self._extract_data_from_project_loader()
                    self.loaded = True
                    logger.info("成功从项目DataLoader加载数据")
                    return True
                else:
                    logger.error("项目DataLoader加载失败 - 评估系统必须使用真实数据")
                    raise RuntimeError("项目DataLoader加载失败，拒绝使用模拟数据")
            else:
                # 不允许使用备用方案
                raise RuntimeError("无法导入项目DataLoader，拒绝使用模拟数据")
                
        except Exception as e:
            logger.error(f"加载Ground Truth数据失败: {e}")
            import traceback
            traceback.print_exc()
            # 绝不使用模拟数据！
            raise RuntimeError(f"必须使用真实数据，禁止模拟数据: {e}")
    
    def _extract_data_from_project_loader(self):
        """从TestDataGenerator获取一致的映射数据，确保评估准确性"""
        try:
            logger.info("🔧 使用TestDataGenerator的数据确保一致性")
            
            # 直接从evaluation系统导入TestDataGenerator获取映射
            try:
                from .test_generator import TestDataGenerator
                test_generator = TestDataGenerator()
                test_generator.load_data()
                
                # 检查数据是否成功加载
                if (test_generator.article_case_mapping is None or 
                    test_generator.articles_data is None or 
                    test_generator.cases_data is None):
                    raise ValueError("TestDataGenerator数据加载不完整")
                
                # 使用TestDataGenerator的映射数据
                self.article_case_mapping = test_generator.article_case_mapping.copy()
                
                # 构建articles_dict从TestDataGenerator的数据
                for article in test_generator.articles_data:
                    article_num = article.get('article_number')
                    if article_num:
                        self.articles_dict[article_num] = {
                            'article_number': article_num,
                            'title': article.get('title', f'第{article_num}条'),
                            'content': article.get('content', article.get('full_text', '')),
                            'chapter': article.get('chapter', ''),
                            'law_name': '刑法'
                        }
                
                # 构建cases_dict从TestDataGenerator的数据
                for case in test_generator.cases_data:
                    case_id = case.get('case_id')
                    if case_id:
                        self.cases_dict[case_id] = {
                            'case_id': case_id,
                            'fact': case.get('fact', ''),
                            'accusations': case.get('accusations', []),
                            'relevant_articles': case.get('relevant_articles', []),
                            'sentence_months': case.get('sentence_info', {}).get('imprisonment_months', 0)
                        }
                
                # 构建case_article_mapping
                for case_id, case in self.cases_dict.items():
                    relevant_articles = case.get('relevant_articles', [])
                    if relevant_articles:
                        self.case_article_mapping[case_id] = relevant_articles
                
                logger.info("✅ 成功使用TestDataGenerator数据")
                
            except Exception as e:
                logger.error(f"TestDataGenerator加载失败: {e}")
                # 回退到原来的方法，但先初始化映射
                self.article_case_mapping = {}
                self._extract_data_from_pkl_files()
            
            # 输出统计信息
            logger.info(f"📊 数据加载完成:")
            logger.info(f"  - 法条数量: {len(self.articles_dict)}")
            logger.info(f"  - 案例数量: {len(self.cases_dict)}")
            logger.info(f"  - 法条到案例映射: {len(self.article_case_mapping)}")
            logger.info(f"  - 案例到法条映射: {len(self.case_article_mapping)}")
            
        except Exception as e:
            logger.error(f"数据提取失败: {e}")
            raise
    
    def _extract_data_from_pkl_files(self):
        """原来的从pkl文件提取数据的方法作为备选方案"""
        try:
            # 🔧 修复：直接从criminal目录加载完整数据，而不是vectors的metadata
            logger.info("🔧 修复：直接从criminal目录加载完整数据")
            project_root = Path(__file__).resolve().parent.parent.parent
            
            # 加载完整的法条数据
            articles_path = project_root / "data" / "processed" / "criminal" / "criminal_articles.pkl"
            if articles_path.exists():
                logger.info(f"📖 加载完整法条数据: {articles_path}")
                _module_adapter.create_fake_modules_if_needed()
                try:
                    # 使用自定义unpickler来处理缺失的类
                    with open(articles_path, 'rb') as f:
                        articles_list = self._safe_pickle_load(f)
                    logger.info(f"✅ 成功加载 {len(articles_list)} 条完整法条数据")
                    
                    # 检查前几个法条的完整字段
                    for i, article in enumerate(articles_list[:3]):
                        # 使用 getattr 而不是 .get() 来访问对象属性
                        article_num = getattr(article, 'article_number', None)
                        content = getattr(article, 'content', '') or getattr(article, 'full_text', '') or getattr(article, 'text', '')
                        title = getattr(article, 'title', '')
                        logger.info(f"📖 法条{i+1}: 编号={article_num}, content长度={len(content)}, title='{title[:50]}...'")
                        logger.info(f"📖 法条{i+1}对象类型: {type(article)}")
                        logger.info(f"📖 法条{i+1}可用属性: {[attr for attr in dir(article) if not attr.startswith('_')]}")
                        if i == 0 and content:
                            logger.info(f"📖 法条{i+1} content前100字符: '{content[:100]}'")
                    
                    # 构建法条字典 - 将对象转换为字典格式
                    for article in articles_list:
                        article_num = getattr(article, 'article_number', None)
                        if article_num:
                            # 转换为字典格式，便于后续使用
                            article_dict = {
                                'article_number': article_num,
                                'title': getattr(article, 'title', ''),
                                'content': getattr(article, 'content', '') or getattr(article, 'full_text', '') or getattr(article, 'text', ''),
                                'chapter': getattr(article, 'chapter', ''),
                                'section': getattr(article, 'section', None),
                                'law_name': getattr(article, 'law_name', ''),
                                'type': getattr(article, 'type', 'article')
                            }
                            self.articles_dict[article_num] = article_dict
                            
                finally:
                    _module_adapter.cleanup_fake_modules()
            else:
                logger.error(f"❌ 法条数据文件不存在: {articles_path}")
                raise FileNotFoundError(f"法条数据文件不存在: {articles_path}")
            
            # 加载完整的案例数据
            cases_path = project_root / "data" / "processed" / "criminal" / "criminal_cases.pkl"
            if cases_path.exists():
                logger.info(f"📖 加载完整案例数据: {cases_path}")
                _module_adapter.create_fake_modules_if_needed()
                try:
                    # 使用自定义unpickler来处理缺失的类
                    with open(cases_path, 'rb') as f:
                        cases_list = self._safe_pickle_load(f)
                    logger.info(f"✅ 成功加载 {len(cases_list)} 个完整案例数据")
                    
                    # 检查前几个案例的完整字段
                    for i, case in enumerate(cases_list[:3]):
                        # 使用 getattr 而不是 .get() 来访问对象属性
                        case_id = getattr(case, 'case_id', None) or getattr(case, 'id', None)
                        fact = getattr(case, 'fact', '') or getattr(case, 'content', '') or getattr(case, 'description', '')
                        content = getattr(case, 'content', '') or getattr(case, 'full_text', '')
                        relevant_articles = getattr(case, 'relevant_articles', [])
                        accusations = getattr(case, 'accusations', [])
                        logger.info(f"📖 案例{i+1}: ID={case_id}, fact长度={len(fact)}, content长度={len(content)}")
                        logger.info(f"📖 案例{i+1}: relevant_articles={relevant_articles}, accusations={accusations}")
                        logger.info(f"📖 案例{i+1}对象类型: {type(case)}")
                        logger.info(f"📖 案例{i+1}可用属性: {[attr for attr in dir(case) if not attr.startswith('_')]}")
                        if i == 0 and fact:
                            logger.info(f"📖 案例{i+1} fact前100字符: '{fact[:100]}'")
                    
                    # 构建案例字典和映射关系 - 将对象转换为字典格式
                    for case in cases_list:
                        case_id = getattr(case, 'case_id', None) or getattr(case, 'id', None)
                        if case_id:
                            # 转换为字典格式，便于后续使用
                            case_dict = {
                                'case_id': case_id,
                                'id': case_id,
                                'fact': getattr(case, 'fact', '') or getattr(case, 'content', '') or getattr(case, 'description', ''),
                                'content': getattr(case, 'content', '') or getattr(case, 'full_text', ''),
                                'relevant_articles': getattr(case, 'relevant_articles', []),
                                'accusations': getattr(case, 'accusations', []),
                                'criminals': getattr(case, 'criminals', []),
                                'sentence_info': getattr(case, 'sentence_info', {}),
                                'type': getattr(case, 'type', 'case')
                            }
                            self.cases_dict[case_id] = case_dict
                            
                            # 构建案例到法条的映射
                            relevant_articles = getattr(case, 'relevant_articles', [])
                            if relevant_articles:
                                self.case_article_mapping[case_id] = relevant_articles
                                
                                # 构建法条到案例的映射
                                for article_num in relevant_articles:
                                    if article_num not in self.article_case_mapping:
                                        self.article_case_mapping[article_num] = []
                                    self.article_case_mapping[article_num].append(case_id)
                                    
                finally:
                    _module_adapter.cleanup_fake_modules()
            else:
                logger.error(f"❌ 案例数据文件不存在: {cases_path}")
                raise FileNotFoundError(f"案例数据文件不存在: {cases_path}")
            
            # 输出统计信息
            logger.info(f"📊 数据加载完成:")
            logger.info(f"  - 法条数量: {len(self.articles_dict)}")
            logger.info(f"  - 案例数量: {len(self.cases_dict)}")
            logger.info(f"  - 法条到案例映射: {len(self.article_case_mapping)}")
            logger.info(f"  - 案例到法条映射: {len(self.case_article_mapping)}")
            
        except Exception as e:
            logger.error(f"从项目数据提取失败: {e}")
            raise
    
    def _safe_pickle_load(self, file_obj):
        """安全的pickle加载，处理缺失的类定义"""
        import pickle
        
        class SafeUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                # 对于缺失的类，创建一个字典来代替
                try:
                    return super().find_class(module, name)
                except (ImportError, AttributeError) as e:
                    logger.debug(f"创建替代类 {module}.{name}: {e}")
                    # 创建一个简单的类来代替缺失的类
                    return type(name, (dict,), {
                        '__module__': module,
                        '__init__': lambda self, *args, **kwargs: dict.__init__(self, kwargs) if kwargs else dict.__init__(self),
                        '__getattr__': lambda self, key: self.get(key, None),
                        '__setattr__': lambda self, key, value: self.__setitem__(key, value)
                    })
        
        try:
            return SafeUnpickler(file_obj).load()
        except Exception as e:
            logger.warning(f"SafeUnpickler失败，使用标准pickle: {e}")
            file_obj.seek(0)  # 重置文件指针
            return pickle.load(file_obj)
    
    def _load_fallback(self) -> bool:
        """备用加载方案，创建模拟数据"""
        logger.warning("使用模拟数据作为备用方案")
        
        # 创建模拟的法条数据
        for i in range(1, 11):  # 模拟10条法条
            article_num = 100 + i
            self.articles_dict[article_num] = {
                'article_number': article_num,
                'content': f'模拟法条内容 {article_num}',
                'chapter': f'第{i}章',
                'law_name': '刑法'
            }
        
        # 创建模拟的案例数据
        for i in range(1, 21):  # 模拟20个案例
            case_id = f'case_{i:03d}'
            relevant_articles = [100 + (i % 10) + 1]  # 每个案例关联一个法条
            
            self.cases_dict[case_id] = {
                'case_id': case_id,
                'id': case_id,
                'fact': f'模拟案例事实 {i}',
                'relevant_articles': relevant_articles,
                'accusations': [f'模拟罪名{i % 5 + 1}']
            }
            
            self.case_article_mapping[case_id] = relevant_articles
            
            # 构建法条到案例的映射
            for article_num in relevant_articles:
                if article_num not in self.article_case_mapping:
                    self.article_case_mapping[article_num] = []
                self.article_case_mapping[article_num].append(case_id)
        
        self.loaded = True
        logger.info("模拟数据创建完成")
        return True
    
    def get_article_cases(self, article_number: int) -> List[str]:
        """
        获取法条关联的案例列表
        
        Args:
            article_number: 法条编号
            
        Returns:
            案例ID列表
        """
        if not self.loaded:
            self.load()
        return self.article_case_mapping.get(article_number, [])
    
    def get_case_articles(self, case_id: str) -> List[int]:
        """
        获取案例关联的法条列表
        
        Args:
            case_id: 案例ID
            
        Returns:
            法条编号列表
        """
        if not self.loaded:
            self.load()
        return self.case_article_mapping.get(case_id, [])
    
    def get_article_content(self, article_number: int) -> str:
        """
        获取法条内容
        
        Args:
            article_number: 法条编号
            
        Returns:
            法条内容文本
        """
        if not self.loaded:
            self.load()
        article = self.articles_dict.get(article_number, {})
        return article.get('content', '')
    
    def get_case_fact(self, case_id: str) -> str:
        """
        获取案例事实
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例事实文本
        """
        if not self.loaded:
            self.load()
        case = self.cases_dict.get(case_id, {})
        return case.get('fact', '')
    
    def get_case_crimes(self, case_id: str) -> List[str]:
        """
        获取案例罪名
        
        Args:
            case_id: 案例ID
            
        Returns:
            罪名列表
        """
        if not self.loaded:
            self.load()
        case = self.cases_dict.get(case_id, {})
        return case.get('accusations', [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息字典
        """
        if not self.loaded:
            self.load()
        
        # 计算统计信息
        total_mappings = len(self.article_case_mapping)
        total_cases_in_mappings = sum(
            len(cases) for cases in self.article_case_mapping.values()
        )
        avg_cases_per_article = (
            total_cases_in_mappings / total_mappings 
            if total_mappings > 0 else 0
        )
        
        # 找出关联案例最多的法条
        max_cases_article = None
        max_cases_count = 0
        for article_num, cases in self.article_case_mapping.items():
            if len(cases) > max_cases_count:
                max_cases_count = len(cases)
                max_cases_article = article_num
        
        return {
            'total_articles': len(self.articles_dict),
            'total_cases': len(self.cases_dict),
            'articles_with_cases': total_mappings,
            'cases_with_articles': len(self.case_article_mapping),
            'avg_cases_per_article': round(avg_cases_per_article, 2),
            'max_cases_article': {
                'article_number': max_cases_article,
                'case_count': max_cases_count
            } if max_cases_article else None
        }