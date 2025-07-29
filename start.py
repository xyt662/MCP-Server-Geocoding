#!/usr/bin/env python3
"""启动脚本"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("错误: 需要Python 3.9或更高版本")
        sys.exit(1)


def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        sys.exit(1)


def setup_environment():
    """设置环境"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("正在创建.env文件...")
        env_file.write_text(env_example.read_text())
        print("请编辑.env文件并设置您的API密钥")


def run_tests():
    """运行测试"""
    print("正在运行测试...")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "-v"], check=True)
        print("测试通过")
    except subprocess.CalledProcessError as e:
        print(f"测试失败: {e}")
        return False
    return True


def start_server(host="0.0.0.0", port=4000, reload=False, workers=1):
    """启动服务器"""
    print(f"正在启动服务器 http://{host}:{port}")
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    else:
        cmd.extend(["--workers", str(workers)])
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"服务器启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Server Geocoding 启动脚本")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=4000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载（开发模式）")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数量")
    parser.add_argument("--install", action="store_true", help="安装依赖")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--setup", action="store_true", help="设置环境")
    
    args = parser.parse_args()
    
    # 检查Python版本
    check_python_version()
    
    # 安装依赖
    if args.install:
        install_dependencies()
        return
    
    # 设置环境
    if args.setup:
        setup_environment()
        return
    
    # 运行测试
    if args.test:
        if not run_tests():
            sys.exit(1)
        return
    
    # 设置环境（如果需要）
    setup_environment()
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )


if __name__ == "__main__":
    main()