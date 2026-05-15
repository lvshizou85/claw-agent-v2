#!/usr/bin/env python3
"""
运行 claude_runtime 测试的脚本
"""

import sys
import os
import asyncio

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入测试模块
try:
    from tests.test_claude_runtime import (
        TestBasicFunctionality,
        TestMessageFormat,
        TestStreamingResponse,
        TestSessionContext,
        TestIntegration
    )
    print("✓ 成功导入测试模块")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("当前 Python 路径:", sys.path)
    sys.exit(1)

# 运行测试
async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("运行 claude_runtime 测试")
    print("="*80)
    
    test_classes = [
        TestBasicFunctionality,
        TestMessageFormat,
        TestStreamingResponse,
        TestSessionContext,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = []
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n测试类: {test_class.__name__}")
        print("-" * 40)
        
        # 获取所有测试方法
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            test_instance = test_class()
            method = getattr(test_instance, method_name)
            
            try:
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                print(f"  ✓ {method_name}")
                passed_tests.append(f"{test_class.__name__}.{method_name}")
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
                failed_tests.append(f"{test_class.__name__}.{method_name}: {e}")
    
    # 输出测试结果
    print("\n" + "="*80)
    print("测试结果摘要")
    print("="*80)
    print(f"总测试数: {total_tests}")
    print(f"通过: {len(passed_tests)}")
    print(f"失败: {len(failed_tests)}")
    
    if failed_tests:
        print("\n失败的测试:")
        for failed in failed_tests:
            print(f"  ✗ {failed}")
        return False
    else:
        print("\n✓ 所有测试通过!")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)