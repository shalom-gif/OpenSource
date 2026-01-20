#!/usr/bin/env python
# coding: utf-8

import unittest

class MathTests(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 2, 3)
    
    def test_subtraction(self):
        self.assertEqual(5 - 2, 3)
    
    def test_multiplication(self):
        self.assertEqual(3 * 4, 12)
    
    def test_division(self):
        self.assertEqual(10 / 2, 5)
    
    def test_string_concat(self):
        self.assertEqual("Hello" + " " + "World", "Hello World")

class ListTests(unittest.TestCase):
    def test_list_length(self):
        my_list = [1, 2, 3, 4, 5]
        self.assertEqual(len(my_list), 5)
    
    def test_list_append(self):
        my_list = [1, 2, 3]
        my_list.append(4)
        self.assertEqual(my_list, [1, 2, 3, 4])

def find_test_classes(module):
    """查找测试类"""
    tests = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            tests.append(obj)
    return tests

def run_custom_tests():
    """自定义测试运行器"""
    module = __import__("__main__")
    test_classes = find_test_classes(module)
    
    print("开始运行测试...")
    print("=" * 40)
    
    for test_class in test_classes:
        print(f"运行测试类: {test_class.__name__}")
        test_instance = test_class()
        
        for method_name in sorted(dir(test_instance)):
            if method_name.startswith("test"):
                test_method = getattr(test_instance, method_name)
                try:
                    test_method()
                    print(f"  ✓ {method_name} - 通过")
                except AssertionError as e:
                    print(f"  ✗ {method_name} - 失败: {e}")
                except Exception as e:
                    print(f"  ✗ {method_name} - 错误: {e}")
    
    print("=" * 40)
    print("测试运行完成")

if __name__ == "__main__":
    # 可以选择使用标准测试运行器或自定义运行器
    choice = input("运行方式: 1=标准unittest, 2=自定义运行器 (输入1或2): ")
    
    if choice == "1":
        # 使用标准unittest
        unittest.main(verbosity=2)
    else:
        # 使用自定义运行器
        run_custom_tests()