
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
        from src.api.app import create_app
        from src.config.settings import settings
        
        # 立即显示前端页面访问信息
        frontend_path = Path(__file__).parent / "frontend" / "index.html"
        if frontend_path.exists():
            print("\n" + "="*60)
            print("前端页面访问方式:")
            print(f"1. 通过Web服务器: http://{settings.HOST}:{settings.PORT}/ui/")
            print(f"2. 直接点击打开: {frontend_path.absolute()}")
            print(f"   (可以直接双击文件或复制路径到浏览器)")
            print("="*60)
        
        app = create_app()
        
        print(f"\nStarting server on http://{settings.HOST}:{settings.PORT}")
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