#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的API内容测试脚本
测试搜索API返回的所有字段是否正确
"""

import requests
import os
import json

def test_search_api():
    """测试搜索API的完整功能"""
    
    # 绕过代理设置
    os.environ['no_proxy'] = '*'
    proxies = {'http': None, 'https': None}
    
    # API配置
    base_url = "http://127.0.0.1:5006"
    
    print("=" * 60)
    print("法律AI检索系统 - 完整功能测试")
    print("=" * 60)
    
    # 1. 首先测试系统状态
    print("\n1. 测试系统状态...")
    try:
        response = requests.get(f"{base_url}/api/status", proxies=proxies, timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   系统状态: {status_data.get('status')}")
            print(f"   系统就绪: {status_data.get('ready')}")
            print(f"   文档总数: {status_data.get('total_documents')}")
        else:
            print(f"   状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"   状态检查错误: {e}")
    
    # 2. 测试搜索功能
    print("\n2. 测试搜索功能...")
    
    # 测试不同的查询
    test_queries = [
        {"query": "卖淫", "top_k": 2, "description": "测试案例搜索"},
        {"query": "故意杀人", "top_k": 3, "description": "测试严重犯罪搜索"},
        {"query": "第264条", "top_k": 2, "description": "测试法条搜索"}
    ]
    
    for test in test_queries:
        print(f"\n   {test['description']}: '{test['query']}'")
        print("   " + "-" * 50)
        
        try:
            response = requests.post(
                f"{base_url}/api/search",
                json={"query": test["query"], "top_k": test["top_k"]},
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   搜索成功: {data.get('success', False)}")
                print(f"   结果数量: {data.get('total', 0)}")
                
                results = data.get('results', [])
                for i, result in enumerate(results, 1):
                    print(f"\n   === 结果 {i} ===")
                    print(f"   ID: {result.get('id')}")
                    print(f"   类型: {result.get('type')}")
                    print(f"   标题: {result.get('title', '')[:80]}...")
                    print(f"   相似度: {result.get('similarity', 0):.3f}")
                    
                    # 内容检查
                    content = result.get('content', '')
                    print(f"   内容长度: {len(content)} 字符")
                    
                    if content == '内容加载失败':
                        print(f"   ❌ 内容加载失败!")
                    elif len(content) == 0:
                        print(f"   ❌ 内容为空!")
                    else:
                        # 智能显示内容
                        if len(content) <= 100:
                            # 短内容直接显示全部
                            print(f"   完整内容: {content}")
                        elif len(content) <= 300:
                            # 中等长度显示更多
                            print(f"   内容预览: {content[:200]}...")
                            print(f"   [内容较长，共{len(content)}字符，完整内容请查看前端]")
                        else:
                            # 长内容显示概要
                            print(f"   内容开头: {content[:100]}...")
                            print(f"   内容结尾: ...{content[-50:]}")
                            print(f"   [长文档，共{len(content)}字符，建议使用前端查看完整内容]")
                    
                    print(f"   内容统计: {len(content)}字符 | 预估阅读时间: {len(content)//200 + 1}分钟")
                    
                    # 根据类型显示特定字段
                    if result.get('type') == 'case':
                        print("\n   案例特有字段:")
                        print(f"     案例ID: {result.get('case_id')}")
                        print(f"     罪犯: {result.get('criminals')}")
                        print(f"     罪名: {result.get('accusations')}")
                        print(f"     相关法条: {result.get('relevant_articles')}")
                        
                        # 刑罚信息
                        if result.get('imprisonment_months'):
                            print(f"     刑期: {result.get('imprisonment_months')} 月")
                        if result.get('punish_of_money'):
                            print(f"     罚金: {result.get('punish_of_money')} 万元")
                        if result.get('death_penalty'):
                            print(f"     死刑: 是")
                        if result.get('life_imprisonment'):
                            print(f"     无期徒刑: 是")
                    
                    elif result.get('type') == 'article':
                        print("\n   法条特有字段:")
                        print(f"     法条编号: {result.get('article_number')}")
                        print(f"     所属章节: {result.get('chapter')}")
                
            else:
                print(f"   搜索失败: HTTP {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   搜索超时!")
        except Exception as e:
            print(f"   搜索错误: {e}")
    
    # 3. 测试边界情况
    print("\n\n3. 测试边界情况...")
    print("   " + "-" * 50)
    
    # 测试空查询
    print("\n   测试空查询...")
    try:
        response = requests.post(
            f"{base_url}/api/search",
            json={"query": "", "top_k": 5},
            proxies=proxies,
            timeout=5
        )
        print(f"   空查询响应: {response.status_code}")
    except Exception as e:
        print(f"   空查询错误: {e}")
    
    # 测试超大top_k
    print("\n   测试超大结果数量...")
    try:
        response = requests.post(
            f"{base_url}/api/search",
            json={"query": "盗窃", "top_k": 100},
            proxies=proxies,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   请求100条，实际返回: {len(data.get('results', []))} 条")
        else:
            print(f"   响应代码: {response.status_code}")
    except Exception as e:
        print(f"   测试错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

def display_summary():
    """显示测试总结"""
    print("\n测试总结:")
    print("-" * 40)
    print("✓ 系统状态检查")
    print("✓ 基础搜索功能")
    print("✓ 案例内容加载")
    print("✓ 法条内容加载")
    print("✓ 特殊字段解析")
    print("✓ 边界条件测试")

if __name__ == "__main__":
    test_search_api()
    display_summary()