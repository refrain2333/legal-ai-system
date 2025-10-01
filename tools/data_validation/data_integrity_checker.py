#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性检查工具
验证criminal和vectors目录数据的一致性

使用方法:
python tools/data_validation/data_integrity_checker.py
"""

import sys
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
import logging
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataIntegrityChecker:
    """数据完整性检查器"""
    
    def __init__(self, data_root: Optional[Path] = None):
        """初始化检查器"""
        self.data_root = data_root or project_root / "data" / "processed"
        self.vectors_dir = self.data_root / "vectors"
        self.criminal_dir = self.data_root / "criminal"
        
        # 检查结果
        self.results = {}
        
        # 数据存储
        self.vector_data = {}
        self.criminal_data = {}
        
    def check_all_integrity(self) -> Dict[str, Any]:
        """检查所有数据完整性"""
        print("=" * 60)
        print("🔍 数据完整性验证工具 - 开始检查")
        print("=" * 60)
        
        # 检查目录存在
        if not self._check_directories():
            return {'error': '数据目录不存在'}
        
        # 加载数据
        if not self._load_all_data():
            return {'error': '数据加载失败'}
        
        # 执行各项检查
        self.results['file_consistency'] = self._check_file_consistency()
        self.results['id_mapping'] = self._check_id_mapping()
        self.results['content_integrity'] = self._check_content_integrity()
        self.results['vector_quality'] = self._check_vector_quality()
        
        # 生成总结报告
        self.results['summary'] = self._generate_summary()
        
        return self.results
    
    def _check_directories(self) -> bool:
        """检查目录存在性"""
        print("📁 检查数据目录...")
        
        if not self.vectors_dir.exists():
            print(f"   ❌ 向量目录不存在: {self.vectors_dir}")
            return False
        print(f"   ✅ 向量目录存在: {self.vectors_dir}")
        
        if not self.criminal_dir.exists():
            print(f"   ❌ 原始数据目录不存在: {self.criminal_dir}")
            return False
        print(f"   ✅ 原始数据目录存在: {self.criminal_dir}")
        
        return True
    
    def _load_all_data(self) -> bool:
        """加载所有数据"""
        print("\n📥 加载数据文件...")
        
        try:
            # 加载向量数据
            articles_vectors_file = self.vectors_dir / "criminal_articles_vectors.pkl"
            cases_vectors_file = self.vectors_dir / "criminal_cases_vectors.pkl"
            
            if articles_vectors_file.exists():
                with open(articles_vectors_file, 'rb') as f:
                    self.vector_data['articles'] = pickle.load(f)
                print(f"   ✅ 加载法条向量数据: {self.vector_data['articles']['total_count']}条")
            else:
                print(f"   ❌ 法条向量文件不存在")
                return False
            
            if cases_vectors_file.exists():
                with open(cases_vectors_file, 'rb') as f:
                    self.vector_data['cases'] = pickle.load(f)
                print(f"   ✅ 加载案例向量数据: {self.vector_data['cases']['total_count']}条")
            else:
                print(f"   ❌ 案例向量文件不存在")
                return False
            
            # 加载原始数据
            articles_criminal_file = self.criminal_dir / "criminal_articles.pkl"
            cases_criminal_file = self.criminal_dir / "criminal_cases.pkl"
            
            if articles_criminal_file.exists():
                with open(articles_criminal_file, 'rb') as f:
                    self.criminal_data['articles'] = pickle.load(f)
                print(f"   ✅ 加载法条原始数据: {len(self.criminal_data['articles'])}条")
            else:
                print(f"   ❌ 法条原始数据文件不存在")
                return False
            
            if cases_criminal_file.exists():
                with open(cases_criminal_file, 'rb') as f:
                    self.criminal_data['cases'] = pickle.load(f)
                print(f"   ✅ 加载案例原始数据: {len(self.criminal_data['cases'])}条")
            else:
                print(f"   ❌ 案例原始数据文件不存在")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 数据加载失败: {e}")
            logger.exception("Failed to load data")
            return False
    
    def _check_file_consistency(self) -> Dict[str, Any]:
        """检查文件一致性"""
        print(f"\n🔗 检查文件一致性...")
        
        consistency = {'articles': {}, 'cases': {}}
        
        # 检查法条数据一致性
        articles_vector_count = self.vector_data['articles']['total_count']
        articles_criminal_count = len(self.criminal_data['articles'])
        
        print(f"   📊 法条数据:")
        print(f"      向量文件: {articles_vector_count}条")
        print(f"      原始文件: {articles_criminal_count}条")
        
        if articles_vector_count == articles_criminal_count:
            print(f"      ✅ 法条数量一致")
            consistency['articles']['count_match'] = True
        else:
            print(f"      ❌ 法条数量不一致")
            consistency['articles']['count_match'] = False
        
        consistency['articles']['vector_count'] = articles_vector_count
        consistency['articles']['criminal_count'] = articles_criminal_count
        
        # 检查案例数据一致性
        cases_vector_count = self.vector_data['cases']['total_count']
        cases_criminal_count = len(self.criminal_data['cases'])
        
        print(f"   📊 案例数据:")
        print(f"      向量文件: {cases_vector_count}条")
        print(f"      原始文件: {cases_criminal_count}条")
        
        if cases_vector_count == cases_criminal_count:
            print(f"      ✅ 案例数量一致")
            consistency['cases']['count_match'] = True
        else:
            print(f"      ❌ 案例数量不一致")
            consistency['cases']['count_match'] = False
        
        consistency['cases']['vector_count'] = cases_vector_count
        consistency['cases']['criminal_count'] = cases_criminal_count
        
        return consistency
    
    def _check_id_mapping(self) -> Dict[str, Any]:
        """检查ID映射关系"""
        print(f"\n🔑 检查ID映射关系...")
        
        mapping = {'articles': {}, 'cases': {}}
        
        # 检查法条ID映射
        vector_article_ids = set()
        criminal_article_ids = set()
        
        # 从向量元数据提取ID
        for meta in self.vector_data['articles']['metadata']:
            if 'id' in meta:
                vector_article_ids.add(meta['id'])
            elif 'article_number' in meta:
                vector_article_ids.add(f"article_{meta['article_number']}")
        
        # 从原始数据提取ID
        for article in self.criminal_data['articles']:
            if hasattr(article, 'article_number'):
                criminal_article_ids.add(f"article_{article.article_number}")
            elif hasattr(article, 'id'):
                criminal_article_ids.add(article.id)
            elif isinstance(article, dict):
                if 'article_number' in article:
                    criminal_article_ids.add(f"article_{article['article_number']}")
                elif 'id' in article:
                    criminal_article_ids.add(article['id'])
        
        print(f"   📊 法条ID对比:")
        print(f"      向量数据ID数量: {len(vector_article_ids)}")
        print(f"      原始数据ID数量: {len(criminal_article_ids)}")
        
        # 计算交集和差集
        common_article_ids = vector_article_ids & criminal_article_ids
        missing_in_vector = criminal_article_ids - vector_article_ids
        missing_in_criminal = vector_article_ids - criminal_article_ids
        
        print(f"      共同ID: {len(common_article_ids)}")
        if missing_in_vector:
            print(f"      ❌ 向量中缺失: {len(missing_in_vector)}个")
        if missing_in_criminal:
            print(f"      ❌ 原始数据中缺失: {len(missing_in_criminal)}个")
        
        if len(common_article_ids) == len(vector_article_ids) == len(criminal_article_ids):
            print(f"      ✅ 法条ID完全匹配")
            mapping['articles']['perfect_match'] = True
        else:
            print(f"      ❌ 法条ID不完全匹配")
            mapping['articles']['perfect_match'] = False
        
        mapping['articles']['common_ids'] = len(common_article_ids)
        mapping['articles']['missing_in_vector'] = len(missing_in_vector)
        mapping['articles']['missing_in_criminal'] = len(missing_in_criminal)
        mapping['articles']['missing_in_vector_list'] = list(missing_in_vector)[:10]  # 只保存前10个用于调试
        mapping['articles']['missing_in_criminal_list'] = list(missing_in_criminal)[:10]
        
        # 检查案例ID映射
        vector_case_ids = set()
        criminal_case_ids = set()
        
        # 从向量元数据提取ID
        for meta in self.vector_data['cases']['metadata']:
            if 'case_id' in meta:
                vector_case_ids.add(meta['case_id'])
            elif 'id' in meta:
                vector_case_ids.add(meta['id'])
        
        # 从原始数据提取ID
        for case in self.criminal_data['cases']:
            if hasattr(case, 'case_id'):
                criminal_case_ids.add(case.case_id)
            elif hasattr(case, 'id'):
                criminal_case_ids.add(case.id)
            elif isinstance(case, dict):
                if 'case_id' in case:
                    criminal_case_ids.add(case['case_id'])
                elif 'id' in case:
                    criminal_case_ids.add(case['id'])
        
        print(f"   📊 案例ID对比:")
        print(f"      向量数据ID数量: {len(vector_case_ids)}")
        print(f"      原始数据ID数量: {len(criminal_case_ids)}")
        
        # 计算交集和差集
        common_case_ids = vector_case_ids & criminal_case_ids
        missing_in_vector_cases = criminal_case_ids - vector_case_ids
        missing_in_criminal_cases = vector_case_ids - criminal_case_ids
        
        print(f"      共同ID: {len(common_case_ids)}")
        if missing_in_vector_cases:
            print(f"      ❌ 向量中缺失: {len(missing_in_vector_cases)}个")
        if missing_in_criminal_cases:
            print(f"      ❌ 原始数据中缺失: {len(missing_in_criminal_cases)}个")
        
        if len(common_case_ids) == len(vector_case_ids) == len(criminal_case_ids):
            print(f"      ✅ 案例ID完全匹配")
            mapping['cases']['perfect_match'] = True
        else:
            print(f"      ❌ 案例ID不完全匹配")
            mapping['cases']['perfect_match'] = False
        
        mapping['cases']['common_ids'] = len(common_case_ids)
        mapping['cases']['missing_in_vector'] = len(missing_in_vector_cases)
        mapping['cases']['missing_in_criminal'] = len(missing_in_criminal_cases)
        mapping['cases']['missing_in_vector_list'] = list(missing_in_vector_cases)[:10]
        mapping['cases']['missing_in_criminal_list'] = list(missing_in_criminal_cases)[:10]
        
        return mapping
    
    def _check_content_integrity(self) -> Dict[str, Any]:
        """检查内容完整性"""
        print(f"\n📝 检查内容完整性...")
        
        integrity = {'articles': {}, 'cases': {}}
        
        # 检查法条内容完整性
        print(f"   📊 法条内容检查:")
        
        empty_content_articles = 0
        total_articles = len(self.criminal_data['articles'])
        
        for article in self.criminal_data['articles']:
            content = None
            if hasattr(article, 'content'):
                content = article.content
            elif hasattr(article, 'full_text'):
                content = article.full_text
            elif isinstance(article, dict):
                content = article.get('content') or article.get('full_text')
            
            if not content or content.strip() == "":
                empty_content_articles += 1
        
        if empty_content_articles == 0:
            print(f"      ✅ 所有法条都有内容")
            integrity['articles']['all_have_content'] = True
        else:
            print(f"      ❌ {empty_content_articles}/{total_articles}法条内容为空")
            integrity['articles']['all_have_content'] = False
        
        integrity['articles']['empty_content_count'] = empty_content_articles
        integrity['articles']['total_count'] = total_articles
        
        # 检查案例内容完整性
        print(f"   📊 案例内容检查:")
        
        empty_content_cases = 0
        total_cases = len(self.criminal_data['cases'])
        
        for case in self.criminal_data['cases']:
            content = None
            if hasattr(case, 'fact'):
                content = case.fact
            elif hasattr(case, 'content'):
                content = case.content
            elif isinstance(case, dict):
                content = case.get('fact') or case.get('content')
            
            if not content or content.strip() == "":
                empty_content_cases += 1
        
        if empty_content_cases == 0:
            print(f"      ✅ 所有案例都有内容")
            integrity['cases']['all_have_content'] = True
        else:
            print(f"      ❌ {empty_content_cases}/{total_cases}案例内容为空")
            integrity['cases']['all_have_content'] = False
        
        integrity['cases']['empty_content_count'] = empty_content_cases
        integrity['cases']['total_count'] = total_cases
        
        return integrity
    
    def _check_vector_quality(self) -> Dict[str, Any]:
        """检查向量质量"""
        print(f"\n🧮 检查向量质量...")
        
        quality = {'articles': {}, 'cases': {}}
        
        # 检查法条向量质量
        print(f"   📊 法条向量质量:")
        articles_vectors = self.vector_data['articles']['vectors']
        
        quality['articles'] = self._analyze_vector_quality(articles_vectors, "法条")
        
        # 检查案例向量质量
        print(f"   📊 案例向量质量:")
        cases_vectors = self.vector_data['cases']['vectors']
        
        quality['cases'] = self._analyze_vector_quality(cases_vectors, "案例")
        
        # 检查向量间相似度分布
        print(f"   🔍 向量相似度分析:")
        quality['similarity_analysis'] = self._analyze_vector_similarities()
        
        return quality
    
    def _analyze_vector_quality(self, vectors: np.ndarray, data_type: str) -> Dict[str, Any]:
        """分析向量质量"""
        analysis = {}
        
        # 基本统计
        analysis['shape'] = vectors.shape
        analysis['mean'] = float(np.mean(vectors))
        analysis['std'] = float(np.std(vectors))
        analysis['min'] = float(np.min(vectors))
        analysis['max'] = float(np.max(vectors))
        
        print(f"      📐 {data_type}向量形状: {vectors.shape}")
        print(f"      📊 均值: {analysis['mean']:.4f}, 标准差: {analysis['std']:.4f}")
        
        # 检查异常值
        zero_vectors = np.all(vectors == 0, axis=1).sum()
        analysis['zero_vectors'] = int(zero_vectors)
        
        if zero_vectors > 0:
            print(f"      ⚠️ 发现{zero_vectors}个零向量")
        else:
            print(f"      ✅ 无零向量")
        
        # 计算向量范数分布
        norms = np.linalg.norm(vectors, axis=1)
        analysis['norm_stats'] = {
            'mean': float(np.mean(norms)),
            'std': float(np.std(norms)),
            'min': float(np.min(norms)),
            'max': float(np.max(norms))
        }
        
        print(f"      📏 向量范数: 均值={analysis['norm_stats']['mean']:.4f}, "
              f"标准差={analysis['norm_stats']['std']:.4f}")
        
        # 检查向量是否归一化
        normalized_check = np.allclose(norms, 1.0, atol=1e-6)
        analysis['is_normalized'] = normalized_check
        
        if normalized_check:
            print(f"      ✅ 向量已归一化")
        else:
            print(f"      ⚠️ 向量未归一化")
        
        return analysis
    
    def _analyze_vector_similarities(self) -> Dict[str, Any]:
        """分析向量相似度"""
        analysis = {}
        
        try:
            # 计算法条向量内部相似度（随机采样以节省计算）
            articles_vectors = self.vector_data['articles']['vectors']
            if len(articles_vectors) > 50:
                # 随机采样50个向量进行相似度计算
                import random
                indices = random.sample(range(len(articles_vectors)), 50)
                sample_vectors = articles_vectors[indices]
            else:
                sample_vectors = articles_vectors
            
            similarities = cosine_similarity(sample_vectors)
            
            # 获取上三角矩阵（排除对角线）
            upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
            
            analysis['articles_internal'] = {
                'mean_similarity': float(np.mean(upper_triangle)),
                'std_similarity': float(np.std(upper_triangle)),
                'min_similarity': float(np.min(upper_triangle)),
                'max_similarity': float(np.max(upper_triangle)),
                'sample_size': len(sample_vectors)
            }
            
            print(f"      📊 法条内部相似度 (样本{len(sample_vectors)}个):")
            print(f"         均值: {analysis['articles_internal']['mean_similarity']:.4f}")
            print(f"         范围: [{analysis['articles_internal']['min_similarity']:.4f}, "
                  f"{analysis['articles_internal']['max_similarity']:.4f}]")
            
            # 简单的法条-案例交叉相似度检查（小样本）
            if len(articles_vectors) > 0 and len(self.vector_data['cases']['vectors']) > 0:
                # 取前10个法条和前10个案例
                articles_sample = articles_vectors[:min(10, len(articles_vectors))]
                cases_sample = self.vector_data['cases']['vectors'][:min(10, len(self.vector_data['cases']['vectors']))]
                
                cross_similarities = cosine_similarity(articles_sample, cases_sample)
                
                analysis['cross_similarity'] = {
                    'mean_similarity': float(np.mean(cross_similarities)),
                    'std_similarity': float(np.std(cross_similarities)),
                    'min_similarity': float(np.min(cross_similarities)),
                    'max_similarity': float(np.max(cross_similarities))
                }
                
                print(f"      📊 法条-案例交叉相似度 (10x10样本):")
                print(f"         均值: {analysis['cross_similarity']['mean_similarity']:.4f}")
                print(f"         范围: [{analysis['cross_similarity']['min_similarity']:.4f}, "
                      f"{analysis['cross_similarity']['max_similarity']:.4f}]")
            
        except Exception as e:
            print(f"      ❌ 相似度分析失败: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成总结报告"""
        print(f"\n" + "=" * 60)
        print("📋 数据完整性验证总结")
        print("=" * 60)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 评估关键问题
        file_consistency = self.results.get('file_consistency', {})
        id_mapping = self.results.get('id_mapping', {})
        content_integrity = self.results.get('content_integrity', {})
        
        critical_issues = []
        warnings = []
        
        # 检查文件一致性问题
        if not file_consistency.get('articles', {}).get('count_match', True):
            critical_issues.append("法条向量和原始数据数量不一致")
        
        if not file_consistency.get('cases', {}).get('count_match', True):
            critical_issues.append("案例向量和原始数据数量不一致")
        
        # 检查ID映射问题
        if not id_mapping.get('articles', {}).get('perfect_match', True):
            critical_issues.append("法条ID映射不完整")
        
        if not id_mapping.get('cases', {}).get('perfect_match', True):
            critical_issues.append("案例ID映射不完整")
        
        # 检查内容完整性问题
        if not content_integrity.get('articles', {}).get('all_have_content', True):
            warnings.append(f"部分法条内容为空 ({content_integrity.get('articles', {}).get('empty_content_count', 0)}个)")
        
        if not content_integrity.get('cases', {}).get('all_have_content', True):
            warnings.append(f"部分案例内容为空 ({content_integrity.get('cases', {}).get('empty_content_count', 0)}个)")
        
        # 检查向量质量问题
        vector_quality = self.results.get('vector_quality', {})
        
        if vector_quality.get('articles', {}).get('zero_vectors', 0) > 0:
            warnings.append(f"法条数据包含零向量 ({vector_quality['articles']['zero_vectors']}个)")
        
        if vector_quality.get('cases', {}).get('zero_vectors', 0) > 0:
            warnings.append(f"案例数据包含零向量 ({vector_quality['cases']['zero_vectors']}个)")
        
        summary['critical_issues'] = critical_issues
        summary['warnings'] = warnings
        
        # 确定总体状态
        if critical_issues:
            summary['overall_status'] = 'critical'
            print("🚨 发现关键问题，需要立即修复")
        elif warnings:
            summary['overall_status'] = 'warning'
            print("⚠️ 发现一些警告，建议优化")
        else:
            summary['overall_status'] = 'healthy'
            print("✅ 数据完整性良好")
        
        # 显示问题详情
        if critical_issues:
            print(f"\n🚨 关键问题:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        if warnings:
            print(f"\n⚠️ 警告:")
            for warning in warnings:
                print(f"   - {warning}")
        
        # 生成建议
        recommendations = []
        
        if critical_issues:
            if any("数量不一致" in issue for issue in critical_issues):
                recommendations.append("重新生成向量数据，确保与原始数据数量匹配")
            
            if any("ID映射" in issue for issue in critical_issues):
                recommendations.append("检查ID生成逻辑，确保向量和原始数据ID对应")
        
        if warnings:
            if any("内容为空" in warning for warning in warnings):
                recommendations.append("检查数据预处理过程，确保所有文档都有有效内容")
            
            if any("零向量" in warning for warning in warnings):
                recommendations.append("检查向量生成过程，重新处理导致零向量的文档")
        
        if not critical_issues and not warnings:
            recommendations.append("数据状态良好，可以正常使用")
        
        summary['recommendations'] = recommendations
        
        if recommendations:
            print(f"\n💡 建议:")
            for rec in recommendations:
                print(f"   - {rec}")
        
        return summary


def main():
    """主函数"""
    try:
        checker = DataIntegrityChecker()
        results = checker.check_all_integrity()
        
        # 保存结果到文件（可选）
        output_file = project_root / "tools" / "data_validation" / f"integrity_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n📄 详细报告已保存至: {output_file}")
        except Exception as e:
            print(f"\n⚠️ 保存报告失败: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ 完整性检查过程出错: {e}")
        logger.exception("Data integrity checking failed")
        return {'error': str(e)}


if __name__ == "__main__":
    main()