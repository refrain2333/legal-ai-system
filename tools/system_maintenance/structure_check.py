#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project Structure Verification Tool
验证项目结构是否符合标准
"""

import os
from pathlib import Path

def verify_structure():
    print("="*50)
    print("Project Structure Verification")
    print("="*50)
    
    # Core structure check
    required_dirs = [
        'src/', 'src/api/', 'src/models/', 'src/services/', 
        'src/data/', 'src/config/', 'src/utils/',
        'tests/', 'tools/', 'data/', 'docs/'
    ]
    
    print("\\n1. Directory Structure:")
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  OK {dir_path}")
        else:
            print(f"  MISSING {dir_path}")
            all_good = False
    
    # Core files check  
    required_files = [
        'src/__init__.py', 'src/main.py',
        'src/api/app.py', 'src/api/search_routes.py',
        'src/models/semantic_embedding.py',
        'src/services/retrieval_service.py',
        'src/data/full_dataset_processor.py',
        'src/config/settings.py',
        'tests/test_core_functionality.py',
        'app.py'  # Main launcher
    ]
    
    print("\\n2. Core Files:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            all_good = False
    
    # Check for unwanted files in root
    print("\\n3. Root Directory Cleanliness:")
    root_py_files = [f for f in os.listdir('.') if f.endswith('.py')]
    allowed_root = ['app.py']
    
    for file in root_py_files:
        if file in allowed_root:
            print(f"  OK {file}")
        else:
            print(f"  UNWANTED {file} (should be moved)")
            all_good = False
    
    # Check for duplicate test dirs
    if Path('src/tests').exists():
        print(f"  ERROR Duplicate test directory: src/tests/")
        all_good = False
    
    print("\\n" + "="*50)
    if all_good:
        print("SUCCESS: Project structure is standardized!")
        print("All directories and files are in correct locations.")
    else:
        print("WARNING: Project structure needs fixes.")
        print("Please review the issues above.")
    
    print("="*50)
    return all_good

if __name__ == "__main__":
    success = verify_structure()
    print(f"\\nVerification result: {'PASS' if success else 'FAIL'}")
    if not success:
        exit(1)