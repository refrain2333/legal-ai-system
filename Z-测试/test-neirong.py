
"""
最终测试脚本
"""

import requests
import os

def final_test():
    """最终测试修复效果"""
    
    # 绕过代理设置
    os.environ['no_proxy'] = '*'
    proxies = {'http': None, 'https': None}
    
    url = "http://127.0.0.1:5005/api/search"
    payload = {"query": "卖淫", "top_k": 2}
    
    try:
        response = requests.post(url, json=payload, proxies=proxies)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应成功! 返回结果数量: {data.get('total', 0)}")
            
            results = data.get('results', [])
            for i, result in enumerate(results):
                print(f"\n=== 结果 {i+1} ===")
                print(f"ID: {result.get('id')}")
                print(f"类型: {result.get('type')}")
                print(f"标题: {result.get('title', '')[:100]}...")
                print(f"相似度: {result.get('similarity', 0):.3f}")
                
                content = result.get('content', '')
                print(f"内容长度: {len(content)} 字符")
                
                if len(content) > 50:
                    print(f"内容正常: {content[:100]}...")
                else:
                    print(f"内容太短: '{content}'")
        else:
            print(f"API请求失败: {response.status_code}")
    
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    final_test()