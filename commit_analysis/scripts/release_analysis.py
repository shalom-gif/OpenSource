"""
版本发布规律分析 
"""
import warnings
warnings.filterwarnings('ignore')

import subprocess
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = True

def get_release_data():
    """获取版本发布数据"""
    print(" 提取版本发布数据...")
    
    # Flask仓库路径
    current_dir = Path(__file__).parent
    open_source_root = current_dir.parent.parent
    flask_path = open_source_root / "flask"
    
    if not flask_path.exists():
        print(f" Flask仓库路径不存在: {flask_path}")
        return None
    
    print(f" Flask仓库路径: {flask_path}")
    
    try:
        # 获取所有标签
        cmd = ['git', '-C', str(flask_path), 'tag', '-l', '--sort=-creatordate']
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            print(f" 无法获取标签列表: {result.stderr}")
            return None
        
        tags = result.stdout.strip().split('\n')
        tags = [t.strip() for t in tags if t.strip()]
        
        if not tags:
            print(" 未找到版本标签")
            return None
        
        print(f" 找到 {len(tags)} 个版本标签")
        
        releases = []
        
        # 获取每个标签的详细信息
        for tag in tags:
            cmd_show = ['git', '-C', str(flask_path), 'show', '--no-patch', 
                       '--format=%H|%ad|%s', '--date=short', tag]
            result_show = subprocess.run(cmd_show, capture_output=True, 
                                        text=True, encoding='utf-8')
            
            if result_show.returncode == 0:
                lines = result_show.stdout.strip().split('\n')
                if lines and '|' in lines[0]:
                    hash_val, date_str, message = lines[0].split('|', 2)
                    
                    try:
                        date = pd.to_datetime(date_str.strip())
                    except:
                        continue  # 跳过日期解析失败的版本
                    
                    # 解析版本号
                    version_info = parse_version_number(tag)
                    
                    releases.append({
                        'tag': tag,
                        'date': date,
                        'message': message.strip(),
                        'year': date.year,
                        'month': date.strftime('%Y-%m'),
                        'major': version_info['major'],
                        'minor': version_info['minor'],
                        'patch': version_info['patch'],
                        'version_type': version_info['type']
                    })
        
        if not releases:
            print(" 未提取到有效的版本信息")
            return None
        
        print(f" 成功提取 {len(releases)} 个版本信息")
        
        # 按日期排序
        releases_df = pd.DataFrame(releases)
        releases_df = releases_df.sort_values('date').reset_index(drop=True)
        
        return releases_df
        
    except Exception as e:
        print(f" 提取版本发布数据时出错: {e}")
        return None

def parse_version_number(tag):
    """解析版本号"""
    tag = tag.strip().lstrip('vV')
    
    version_info = {
        'major': None,
        'minor': None,
        'patch': None,
        'type': 'unknown'
    }
    
    # 匹配语义化版本号
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
    match = re.match(pattern, tag)
    
    if match:
        version_info['major'] = int(match.group(1))
        version_info['minor'] = int(match.group(2))
        version_info['patch'] = int(match.group(3))
        
        # 判断版本类型
        if match.group(4):  # 有预发布标识
            version_info['type'] = 'prerelease'
        elif version_info['patch'] == 0 and version_info['minor'] == 0:
            version_info['type'] = 'major'
        elif version_info['patch'] == 0:
            version_info['type'] = 'minor'
        else:
            version_info['type'] = 'patch'
    else:
        # 尝试匹配简单版本号
        simple_pattern = r'^(\d+)\.(\d+)$'
        simple_match = re.match(simple_pattern, tag)
        
        if simple_match:
            version_info['major'] = int(simple_match.group(1))
            version_info['minor'] = int(simple_match.group(2))
            version_info['patch'] = 0
            version_info['type'] = 'minor' if version_info['minor'] > 0 else 'major'
    
    return version_info

def analyze_releases(releases_df):
    """分析版本发布数据"""
    print("\n 分析版本发布数据...")
    
    if releases_df is None or len(releases_df) == 0:
        print(" 没有版本发布数据")
        return {}, {}
    
    patterns = {}
    
    # 1. 基本统计
    patterns['total_releases'] = len(releases_df)
    patterns['first_release'] = releases_df.iloc[0]['date']
    patterns['last_release'] = releases_df.iloc[-1]['date']
    
    print(f" 基本统计:")
    print(f"  总版本数: {patterns['total_releases']:,}")
    print(f"  最早版本: {releases_df.iloc[0]['tag']} ({patterns['first_release'].strftime('%Y-%m-%d')})")
    print(f"  最新版本: {releases_df.iloc[-1]['tag']} ({patterns['last_release'].strftime('%Y-%m-%d')})")
    
    # 2. 版本类型分布
    print(f"\n 版本类型分布:")
    type_counts = releases_df['version_type'].value_counts()
    
    patterns['version_types'] = {}
    for vtype, count in type_counts.items():
        percentage = (count / len(releases_df)) * 100
        patterns['version_types'][vtype] = {
            'count': count,
            'percentage': percentage
        }
        print(f"  {vtype:<10}: {count:>4} ({percentage:>5.1f}%)")
    
    # 3. 年度发布频率
    print(f"\n 年度发布频率:")
    yearly_counts = releases_df['year'].value_counts().sort_index()
    patterns['yearly_counts'] = yearly_counts.to_dict()
    
    for year, count in sorted(patterns['yearly_counts'].items()):
        print(f"  {year}: {count} 个版本")
    
    # 4. 发布时间间隔分析
    print(f"\n 发布时间间隔分析:")
    
    if len(releases_df) > 1:
        # 计算发布间隔
        intervals = []
        for i in range(1, len(releases_df)):
            prev_date = releases_df.iloc[i-1]['date']
            curr_date = releases_df.iloc[i]['date']
            days_diff = (curr_date - prev_date).days
            intervals.append(days_diff)
        
        intervals_df = pd.DataFrame(intervals, columns=['days'])
        
        patterns['avg_interval_days'] = intervals_df['days'].mean()
        patterns['median_interval_days'] = intervals_df['days'].median()
        patterns['min_interval_days'] = intervals_df['days'].min()
        patterns['max_interval_days'] = intervals_df['days'].max()
        
        print(f"  平均发布间隔: {patterns['avg_interval_days']:.1f} 天")
        print(f"  中位数发布间隔: {patterns['median_interval_days']:.1f} 天")
        print(f"  最短发布间隔: {patterns['min_interval_days']:.0f} 天")
        print(f"  最长发布间隔: {patterns['max_interval_days']:.0f} 天")
        
        # 按版本类型分析间隔
        print(f"\n 不同类型版本的发布间隔:")
        
        # 为每个版本添加间隔天数（第一个版本设为NaN）
        releases_df['days_since_previous'] = np.nan
        for i in range(1, len(releases_df)):
            prev_date = releases_df.iloc[i-1]['date']
            curr_date = releases_df.iloc[i]['date']
            releases_df.loc[i, 'days_since_previous'] = (curr_date - prev_date).days
        
        # 按版本类型分组计算
        interval_stats = releases_df.groupby('version_type')['days_since_previous'].agg(['mean', 'median', 'count'])
        patterns['interval_by_type'] = interval_stats.to_dict('index')
        
        for vtype, stats in patterns['interval_by_type'].items():
            if stats['count'] > 0:  # 确保有数据
                print(f"  {vtype:<10}: 平均 {stats['mean']:.1f} 天, 中位数 {stats['median']:.1f} 天, 数量 {int(stats['count'])}")
    
    # 5. 主版本分析
    print(f"\n 主版本分析:")
    major_counts = releases_df['major'].value_counts().sort_index()
    patterns['major_versions'] = major_counts.to_dict()
    
    for major, count in patterns['major_versions'].items():
        print(f"  v{major}.x: {count:>4} 个版本")
    
    return patterns, releases_df

def create_visualizations(releases_df, patterns):
    """创建可视化图表"""
    print("\n 创建可视化图表...")
    
    # 输出目录
    output_dir = Path(__file__).parent.parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. 年度发布趋势图
    if len(releases_df) > 0:
        plt.figure(figsize=(12, 6))
        
        yearly_counts = releases_df['year'].value_counts().sort_index()
        
        plt.bar(yearly_counts.index.astype(str), yearly_counts.values, 
                color='steelblue', alpha=0.7)
        plt.plot(yearly_counts.index.astype(str), yearly_counts.values, 
                color='darkblue', linewidth=2, marker='o', markersize=5)
        
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of Releases', fontsize=12)
        plt.title('Flask Release Frequency by Year', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'yearly_releases.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("年度发布趋势图已保存")
    
    # 2. 版本类型分布图
    if 'version_types' in patterns:
        plt.figure(figsize=(10, 6))
        
        version_types = list(patterns['version_types'].keys())
        counts = [patterns['version_types'][t]['count'] for t in version_types]
        
        colors = plt.cm.Set3(range(len(version_types)))
        plt.bar(version_types, counts, color=colors, alpha=0.7)
        
        plt.xlabel('Release Type', fontsize=12)
        plt.ylabel('Number of Releases', fontsize=12)
        plt.title('Release Type Distribution', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        # 添加数值标签
        for i, count in enumerate(counts):
            plt.text(i, count + max(counts)*0.01, str(count), 
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'release_types.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("版本类型分布图已保存")
    
    # 3. 发布时间线图
    if len(releases_df) > 0:
        plt.figure(figsize=(14, 6))
        
        # 创建时间线
        fig, ax = plt.subplots(figsize=(14, 4))
        
        # 颜色映射
        type_colors = {
            'major': 'red',
            'minor': 'orange',
            'patch': 'green',
            'prerelease': 'blue',
            'unknown': 'gray'
        }
        
        for _, release in releases_df.iterrows():
            date = release['date']
            version_type = release['version_type']
            color = type_colors.get(version_type, 'gray')
            
            # 根据版本类型设置不同大小
            size = 80 if version_type == 'major' else 40
            
            ax.scatter(date, 0, color=color, s=size, alpha=0.7)
        
        ax.set_xlabel('Date', fontsize=12)
        ax.set_yticks([])
        ax.set_title('Flask Release Timeline', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # 创建图例
        legend_elements = []
        for vtype, color in type_colors.items():
            if vtype in releases_df['version_type'].values:
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                 markerfacecolor=color, markersize=8, label=vtype))
        
        ax.legend(handles=legend_elements, loc='upper left')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'release_timeline.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("发布时间线图已保存")
    
    print(f"所有图表已保存到 {output_dir}")

def save_data(releases_df, patterns):
    """保存数据"""
    print("\n保存数据...")
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存版本数据
    if releases_df is not None and len(releases_df) > 0:
        releases_df.to_csv(data_dir / 'releases_summary.csv', index=False)
        print("版本发布摘要已保存到 releases_summary.csv")
    
    # 保存分析结果
    if patterns:
        # 将字典转换为DataFrame保存
        import json
        with open(data_dir / 'release_patterns.json', 'w') as f:
            json.dump(patterns, f, indent=2, default=str)
        print("发布模式分析已保存到 release_patterns.json")

def generate_report(releases_df, patterns):
    """生成分析报告"""
    print("\n生成分析报告...")
    
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / 'release_analysis_report.md'
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('# Flask项目版本发布规律分析报告\n\n')
            f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            # 基本统计
            if releases_df is not None and len(releases_df) > 0:
                f.write('## 基本统计\n\n')
                f.write(f'- **总版本数**: {len(releases_df):,}\n')
                f.write(f'- **最早版本**: {releases_df.iloc[0]["tag"]} ({releases_df.iloc[0]["date"].strftime("%Y-%m-%d")})\n')
                f.write(f'- **最新版本**: {releases_df.iloc[-1]["tag"]} ({releases_df.iloc[-1]["date"].strftime("%Y-%m-%d")})\n')
                
                if len(releases_df) > 1:
                    days_range = (releases_df.iloc[-1]['date'] - releases_df.iloc[0]['date']).days
                    f.write(f'- **时间跨度**: {days_range} 天 ({days_range/365.25:.1f} 年)\n')
                
                f.write('\n')
            
            # 版本类型分布
            if 'version_types' in patterns:
                f.write('## 版本类型分布\n\n')
                f.write('| 类型 | 数量 | 占比 |\n')
                f.write('|------|------|------|\n')
                
                for vtype, stats in patterns['version_types'].items():
                    f.write(f'| {vtype} | {stats["count"]:,} | {stats["percentage"]:.1f}% |\n')
                
                f.write('\n')
            
            # 年度发布趋势
            if 'yearly_counts' in patterns:
                f.write('## 年度发布趋势\n\n')
                f.write('| 年份 | 发布数 | 累计发布数 |\n')
                f.write('|------|--------|------------|\n')
                
                cumulative = 0
                for year, count in sorted(patterns['yearly_counts'].items()):
                    cumulative += count
                    f.write(f'| {year} | {count} | {cumulative} |\n')
                
                f.write('\n')
            
            # 发布间隔分析
            if 'avg_interval_days' in patterns:
                f.write('## 发布间隔分析\n\n')
                f.write(f'- **平均发布间隔**: {patterns["avg_interval_days"]:.1f} 天\n')
                f.write(f'- **中位数发布间隔**: {patterns["median_interval_days"]:.1f} 天\n')
                f.write(f'- **最短发布间隔**: {patterns["min_interval_days"]:.0f} 天\n')
                f.write(f'- **最长发布间隔**: {patterns["max_interval_days"]:.0f} 天\n\n')
            
            # 按版本类型的发布间隔
            if 'interval_by_type' in patterns:
                f.write('### 按版本类型的发布间隔\n\n')
                f.write('| 类型 | 平均间隔(天) | 中位数间隔(天) | 数量 |\n')
                f.write('|------|--------------|----------------|------|\n')
                
                for vtype, stats in patterns['interval_by_type'].items():
                    # 确保所有值都存在
                    mean_val = stats.get('mean', 0)
                    median_val = stats.get('median', 0)
                    count_val = int(stats.get('count', 0))
                    
                    f.write(f'| {vtype} | {mean_val:.1f} | {median_val:.1f} | {count_val} |\n')
                
                f.write('\n')
            
            # 主版本分析
            if 'major_versions' in patterns:
                f.write('## 主版本分析\n\n')
                f.write('| 主版本 | 发布数 |\n')
                f.write('|--------|--------|\n')
                
                for major, count in patterns['major_versions'].items():
                    f.write(f'| v{major}.x | {count} |\n')
                
                f.write('\n')
            
            # 关键发现
            f.write('## 关键发现\n\n')
            
            key_findings = []
            
            if 'avg_interval_days' in patterns:
                avg_interval = patterns['avg_interval_days']
                if avg_interval < 30:
                    key_findings.append(f"发布频率高，平均每 {avg_interval:.0f} 天发布一个版本")
                elif avg_interval < 90:
                    key_findings.append(f"发布频率中等，平均每 {avg_interval:.0f} 天发布一个版本")
                else:
                    key_findings.append(f"发布频率较低，平均每 {avg_interval:.0f} 天发布一个版本")
            
            if 'version_types' in patterns:
                major_pct = patterns['version_types'].get('major', {}).get('percentage', 0)
                if major_pct > 20:
                    key_findings.append(f"主版本更新频繁 ({major_pct:.1f}%)，项目可能处于快速发展阶段")
            
            # 计算最近3年平均发布数
            if 'yearly_counts' in patterns and len(patterns['yearly_counts']) >= 3:
                recent_years = sorted(patterns['yearly_counts'].keys())[-3:]
                recent_counts = [patterns['yearly_counts'][y] for y in recent_years]
                recent_avg = sum(recent_counts) / len(recent_counts)
                
                if recent_avg > 10:
                    key_findings.append(f"最近发布活跃，年均 {recent_avg:.1f} 个版本")
                elif recent_avg < 3:
                    key_findings.append(f"最近发布较少，年均 {recent_avg:.1f} 个版本")
            
            # 输出关键发现
            if key_findings:
                for i, finding in enumerate(key_findings, 1):
                    f.write(f'{i}. {finding}\n')
            else:
                f.write('1. 项目遵循语义化版本规范\n')
                f.write('2. 发布节奏相对稳定\n')
                f.write('3. 版本管理良好\n')
            
            f.write('\n## 改进建议\n\n')
            
            suggestions = []
            
            if 'avg_interval_days' in patterns and patterns['avg_interval_days'] > 180:
                suggestions.append("发布间隔较长，考虑增加发布频率以更快响应需求")
            
            if 'version_types' in patterns:
                patch_pct = patterns['version_types'].get('patch', {}).get('percentage', 0)
                if patch_pct > 70:
                    suggestions.append("补丁版本占比过高，建议合并小改动为次版本发布")
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    f.write(f'{i}. {suggestion}\n')
            else:
                f.write('1. 继续保持良好的发布节奏\n')
                f.write('2. 考虑自动化发布流程\n')
                f.write('3. 定期回顾发布策略\n')
            
            f.write('\n## 生成文件\n\n')
            f.write('### 数据文件\n')
            f.write('- `releases_summary.csv` - 版本发布摘要\n')
            f.write('- `release_patterns.json` - 发布模式分析\n')
            
            f.write('\n### 图表文件\n')
            f.write('- `yearly_releases.png` - 年度发布趋势图\n')
            f.write('- `release_types.png` - 版本类型分布图\n')
            f.write('- `release_timeline.png` - 发布时间线图\n')
            
            f.write('\n---\n')
            f.write('*报告生成完成*\n')
        
        print(f"分析报告已生成: {report_file}")
        
    except Exception as e:
        print(f"生成报告时出错: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print(" Flask项目版本发布规律分析")
    print("=" * 60)
    
    # 1. 获取版本发布数据
    releases_df = get_release_data()
    if releases_df is None or len(releases_df) == 0:
        print("无法获取版本发布数据，分析终止")
        return
    
    # 2. 分析版本发布数据
    patterns, releases_df = analyze_releases(releases_df)
    
    # 3. 创建可视化图表
    create_visualizations(releases_df, patterns)
    
    # 4. 保存数据
    save_data(releases_df, patterns)
    
    # 5. 生成报告
    generate_report(releases_df, patterns)
    
    print("\n" + "=" * 60)
    print(" 版本发布规律分析完成！")
    print("\n 输出文件:")
    print("   数据文件: ../data/")
    print("   图表文件: ../figures/")
    print("   报告文件: ../reports/release_analysis_report.md")
    print("=" * 60)

if __name__ == "__main__":
    main()