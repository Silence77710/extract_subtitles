#!/bin/bash

# 安装脚本
# 自动安装所有依赖项

echo "开始安装依赖..."

# 检查是否安装了 Homebrew
if ! command -v brew &> /dev/null
then
    echo "未检测到 Homebrew，正在安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew 已安装"
fi

# 使用 Homebrew 安装 yt-dlp
echo "正在安装 yt-dlp..."
brew install yt-dlp

# 创建虚拟环境
echo "正在创建 Python 虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip 到最新版本
echo "正在升级 pip..."
python3 -m pip install --upgrade pip

# 安装 Python 依赖
echo "正在安装 Python 依赖..."
pip install -r requirements.txt

echo "所有依赖安装完成！"
echo "请运行以下命令激活虚拟环境:"
echo "source venv/bin/activate"
