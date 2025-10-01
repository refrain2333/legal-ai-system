#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的向量格式检查工具
专门用于快速验证向量数据格式，避免复杂依赖

使用方法:
python tools/data_validation/simple_vector_checker.py
"""

import sys
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_vector_file(file_path: Path, file_type: str) -> Dict[str, Any]:
    """检查单个向量文件"""
    print(f"\n[检查] {file_type}: {file_path.name}")
    
    if not file_path.exists():
        print(f"   [错误] 文件不存在")
        return {'status': 'error', 'error': 'file_not_found'}
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"   [信息] 文件大小: {file_size_mb:.2f} MB")
    
    try:
        # 加载数据
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        result = {'status': 'success', 'file_size_mb': file_size_mb}
        
        # 检查基本结构
        if not isinstance(data, dict):
            print(f"   [错误] 数据不是字典格式")
            return {'status': 'error', 'error': 'not_dict_format'}
        
        print(f"   [成功] 数据为字典格式")
        
        # 检查必需字段
        required_fields = ['vectors', 'metadata', 'total_count']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"   [错误] 缺少必需字段: {missing_fields}")
            result['missing_fields'] = missing_fields
        else:
            print(f"   [成功] 包含所有必需字段")
        
        # 检查向量数据
        if 'vectors' in data:
            vectors = data['vectors']
            if isinstance(vectors, np.ndarray):
                print(f"   [成功] 向量为numpy数组")
                print(f"   [信息] 向量形状: {vectors.shape}")
                print(f"   [信息] 数据类型: {vectors.dtype}")
                
                # 检查维度
                if len(vectors.shape) == 2 and vectors.shape[1] == 768:
                    print(f"   [成功] 向量维度正确: 768维")
                else:
                    print(f"   [错误] 向量维度错误")
                
                # 检查异常值
                nan_count = np.isnan(vectors).sum()
                inf_count = np.isinf(vectors).sum()
                zero_vectors = np.all(vectors == 0, axis=1).sum()
                
                if nan_count == 0:
                    print(f"   [成功] 无NaN值")
                else:
                    print(f"   [错误] 发现{nan_count}个NaN值")
                
                if inf_count == 0:
                    print(f"   [成功] 无Inf值")
                else:
                    print(f"   [错误] 发现{inf_count}个Inf值")
                
                if zero_vectors == 0:
                    print(f"   [成功] 无零向量")
                else:
                    print(f"   [警告] 发现{zero_vectors}个零向量")
                
                result.update({
                    'vector_shape': vectors.shape,
                    'vector_dtype': str(vectors.dtype),
                    'nan_count': int(nan_count),
                    'inf_count': int(inf_count),
                    'zero_vectors': int(zero_vectors)
                })
            else:
                print(f"   [错误] 向量不是numpy数组")
                result['vector_error'] = 'not_numpy_array'
        
        # 检查元数据
        if 'metadata' in data:
            metadata = data['metadata']
            if isinstance(metadata, list):
                print(f"   [成功] 元数据为列表格式")
                print(f"   [信息] 元数据条目数量: {len(metadata)}")
                result['metadata_count'] = len(metadata)
            else:
                print(f"   [错误] 元数据不是列表格式")
                result['metadata_error'] = 'not_list_format'
        
        # 检查计数一致性
        if 'total_count' in data and 'vectors' in data and 'metadata' in data:
            total_count = data['total_count']
            vector_count = len(data['vectors']) if isinstance(data['vectors'], np.ndarray) else 0
            metadata_count = len(data['metadata']) if isinstance(data['metadata'], list) else 0
            
            print(f"   [信息] 数量统计:")
            print(f"      total_count: {total_count}")
            print(f"      向量数量: {vector_count}")
            print(f"      元数据数量: {metadata_count}")
            
            if total_count == vector_count == metadata_count:
                print(f"   [成功] 计数一致")
                result['count_consistent'] = True
            else:
                print(f"   [错误] 计数不一致")
                result['count_consistent'] = False
        
        return result
        
    except Exception as e:
        print(f"   [错误] 加载文件失败: {e}")
        return {'status': 'error', 'error': str(e)}

def main():
    """主函数"""
    print("=" * 60)
    print("简化向量格式验证工具")
    print("=" * 60)
    
    data_root = project_root / "data" / "processed"
    vectors_dir = data_root / "vectors"
    
    if not vectors_dir.exists():
        print(f"[错误] 向量目录不存在: {vectors_dir}")
        return
    
    # 检查法条向量
    articles_file = vectors_dir / "criminal_articles_vectors.pkl"
    articles_result = check_vector_file(articles_file, "法条向量")
    
    # 检查案例向量  
    cases_file = vectors_dir / "criminal_cases_vectors.pkl"
    cases_result = check_vector_file(cases_file, "案例向量")
    
    # 生成总结
    print(f"\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    # 检查结果
    issues = []
    
    for result, name in [(articles_result, "法条向量"), (cases_result, "案例向量")]:
        if result.get('status') == 'error':
            issues.append(f"{name}文件检查失败")
        else:
            if result.get('missing_fields'):
                issues.append(f"{name}缺少必需字段")
            if result.get('vector_error'):
                issues.append(f"{name}向量格式错误")
            if result.get('nan_count', 0) > 0:
                issues.append(f"{name}包含NaN值")
            if result.get('inf_count', 0) > 0:
                issues.append(f"{name}包含Inf值")
            if not result.get('count_consistent', True):
                issues.append(f"{name}数据计数不一致")
    
    if not issues:
        print("[成功] 所有检查通过，向量数据格式正确！")
        print("[建议] 数据可以正常使用")
    else:
        print(f"[问题] 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"   - {issue}")
        
        print(f"\n[建议]:")
        if any("文件检查失败" in issue for issue in issues):
            print("   - 检查数据文件是否存在和可读")
        if any("缺少必需字段" in issue for issue in issues):
            print("   - 重新生成向量文件，确保包含所有必需字段")
        if any("NaN值" in issue or "Inf值" in issue for issue in issues):
            print("   - 检查向量生成过程，确保数值计算正确")
        if any("数据计数不一致" in issue for issue in issues):
            print("   - 重新生成向量文件，确保数据同步")
    
    # 保存简单报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = project_root / "tools" / "data_validation" / f"simple_check_report_{timestamp}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("简化向量格式验证报告\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("法条向量检查结果:\n")
            f.write("-" * 20 + "\n")
            f.write(f"状态: {articles_result.get('status', 'unknown')}\n")
            if 'file_size_mb' in articles_result:
                f.write(f"文件大小: {articles_result['file_size_mb']:.2f} MB\n")
            if 'vector_shape' in articles_result:
                f.write(f"向量形状: {articles_result['vector_shape']}\n")
            f.write("\n")
            
            f.write("案例向量检查结果:\n")
            f.write("-" * 20 + "\n")
            f.write(f"状态: {cases_result.get('status', 'unknown')}\n")
            if 'file_size_mb' in cases_result:
                f.write(f"文件大小: {cases_result['file_size_mb']:.2f} MB\n")
            if 'vector_shape' in cases_result:
                f.write(f"向量形状: {cases_result['vector_shape']}\n")
            f.write("\n")
            
            if issues:
                f.write("发现的问题:\n")
                f.write("-" * 20 + "\n")
                for issue in issues:
                    f.write(f"- {issue}\n")
            else:
                f.write("验证结果: 所有检查通过\n")
        
        print(f"\n[报告] 报告已保存: {report_file}")
        
    except Exception as e:
        print(f"\n[警告] 保存报告失败: {e}")

if __name__ == "__main__":
    main()