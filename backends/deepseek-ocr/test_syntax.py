#!/usr/bin/env python3
"""
Test script to check for syntax errors in DeepSeek backend modules
"""

import ast
import os

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def test_all_modules():
    """Test all DeepSeek backend modules for syntax errors"""
    modules_to_test = [
        'deepseek_ocr_backend.py',
        'deepseek_ocr.py',
        'config.py',
        'process/ngram_norepeat.py',
        'deepencoder/build_linear.py'
    ]

    print("Testing DeepSeek backend modules for syntax errors...")
    print("=" * 50)

    all_passed = True
    for module in modules_to_test:
        if os.path.exists(module):
            success, error = check_syntax(module)
            if success:
                print(f"✓ {module}: Syntax OK")
            else:
                print(f"✗ {module}: Syntax Error - {error}")
                all_passed = False
        else:
            print(f"✗ {module}: File not found")
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("✓ All modules passed syntax check")
    else:
        print("✗ Some modules have syntax errors")

    return all_passed

if __name__ == "__main__":
    test_all_modules()