#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
临时脚本: 基于现有数据动态生成法律词典
生命周期: 生成词典后删除
"""

import pandas as pd
import jieba
import jieba.analyse
from collections import Counter
import pickle
import re
from pathlib import Path

def analyze_legal_corpus():
    print('=== 分析现有法律语料生成专业词典 ===')
    
    # 1. 加载数据
    try:
        with open('data/processed/full_dataset.pkl', 'rb') as f:
            dataset = pickle.load(f)
        print(f'加载数据: {len(dataset)} 条文档')
        
        # 提取所有文本
        all_texts = []
        for doc in dataset:
            if isinstance(doc, dict):
                content = doc.get('content', '') or doc.get('content_preview', '') or doc.get('title', '')
                all_texts.append(str(content))
            else:
                all_texts.append(str(doc))
                
    except Exception as e:
        print(f'PKL文件加载失败: {e}')
        print('尝试使用CSV数据...')
        
        all_texts = []
        try:
            laws_df = pd.read_csv('data/raw/法律条文.csv')
            if not laws_df.empty and '内容' in laws_df.columns:
                all_texts.extend(laws_df['内容'].fillna('').astype(str).tolist())
                print(f'加载法律条文: {len(laws_df)} 条')
        except Exception as e:
            print(f'法律条文加载失败: {e}')
            
        try:
            cases_df = pd.read_csv('data/raw/案例.csv')
            if not cases_df.empty and '案例描述' in cases_df.columns:
                all_texts.extend(cases_df['案例描述'].fillna('').astype(str).tolist())
                print(f'加载案例: {len(cases_df)} 条')
        except Exception as e:
            print(f'案例数据加载失败: {e}')
    
    if not all_texts:
        print('ERROR: 没有找到可用的文本数据')
        return {}
    
    # 2. 合并文本进行分析
    sample_texts = [text for text in all_texts if len(str(text).strip()) > 10][:2000]  # 取前2000条有效文本
    combined_text = ' '.join(sample_texts)
    
    print(f'分析文本: {len(sample_texts)} 条文档，总长度 {len(combined_text)} 字符')
    
    # 3. 使用jieba提取高频专业词汇
    print('\n=== TF-IDF关键词提取 ===')
    try:
        keywords_tfidf = jieba.analyse.extract_tags(
            combined_text, 
            topK=150, 
            withWeight=True,
            allowPOS=['n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn']  # 名词和动词
        )
        
        print('Top 20 TF-IDF关键词:')
        for i, (word, weight) in enumerate(keywords_tfidf[:20]):
            print(f'{i+1:2d}. {word:10s} ({weight:.4f})')
            
    except Exception as e:
        print(f'TF-IDF提取失败: {e}')
        keywords_tfidf = []
    
    # 4. 使用TextRank提取
    print('\n=== TextRank关键词提取 ===')
    try:
        keywords_textrank = jieba.analyse.textrank(
            combined_text,
            topK=100,
            withWeight=True,
            allowPOS=['n', 'nr', 'ns', 'nt', 'nz']
        )
        
        print('Top 15 TextRank关键词:')
        for i, (word, weight) in enumerate(keywords_textrank[:15]):
            print(f'{i+1:2d}. {word:10s} ({weight:.4f})')
            
    except Exception as e:
        print(f'TextRank提取失败: {e}')
        keywords_textrank = []
    
    # 5. 智能筛选和合并
    print('\n=== 智能筛选法律专业词汇 ===')
    
    # 法律领域特征词
    legal_patterns = [
        r'.*法.*', r'.*律.*', r'.*条.*', r'.*款.*', r'.*罪.*',
        r'.*权.*', r'.*责.*', r'.*诉.*', r'.*讼.*', r'.*判.*',
        r'.*合同.*', r'.*协议.*', r'.*赔偿.*', r'.*损害.*',
        r'.*民事.*', r'.*刑事.*', r'.*行政.*', r'.*商事.*'
    ]
    
    # 合并两种算法的结果
    combined_keywords = {}
    for word, weight in keywords_tfidf:
        combined_keywords[word] = combined_keywords.get(word, 0) + weight * 0.7
    for word, weight in keywords_textrank:
        combined_keywords[word] = combined_keywords.get(word, 0) + weight * 0.3
    
    # 智能筛选
    filtered_legal_keywords = {}
    
    for word, weight in combined_keywords.items():
        if len(word) >= 2 and len(word) <= 8:  # 合理长度
            # 检查是否符合法律词汇模式
            is_legal = False
            
            # 1. 正则匹配法律特征
            for pattern in legal_patterns:
                if re.match(pattern, word):
                    is_legal = True
                    weight *= 1.3  # 法律特征词加权
                    break
            
            # 2. 高权重词汇(说明重要性高)
            if not is_legal and weight > 0.015:
                is_legal = True
            
            # 3. 排除常见无意义词
            exclude_words = {'这个', '一个', '可以', '应该', '需要', '进行', '相关', '有关', '其他', '以及', '或者', '但是', '因此', '所以'}
            if word not in exclude_words and is_legal:
                filtered_legal_keywords[word] = weight
    
    # 排序展示结果
    sorted_legal = sorted(filtered_legal_keywords.items(), key=lambda x: x[1], reverse=True)
    
    print(f'筛选出 {len(sorted_legal)} 个法律专业词汇')
    print('Top 40 法律专业词汇:')
    for i, (word, weight) in enumerate(sorted_legal[:40]):
        print(f'{i+1:2d}. {word:12s} ({weight:.4f})')
    
    # 6. 按类别组织词汇
    categorized_dict = {
        'high_weight': {},      # 高权重核心词汇
        'legal_pattern': {},    # 法律模式词汇  
        'medium_weight': {},    # 中等权重词汇
        'all_keywords': {}      # 所有关键词
    }
    
    for word, weight in sorted_legal:
        categorized_dict['all_keywords'][word] = weight
        
        if weight > 0.03:
            categorized_dict['high_weight'][word] = weight
        elif weight > 0.02:
            categorized_dict['legal_pattern'][word] = weight
        else:
            categorized_dict['medium_weight'][word] = weight
    
    # 7. 保存动态词典
    output_path = 'data/processed/dynamic_legal_dictionary.pkl'
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(categorized_dict, f)
    
    print('\n动态法律词典已生成并保存到:', output_path)
    high_count = len(categorized_dict["high_weight"])
    pattern_count = len(categorized_dict["legal_pattern"])
    medium_count = len(categorized_dict["medium_weight"])
    total_count = len(categorized_dict["all_keywords"])
    
    print(f'   - 高权重词汇: {high_count} 个')
    print(f'   - 法律模式词汇: {pattern_count} 个') 
    print(f'   - 中等权重词汇: {medium_count} 个')
    print(f'   - 总词汇量: {total_count} 个')
    
    return categorized_dict

def test_generated_dictionary():
    """测试生成的词典效果"""
    print('\n=== 测试动态生成的词典 ===')
    
    try:
        with open('data/processed/dynamic_legal_dictionary.pkl', 'rb') as f:
            legal_dict = pickle.load(f)
            
        test_texts = [
            '合同违约责任承担',
            '交通事故人身损害赔偿',
            '刑事诉讼程序规定',
            '行政处罚决定书'
        ]
        
        for text in test_texts:
            print(f'\n测试文本: {text}')
            words = jieba.lcut(text)
            
            matched_words = []
            for word in words:
                all_keywords = legal_dict['all_keywords']
                high_weight = legal_dict['high_weight']
                
                if word in all_keywords:
                    weight = all_keywords[word]
                    category = 'high' if word in high_weight else 'medium'
                    matched_words.append((word, weight, category))
            
            if matched_words:
                print('  匹配到的法律专业词:')
                for word, weight, cat in matched_words:
                    print(f'    - {word} (权重:{weight:.4f}, 类别:{cat})')
            else:
                print('  未匹配到专业词汇')
                
    except Exception as e:
        print(f'词典测试失败: {e}')

if __name__ == '__main__':
    # 生成动态词典
    legal_dict = analyze_legal_corpus()
    
    if legal_dict:
        # 测试词典效果
        test_generated_dictionary()
    else:
        print('词典生成失败')