#!/usr/bin/env python3
"""
本地媒体检索系统统一启动脚本
支持前端热更新开发模式和生产模式
"""

import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path

class LocalNASStarter:
    def __init__(self):
        self.frontend_process = None
        self.backend_process = None
        self.is_dev_mode = True
        self.project_root = Path(__file__).parent
        
    def check_dependencies(self):
        """检查依赖是否安装"""
        print("🔍 检查依赖...")
        
        # 检查Python依赖
        try:
            import fastapi
            import uvicorn
            print("✅ Python后端依赖已安装")
        except ImportError:
            print("❌ Python依赖缺失，正在安装...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Python依赖安装完成")
        
        # 检查Node.js依赖
        frontend_dir = self.project_root / "frontend"
        if not (frontend_dir / "node_modules").exists():
            print("❌ Node.js依赖缺失，正在安装...")
            subprocess.run(["tnpm", "install"], cwd=frontend_dir, check=True)
            print("✅ Node.js依赖安装完成")
        else:
            print("✅ Node.js依赖已安装")
    
    def build_frontend(self):
        """构建前端"""
        print("🏗️  构建前端...")
        frontend_dir = self.project_root / "frontend"
        subprocess.run(["tnpm", "run", "build"], cwd=frontend_dir, check=True)
        print("✅ 前端构建完成")
    
    def start_frontend_dev(self):
        """启动前端开发服务器"""
        print("🚀 启动前端开发服务器...")
        frontend_dir = self.project_root / "frontend"
        
        # 设置环境变量
        env = os.environ.copy()
        env["BROWSER"] = "none"  # 不自动打开浏览器
        env["PORT"] = "3000"
        
        self.frontend_process = subprocess.Popen(
            ["tnpm", "start"],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 在后台线程中输出前端日志
        def log_frontend():
            for line in iter(self.frontend_process.stdout.readline, ''):
                if line.strip():
                    print(f"[前端] {line.strip()}")
        
        threading.Thread(target=log_frontend, daemon=True).start()
    
    def start_backend(self, workers=None):
        """启动后端服务器"""
        print("🚀 启动后端服务器...")
        
        # 修改后端以支持静态文件托管
        self.modify_backend_for_static_files()
        
        # 构建uvicorn命令
        backend_dir = self.project_root / "backend"
        uvicorn_cmd = [
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        # 根据模式添加不同参数
        if self.is_dev_mode:
            # 开发模式：启用热重载，单worker
            uvicorn_cmd.append("--reload")
            print("🔧 开发模式：启用热重载")
        else:
            # 生产模式：多worker，优化性能
            if workers is None:
                # 自动检测CPU核心数
                import multiprocessing
                workers = min(multiprocessing.cpu_count(), 4)  # 最多4个worker
            
            uvicorn_cmd.extend([
                "--workers", str(workers),
                "--access-log",
                "--log-level", "info"
            ])
            print(f"🏭 生产模式：启动 {workers} 个worker进程")
        
        # 启动后端
        self.backend_process = subprocess.Popen(
            uvicorn_cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 在后台线程中输出后端日志
        def log_backend():
            for line in iter(self.backend_process.stdout.readline, ''):
                if line.strip():
                    print(f"[后端] {line.strip()}")
        
        threading.Thread(target=log_backend, daemon=True).start()
    
    def modify_backend_for_static_files(self):
        """检查后端静态文件支持（已预配置）"""
        backend_main = self.project_root / "backend" / "main.py"
        
        # 读取现有内容检查是否已配置
        with open(backend_main, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含静态文件支持
        if "StaticFiles" in content and "serve_frontend" in content:
            print("✅ 后端静态文件支持已配置")
        else:
            print("⚠️  后端静态文件支持未配置，请手动配置或重新运行安装")
    
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        print("\n🛑 正在关闭服务...")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            print("✅ 前端服务已关闭")
        
        if self.backend_process:
            self.backend_process.terminate()
            print("✅ 后端服务已关闭")
        
        sys.exit(0)
    
    def run(self, dev_mode=True, workers=None):
        """运行应用"""
        self.is_dev_mode = dev_mode
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 检查依赖
            self.check_dependencies()
            
            if dev_mode:
                print("🔧 开发模式启动")
                # 开发模式：启动前端开发服务器
                self.start_frontend_dev()
                time.sleep(3)  # 等待前端启动
            else:
                print("🏭 生产模式启动")
                # 生产模式：构建前端
                self.build_frontend()
            
            # 启动后端
            self.start_backend(workers=workers)
            
            print("\n🎉 服务启动成功！")
            if dev_mode:
                print("📱 前端开发服务器: http://localhost:3000")
            print("🔧 后端API服务器: http://localhost:8000")
            print("📚 API文档: http://localhost:8000/docs")
            print("\n按 Ctrl+C 退出")
            
            # 保持主线程运行
            while True:
                time.sleep(1)
                
                # 检查进程状态
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ 后端进程意外退出")
                    break
                
                if dev_mode and self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ 前端进程意外退出")
                    break
        
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            self.signal_handler(signal.SIGTERM, None)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="本地媒体检索系统启动器")
    parser.add_argument("--prod", action="store_true", help="生产模式（构建前端）")
    parser.add_argument("--dev", action="store_true", help="开发模式（前端热更新）")
    parser.add_argument("--workers", type=int, help="worker进程数量（仅生产模式有效，默认自动检测）")
    
    args = parser.parse_args()
    
    # 默认开发模式
    dev_mode = True
    if args.prod:
        dev_mode = False
    elif args.dev:
        dev_mode = True
    
    starter = LocalNASStarter()
    starter.run(dev_mode=dev_mode, workers=args.workers)

if __name__ == "__main__":
    main() 