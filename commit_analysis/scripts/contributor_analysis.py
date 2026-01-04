"""
贡献者活跃度分析 - 分析Flask项目的贡献者参与模式和活跃度
"""
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# 使用英文字体，避免中文字体警告
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = True

def get_contributor_data():
    """获取贡献者提交数据"""
    print("获取贡献者数据...")
    
    # 确保在flask子目录中执行git命令
    flask_path = Path(__file__).parent.parent.parent / "flask"
    
    # 获取所有提交的作者和日期
    result = subprocess.run(
        ["git", "-C", str(flask_path), "log", "--pretty=format:%an|%ad", "--date=short"],
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
                author, date_str = parts
                commits.append({
                    'author': author.strip(),
                    'date': date_str,
                    'year': int(date_str.split('-')[0]),
                    'month': int(date_str.split('-')[1]),
                    'day': int(date_str.split('-')[2]) if len(date_str.split('-')) > 2 else 1
                })
    
    print(f" 获取到 {len(commits)} 条提交记录")
    return commits

def analyze_contributor_stats(commits):
    """分析贡献者统计信息"""
    print("\n 分析贡献者统计...")
    
    df = pd.DataFrame(commits)
    df['date'] = pd.to_datetime(df['date'])
    
    # 按作者分组分析
    author_stats = df.groupby('author').agg({
        'date': ['min', 'max', 'count'],
        'year': 'nunique'
    })
    
    # 重命名列
    author_stats.columns = ['first_commit', 'last_commit', 'commit_count', 'active_years']
    author_stats = author_stats.sort_values('commit_count', ascending=False).reset_index()
    
    # 计算活跃天数
    author_stats['active_days'] = (author_stats['last_commit'] - author_stats['first_commit']).dt.days
    author_stats['active_days'] = author_stats['active_days'].apply(lambda x: max(0, x))
    
    # 计算每月平均提交数
    author_stats['monthly_avg'] = author_stats['commit_count'] / author_stats['active_days'] * 30
    author_stats['monthly_avg'] = author_stats['monthly_avg'].fillna(0)
    
    # 计算贡献者排名百分比
    total_commits = author_stats['commit_count'].sum()
    author_stats['commit_percentage'] = author_stats['commit_count'] / total_commits * 100
    author_stats['cumulative_percentage'] = author_stats['commit_percentage'].cumsum()
    
    # 计算贡献者分类
    author_stats['contributor_type'] = author_stats.apply(classify_contributor, axis=1)
    
    return author_stats, df

def classify_contributor(row):
    """根据提交数和活跃时间分类贡献者"""
    commit_count = row['commit_count']
    active_days = row['active_days']
    
    if commit_count >= 100 and active_days >= 365:
        return 'Core Contributor'
    elif commit_count >= 50:
        return 'Active Contributor'
    elif commit_count >= 10:
        return 'Regular Contributor'
    elif commit_count >= 2:
        return 'Occasional Contributor'
    else:
        return 'One-time Contributor'

def analyze_contribution_patterns(author_stats, df):
    """分析贡献模式"""
    print(" 分析贡献模式...")
    
    patterns = {}
    
    # 1. 贡献集中度分析
    total_authors = len(author_stats)
    top_10_percent = int(total_authors * 0.1)
    top_10_percent_commits = author_stats.head(top_10_percent)['commit_count'].sum()
    total_commits = author_stats['commit_count'].sum()
    
    patterns['total_commits'] = total_commits
    patterns['total_authors'] = total_authors
    patterns['top_10_percent_contribution'] = top_10_percent_commits / total_commits * 100
    
    # 2. 帕累托分析（80/20法则）
    for threshold in [20, 30, 50]:
        # 计算前threshold%的贡献者提交数占比
        threshold_index = int(total_authors * threshold / 100)
        if threshold_index > 0:
            threshold_commits = author_stats.head(threshold_index)['commit_count'].sum()
            patterns[f'top_{threshold}_percent_commits'] = threshold_commits / total_commits * 100
        else:
            patterns[f'top_{threshold}_percent_commits'] = 0
    
    # 3. 贡献者留存分析
    current_year = datetime.now().year
    retention_data = {}
    
    for year in range(df['year'].min(), current_year + 1):
        year_authors = set(df[df['year'] == year]['author'].unique())
        if year_authors:
            # 计算第二年是否继续贡献
            if year + 1 <= current_year:
                next_year_authors = set(df[df['year'] == year + 1]['author'].unique())
                if year_authors:  # 避免除以0
                    retention_rate = len(year_authors & next_year_authors) / len(year_authors) * 100
                    retention_data[year] = retention_rate
    
    patterns['retention_rates'] = retention_data
    
    # 4. 新贡献者分析
    yearly_new_authors = {}
    all_authors = set()
    
    for year in sorted(df['year'].unique()):
        year_authors = set(df[df['year'] == year]['author'].unique())
        new_authors = year_authors - all_authors
        yearly_new_authors[year] = len(new_authors)
        all_authors.update(new_authors)
    
    patterns['yearly_new_authors'] = yearly_new_authors
    patterns['total_unique_authors'] = len(all_authors)
    
    # 5. 活跃贡献者趋势
    yearly_active_authors = {}
    for year in sorted(df['year'].unique()):
        active_count = df[df['year'] == year]['author'].nunique()
        yearly_active_authors[year] = active_count
    
    patterns['yearly_active_authors'] = yearly_active_authors
    
    return patterns

def save_analysis_results(author_stats, patterns, output_dir):
    """保存分析结果"""
    # 确保输出目录存在
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存贡献者统计数据
    author_stats.to_csv(output_dir / 'contributor_stats.csv', index=False)
    
    # 保存前100名贡献者
    top_100 = author_stats.head(100)
    top_100.to_csv(output_dir / 'top_100_contributors.csv', index=False)
    
    # 保存贡献模式数据（排除不能序列化的字典）
    patterns_serializable = {}
    for key, value in patterns.items():
        if isinstance(value, dict):
            # 将字典转换为字符串以便保存
            patterns_serializable[key] = str(value)
        else:
            patterns_serializable[key] = value
    
    patterns_df = pd.DataFrame([patterns_serializable])
    patterns_df.to_csv(output_dir / 'contribution_patterns.csv', index=False)
    
    # 保存年度新贡献者数据
    if 'yearly_new_authors' in patterns:
        yearly_new_df = pd.DataFrame(list(patterns['yearly_new_authors'].items()), 
                                    columns=['year', 'new_authors'])
        yearly_new_df.to_csv(output_dir / 'yearly_new_contributors.csv', index=False)
    
    # 保存年度活跃贡献者数据
    if 'yearly_active_authors' in patterns:
        yearly_active_df = pd.DataFrame(list(patterns['yearly_active_authors'].items()), 
                                       columns=['year', 'active_authors'])
        yearly_active_df.to_csv(output_dir / 'yearly_active_contributors.csv', index=False)
    
    # 保存留存率数据
    if 'retention_rates' in patterns and patterns['retention_rates']:
        retention_df = pd.DataFrame(list(patterns['retention_rates'].items()), 
                                   columns=['year', 'retention_rate'])
        retention_df.to_csv(output_dir / 'retention_rates.csv', index=False)
    
    print(f" 贡献者数据已保存到 {output_dir}")

def create_visualizations(author_stats, patterns, figures_dir):
    """创建可视化图表"""
    # 确保图表目录存在
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置图表样式
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 获取总提交数
    total_commits = author_stats['commit_count'].sum()
    
    # 1. 前20名贡献者提交数柱状图
    plt.figure(figsize=(14, 8))
    top_20 = author_stats.head(20)
    
    # 缩短长名字
    short_names = [name if len(name) <= 20 else name[:17] + '...' for name in top_20['author']]
    
    bars = plt.bar(range(len(top_20)), top_20['commit_count'], color='steelblue', alpha=0.8)
    plt.title('Top 20 Contributors by Commit Count', fontsize=16, fontweight='bold')
    plt.xlabel('Contributor', fontsize=12)
    plt.ylabel('Commit Count', fontsize=12)
    plt.xticks(range(len(top_20)), short_names, rotation=45, ha='right', fontsize=10)
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (bar, count) in enumerate(zip(bars, top_20['commit_count'])):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(top_20['commit_count'])*0.01,
                f'{count:,}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'top_20_contributors.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. 贡献者类型分布饼图
    plt.figure(figsize=(10, 8))
    type_counts = author_stats['contributor_type'].value_counts()
    
    colors = plt.cm.Set3(range(len(type_counts)))
    wedges, texts, autotexts = plt.pie(type_counts.values, labels=type_counts.index, 
                                       autopct='%1.1f%%', colors=colors, startangle=90,
                                       textprops={'fontsize': 11})
    
    plt.title('Contributor Type Distribution', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(figures_dir / 'contributor_type_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. 贡献集中度帕累托图
    plt.figure(figsize=(12, 6))
    
    # 计算累积百分比
    author_stats_sorted = author_stats.sort_values('commit_count', ascending=False).reset_index()
    author_stats_sorted['cumulative_percentage'] = author_stats_sorted['commit_count'].cumsum() / total_commits * 100
    author_stats_sorted['percentage_of_contributors'] = (author_stats_sorted.index + 1) / len(author_stats_sorted) * 100
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # 贡献者百分比 vs 提交百分比
    ax1.plot(author_stats_sorted['percentage_of_contributors'], 
             author_stats_sorted['cumulative_percentage'], 
             color='blue', linewidth=2, label='Cumulative Commits %')
    
    # 添加80/20参考线
    ax1.plot([0, 100], [0, 100], '--', color='gray', alpha=0.5, label='Linear (Equal Distribution)')
    ax1.axvline(x=20, color='red', linestyle='--', alpha=0.7, label='20% of Contributors')
    ax1.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='80% of Commits')
    
    ax1.set_xlabel('Percentage of Contributors (%)', fontsize=12)
    ax1.set_ylabel('Percentage of Commits (%)', fontsize=12)
    ax1.set_title('Pareto Chart: Contribution Concentration', fontsize=16, fontweight='bold')
    ax1.grid(alpha=0.3)
    ax1.legend()
    
    # 添加实际数值标注
    for threshold in [10, 20, 30, 50]:
        idx = int(len(author_stats_sorted) * threshold / 100) - 1
        if idx >= 0 and idx < len(author_stats_sorted):
            x_val = author_stats_sorted.iloc[idx]['percentage_of_contributors']
            y_val = author_stats_sorted.iloc[idx]['cumulative_percentage']
            ax1.annotate(f'{threshold}% contributors\n{y_val:.1f}% commits', 
                        xy=(x_val, y_val), xytext=(x_val+5, y_val-5),
                        arrowprops=dict(arrowstyle='->', color='green'),
                        fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'contribution_concentration.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 4. 年度新贡献者趋势
    if 'yearly_new_authors' in patterns:
        plt.figure(figsize=(14, 6))
        
        yearly_new = patterns['yearly_new_authors']
        years = list(yearly_new.keys())
        new_authors = list(yearly_new.values())
        
        bars = plt.bar(years, new_authors, color='lightgreen', alpha=0.7)
        plt.plot(years, new_authors, color='darkgreen', linewidth=2, marker='o', markersize=5)
        
        plt.title('New Contributors Per Year', fontsize=16, fontweight='bold')
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of New Contributors', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        
        # 添加数值标签
        for i, (year, count) in enumerate(zip(years, new_authors)):
            if count > 0:
                plt.text(i, count + max(new_authors)*0.02, str(count), 
                        ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(figures_dir / 'yearly_new_contributors.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    # 5. 贡献者活跃时长分布
    plt.figure(figsize=(12, 6))
    
    # 过滤掉一次性贡献者
    active_authors = author_stats[author_stats['active_days'] > 0]
    
    # 分组
    bins = [0, 30, 365, 365*3, 365*5, 365*10, active_authors['active_days'].max()]
    labels = ['<1 month', '1-12 months', '1-3 years', '3-5 years', '5-10 years', '>10 years']
    
    active_authors['active_period'] = pd.cut(active_authors['active_days'], bins=bins, labels=labels)
    period_counts = active_authors['active_period'].value_counts()
    
    plt.bar(period_counts.index.astype(str), period_counts.values, color='orange', alpha=0.7)
    plt.title('Contributor Activity Duration Distribution', fontsize=16, fontweight='bold')
    plt.xlabel('Activity Duration', fontsize=12)
    plt.ylabel('Number of Contributors', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (period, count) in enumerate(zip(period_counts.index, period_counts.values)):
        plt.text(i, count + max(period_counts.values)*0.01, str(count), 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(figures_dir / 'contributor_activity_duration.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 6. 年度活跃贡献者趋势
    if 'yearly_active_authors' in patterns:
        plt.figure(figsize=(14, 6))
        
        yearly_active = patterns['yearly_active_authors']
        years = list(yearly_active.keys())
        active_counts = list(yearly_active.values())
        
        plt.plot(years, active_counts, color='blue', linewidth=2, marker='o', markersize=5)
        plt.fill_between(years, active_counts, color='blue', alpha=0.2)
        
        plt.title('Active Contributors Per Year', fontsize=16, fontweight='bold')
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of Active Contributors', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(figures_dir / 'yearly_active_contributors.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    print(f" 贡献者图表已保存到 {figures_dir}")

def generate_report(author_stats, patterns, report_dir):
    """生成贡献者分析报告"""
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / 'contributor_analysis_report.md'
    
    # 计算关键指标
    total_authors = len(author_stats)
    total_commits = author_stats['commit_count'].sum()
    avg_commits_per_author = total_commits / total_authors if total_authors > 0 else 0
    
    # 核心贡献者统计
    core_contributors = author_stats[author_stats['contributor_type'] == 'Core Contributor']
    active_contributors = author_stats[author_stats['contributor_type'] == 'Active Contributor']
    regular_contributors = author_stats[author_stats['contributor_type'] == 'Regular Contributor']
    
    # 计算贡献集中度
    top_10_authors = author_stats.head(10)
    top_10_commits = top_10_authors['commit_count'].sum()
    top_10_percentage = top_10_commits / total_commits * 100
    
    top_20_authors = author_stats.head(20)
    top_20_commits = top_20_authors['commit_count'].sum()
    top_20_percentage = top_20_commits / total_commits * 100
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# Flask项目贡献者活跃度分析报告\n\n')
        f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        
        f.write('##  贡献者总体统计\n\n')
        f.write(f'- **总贡献者数**: {total_authors:,} 人\n')
        f.write(f'- **总提交数**: {total_commits:,} 次\n')
        f.write(f'- **平均每人提交数**: {avg_commits_per_author:.1f} 次\n')
        f.write(f'- **项目持续时间**: {author_stats["active_days"].max() // 365} 年\n\n')
        
        f.write('##  核心贡献者统计\n\n')
        f.write(f'- **核心贡献者** (≥100次提交且活跃≥1年): {len(core_contributors)} 人\n')
        f.write(f'- **活跃贡献者** (≥50次提交): {len(active_contributors)} 人\n')
        f.write(f'- **常规贡献者** (≥10次提交): {len(regular_contributors)} 人\n')
        f.write(f'- **一次性贡献者** (1次提交): {len(author_stats[author_stats["commit_count"] == 1])} 人\n\n')
        
        f.write('##  贡献集中度分析\n\n')
        f.write('| 指标 | 数值 | 说明 |\n')
        f.write('|------|------|------|\n')
        f.write(f'| 前10名贡献者提交占比 | {top_10_percentage:.1f}% | 前10人贡献了{top_10_commits:,}次提交 |\n')
        f.write(f'| 前20名贡献者提交占比 | {top_20_percentage:.1f}% | 前20人贡献了{top_20_commits:,}次提交 |\n')
        f.write(f'| 帕累托法则 (80/20) | {patterns.get("top_20_percent_commits", 0):.1f}% | 前20%贡献者的提交占比 |\n')
        f.write(f'| 帕累托法则 (70/30) | {patterns.get("top_30_percent_commits", 0):.1f}% | 前30%贡献者的提交占比 |\n\n')
        
        f.write('### 前10名贡献者\n\n')
        f.write('| 排名 | 贡献者 | 提交数 | 占比 | 首次提交 | 最后提交 | 活跃天数 | 类型 |\n')
        f.write('|------|--------|--------|------|----------|----------|----------|------|\n')
        
        for i, (_, row) in enumerate(top_10_authors.iterrows(), 1):
            first_date = row['first_commit'].strftime('%Y-%m-%d') if not pd.isna(row['first_commit']) else 'N/A'
            last_date = row['last_commit'].strftime('%Y-%m-%d') if not pd.isna(row['last_commit']) else 'N/A'
            f.write(f'| {i} | {row["author"]} | {row["commit_count"]:,} | {row["commit_percentage"]:.1f}% | {first_date} | {last_date} | {row["active_days"]} | {row["contributor_type"]} |\n')
        
        f.write('\n##  贡献者增长趋势\n\n')
        
        # 年度新贡献者分析
        if 'yearly_new_authors' in patterns:
            yearly_new = patterns['yearly_new_authors']
            years = sorted(yearly_new.keys())
            
            f.write('| 年份 | 新贡献者数 | 累计贡献者数 |\n')
            f.write('|------|------------|--------------|\n')
            
            cumulative = 0
            for year in years:
                new_authors = yearly_new[year]
                cumulative += new_authors
                f.write(f'| {year} | {new_authors} | {cumulative} |\n')
            
            # 分析新贡献者趋势
            if len(years) >= 3:
                recent_new = [yearly_new[y] for y in years[-3:]]
                avg_recent_new = sum(recent_new) / len(recent_new)
                
                f.write(f'\n**趋势分析**: \n')
                f.write(f'- 最近3年平均每年新增贡献者: {avg_recent_new:.1f}人\n')
                if avg_recent_new > 20:
                    f.write('- **社区吸引力强**: 每年有大量新贡献者加入\n')
                elif avg_recent_new > 10:
                    f.write('- **社区活跃**: 保持稳定的新贡献者流入\n')
                else:
                    f.write('- **社区稳定**: 新贡献者增长平稳\n')
        
        f.write('\n##  贡献者参与模式分析\n\n')
        
        # 贡献者留存率分析
        if 'retention_rates' in patterns and patterns['retention_rates']:
            retention_years = list(patterns['retention_rates'].keys())
            retention_values = list(patterns['retention_rates'].values())
            
            if len(retention_years) >= 3:
                recent_retention = sum(retention_values[-3:]) / 3
                f.write(f'- **平均留存率**: 最近3年平均留存率为{recent_retention:.1f}%\n')
                
                if recent_retention > 50:
                    f.write('  - **留存率高**: 超过一半的贡献者会继续贡献，社区粘性强\n')
                elif recent_retention > 30:
                    f.write('  - **留存率中等**: 约三分之一贡献者会继续贡献\n')
                else:
                    f.write('  - **留存率较低**: 多数贡献者只贡献一次，社区需要更多激励措施\n')
        
        # 贡献者活跃时长分析
        active_authors = author_stats[author_stats['active_days'] > 0]
        if len(active_authors) > 0:
            active_days_stats = active_authors['active_days'].describe()
            
            f.write(f'- **活跃时长统计**:\n')
            f.write(f'  - 中位数: {active_days_stats["50%"]:.0f}天\n')
            f.write(f'  - 平均值: {active_days_stats["mean"]:.0f}天\n')
            f.write(f'  - 最大值: {active_days_stats["max"]:.0f}天\n')
            
            # 长期贡献者分析
            long_term = author_stats[author_stats['active_days'] > 365]
            if len(long_term) > 0:
                f.write(f'  - 长期贡献者(>1年): {len(long_term)}人 ({len(long_term)/total_authors*100:.1f}%)\n')
        
        f.write('\n##  社区健康度评估\n\n')
        
        # 社区健康度评分
        health_score = 0
        health_indicators = []
        
        # 指标1: 新贡献者增长
        if 'yearly_new_authors' in patterns and patterns['yearly_new_authors']:
            yearly_new = patterns['yearly_new_authors']
            years = list(yearly_new.keys())
            if len(years) >= 3:
                recent_growth = sum([yearly_new[y] for y in years[-3:]]) / 3
                if recent_growth > 20:
                    health_score += 25
                    health_indicators.append(' 新贡献者增长强劲 (+25)')
                elif recent_growth > 10:
                    health_score += 15
                    health_indicators.append(' 新贡献者稳定增长 (+15)')
                else:
                    health_score += 5
                    health_indicators.append(' 新贡献者增长较慢 (+5)')
        
        # 指标2: 贡献集中度
        if top_20_percentage < 90:
            health_score += 25
            health_indicators.append(' 贡献分布较为分散 (+25)')
        elif top_20_percentage < 95:
            health_score += 15
            health_indicators.append(' 贡献相对集中 (+15)')
        else:
            health_score += 5
            health_indicators.append(' 贡献高度集中 (+5)')
        
        # 指标3: 长期贡献者比例
        long_term = author_stats[author_stats['active_days'] > 365]
        long_term_ratio = len(long_term) / total_authors if total_authors > 0 else 0
        if long_term_ratio > 0.1:
            health_score += 25
            health_indicators.append(' 长期贡献者比例良好 (+25)')
        elif long_term_ratio > 0.05:
            health_score += 15
            health_indicators.append(' 长期贡献者比例一般 (+15)')
        else:
            health_score += 5
            health_indicators.append(' 长期贡献者较少 (+5)')
        
        # 指标4: 社区多样性（一次性贡献者比例）
        one_time_ratio = len(author_stats[author_stats['commit_count'] == 1]) / total_authors if total_authors > 0 else 0
        if one_time_ratio < 0.5:
            health_score += 25
            health_indicators.append(' 社区参与深度良好 (+25)')
        elif one_time_ratio < 0.7:
            health_score += 15
            health_indicators.append(' 社区参与深度一般 (+15)')
        else:
            health_score += 5
            health_indicators.append(' 一次性贡献者过多 (+5)')
        
        f.write(f'### 社区健康度评分: {health_score}/100\n\n')
        
        for indicator in health_indicators:
            f.write(f'- {indicator}\n')
        
        if health_score >= 80:
            f.write('\n**评估结果**: 社区健康度优秀，贡献者生态系统活跃且可持续。\n')
        elif health_score >= 60:
            f.write('\n**评估结果**: 社区健康度良好，有改进空间但整体稳定。\n')
        else:
            f.write('\n**评估结果**: 社区健康度需关注，建议采取措施提高贡献者留存和多样性。\n')
        
        f.write('\n##  生成文件\n\n')
        f.write('### 数据文件\n')
        f.write('- `contributor_stats.csv` - 所有贡献者详细统计\n')
        f.write('- `top_100_contributors.csv` - 前100名贡献者\n')
        f.write('- `contribution_patterns.csv` - 贡献模式统计\n')
        f.write('- `yearly_new_contributors.csv` - 年度新贡献者\n')
        f.write('- `yearly_active_contributors.csv` - 年度活跃贡献者\n')
        f.write('- `retention_rates.csv` - 贡献者留存率\n')
        
        f.write('\n### 图表文件\n')
        f.write('- `top_20_contributors.png` - 前20名贡献者柱状图\n')
        f.write('- `contributor_type_distribution.png` - 贡献者类型分布饼图\n')
        f.write('- `contribution_concentration.png` - 贡献集中度帕累托图\n')
        f.write('- `yearly_new_contributors.png` - 年度新贡献者趋势图\n')
        f.write('- `contributor_activity_duration.png` - 贡献者活跃时长分布\n')
        f.write('- `yearly_active_contributors.png` - 年度活跃贡献者趋势\n')
        
        f.write('\n##  改进建议\n\n')
        
        if health_score < 60:
            f.write('1. **提高贡献者留存**: 建立更完善的新手引导文档和导师制度\n')
            f.write('2. **降低贡献门槛**: 标记更多"good first issue"，提供清晰的贡献指南\n')
            f.write('3. **激励长期贡献**: 建立贡献者认可机制，如月度贡献者表彰\n')
            f.write('4. **扩大社区参与**: 举办线上线下活动，吸引更多潜在贡献者\n')
        elif health_score < 80:
            f.write('1. **优化贡献流程**: 简化代码审查流程，加快PR合并速度\n')
            f.write('2. **加强社区互动**: 定期组织技术分享，增强社区凝聚力\n')
            f.write('3. **关注新贡献者**: 为新贡献者提供专门的技术支持和指导\n')
        else:
            f.write('1. **保持良好实践**: 继续当前的社区管理策略\n')
            f.write('2. **探索创新模式**: 尝试新的贡献者激励和认可方式\n')
            f.write('3. **分享成功经验**: 总结社区建设经验，帮助其他开源项目\n')
    
    print(f" 贡献者分析报告已生成: {report_file}")

def main():
    """主函数"""
    print("=" * 70)
    print(" Flask项目贡献者活跃度分析")
    print("=" * 70)
    
    # 1. 获取贡献者数据
    commits = get_contributor_data()
    if not commits:
        return
    
    # 2. 分析贡献者统计
    author_stats, df = analyze_contributor_stats(commits)
    
    # 3. 分析贡献模式
    patterns = analyze_contribution_patterns(author_stats, df)
    
    # 4. 保存分析结果
    project_root = Path(__file__).parent.parent.parent
    save_dir = project_root / "commit_analysis" / "data"
    save_analysis_results(author_stats, patterns, save_dir)
    
    # 5. 创建可视化图表
    figures_dir = project_root / "commit_analysis" / "figures"
    create_visualizations(author_stats, patterns, figures_dir)
    
    # 6. 生成报告
    report_dir = project_root / "commit_analysis" / "reports"
    generate_report(author_stats, patterns, report_dir)
    
    # 7. 显示关键发现
    print("\n" + "=" * 70)
    print(" 关键发现")
    print("=" * 70)
    
    total_authors = len(author_stats)
    total_commits = author_stats['commit_count'].sum()
    top_10_commits = author_stats.head(10)['commit_count'].sum()
    top_10_percentage = top_10_commits / total_commits * 100
    
    print(f" 贡献者总数: {total_authors:,} 人")
    print(f" 提交总数: {total_commits:,} 次")
    print(f" 前10名贡献者提交占比: {top_10_percentage:.1f}%")
    print(f" 核心贡献者: {len(author_stats[author_stats['contributor_type'] == 'Core Contributor'])} 人")
    print(f" 一次性贡献者: {len(author_stats[author_stats['commit_count'] == 1])} 人")
    
    # 年度新贡献者
    if 'yearly_new_authors' in patterns:
        yearly_new = patterns['yearly_new_authors']
        recent_years = sorted(yearly_new.keys())[-3:] if yearly_new else []
        recent_new = sum(yearly_new[y] for y in recent_years) if recent_years else 0
        print(f" 最近3年新增贡献者: {recent_new} 人")
    
    # 最活跃的贡献者
    if len(author_stats) > 0:
        top_contributor = author_stats.iloc[0]
        print(f" 最活跃贡献者: {top_contributor['author']} ({top_contributor['commit_count']:,}次提交)")
    
    # 8. 下一步建议
    print("\n" + "=" * 70)
    print(" 贡献者活跃度分析完成！")


if __name__ == "__main__":
    main()
    input("\n按回车键退出...")