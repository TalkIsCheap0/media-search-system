#!/usr/bin/env python3
"""
本地媒体检索系统 - 后端启动脚本
"""

import sys
import os
import logging
import uvicorn

# 禁用ChromaDB遥测功能，避免SSL连接错误日志
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_search.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """启动FastAPI服务器"""
    logger.info("正在启动本地媒体检索系统后端服务...")
    
    try:
        # 导入主应用
        from main import app
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False  # 生产环境建议设为False
        )
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 