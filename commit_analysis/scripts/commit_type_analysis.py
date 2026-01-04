"""
提交类型与代码变更分析 - 分析Flask项目的提交类型、代码变更模式和文件变更情况
"""
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import subprocess
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 使用英文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = True

def get_commit_data():
    """获取提交数据"""
    print(" 提取提交数据...")

    current_dir = Path(__file__).parent  # scripts目录
    project_root = current_dir.parent  # commit_analysis目录
    open_source_root = project_root.parent  # OpenSource目录
    flask_path = open_source_root / "flask"
    
    if not flask_path.exists():
        print(f" Flask仓库路径不存在: {flask_path}")
        print(f"  当前脚本路径: {Path(__file__)}")
        print(f"  项目根目录: {project_root}")
        print(f"  OpenSource目录: {open_source_root}")
        return None
    
    print(f" Flask仓库路径: {flask_path}")
    

    cmd = ['git', '-C', str(flask_path), 'log', 
           '--pretty=format:%H|%an|%ad|%s', 
           '--date=short', '--numstat',
           '--max-count', '500']  # 限制500个提交
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            print(f" 无法获取git提交数据: {result.stderr[:200]}")
            return None
        
        lines = result.stdout.strip().split('\n')
        
        if not lines or (len(lines) == 1 and not lines[0]):
            print(" 未提取到提交数据")
            return None
        
        commits = []
        current_commit = None
        
        for line in lines:
            if line and '|' in line and '\t' not in line:
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split('|', 3)
                if len(parts) == 4:
                    hash_val, author, date, message = parts
                    try:
                        date_obj = pd.to_datetime(date.strip())
                    except:
                        date_obj = pd.NaT
                    
                    current_commit = {
                        'hash': hash_val.strip(),
                        'author': author.strip(),
                        'date': date_obj,
                        'message': message.strip(),
                        'year': int(date.strip().split('-')[0]) if date.strip() and '-' in date else None,
                        'month': date.strip()[:7] if date.strip() and len(date.strip()) >= 7 else None,
                        'files': [],
                        'additions': 0,
                        'deletions': 0,
                        'changed_lines': 0,
                        'file_count': 0,
                        'commit_type': classify_commit_type(message.strip())
                    }
            elif line and '\t' in line:
                # 文件变更统计行
                if current_commit:
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        additions_str, deletions_str, filename = parts
                        
                        additions = 0
                        deletions = 0
                        try:
                            additions = int(additions_str) if additions_str != '-' else 0
                            deletions = int(deletions_str) if deletions_str != '-' else 0
                        except:
                            pass
                        
                        current_commit['files'].append({
                            'filename': filename,
                            'additions': additions,
                            'deletions': deletions,
                            'changed_lines': additions + deletions
                        })
                        
                        current_commit['additions'] += additions
                        current_commit['deletions'] += deletions
                        current_commit['changed_lines'] += (additions + deletions)
                        current_commit['file_count'] += 1
        
        # 添加最后一个提交
        if current_commit:
            commits.append(current_commit)
        
        print(f" 成功提取 {len(commits)} 个提交")
        return commits
        
    except Exception as e:
        print(f" 提取提交数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def classify_commit_type(message):
    """分类提交类型"""
    if not isinstance(message, str):
        return 'other'
    
    message = message.lower()
    
    patterns = {
        'feature': [r'add\b', r'feat\b', r'feature\b', r'new\b', r'implement\b'],
        'bugfix': [r'fix\b', r'bug\b', r'issue\b', r'error\b', r'bugfix\b'],
        'refactor': [r'refactor\b', r'cleanup\b', r'clean\b', r'optimize\b'],
        'documentation': [r'doc\b', r'documentation\b', r'readme\b', r'comment\b'],
        'test': [r'test\b', r'unit\b', r'coverage\b', r'fixture\b'],
        'style': [r'style\b', r'format\b', r'pep8\b', r'whitespace\b'],
        'chore': [r'chore\b', r'bump\b', r'update\b.*version', r'dependency\b'],
        'performance': [r'performance\b', r'optimization\b', r'speed\b']
    }
    
    for commit_type, regex_list in patterns.items():
        for pattern in regex_list:
            try:
                if re.search(pattern, message, re.IGNORECASE):
                    return commit_type
            except:
                continue
    
    return 'other'

def analyze_commits(commits):
    """分析提交数据"""
    print("\n 分析提交数据...")
    
    if not commits:
        return None, None, None
    
    df = pd.DataFrame(commits)
    df['net_lines'] = df['additions'] - df['deletions']
    
    # 1. 基本统计
    total_commits = len(df)
    total_additions = df['additions'].sum()
    total_deletions = df['deletions'].sum()
    total_changed = df['changed_lines'].sum()
    
    print(f" 基本统计:")
    print(f"  总提交数: {total_commits:,}")
    print(f"  总增加行数: {total_additions:,}")
    print(f"  总删除行数: {total_deletions:,}")
    print(f"  总变更行数: {total_changed:,}")
    print(f"  平均每提交变更: {df['changed_lines'].mean():.1f} 行")
    
    # 2. 提交类型分析
    print(f"\n 提交类型分布:")
    type_counts = df['commit_type'].value_counts()
    
    type_stats = {}
    for commit_type, count in type_counts.items():
        type_data = df[df['commit_type'] == commit_type]
        type_stats[commit_type] = {
            'count': count,
            'percentage': (count / total_commits) * 100,
            'total_changed_lines': type_data['changed_lines'].sum(),
            'avg_changed_lines': type_data['changed_lines'].mean()
        }
    
    print(f"{'类型':<15} {'数量':<8} {'占比%':<8} {'总变更行数':<12} {'平均变更行数':<12}")
    print("-" * 70)
    for commit_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"{commit_type:<15} {stats['count']:<8} {stats['percentage']:<8.1f} "
              f"{stats['total_changed_lines']:<12,} {stats['avg_changed_lines']:<12.1f}")
    
    # 3. 文件变更分析
    print(f"\n 文件变更分析:")
    file_stats_dict = defaultdict(lambda: {
        'commit_count': 0,
        'total_changed_lines': 0,
        'authors': set()
    })
    
    for commit in commits:
        for file_info in commit['files']:
            filename = file_info['filename']
            stats = file_stats_dict[filename]
            stats['commit_count'] += 1
            stats['total_changed_lines'] += file_info['changed_lines']
            stats['authors'].add(commit['author'])
    
    file_stats_list = []
    for filename, stats in file_stats_dict.items():
        file_stats_list.append({
            'filename': filename,
            'commit_count': stats['commit_count'],
            'total_changed_lines': stats['total_changed_lines'],
            'author_count': len(stats['authors'])
        })
    
    file_stats = pd.DataFrame(file_stats_list)
    file_stats = file_stats.sort_values('commit_count', ascending=False).reset_index(drop=True)
    
    print(f"{'文件名':<40} {'提交次数':<10} {'变更行数':<12} {'作者数':<8}")
    print("-" * 90)
    for i, row in file_stats.head(10).iterrows():
        filename = row['filename']
        if len(filename) > 35:
            filename = '...' + filename[-32:]
        print(f"{filename:<40} {row['commit_count']:<10,} {row['total_changed_lines']:<12,} {row['author_count']:<8}")
    
    # 4. 变更规模分析
    print(f"\n 变更规模分析:")
    small = len(df[df['changed_lines'] <= 10])
    medium = len(df[(df['changed_lines'] > 10) & (df['changed_lines'] <= 100)])
    large = len(df[df['changed_lines'] > 100])
    
    print(f"  小变更(≤10行): {small:,} ({small/total_commits*100:.1f}%)")
    print(f"  中变更(11-100行): {medium:,} ({medium/total_commits*100:.1f}%)")
    print(f"  大变更(>100行): {large:,} ({large/total_commits*100:.1f}%)")
    
    return df, type_stats, file_stats

def create_visualizations(df, type_stats, file_stats):
    """创建可视化图表"""
    print("\n 创建可视化图表...")
    
    # 输出目录
    output_dir = Path(__file__).parent.parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. 提交类型分布饼图
    if type_stats:
        plt.figure(figsize=(10, 8))
        
        labels = list(type_stats.keys())
        sizes = [stats['count'] for stats in type_stats.values()]
        
        # 合并小类型
        threshold = sum(sizes) * 0.05
        filtered_labels = []
        filtered_sizes = []
        other_size = 0
        
        for label, size in zip(labels, sizes):
            if size >= threshold:
                filtered_labels.append(label)
                filtered_sizes.append(size)
            else:
                other_size += size
        
        if other_size > 0:
            filtered_labels.append('other')
            filtered_sizes.append(other_size)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(filtered_labels)))
        
        plt.pie(filtered_sizes, labels=filtered_labels, autopct='%1.1f%%',
               colors=colors, startangle=90, textprops={'fontsize': 10})
        plt.title('Commit Type Distribution', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / 'commit_type_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(" 提交类型分布饼图已保存")
    
    # 2. 变更规模分布图
    if df is not None and len(df) > 0:
        plt.figure(figsize=(12, 6))
        
        changed_lines = df['changed_lines']
        filtered_lines = changed_lines[changed_lines <= 200]  # 过滤极端值
        
        plt.hist(filtered_lines, bins=30, alpha=0.7, color='steelblue', edgecolor='black')
        plt.axvline(x=10, color='red', linestyle='--', alpha=0.7, label='Small (≤10 lines)')
        plt.axvline(x=100, color='orange', linestyle='--', alpha=0.7, label='Medium (≤100 lines)')
        
        plt.xlabel('Changed Lines per Commit', fontsize=12)
        plt.ylabel('Number of Commits', fontsize=12)
        plt.title('Distribution of Code Change Sizes', fontsize=16, fontweight='bold')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / 'change_size_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(" 变更规模分布图已保存")
    
    # 3. 最活跃文件图
    if file_stats is not None and len(file_stats) > 0:
        plt.figure(figsize=(14, 8))
        
        top_files = file_stats.head(15).copy()
        top_files['filename_short'] = top_files['filename'].apply(
            lambda x: x if len(x) <= 25 else '...' + x[-22:]
        )
        
        y_pos = np.arange(len(top_files))
        plt.barh(y_pos, top_files['commit_count'], color='skyblue', alpha=0.7)
        plt.yticks(y_pos, top_files['filename_short'], fontsize=10)
        plt.xlabel('Number of Commits', fontsize=12)
        plt.title('Top 15 Most Frequently Changed Files', fontsize=16, fontweight='bold')
        plt.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'top_files_changes.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(" 最活跃文件图已保存")
    
    print(f" 所有图表已保存到 {output_dir}")

def save_data(df, file_stats):
    """保存数据到CSV"""
    print("\n 保存数据...")
    
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存提交摘要
    if df is not None and len(df) > 0:
        commits_summary = df[['hash', 'author', 'date', 'message', 'commit_type', 
                              'additions', 'deletions', 'changed_lines', 'file_count']].copy()
        commits_summary.to_csv(data_dir / 'commits_summary.csv', index=False)
        print(" 提交摘要已保存到 commits_summary.csv")
    
    # 保存文件统计
    if file_stats is not None and len(file_stats) > 0:
        file_stats.to_csv(data_dir / 'file_statistics.csv', index=False)
        print(" 文件统计已保存到 file_statistics.csv")

def generate_report(df, type_stats, file_stats):
    """生成分析报告"""
    print("\n 生成分析报告...")
    
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / 'commit_analysis_report.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# Flask项目提交类型与代码变更分析报告\n\n')
        f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        
        # 基本统计
        if df is not None and len(df) > 0:
            total_commits = len(df)
            total_changed = df['changed_lines'].sum()
            
            f.write('##  基本统计\n\n')
            f.write(f'- **分析提交数**: {total_commits:,}\n')
            f.write(f'- **总变更行数**: {total_changed:,} 行\n')
            f.write(f'- **平均每提交变更**: {df["changed_lines"].mean():.1f} 行\n')
            f.write(f'- **平均每提交文件数**: {df["file_count"].mean():.1f} 个\n\n')
        
        # 提交类型分析
        if type_stats:
            f.write('##  提交类型分析\n\n')
            f.write('| 类型 | 数量 | 占比% | 总变更行数 | 平均变更行数 |\n')
            f.write('|------|------|-------|------------|--------------|\n')
            
            for commit_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
                f.write(f'| {commit_type} | {stats["count"]:,} | {stats["percentage"]:.1f}% | '
                       f'{stats["total_changed_lines"]:,} | {stats["avg_changed_lines"]:.1f} |\n')
            
            f.write('\n')
        
        # 最活跃文件
        if file_stats is not None and len(file_stats) > 0:
            f.write('##  最活跃文件\n\n')
            f.write('| 文件名 | 提交次数 | 变更行数 | 作者数 |\n')
            f.write('|--------|----------|----------|--------|\n')
            
            for i, row in file_stats.head(10).iterrows():
                filename = row['filename']
                if len(filename) > 40:
                    filename = '...' + filename[-37:]
                f.write(f'| {filename} | {row["commit_count"]:,} | {row["total_changed_lines"]:,} | {row["author_count"]} |\n')
            
            f.write('\n')
        
        # 变更规模分析
        if df is not None and len(df) > 0:
            total_commits = len(df)
            small = len(df[df['changed_lines'] <= 10])
            medium = len(df[(df['changed_lines'] > 10) & (df['changed_lines'] <= 100)])
            large = len(df[df['changed_lines'] > 100])
            
            f.write('##  变更规模分析\n\n')
            f.write(f'- **小变更提交** (≤10行): {small:,} ({small/total_commits*100:.1f}%)\n')
            f.write(f'- **中变更提交** (11-100行): {medium:,} ({medium/total_commits*100:.1f}%)\n')
            f.write(f'- **大变更提交** (>100行): {large:,} ({large/total_commits*100:.1f}%)\n\n')
        
        # 关键发现
        f.write('##  关键发现\n\n')
        
        if type_stats:
            # 检查bug修复占比
            bugfix_pct = type_stats.get('bugfix', {}).get('percentage', 0)
            if bugfix_pct > 20:
                f.write('1. **Bug修复占比较高**：项目处于维护阶段，需关注代码质量\n')
            
            # 检查功能开发占比
            feature_pct = type_stats.get('feature', {}).get('percentage', 0)
            if feature_pct > 30:
                f.write('2. **功能开发活跃**：项目处于活跃开发阶段\n')
        
        if df is not None and len(df) > 0:
            avg_changes = df['changed_lines'].mean()
            if avg_changes > 100:
                f.write('3. **变更量较大**：建议拆分为更小的提交\n')
            elif avg_changes < 50:
                f.write('3. **变更粒度适中**：开发流程良好\n')
        
        # 建议
        f.write('\n##  改进建议\n\n')
        f.write('1. **持续监控**：定期分析提交模式，了解项目健康状况\n')
        f.write('2. **优化流程**：鼓励小批量提交，提高代码审查效率\n')
        f.write('3. **关注核心文件**：重点关注最活跃文件的代码质量\n')
        f.write('4. **平衡开发类型**：确保功能开发、bug修复和重构的平衡\n')
        
        f.write('\n---\n')
        f.write('*报告生成完成*\n')
    
    print(f" 分析报告已生成: {report_file}")

def main():
    """主函数"""
    print("=" * 70)
    print(" Flask项目提交类型与代码变更分析")
    print("=" * 70)
    
    # 1. 获取提交数据
    commits = get_commit_data()
    if not commits:
        print(" 无法获取提交数据，分析终止")
        return
    
    # 2. 分析数据
    df, type_stats, file_stats = analyze_commits(commits)
    
    # 3. 创建可视化图表
    create_visualizations(df, type_stats, file_stats)
    
    # 4. 保存数据
    save_data(df, file_stats)
    
    # 5. 生成报告
    generate_report(df, type_stats, file_stats)
    
    print("\n" + "=" * 70)
    print(" 分析完成！")
    print("\n 输出文件:")
    print("   数据文件: ../data/")
    print("   图表文件: ../figures/")
    print("   报告文件: ../reports/commit_analysis_report.md")
    print("=" * 70)

if __name__ == "__main__":
    main()