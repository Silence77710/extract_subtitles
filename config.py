#!/usr/bin/env python3
"""
配置文件，用于管理 Coze 工作流和其他配置项
"""

import os
import json

class Config:
    # Coze API 配置
    COZE_API_BASE_URL = os.environ.get('COZE_API_BASE_URL', 'https://api.coze.cn/v1')
    COZE_WORKFLOW_ID = os.environ.get('COZE_WORKFLOW_ID', '')
    COZE_TOKEN = os.environ.get('COZE_TOKEN', '')
    
    # 应用配置
    SUBTITLES_DIR = "subtitles"
    COOKIES_DIR = "cookies"
    
    @classmethod
    def is_coze_configured(cls):
        """检查 Coze 配置是否完整"""
        return bool(cls.COZE_WORKFLOW_ID and cls.COZE_TOKEN)
    
    @classmethod
    def load_from_file(cls, config_file='coze_config.json'):
        """从文件加载 Coze 配置"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                cls.COZE_WORKFLOW_ID = config_data.get('workflow_id', cls.COZE_WORKFLOW_ID)
                cls.COZE_TOKEN = config_data.get('token', cls.COZE_TOKEN)
                cls.COZE_API_BASE_URL = config_data.get('api_base_url', cls.COZE_API_BASE_URL)
                return True
            except Exception as e:
                print(f"加载配置文件时出错: {e}")
                return False
        return False
    
    @classmethod
    def save_to_file(cls, config_file='coze_config.json'):
        """保存 Coze 配置到文件"""
        config_data = {
            'workflow_id': cls.COZE_WORKFLOW_ID,
            'token': cls.COZE_TOKEN,
            'api_base_url': cls.COZE_API_BASE_URL
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
            return False

# 在模块加载时尝试从文件加载配置
Config.load_from_file()