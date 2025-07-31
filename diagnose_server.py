#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断服务器状态
"""

import requests
import json
import os

def diagnose_server():
    """诊断服务器状态"""
    
    print("=== 服务器诊断 ===")
    
    # 1. 检查服务器是否运行
    try:
        response = requests.get("http://localhost:8000/docs")
        print("✓ 服务器正在运行")
    except Exception as e:
        print(f"✗ 服务器未运行: {e}")
        return
    
    # 2. 检查Excel文件是否存在
    excel_files = ["1111.xlsx", "2222.xlsx", "1111.csv", "2222.csv"]
    print("\n=== 检查文件 ===")
    for file in excel_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
    
    # 3. 测试简单的API调用
    print("\n=== 测试API ===")
    test_input = {
        "args": {
            "eventId": 1,
            "eventName": "设备故障",
            "startTime": "2025-07-22 07:00:00",
            "trainNo": "G1",
            "preStation": "天津南",
            "nextStation": "济南西",
            "upDown": 1,
            "addressType": "区间",
            "eventType": 2
        },
        "graph": {
            "A": {
                "description": "开始",
                "type": "action",
                "predict_time": "10",
                "state": "not done"
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/affect/predict",
            json=test_input,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✓ API调用成功")
        else:
            print("✗ API调用失败")
            
    except Exception as e:
        print(f"✗ API调用异常: {e}")

if __name__ == "__main__":
    diagnose_server() 