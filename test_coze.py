#!/usr/bin/env python3
"""
测试 Coze 工作流连接
"""

import requests
import json

# Coze 配置
COZE_WORKFLOW_ID = ""  # 在这里填入您的工作流 ID
COZE_TOKEN = ""        # 在这里填入您的令牌
COZE_API_BASE_URL = "https://api.coze.cn/v1"

def test_coze_connection():
    """测试 Coze API 连接"""
    if not COZE_WORKFLOW_ID or not COZE_TOKEN:
        print("错误: 请先设置 COZE_WORKFLOW_ID 和 COZE_TOKEN")
        return
    
    # Coze API URL
    api_url = f"{COZE_API_BASE_URL}/workflows/{COZE_WORKFLOW_ID}/run"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {COZE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 请求数据 - 根据实际格式调整
    payload = {
        "workflow_id": int(COZE_WORKFLOW_ID),
        "parameters": {
            "subtitle": "This is a test subtitle content for testing the Coze workflow connection. This should be replaced with actual subtitle content after cleaning."
        }
    }
    
    print(f"正在测试 Coze API 连接...")
    print(f"URL: {api_url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送 POST 请求到 Coze API
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.content:
            print(f"响应内容长度: {len(response.text)} 字符")
            print(f"响应内容预览: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")
            try:
                json_response = response.json()
                print(f"JSON 解析成功")
                print(f"响应码: {json_response.get('code', 'N/A')}")
                print(f"消息: {json_response.get('msg', 'N/A')}")
                if 'data' in json_response:
                    print(f"数据字段存在: {len(json_response['data'])} 字符")
            except json.JSONDecodeError:
                print("响应不是有效的 JSON 格式")
        else:
            print("响应为空")
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

if __name__ == "__main__":
    test_coze_connection()