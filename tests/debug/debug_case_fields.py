#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试案例数据字段映射问题
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_case_fields():
    print("=== 调试案例字段映射问题 ===")
    
    from src.infrastructure.storage.data_loader import get_data_loader
    
    loader = get_data_loader()
    
    # 确保数据已加载
    if not loader.vectors_loaded:
        loader.load_vectors()
    
    # 加载原始数据
    loader._load_original_data_type('cases')
    
    if 'cases' in loader.original_data:
        cases = loader.original_data['cases']
        print(f"找到 {len(cases)} 个案例")
        
        # 找到目标案例 case_008466
        target_case = None
        for case in cases:
            case_id = getattr(case, 'case_id', None)
            if case_id == 'case_008466':
                target_case = case
                break
        
        if target_case:
            print(f"\n找到目标案例: case_008466")
            print(f"案例对象类型: {type(target_case)}")
            print(f"案例所有属性: {dir(target_case)}")
            
            # 检查关键字段
            print(f"\n--- 关键字段检查 ---")
            print(f"case_id: {getattr(target_case, 'case_id', 'N/A')}")
            print(f"criminals: {getattr(target_case, 'criminals', 'N/A')}")
            print(f"accusations: {getattr(target_case, 'accusations', 'N/A')}")
            print(f"relevant_articles: {getattr(target_case, 'relevant_articles', 'N/A')}")
            print(f"fact: {getattr(target_case, 'fact', 'N/A')[:100] if getattr(target_case, 'fact', None) else 'N/A'}...")
            
            # 检查是否有meta字段
            if hasattr(target_case, 'meta'):
                meta = getattr(target_case, 'meta')
                print(f"\n--- Meta字段检查 ---")
                print(f"meta类型: {type(meta)}")
                if hasattr(meta, '__dict__'):
                    print(f"meta属性: {dir(meta)}")
                elif isinstance(meta, dict):
                    print(f"meta字典键: {list(meta.keys())}")
                    for key, value in meta.items():
                        print(f"  {key}: {value}")
            
            # 检查sentence_info字段
            if hasattr(target_case, 'sentence_info'):
                sentence_info = getattr(target_case, 'sentence_info')
                print(f"\n--- Sentence_info字段检查 ---")
                print(f"sentence_info类型: {type(sentence_info)}")
                if isinstance(sentence_info, dict):
                    print(f"sentence_info内容: {sentence_info}")
                elif hasattr(sentence_info, '__dict__'):
                    print(f"sentence_info属性: {dir(sentence_info)}")
            
        else:
            print(f"未找到目标案例 case_008466")
            # 显示前几个案例的case_id
            print(f"前5个案例的case_id:")
            for i, case in enumerate(cases[:5]):
                case_id = getattr(case, 'case_id', 'N/A')
                print(f"  {i}: {case_id}")
    else:
        print("未加载到cases数据")

if __name__ == "__main__":
    debug_case_fields()