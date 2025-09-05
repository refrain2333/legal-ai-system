# 项目初始化指南

## 📋 初始化步骤

按照以下3个步骤完成项目初始化：

### 步骤1: 环境检查
```bash
python scripts/init/step1_env_check.py
```
**功能**: 检查Python版本、虚拟环境状态、关键依赖包
**输出**: 环境状态报告和解决建议

### 步骤2: 项目设置  
```bash
python scripts/init/step2_project_setup.py
```
**功能**: 创建目录结构、设置配置文件、验证数据文件
**输出**: 项目结构设置结果

### 步骤3: 最终检查
```bash
python scripts/init/step3_final_check.py
```
**功能**: 全面验证项目是否ready，提供启动指南
**输出**: 完整性检查和使用说明

## 🎯 快速初始化

如果你想一次性运行所有步骤：
```bash
# 依次运行三个步骤
python scripts/init/step1_env_check.py && \
python scripts/init/step2_project_setup.py && \
python scripts/init/step3_final_check.py
```

## 📁 辅助脚本

### 依赖安装脚本
- `install_dependencies.sh` (Linux/Mac)  
- `install_dependencies.bat` (Windows)

### 环境设置脚本
- `setup_env.sh` (Linux/Mac)
- `setup_env.bat` (Windows)

## ⚠️ 常见问题

**Q: Python版本不够怎么办？**
A: 安装Python 3.9+或使用conda创建新环境

**Q: 虚拟环境问题？**
A: 推荐使用conda: `conda create -n legal-ai python=3.9 -y`

**Q: 依赖安装失败？**
A: 确保在虚拟环境中，使用`pip install -r requirements_fixed.txt`

**Q: 数据文件缺失？**
A: 确保data/raw/目录包含所需的CSV文件

## 📞 获取帮助

如果遇到问题：
1. 重新运行对应的步骤脚本
2. 查看输出的具体错误信息
3. 按照建议进行修复
4. 运行`step3_final_check.py`验证

---
**说明**: 这些脚本设计为逐步引导，每个步骤都会给出明确的下一步指示。