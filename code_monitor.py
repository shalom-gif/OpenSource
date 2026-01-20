#!/usr/bin/env python
# coding: utf-8

from sys import monitoring

depth = 0
call_count = {}

def on_start(code, offset):
    global depth
    depth += 1
    call_count[code.co_name] = call_count.get(code.co_name, 0) + 1
    
    prefix = "  " * (depth - 1) + ">"
    print(f"{prefix} 进入 {code.co_name} [深度:{depth}]")

def on_return(code, offset, retval):
    global depth
    prefix = "  " * (depth - 1) + "<"
    print(f"{prefix} 离开 {code.co_name} -> {retval}")
    depth -= 1

def setup_monitor():
    """设置监控器"""
    ID = 3
    monitoring.use_tool_id(ID, "tracer")
    monitoring.register_callback(ID, monitoring.events.PY_START, on_start)
    monitoring.register_callback(ID, monitoring.events.PY_RETURN, on_return)
    return ID

def trace(func):
    """追踪装饰器"""
    def inner(*args, **kwargs):
        ID = setup_monitor()
        monitoring.set_local_events(ID, func.__code__, 
                                   monitoring.events.PY_START|monitoring.events.PY_RETURN)
        result = func(*args, **kwargs)
        monitoring.free_tool_id(ID)
        return result
    return inner

# 测试函数1: 斐波那契数列
@trace
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 测试函数2: 阶乘
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

# 测试函数3: 累加
def sum_n(n):
    if n <= 0:
        return 0
    return n + sum_n(n-1)

def main():
    """主函数"""
    print("代码监控示例")
    print("=" * 40)
    
    # 监控斐波那契函数
    print("1. 监控 fibonacci(4):")
    result = fibonacci(4)
    print(f"   结果: {result}")
    
    print("\n" + "=" * 40)
    
    # 设置全局监控测试阶乘函数
    print("2. 全局监控 factorial(3):")
    ID = setup_monitor()
    monitoring.set_events(ID, monitoring.events.PY_START|monitoring.events.PY_RETURN)
    result = factorial(3)
    monitoring.set_events(ID, 0)
    monitoring.free_tool_id(ID)
    print(f"   结果: {result}")
    
    print("\n" + "=" * 40)
    
    # 测试累加函数
    print("3. 监控 sum_n(3):")
    ID = setup_monitor()
    monitoring.set_local_events(ID, sum_n.__code__, 
                               monitoring.events.PY_START|monitoring.events.PY_RETURN)
    result = sum_n(3)
    monitoring.free_tool_id(ID)
    print(f"   结果: {result}")
    
    print("\n" + "=" * 40)
    print("函数调用统计:")
    for func, count in call_count.items():
        print(f"  {func}: {count}次")

if __name__ == "__main__":
    main()