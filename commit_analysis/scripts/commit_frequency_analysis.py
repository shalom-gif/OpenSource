"""
提交频率分析 - 分析Flask项目的提交时间分布规律
"""
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 使用英文字体，避免中文字体警告
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = True

def get_commit_data():
    """获取Flask项目的提交数据"""
    print(" 开始获取Flask提交数据...")
    
    # 确保在flask子目录中执行git命令
    flask_path = Path(__file__).parent.parent.parent / "flask"
    
    # 获取所有提交的日期和作者
    result = subprocess.run(
        ["git", "-C", str(flask_path), "log", "--pretty=format:%ad|%an", "--date=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(" 无法获取git提交数据")
        return None
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) == 2:
                date_str, author = parts
                commits.append({
                    'date': date_str,
                    'author': author,
                    'year': int(date_str.split('-')[0]),
                    'month': int(date_str.split('-')[1]),
                    'day': int(date_str.split('-')[2]) if len(date_str.split('-')) > 2 else 1
                })
    
    print(f" 获取到 {len(commits)} 条提交记录")
    return commits

def analyze_time_distribution(commits):
    """分析时间分布"""
    print("\n 分析提交时间分布...")
    
    df = pd.DataFrame(commits)
    df['date'] = pd.to_datetime(df['date'])
    

    yearly = df['year'].value_counts().sort_index()
    monthly = df['month'].value_counts().sort_index()
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    year_month_counts = df['year_month'].value_counts().sort_index()
    df['weekday'] = df['date'].dt.day_name()
    weekday_counts = df['weekday'].value_counts()
    
    return {
        'yearly': yearly,
        'monthly': monthly,
        'year_month': year_month_counts,
        'weekday': weekday_counts,
        'dataframe': df
    }

def save_analysis_results(stats, output_dir):
    """保存分析结果"""
    # 确保输出目录存在
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存统计数据
    stats['yearly'].to_csv(output_dir / 'yearly_commits.csv', header=['count'])
    stats['monthly'].to_csv(output_dir / 'monthly_commits.csv', header=['count'])
    stats['year_month'].to_csv(output_dir / 'year_month_commits.csv', header=['count'])
    stats['weekday'].to_csv(output_dir / 'weekday_commits.csv', header=['count'])
    
    # 保存原始数据（抽样，避免文件太大）
    stats['dataframe'].head(1000).to_csv(output_dir / 'sample_commits.csv', index=False)
    
    print(f" 数据已保存到 {output_dir}")

def create_visualizations(stats, figures_dir):
    """创建可视化图表"""
    # 确保图表目录存在
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置图表样式
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. 年度提交趋势图（英文标题）
    plt.figure(figsize=(14, 6))
    plt.bar(stats['yearly'].index.astype(str), stats['yearly'].values, color='skyblue', alpha=0.8)
    plt.title('Flask Project Annual Commit Trend (2010-2025)', fontsize=16, fontweight='bold')
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Commit Count', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, v in enumerate(stats['yearly'].values):
        plt.text(i, v + max(stats['yearly'].values)*0.01, str(v), 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'yearly_commit_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. 月度提交分布图（英文标题）
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    plt.figure(figsize=(12, 6))
    plt.bar(month_names, stats['monthly'].loc[range(1, 13)], color='lightcoral', alpha=0.8)
    plt.title('Flask Project Monthly Commit Distribution (All Years)', fontsize=16, fontweight='bold')
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Commit Count', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'monthly_commit_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. 最近36个月的详细趋势（英文标题）
    recent_data = stats['year_month'].tail(36)
    
    plt.figure(figsize=(16, 6))
    plt.plot(range(len(recent_data)), recent_data.values, 
             marker='o', linewidth=2, markersize=4, color='green', alpha=0.7)
    plt.title('Flask Project Monthly Commit Trend (Last 3 Years)', fontsize=16, fontweight='bold')
    plt.xlabel('Time Series', fontsize=12)
    plt.ylabel('Commit Count', fontsize=12)
    plt.xticks(range(len(recent_data)), recent_data.index, rotation=45, fontsize=9)
    plt.grid(alpha=0.3)
    
    # 标记最高点
    max_idx = recent_data.values.argmax()
    max_val = recent_data.values[max_idx]
    max_date = recent_data.index[max_idx]
    plt.annotate(f'Peak: {max_val}\n{max_date}', 
                xy=(max_idx, max_val),
                xytext=(max_idx, max_val + max_val*0.15),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                ha='center', color='red', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'recent_36months_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 4. 星期几提交分布
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_data = stats['weekday'].reindex(weekday_order)
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.Set3(range(len(weekday_data)))
    plt.bar(weekday_data.index, weekday_data.values, color=colors, alpha=0.8)
    plt.title('Flask Project Weekday Commit Distribution', fontsize=16, fontweight='bold')
    plt.xlabel('Weekday', fontsize=12)
    plt.ylabel('Commit Count', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'weekday_commit_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f" 图表已保存到 {figures_dir}")

def generate_report(stats, report_dir):
    """生成分析报告（自动生成分析结论）"""
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / 'commit_frequency_report.md'
    
    # 计算更多统计信息用于分析结论
    df = stats['dataframe']
    total_commits = len(df)
    
    # 计算最近3年趋势
    current_year = datetime.now().year
    recent_years = [current_year-2, current_year-1, current_year]
    recent_commits = df[df['year'].isin(recent_years)].shape[0]
    older_commits = df[~df['year'].isin(recent_years)].shape[0]
    
    # 计算年度变化率
    years = sorted(stats['yearly'].index.tolist())
    if len(years) >= 2:
        recent_trend = stats['yearly'].tail(3)
        if len(recent_trend) >= 2:
            growth_rate = ((recent_trend.iloc[-1] - recent_trend.iloc[0]) / 
                         recent_trend.iloc[0] * 100)
        else:
            growth_rate = 0
    else:
        growth_rate = 0
    
    # 计算季节分布
    seasonal_pattern = ""
    quarter_counts = {
        'Q1 (1-3月)': df[df['month'].isin([1,2,3])].shape[0],
        'Q2 (4-6月)': df[df['month'].isin([4,5,6])].shape[0],
        'Q3 (7-9月)': df[df['month'].isin([7,8,9])].shape[0],
        'Q4 (10-12月)': df[df['month'].isin([10,11,12])].shape[0]
    }
    busiest_quarter = max(quarter_counts, key=quarter_counts.get)
    
    # 计算工作模式
    weekday_counts = stats['weekday']
    weekend_days = ['Saturday', 'Sunday']
    weekend_commits = sum(weekday_counts.get(day, 0) for day in weekend_days)
    weekday_commits = total_commits - weekend_commits
    weekend_ratio = weekend_commits / total_commits * 100 if total_commits > 0 else 0
    
    # 计算项目阶段
    project_age_years = stats['yearly'].index.max() - stats['yearly'].index.min() + 1
    if project_age_years < 3:
        stage = "初期阶段"
    elif growth_rate > 10:
        stage = "快速发展期"
    elif abs(growth_rate) <= 10:
        stage = "稳定维护期"
    else:
        stage = "成熟稳定期"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# Flask项目提交频率分析报告\n\n')
        f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        
        f.write('##  关键统计\n\n')
        f.write(f'- **总提交数**: {total_commits:,}\n')
        f.write(f'- **时间跨度**: {df["date"].min().year}年 - {df["date"].max().year}年\n')
        f.write(f'- **涉及作者数**: {df["author"].nunique()}\n')
        f.write(f'- **项目年龄**: {project_age_years}年\n\n')
        
        f.write('##  年度提交趋势\n\n')
        f.write('| 年份 | 提交数 | 占比 |\n')
        f.write('|------|--------|------|\n')
        for year, count in stats['yearly'].items():
            percentage = (count / total_commits) * 100
            f.write(f'| {year} | {count:,} | {percentage:.1f}% |\n')
        
        f.write(f'\n**最活跃年份**: {stats["yearly"].idxmax()}年 ({stats["yearly"].max():,}次提交，占比{stats["yearly"].max()/total_commits*100:.1f}%)\n')
        f.write(f'**最不活跃年份**: {stats["yearly"].idxmin()}年 ({stats["yearly"].min():,}次提交)\n')
        if growth_rate != 0:
            trend = "增长" if growth_rate > 0 else "下降"
            f.write(f'**近期趋势**: 最近3年活跃度{trend}{abs(growth_rate):.1f}%\n\n')
        
        f.write('##  月度分布\n\n')
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月', 
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        
        f.write('| 月份 | 提交数 | 占比 |\n')
        f.write('|------|--------|------|\n')
        for month_num in range(1, 13):
            count = stats['monthly'].get(month_num, 0)
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            f.write(f'| {month_names[month_num-1]} | {count:,} | {percentage:.1f}% |\n')
        
        f.write(f'\n**提交最多的月份**: {month_names[stats["monthly"].idxmax()-1]} ({stats["monthly"].max():,}次，占比{stats["monthly"].max()/total_commits*100:.1f}%)\n')
        f.write(f'**提交最少的月份**: {month_names[stats["monthly"].idxmin()-1]} ({stats["monthly"].min():,}次)\n')
        
        f.write('\n##  自动生成的分析结论\n\n')
        
        # 1. 开发活跃度趋势
        f.write('### 1. 开发活跃度趋势\n')
        if stats['yearly'].idxmax() == stats['yearly'].index.min():
            f.write('Flask项目在初始年份（{}年）最为活跃，共提交了{}次，占总提交数的{:.1f}%。随后活跃度有所波动，这符合开源项目的一般发展规律。\n'.format(
                stats['yearly'].idxmax(), stats['yearly'].max(), stats['yearly'].max()/total_commits*100))
        elif stats['yearly'].idxmax() == stats['yearly'].index.max():
            f.write('Flask项目在最近一年（{}年）最为活跃，共提交了{}次，占总提交数的{:.1f}%，表明项目仍然在积极维护和开发中。\n'.format(
                stats['yearly'].idxmax(), stats['yearly'].max(), stats['yearly'].max()/total_commits*100))
        else:
            f.write('Flask项目在{}年达到活跃度峰值，共提交了{}次，占总提交数的{:.1f}%。项目经历了从启动到成熟的过程。\n'.format(
                stats['yearly'].idxmax(), stats['yearly'].max(), stats['yearly'].max()/total_commits*100))
        
        # 2. 季节性规律
        f.write('\n### 2. 季节性规律\n')
        f.write('从月度分布来看，提交最活跃的月份是{}月（{}次提交，占比{:.1f}%）。这可能与以下因素有关：\n'.format(
            stats['monthly'].idxmax(), stats['monthly'].max(), stats['monthly'].max()/total_commits*100))
        f.write('- **季度分布**: {}的提交最多，共{}次（占比{:.1f}%），表明开发活动在该季度最为集中。\n'.format(
            busiest_quarter, quarter_counts[busiest_quarter], quarter_counts[busiest_quarter]/total_commits*100))
        f.write('- **月份对比**: 提交最多的月份（{}月）比最少的月份（{}月）多{:,}次提交，差异明显。\n'.format(
            stats['monthly'].idxmax(), stats['monthly'].idxmin(), 
            stats['monthly'].max() - stats['monthly'].min()))
        
        # 3. 开发节奏
        f.write('\n### 3. 开发节奏\n')
        f.write('提交最多的工作日是{}（{}次提交，占比{:.1f}%）。\n'.format(
            stats['weekday'].idxmax(), stats['weekday'].max(), stats['weekday'].max()/total_commits*100))
        f.write('- **工作日 vs 周末**: 工作日提交占{:.1f}%，周末提交占{:.1f}%。\n'.format(
            weekday_commits/total_commits*100, weekend_ratio))
        if weekend_ratio < 10:
            f.write('- **工作模式**: 周末提交较少（<10%），表明大部分开发者在正常工作时间内贡献代码。\n')
        elif weekend_ratio > 20:
            f.write('- **工作模式**: 周末提交较多（>20%），表明社区包含大量业余时间贡献者。\n')
        else:
            f.write('- **工作模式**: 周末提交适中，表明项目同时有专业开发者和业余贡献者参与。\n')
        
        # 4. 近期趋势
        f.write('\n### 4. 近期趋势\n')
        f.write('最近3年（{}、{}、{}年）共提交了{}次，占总提交数的{:.1f}%。\n'.format(
            *recent_years, recent_commits, recent_commits/total_commits*100))
        
        if growth_rate > 5:
            f.write('- **趋势判断**: 项目处于**上升期**，最近3年提交活跃度增长{:.1f}%，表明项目仍在快速发展。\n'.format(growth_rate))
        elif abs(growth_rate) <= 5:
            f.write('- **趋势判断**: 项目处于**稳定期**，提交频率保持相对稳定（变化率{:.1f}%），表明项目已进入成熟维护阶段。\n'.format(growth_rate))
        else:
            f.write('- **趋势判断**: 项目处于**调整期**，最近3年提交活跃度下降{:.1f}%，可能是项目已相对成熟或开发重点转移。\n'.format(abs(growth_rate)))
        
        f.write('- **项目阶段**: 基于{}年的发展历程和当前提交频率，项目处于**{}**。\n'.format(project_age_years, stage))
        
        f.write('\n##  生成文件\n\n')
        f.write('### 数据文件\n')
        f.write('- `commit_analysis/data/yearly_commits.csv` - 年度提交统计\n')
        f.write('- `commit_analysis/data/monthly_commits.csv` - 月度提交统计\n')
        f.write('- `commit_analysis/data/year_month_commits.csv` - 年月提交统计\n')
        f.write('- `commit_analysis/data/weekday_commits.csv` - 星期几提交统计\n')
        
        f.write('\n### 图表文件\n')
        f.write('- `commit_analysis/figures/yearly_commit_trend.png` - 年度提交趋势图\n')
        f.write('- `commit_analysis/figures/monthly_commit_distribution.png` - 月度分布图\n')
        f.write('- `commit_analysis/figures/recent_36months_trend.png` - 最近36个月趋势\n')
        f.write('- `commit_analysis/figures/weekday_commit_distribution.png` - 星期几分布图\n')
    
    print(f" 报告已生成: {report_file}")

def main():
    """主函数"""
    print("=" * 60)
    print(" Flask项目提交频率分析")
    print("=" * 60)
    
    # 1. 获取提交数据
    commits = get_commit_data()
    if not commits:
        return
    
    # 2. 分析时间分布
    stats = analyze_time_distribution(commits)
    
    # 3. 保存分析结果
    project_root = Path(__file__).parent.parent.parent
    save_analysis_results(stats, project_root / "commit_analysis" / "data")
    
    # 4. 创建可视化图表
    create_visualizations(stats, project_root / "commit_analysis" / "figures")
    
    # 5. 生成报告
    generate_report(stats, project_root / "commit_analysis" / "reports")
    
    # 6. 显示关键发现
    print("\n" + "=" * 60)
    print(" 关键发现")
    print("=" * 60)
    print(f" 时间跨度: {stats['dataframe']['date'].min().year} - {stats['dataframe']['date'].max().year}")
    print(f" 总提交数: {len(stats['dataframe']):,}")
    print(f" 涉及作者: {stats['dataframe']['author'].nunique()} 人")
    print(f" 最活跃年份: {stats['yearly'].idxmax()}年 ({stats['yearly'].max():,}次提交)")
    print(f" 提交最多月份: {stats['monthly'].idxmax()}月 ({stats['monthly'].max():,}次提交)")
    print(f" 提交最多星期: {stats['weekday'].idxmax()} ({stats['weekday'].max():,}次提交)")
    
    # 计算最近3年趋势
    current_year = datetime.now().year
    recent_years = [current_year-2, current_year-1, current_year]
    recent_commits = stats['dataframe'][stats['dataframe']['year'].isin(recent_years)].shape[0]
    print(f" 最近3年提交数: {recent_commits:,} ({recent_commits/len(stats['dataframe'])*100:.1f}%)")
    


if __name__ == "__main__":
    # 检查必要的库
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError:
        print(" 缺少必要的库，请先安装:")
        print("   pip install pandas matplotlib seaborn")
        exit(1)
    
    main()
    
    # 防止窗口立即关闭
    input("\n按回车键退出...")