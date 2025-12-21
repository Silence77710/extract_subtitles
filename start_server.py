#!/usr/bin/env python3
"""
启动脚本，确保在正确的虚拟环境中运行应用
"""

import subprocess
import sys
import os

def main():
    # 检查虚拟环境是否存在
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("错误: 找不到虚拟环境 'venv'")
        print("请先运行 ./install.sh 脚本来设置环境")
        sys.exit(1)

    # 激活虚拟环境并运行主应用
    activate_script = os.path.join(venv_path, "bin", "activate")
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    
    # 构建命令
    python_exe = os.path.join(venv_path, "bin", "python")
    if sys.platform == "win32":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    
    cmd = [python_exe, "main.py"] + sys.argv[1:]
    
    # 运行命令
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("错误: 找不到Python解释器")
        print("请确认虚拟环境已正确创建")
        sys.exit(1)

if __name__ == "__main__":
    main()