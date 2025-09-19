#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试向量元数据vs原始数据字段映射
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_metadata_vs_original():
    print("=== 调试向量元数据 vs 原始数据字段映射 ===")
    
    from src.infrastructure.storage.data_loader import get_data_loader
    
    loader = get_data_loader()
    
    # 确保数据已加载
    if not loader.vectors_loaded:
        loader.load_vectors()
    
    # 获取向量元数据
    cases_metadata = loader.get_metadata('cases')
    print(f"找到 {len(cases_metadata) if cases_metadata else 0} 个案例向量元数据")
    
    if cases_metadata:
        # 查看第一个案例的元数据结构
        first_meta = cases_metadata[0]
        print(f"\n向量元数据示例 (第1个):")
        print(f"元数据键: {list(first_meta.keys())}")
        print(f"case_id: {first_meta.get('case_id')}")
        print(f"accusations: {first_meta.get('accusations')}")
        print(f"criminals: {first_meta.get('criminals')}")
        print(f"punish_of_money: {first_meta.get('punish_of_money')}")
        print(f"sentence_months: {first_meta.get('sentence_months')}")
        print(f"fine_amount: {first_meta.get('fine_amount')}")
        
        # 找到特定案例的元数据
        target_meta = None
        for meta in cases_metadata:
            if meta.get('case_id') == 'case_008466':
                target_meta = meta
                break
        
        if target_meta:
            print(f"\n目标案例 case_008466 的向量元数据:")
            for key, value in target_meta.items():
                print(f"  {key}: {value}")
        
        # 加载原始数据并比较
        loader._load_original_data_type('cases')
        
        if 'cases' in loader.original_data:
            cases = loader.original_data['cases']
            target_case = None
            for case in cases:
                case_id = getattr(case, 'case_id', None)
                if case_id == 'case_008466':
                    target_case = case
                    break
            
            if target_case:
                print(f"\n目标案例 case_008466 的原始数据:")
                print(f"  case_id: {getattr(target_case, 'case_id', 'N/A')}")
                print(f"  criminals: {getattr(target_case, 'criminals', 'N/A')}")
                print(f"  accusations: {getattr(target_case, 'accusations', 'N/A')}")
                print(f"  sentence_info: {getattr(target_case, 'sentence_info', 'N/A')}")
                
                # 如果有sentence_info，展开它
                sentence_info = getattr(target_case, 'sentence_info', {})
                if sentence_info:
                    print(f"  sentence_info.imprisonment_months: {sentence_info.get('imprisonment_months')}")
                    print(f"  sentence_info.fine_amount: {sentence_info.get('fine_amount')}")
                    print(f"  sentence_info.death_penalty: {sentence_info.get('death_penalty')}")
                    print(f"  sentence_info.life_imprisonment: {sentence_info.get('life_imprisonment')}")

if __name__ == "__main__":
    debug_metadata_vs_original()