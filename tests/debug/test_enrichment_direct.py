#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试enrichment逻辑
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enrichment_logic():
    print("=== 测试enrichment逻辑 ===")
    
    from src.infrastructure.search.vector_search_engine import get_enhanced_search_engine
    
    engine = get_enhanced_search_engine()
    
    # 加载数据
    engine.load_data()
    
    # 获取一个案例的元数据
    loader = engine._get_data_loader()
    cases_metadata = loader.get_metadata('cases')
    
    if cases_metadata:
        # 找到目标案例
        target_meta = None
        for meta in cases_metadata:
            if meta.get('case_id') == 'case_008466':
                target_meta = meta
                break
        
        if target_meta:
            print(f"\n原始元数据:")
            print(f"  case_id: {target_meta.get('case_id')}")
            print(f"  criminals: {target_meta.get('criminals')}")
            print(f"  punish_of_money: {target_meta.get('punish_of_money')}")
            print(f"  imprisonment_months: {target_meta.get('imprisonment_months')}")
            
            # 测试enrichment
            enriched = engine._enrich_case_metadata(target_meta)
            
            print(f"\n增强后的元数据:")
            print(f"  case_id: {enriched.get('case_id')}")
            print(f"  criminals: {enriched.get('criminals')}")
            print(f"  punish_of_money: {enriched.get('punish_of_money')}")
            print(f"  imprisonment_months: {enriched.get('imprisonment_months')}")
            print(f"  death_penalty: {enriched.get('death_penalty')}")
            print(f"  life_imprisonment: {enriched.get('life_imprisonment')}")

if __name__ == "__main__":
    test_enrichment_logic()