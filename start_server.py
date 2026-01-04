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
    
    # 构建Python可执行文件路径
    if sys.platform == "win32":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python")
    
    # 检查venv Python是否可用（存在、可执行且非空）
    use_venv = False
    if os.path.exists(venv_path):
        if os.path.exists(python_exe):
            # 检查文件是否可执行且非空
            if os.access(python_exe, os.X_OK) and os.path.getsize(python_exe) > 0:
                use_venv = True
            else:
                print("警告: 虚拟环境的Python可执行文件损坏，将使用系统Python")
        else:
            print("警告: 虚拟环境中找不到Python可执行文件，将使用系统Python")
    else:
        print("警告: 找不到虚拟环境 'venv'，将使用系统Python")
    
    # 如果venv不可用，使用系统Python
    if not use_venv:
        python_exe = sys.executable
        print(f"使用系统Python: {python_exe}")
    
    # 设置环境变量以使用venv的site-packages（如果venv存在）
    env = os.environ.copy()
    if os.path.exists(venv_path):
        if sys.platform == "win32":
            site_packages = os.path.join(venv_path, "Lib", "site-packages")
        else:
            site_packages = os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
        
        if os.path.exists(site_packages):
            # 将venv的site-packages添加到PYTHONPATH
            current_pythonpath = env.get("PYTHONPATH", "")
            if current_pythonpath:
                env["PYTHONPATH"] = f"{site_packages}{os.pathsep}{current_pythonpath}"
            else:
                env["PYTHONPATH"] = site_packages
    
    cmd = [python_exe, "main.py"] + sys.argv[1:]
    
    # 运行命令
    try:
        result = subprocess.run(cmd, check=True, env=env)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("错误: 找不到Python解释器")
        print("请确认虚拟环境已正确创建或系统Python已安装")
        sys.exit(1)

if __name__ == "__main__":
    main()