#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟前端API请求，检查数据格式
"""

import requests
import json
import os

def test_frontend_api_format():
    """模拟前端的API请求"""
    
    # 绕过代理设置
    os.environ['no_proxy'] = '*'
    proxies = {'http': None, 'https': None}
    
    url = "http://127.0.0.1:5005/api/search"
    payload = {"query": "卖淫", "top_k": 2}  # 和前端一样的请求
    
    try:
        print("=== 模拟前端API请求 ===")
        response = requests.post(url, json=payload, proxies=proxies)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应状态: 成功")
            print(f"返回结果数量: {data.get('total', 0)}")
            
            results = data.get('results', [])
            
            for i, result in enumerate(results):
                if result.get('type') == 'case':
                    print(f"\n=== 案例 {i+1} - 前端会看到的数据 ===")
                    print(f"result.type: {result.get('type')}")
                    print(f"result.case_id: {result.get('case_id')}")
                    print(f"result.criminals: {result.get('criminals')}")
                    print(f"result.accusations: {result.get('accusations')}")
                    print(f"result.punish_of_money: {result.get('punish_of_money')}")
                    print(f"result.imprisonment_months: {result.get('imprisonment_months')}")
                    print(f"result.death_penalty: {result.get('death_penalty')}")
                    print(f"result.life_imprisonment: {result.get('life_imprisonment')}")
                    
                    # 检查前端条件判断
                    print(f"\n=== 前端条件判断 ===")
                    print(f"result.criminals && result.criminals.length > 0: {result.get('criminals') and len(result.get('criminals', [])) > 0}")
                    print(f"result.punish_of_money 存在: {bool(result.get('punish_of_money'))}")
                    print(f"result.imprisonment_months 存在: {bool(result.get('imprisonment_months'))}")
                    
                    # 模拟前端生成的HTML
                    print(f"\n=== 前端会生成的HTML ===")
                    criminals = result.get('criminals', [])
                    if criminals and len(criminals) > 0:
                        print(f"被告人: {', '.join(criminals)}")
                    else:
                        print("被告人: (不会显示)")
                        
                    punish_money = result.get('punish_of_money')
                    if punish_money:
                        print(f"罚款金额: {punish_money}元")
                    else:
                        print("罚款金额: (不会显示)")
                        
                    imprisonment = result.get('imprisonment_months')
                    if imprisonment:
                        print(f"有期徒刑: {imprisonment}个月")
                    else:
                        print("有期徒刑: (不会显示)")
                        
                    break  # 只检查第一个案例
            
        else:
            print(f"API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_frontend_api_format()