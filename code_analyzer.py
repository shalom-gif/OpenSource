#!/usr/bin/env python
# coding: utf-8

import libcst

class FunctionAnalyzer(libcst.CSTVisitor):
    def __init__(self):
        self.functions = {}
        self.current_function = None
    
    def visit_FunctionDef(self, node: libcst.FunctionDef):
        self.current_function = node.name.value
        self.functions[self.current_function] = {
            "name": node.name.value,
            "line_start": node.start_line,
            "line_end": node.end_line,
            "params": [p.name.value for p in node.params.params],
            "integers": [],
            "calls": []
        }
    
    def leave_FunctionDef(self, node: libcst.FunctionDef):
        self.current_function = None
    
    def visit_Integer(self, node: libcst.Integer):
        if self.current_function:
            self.functions[self.current_function]["integers"].append(node.value)
    
    def visit_Call(self, node: libcst.Call):
        if self.current_function and isinstance(node.func, libcst.Name):
            self.functions[self.current_function]["calls"].append(node.func.value)

class CodeTransformer(libcst.CSTTransformer):
    def leave_Integer(self, node: libcst.Integer, updated: libcst.Integer):
        # 将所有整数加1
        try:
            new_value = str(int(updated.value) + 1)
            return updated.with_changes(value=new_value)
        except ValueError:
            return updated

def analyze_code(source_code):
    """分析代码"""
    module = libcst.parse_module(source_code)
    analyzer = FunctionAnalyzer()
    module.visit(analyzer)
    
    return analyzer.functions

def transform_code(source_code):
    """转换代码"""
    module = libcst.parse_module(source_code)
    transformer = CodeTransformer()
    transformed = module.visit(transformer)
    return transformed.code

def main():
    """主函数"""
    print("代码分析工具")
    print("=" * 40)
    
    # 示例代码
    sample_code = '''
def calculate_area(radius):
    area = 3.14159 * radius * radius
    return area

def fibonacci(n):
    if n <= 1:
        return 1
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    print("开始计算")
    area = calculate_area(5)
    print(f"面积: {area}")
    
    for i in range(3):
        fib = fibonacci(i)
        print(f"fib({i}) = {fib}")
'''
    
    print("原始代码:")
    print(sample_code)
    
    print("\n代码分析结果:")
    analysis = analyze_code(sample_code)
    for func_name, info in analysis.items():
        print(f"\n函数: {func_name}")
        print(f"  参数: {info['params']}")
        print(f"  行号: {info['line_start']}-{info['line_end']}")
        if info['integers']:
            print(f"  整数常量: {info['integers']}")
        if info['calls']:
            print(f"  函数调用: {list(set(info['calls']))}")
    
    print("\n" + "=" * 40)
    print("转换后的代码(所有整数加1):")
    transformed = transform_code(sample_code)
    print(transformed)
    
    print("\n转换后的代码分析:")
    new_analysis = analyze_code(transformed)
    for func_name, info in new_analysis.items():
        if info['integers']:
            print(f"  {func_name}: 整数常量变为 {info['integers']}")

if __name__ == "__main__":
    main()