@echo off
REM 法智导航项目 - 依赖安装脚本
echo 法智导航 - 依赖安装
echo ================================

REM 检查是否在legal-ai环境中
echo 当前Python路径:
where python
echo.

REM 激活legal-ai环境（如果还没有激活）
echo 激活legal-ai环境...
call conda activate legal-ai
if errorlevel 1 (
    echo 错误: 无法激活legal-ai环境
    echo 请先运行: conda create -n legal-ai python=3.9 -y
    pause
    exit /b 1
)

echo 确认环境激活成功:
where python
echo.

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 分批安装依赖
echo.
echo 第1批: 基础依赖
echo ------------------------
python -m pip install pydantic>=2.0.0 pydantic-settings>=2.0.0
python -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0
python -m pip install python-multipart aiofiles pyyaml python-dotenv

echo.
echo 第2批: 工具依赖
echo ------------------------
python -m pip install loguru tqdm httpx pytest pytest-asyncio
python -m pip install pylint black isort psutil

echo.
echo 第3批: 数据处理依赖
echo ------------------------
python -m pip install pandas numpy matplotlib seaborn

echo.
echo 第4批: AI/ML依赖（可能需要较长时间）
echo ------------------------
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers sentence-transformers
python -m pip install faiss-cpu

echo.
echo ================================
echo 安装完成！
echo 运行以下命令验证安装:
echo python scripts/simple_check.py
echo.
pause