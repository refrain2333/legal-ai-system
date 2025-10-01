#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量格式检查工具
验证向量数据文件的格式和完整性

使用方法:
python tools/data_validation/vector_format_checker.py
"""

import sys
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorFormatChecker:
    """向量格式检查器"""
    
    def __init__(self, data_root: Optional[Path] = None):
        """初始化检查器"""
        self.data_root = data_root or project_root / "data" / "processed"
        self.vectors_dir = self.data_root / "vectors"
        self.criminal_dir = self.data_root / "criminal"
        
        # 预期配置
        self.expected_vector_dim = 768  # Lawformer向量维度
        self.expected_vector_dtype = np.float32
        self.required_vector_fields = ['vectors', 'metadata', 'total_count']
        
        # 检查结果
        self.results = {}
        
    def check_all_vectors(self) -> Dict[str, Any]:
        """检查所有向量文件"""
        print("=" * 60)
        print("🔍 向量格式验证工具 - 开始检查")
        print("=" * 60)
        
        # 检查向量目录
        if not self.vectors_dir.exists():
            error_msg = f"向量数据目录不存在: {self.vectors_dir}"
            print(f"❌ {error_msg}")
            return {'error': error_msg}
        
        # 检查法条向量
        articles_file = self.vectors_dir / "criminal_articles_vectors.pkl"
        self.results['articles'] = self._check_vector_file(articles_file, "法条向量")
        
        # 检查案例向量
        cases_file = self.vectors_dir / "criminal_cases_vectors.pkl"
        self.results['cases'] = self._check_vector_file(cases_file, "案例向量")
        
        # 生成总结报告
        self.results['summary'] = self._generate_summary()
        
        return self.results
    
    def _check_vector_file(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """检查单个向量文件"""
        print(f"\n📁 检查{file_type}文件: {file_path.name}")
        
        if not file_path.exists():
            print(f"   ❌ 文件不存在")
            return {'status': 'error', 'error': 'file_not_found'}
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"   📊 文件大小: {file_size_mb:.2f} MB")
        
        try:
            # 加载数据
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            result = {
                'status': 'success',
                'file_size_mb': file_size_mb,
                'checks': {}
            }
            
            # 检查基本结构
            result['checks']['structure'] = self._check_data_structure(data, file_type)
            
            # 检查向量数据
            if 'vectors' in data:
                result['checks']['vectors'] = self._check_vector_data(data['vectors'], file_type)
            
            # 检查元数据
            if 'metadata' in data:
                result['checks']['metadata'] = self._check_metadata(data['metadata'], file_type)
            
            # 检查计数一致性
            result['checks']['count_consistency'] = self._check_count_consistency(data, file_type)
            
            return result
            
        except Exception as e:
            error_msg = f"加载文件失败: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {'status': 'error', 'error': error_msg}
    
    def _check_data_structure(self, data: Any, file_type: str) -> Dict[str, Any]:
        """检查数据结构"""
        print(f"   🔧 检查数据结构...")
        
        checks = {}
        
        # 检查是否为字典
        if not isinstance(data, dict):
            print(f"      ❌ 数据不是字典格式")
            checks['is_dict'] = False
            return checks
        
        checks['is_dict'] = True
        print(f"      ✅ 数据为字典格式")
        
        # 检查必需字段
        missing_fields = []
        for field in self.required_vector_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            checks['required_fields'] = False
            print(f"      ❌ 缺少必需字段: {missing_fields}")
        else:
            checks['required_fields'] = True
            print(f"      ✅ 包含所有必需字段: {self.required_vector_fields}")
        
        # 显示实际字段
        actual_fields = list(data.keys())
        print(f"      📋 实际字段: {actual_fields}")
        checks['actual_fields'] = actual_fields
        
        return checks
    
    def _check_vector_data(self, vectors: Any, file_type: str) -> Dict[str, Any]:
        """检查向量数据"""
        print(f"   🧮 检查向量数据...")
        
        checks = {}
        
        # 检查向量类型
        if not isinstance(vectors, np.ndarray):
            print(f"      ❌ 向量不是numpy数组")
            checks['is_numpy_array'] = False
            return checks
        
        checks['is_numpy_array'] = True
        print(f"      ✅ 向量为numpy数组")
        
        # 检查向量形状
        shape = vectors.shape
        print(f"      📐 向量形状: {shape}")
        checks['shape'] = shape
        
        if len(shape) != 2:
            print(f"      ❌ 向量应为2D数组")
            checks['is_2d'] = False
        else:
            checks['is_2d'] = True
            print(f"      ✅ 向量为2D数组")
        
        # 检查向量维度
        if len(shape) >= 2:
            actual_dim = shape[1]
            if actual_dim != self.expected_vector_dim:
                print(f"      ❌ 向量维度错误: 实际{actual_dim}, 预期{self.expected_vector_dim}")
                checks['correct_dimension'] = False
            else:
                print(f"      ✅ 向量维度正确: {actual_dim}")
                checks['correct_dimension'] = True
        
        # 检查数据类型
        actual_dtype = vectors.dtype
        print(f"      🔢 数据类型: {actual_dtype}")
        checks['dtype'] = str(actual_dtype)
        
        if actual_dtype != self.expected_vector_dtype:
            print(f"      ⚠️ 数据类型非预期: 实际{actual_dtype}, 推荐{self.expected_vector_dtype}")
            checks['expected_dtype'] = False
        else:
            print(f"      ✅ 数据类型正确")
            checks['expected_dtype'] = True
        
        # 检查向量有效性
        checks['validity'] = self._check_vector_validity(vectors)
        
        return checks
    
    def _check_vector_validity(self, vectors: np.ndarray) -> Dict[str, Any]:
        """检查向量有效性"""
        print(f"      🔍 检查向量有效性...")
        
        validity = {}
        
        # 检查NaN值
        nan_count = np.isnan(vectors).sum()
        if nan_count > 0:
            print(f"         ❌ 发现{nan_count}个NaN值")
            validity['has_nan'] = True
            validity['nan_count'] = int(nan_count)
        else:
            print(f"         ✅ 无NaN值")
            validity['has_nan'] = False
        
        # 检查Inf值
        inf_count = np.isinf(vectors).sum()
        if inf_count > 0:
            print(f"         ❌ 发现{inf_count}个Inf值")
            validity['has_inf'] = True
            validity['inf_count'] = int(inf_count)
        else:
            print(f"         ✅ 无Inf值")
            validity['has_inf'] = False
        
        # 检查零向量
        zero_vectors = np.all(vectors == 0, axis=1)
        zero_count = zero_vectors.sum()
        if zero_count > 0:
            print(f"         ⚠️ 发现{zero_count}个零向量")
            validity['has_zero_vectors'] = True
            validity['zero_count'] = int(zero_count)
        else:
            print(f"         ✅ 无零向量")
            validity['has_zero_vectors'] = False
        
        # 计算基本统计信息
        validity['stats'] = {
            'mean': float(np.mean(vectors)),
            'std': float(np.std(vectors)),
            'min': float(np.min(vectors)),
            'max': float(np.max(vectors))
        }
        
        print(f"         📊 统计: 均值={validity['stats']['mean']:.4f}, "
              f"标准差={validity['stats']['std']:.4f}")
        
        return validity
    
    def _check_metadata(self, metadata: Any, file_type: str) -> Dict[str, Any]:
        """检查元数据"""
        print(f"   📋 检查元数据...")
        
        checks = {}
        
        # 检查元数据类型
        if not isinstance(metadata, list):
            print(f"      ❌ 元数据不是列表格式")
            checks['is_list'] = False
            return checks
        
        checks['is_list'] = True
        print(f"      ✅ 元数据为列表格式")
        
        # 检查元数据数量
        meta_count = len(metadata)
        print(f"      📊 元数据条目数量: {meta_count}")
        checks['count'] = meta_count
        
        if meta_count == 0:
            print(f"      ⚠️ 元数据为空")
            checks['is_empty'] = True
            return checks
        
        checks['is_empty'] = False
        
        # 检查元数据字段
        if metadata:
            sample_meta = metadata[0]
            if isinstance(sample_meta, dict):
                fields = list(sample_meta.keys())
                print(f"      📋 元数据字段: {fields}")
                checks['fields'] = fields
                
                # 根据文件类型检查预期字段
                if file_type == "法条向量":
                    expected_fields = ['id', 'article_number', 'title']
                    checks['expected_fields_present'] = all(field in fields for field in expected_fields)
                elif file_type == "案例向量":
                    expected_fields = ['id', 'case_id', 'accusations']
                    checks['expected_fields_present'] = all(field in fields for field in expected_fields)
            else:
                print(f"      ❌ 元数据项不是字典格式")
                checks['items_are_dicts'] = False
        
        return checks
    
    def _check_count_consistency(self, data: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """检查计数一致性"""
        print(f"   🔢 检查计数一致性...")
        
        checks = {}
        
        total_count = data.get('total_count', 0)
        vector_count = len(data.get('vectors', []))
        metadata_count = len(data.get('metadata', []))
        
        print(f"      📊 total_count: {total_count}")
        print(f"      📊 向量数量: {vector_count}")
        print(f"      📊 元数据数量: {metadata_count}")
        
        # 检查一致性
        counts_consistent = (total_count == vector_count == metadata_count)
        
        if counts_consistent:
            print(f"      ✅ 计数一致")
            checks['consistent'] = True
        else:
            print(f"      ❌ 计数不一致")
            checks['consistent'] = False
        
        checks['total_count'] = total_count
        checks['vector_count'] = vector_count
        checks['metadata_count'] = metadata_count
        
        return checks
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成总结报告"""
        print(f"\n" + "=" * 60)
        print("📋 验证总结报告")
        print("=" * 60)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files_checked': 0,
            'successful_files': 0,
            'failed_files': 0,
            'issues_found': [],
            'recommendations': []
        }
        
        for file_type, result in self.results.items():
            if file_type == 'summary':
                continue
            
            summary['total_files_checked'] += 1
            
            if result.get('status') == 'success':
                summary['successful_files'] += 1
                print(f"✅ {file_type}向量文件: 检查通过")
                
                # 检查详细问题
                issues = self._extract_issues(result, file_type)
                summary['issues_found'].extend(issues)
                
            else:
                summary['failed_files'] += 1
                print(f"❌ {file_type}向量文件: 检查失败 - {result.get('error', '未知错误')}")
                summary['issues_found'].append(f"{file_type}向量文件加载失败")
        
        # 生成建议
        summary['recommendations'] = self._generate_recommendations(summary['issues_found'])
        
        print(f"\n📊 检查结果:")
        print(f"   - 总文件数: {summary['total_files_checked']}")
        print(f"   - 成功: {summary['successful_files']}")
        print(f"   - 失败: {summary['failed_files']}")
        
        if summary['issues_found']:
            print(f"\n⚠️ 发现的问题:")
            for issue in summary['issues_found']:
                print(f"   - {issue}")
        
        if summary['recommendations']:
            print(f"\n💡 建议:")
            for rec in summary['recommendations']:
                print(f"   - {rec}")
        
        if not summary['issues_found']:
            print(f"\n🎉 所有向量数据格式正确，可以正常使用！")
        
        return summary
    
    def _extract_issues(self, result: Dict[str, Any], file_type: str) -> List[str]:
        """提取检查中发现的问题"""
        issues = []
        checks = result.get('checks', {})
        
        # 结构问题
        if not checks.get('structure', {}).get('required_fields', True):
            issues.append(f"{file_type}缺少必需字段")
        
        # 向量问题
        vector_checks = checks.get('vectors', {})
        if not vector_checks.get('is_2d', True):
            issues.append(f"{file_type}向量不是2D数组")
        
        if not vector_checks.get('correct_dimension', True):
            issues.append(f"{file_type}向量维度不正确")
        
        if not vector_checks.get('expected_dtype', True):
            issues.append(f"{file_type}向量数据类型非推荐类型")
        
        validity = vector_checks.get('validity', {})
        if validity.get('has_nan', False):
            issues.append(f"{file_type}向量包含NaN值")
        
        if validity.get('has_inf', False):
            issues.append(f"{file_type}向量包含Inf值")
        
        if validity.get('has_zero_vectors', False):
            issues.append(f"{file_type}包含零向量")
        
        # 计数问题
        if not checks.get('count_consistency', {}).get('consistent', True):
            issues.append(f"{file_type}数据计数不一致")
        
        return issues
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """根据问题生成建议"""
        recommendations = []
        
        if any("缺少必需字段" in issue for issue in issues):
            recommendations.append("重新生成向量文件，确保包含所有必需字段")
        
        if any("向量维度不正确" in issue for issue in issues):
            recommendations.append("检查Lawformer模型配置，确保输出768维向量")
        
        if any("NaN值" in issue or "Inf值" in issue for issue in issues):
            recommendations.append("检查向量生成过程，确保数值计算正确")
        
        if any("零向量" in issue for issue in issues):
            recommendations.append("检查输入文本质量，确保所有文档都有有意义的内容")
        
        if any("数据计数不一致" in issue for issue in issues):
            recommendations.append("重新生成向量文件，确保向量、元数据和计数字段同步")
        
        return recommendations


def main():
    """主函数"""
    try:
        checker = VectorFormatChecker()
        results = checker.check_all_vectors()
        
        # 保存结果到文件（可选）
        output_file = project_root / "tools" / "data_validation" / f"vector_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n📄 详细报告已保存至: {output_file}")
        except Exception as e:
            print(f"\n⚠️ 保存报告失败: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        logger.exception("Vector format checking failed")
        return {'error': str(e)}


if __name__ == "__main__":
    main()