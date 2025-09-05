#!/bin/bash
# 法智导航项目 - 依赖安装脚本（Linux/Mac版本）

echo "法智导航 - 依赖安装"
echo "================================"

# 检查conda是否可用
if ! command -v conda &> /dev/null; then
    echo "错误: conda未找到，请先安装Miniconda或Anaconda"
    exit 1
fi

# 激活legal-ai环境
echo "激活legal-ai环境..."
source activate legal-ai
if [ $? -ne 0 ]; then
    echo "错误: 无法激活legal-ai环境"
    echo "请先运行: conda create -n legal-ai python=3.9 -y"
    exit 1
fi

echo "确认环境激活成功:"
which python
echo

# 升级pip
echo "升级pip..."
python -m pip install --upgrade pip

# 分批安装依赖
echo
echo "第1批: 基础依赖"
echo "------------------------"
python -m pip install pydantic==1.10.12 pydantic-settings==2.0.3
python -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0
python -m pip install python-multipart aiofiles pyyaml python-dotenv

echo
echo "第2批: 工具依赖"
echo "------------------------"
python -m pip install loguru tqdm httpx pytest pytest-asyncio
python -m pip install pylint black isort psutil

echo
echo "第3批: 数据处理依赖"
echo "------------------------"
python -m pip install pandas numpy matplotlib seaborn

echo
echo "第4批: AI/ML依赖（可能需要较长时间）"
echo "------------------------"
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers sentence-transformers
python -m pip install faiss-cpu

echo
echo "================================"
echo "安装完成！"
echo "运行以下命令验证安装:"
echo "python scripts/simple_check.py"
echo