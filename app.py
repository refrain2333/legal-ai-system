#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法智导航系统简化启动脚本 - 无Emoji版本
Simple startup script for Legal AI system
"""

import sys
import os
import uvicorn
from pathlib import Path

# 设置控制台编码
if sys.platform.startswith('win'):
    os.environ["PYTHONIOENCODING"] = "utf-8"

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """简化版主函数"""
    print("="*60)
    print("Legal AI System - Starting Server...")
    print("Semantic Document Retrieval Service")
    print("="*60)
    
    try:
        # 直接导入和创建app
        from src.api.app import create_app
        from src.config.settings import settings
        
        app = create_app()
        
        print(f"Starting server on http://{settings.HOST}:{settings.PORT}")
        print("Press Ctrl+C to stop the server")
        print("="*60)
        
        # 启动服务器 - 禁用reload避免问题
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # 禁用reload避免import string问题
            workers=1,
            log_level="info",
            access_log=False  # 禁用访问日志避免编码问题
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"ERROR: Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()