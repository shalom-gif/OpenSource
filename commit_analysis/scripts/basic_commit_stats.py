"""
基本提交统计脚本
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

print(" 基本提交统计分析")
print("=" * 50)

# 获取当前脚本的绝对路径
current_dir = Path(__file__).parent.absolute()
print(f"当前脚本位置：{current_dir}")

# 确定OpenSource目录（脚本所在目录的父目录的父目录）
opensource_dir = current_dir.parent.parent
print(f"OpenSource目录：{opensource_dir}")

# Flask应该就在OpenSource目录下
flask_dir = opensource_dir / "flask"
print(f"预期Flask位置：{flask_dir}")

# 检查目录是否存在
if not flask_dir.exists():
    print(f" 找不到Flask目录，请确认：")
    print(f"   1. 是否在OpenSource目录下克隆了Flask？")
    print(f"   2. 克隆命令：git clone https://github.com/pallets/flask.git")
    print(f"   3. 应该在 {opensource_dir} 目录执行克隆")
    sys.exit(1)

print("\n 检查Flask目录内容：")
os.chdir(flask_dir)  # 切换到Flask目录
result = subprocess.run(["dir"], shell=True, capture_output=True, text=True)
print(result.stdout[:500])  # 显示前500字符

# 检查关键文件
print("\n 检查关键文件：")
check_files = [".git"]
for file in check_files:
    if (flask_dir / file).exists():
        print(f"  ✅ {file} 存在")
    else:
        print(f"  ❌ {file} 缺失")

# 获取提交信息
print("\n 获取提交信息...")
try:
    # 总提交数
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    total_commits = result.stdout.strip()
    
    # 最早提交
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%ad", "--date=short"],
        capture_output=True,
        text=True,
        check=True
    )
    first_date = result.stdout.strip().split('\n')[0] if result.stdout else "未知"
    
    # 最新提交
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short"],
        capture_output=True,
        text=True,
        check=True
    )
    last_date = result.stdout.strip()
    
    print(f"\n Flask仓库统计：")
    print(f"   总提交数：{total_commits}")
    print(f"   最早提交：{first_date}")
    print(f"   最新提交：{last_date}")
    
    # 保存报告
    report_dir = opensource_dir / "commit_analysis" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / "basic_commit_stats_report.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Flask基本提交统计报告\n\n")
        f.write("## 统计信息\n\n")
        f.write(f"- **统计时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **仓库位置**：{flask_dir}\n")
        f.write(f"- **总提交数**：{total_commits} 次提交\n")
        f.write(f"- **最早提交**：{first_date}\n")
        f.write(f"- **最近提交**：{last_date}\n")
        
        if first_date and last_date and first_date != "未知":
            try:
                from datetime import datetime as dt
                start = dt.strptime(first_date, "%Y-%m-%d")
                end = dt.strptime(last_date, "%Y-%m-%d")
                days = (end - start).days
                years = days / 365.25
                f.write(f"- **时间跨度**：{days} 天（约 {years:.1f} 年）\n")
            except ValueError:
                f.write(f"- **时间跨度**：无法计算\n")
        
    
    
    print(f"\n 报告已保存：{report_file}")
    
except subprocess.CalledProcessError as e:
    print(f" Git命令执行失败：{e}")
    print(f"   错误信息：{e.stderr}")
except Exception as e:
    print(f" 发生错误：{e}")

print("\n" + "=" * 50)
print(" 基本提交统计完成！")