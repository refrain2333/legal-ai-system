#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤3: 最终检查
全面验证项目是否ready，可以开始开发
"""

import sys
import os
from pathlib import Path

# 设置环境编码，避免Windows控制台编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def safe_print(text):
    """安全打印，避免Unicode编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 替换特殊字符为ASCII
        safe_text = text.replace('🔍', '[CHECK]').replace('✅', '[OK]').replace('❌', '[ERROR]')
        safe_text = safe_text.replace('📁', '[DIR]').replace('📄', '[FILE]').replace('🚀', '[START]')
        safe_text = safe_text.replace('⚠️', '[WARN]').replace('💡', '[INFO]')
        print(safe_text)

def final_env_check():
    """最终环境检查"""
    safe_print("[CHECK] 环境状态...")
    
    # Python版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_ok = sys.version_info >= (3, 9)
    safe_print(f"   Python {py_version}: {'[OK]' if python_ok else '[ERROR]'}")
    
    # 虚拟环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    env_ok = conda_env or venv_active
    
    if conda_env:
        safe_print(f"   Conda环境 ({conda_env}): [OK]")
    elif venv_active:
        safe_print(f"   Python虚拟环境: [OK]")
    else:
        safe_print(f"   虚拟环境: [ERROR] 未使用")
    
    return python_ok and env_ok

def final_structure_check():
    """最终结构检查"""
    safe_print("[CHECK] 项目结构...")
    
    required_dirs = [
        "src/api", "src/config", "data/raw", "logs/app", 
        "models/pretrained", "data/processed"
    ]
    
    missing_dirs = []
    for d in required_dirs:
        if not Path(d).exists():
            missing_dirs.append(d)
    
    if missing_dirs:
        safe_print(f"   目录结构: [ERROR] 缺失{len(missing_dirs)}个")
        return False
    else:
        safe_print(f"   目录结构: [OK]")
        return True

def final_data_check():
    """最终数据检查"""
    safe_print("[CHECK] 数据文件...")
    
    data_files = [
        "data/raw/raw_laws(1).csv",
        "data/raw/raw_cases(1).csv"
    ]
    
    total_size = 0
    missing = 0
    
    for f in data_files:
        path = Path(f)
        if path.exists():
            total_size += path.stat().st_size / 1024 / 1024
        else:
            missing += 1
    
    if missing == 0:
        safe_print(f"   数据文件: [OK] (总计{total_size:.1f}MB)")
        return True
    else:
        safe_print(f"   数据文件: [ERROR] 缺失{missing}个")
        return False

def final_config_check():
    """最终配置检查"""
    safe_print("[CHECK] 配置文件...")
    
    config_files = [".env", "requirements_fixed.txt"]
    missing = []
    
    for f in config_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        safe_print(f"   配置文件: [ERROR] 缺失{len(missing)}个")
        return False
    else:
        safe_print(f"   配置文件: [OK]")
        return True

def final_deps_check():
    """最终依赖检查"""
    safe_print("[CHECK] 核心依赖...")
    
    core_deps = ['torch', 'transformers', 'fastapi', 'pydantic', 'loguru']
    installed = 0
    
    for dep in core_deps:
        try:
            __import__(dep)
            installed += 1
        except ImportError:
            pass
    
    if installed == len(core_deps):
        safe_print(f"   核心依赖: [OK] ({installed}/{len(core_deps)})")
        return True
    else:
        safe_print(f"   核心依赖: [ERROR] ({installed}/{len(core_deps)})")
        return False

def print_startup_guide():
    """打印启动指南"""
    safe_print("\n[START] 项目启动指南:")
    safe_print("   1. 启动开发服务器:")
    safe_print("      python src/main.py")
    safe_print("")
    safe_print("   2. 访问API文档:")
    safe_print("      http://localhost:5005/docs")
    safe_print("")
    safe_print("   3. 常用开发命令:")
    safe_print("      pytest                    # 运行测试")
    safe_print("      black src/ tests/        # 代码格式化") 
    safe_print("      python scripts/validate_data.py  # 数据验证")

def print_troubleshooting():
    """打印问题解决指南"""
    safe_print("\n[WARN] 问题解决:")
    safe_print("   环境问题: python scripts/init/step1_env_check.py")
    safe_print("   配置问题: python scripts/init/step2_project_setup.py")
    safe_print("   数据问题: 确保data/raw/目录有完整数据文件")

def main():
    print("="*50)
    print("步骤3: 最终检查")
    print("="*50)
    
    # 执行各项检查
    checks = [
        final_env_check(),
        final_structure_check(), 
        final_data_check(),
        final_config_check(),
        final_deps_check()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    safe_print(f"\n[INFO] 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        safe_print("[OK] 恭喜! 项目已完全ready!")
        print_startup_guide()
        return_code = 0
    else:
        safe_print("[WARN] 还有问题需要解决")
        print_troubleshooting()
        return_code = 1
    
    print("="*50)
    return return_code

if __name__ == "__main__":
    sys.exit(main())