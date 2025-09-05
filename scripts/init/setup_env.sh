#!/bin/bash
# 法智导航项目 - Conda环境设置脚本

echo "法智导航 - Conda虚拟环境设置"
echo "================================"

# 方案一：使用Conda虚拟环境 (推荐)
echo ""
echo "方案一：Conda虚拟环境 (推荐)"
echo "----------------------------"
echo "1. 创建虚拟环境："
echo "conda create -n legal-ai python=3.9 -y"
echo ""
echo "2. 激活虚拟环境："
echo "conda activate legal-ai"
echo ""  
echo "3. 安装依赖："
echo "pip install -r requirements.txt"
echo ""
echo "4. 验证安装："
echo "python scripts/simple_init.py"
echo ""
echo "5. 启动项目："
echo "python src/main.py"
echo ""

# 方案二：Python venv虚拟环境
echo "方案二：Python venv虚拟环境"
echo "---------------------------"
echo "1. 创建虚拟环境："
echo "python -m venv venv"
echo ""
echo "2. 激活虚拟环境："
echo "# Windows:"
echo "venv\\Scripts\\activate"
echo "# Linux/Mac:"
echo "source venv/bin/activate"
echo ""
echo "3. 安装依赖："
echo "pip install -r requirements.txt"
echo ""

# 环境管理命令
echo "环境管理命令"
echo "------------"
echo "查看环境列表: conda env list"
echo "删除环境: conda env remove -n legal-ai"
echo "导出环境: conda env export > environment.yml"
echo ""

# 不推荐的方案
echo "⚠️  不推荐：直接全局安装"
echo "------------------------"
echo "原因："
echo "- 可能与其他项目产生依赖冲突"
echo "- torch, transformers等库体积大(2GB+)"
echo "- 难以管理不同项目的依赖版本"
echo "- 无法轻易回退或重置环境"