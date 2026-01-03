import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import urllib3

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 配置部分 ===
REPO_OWNER = "pallets"
REPO_NAME = "flask"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
PARAMS = {
    "state": "closed",
    "labels": "bug",
    "per_page": 100,
    "page": 1
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FIG_DIR = os.path.join(BASE_DIR, "figures")

def fetch_bugs():
    print(f"正在从 GitHub 获取 {REPO_NAME} 的 Bug 数据...")
    headers = {"User-Agent": "Student-Project-Analysis"}
    
    # 修改在这里：增加了 verify=False
    response = requests.get(API_URL, params=PARAMS, headers=headers, verify=False)
    
    if response.status_code != 200:
        print(f"获取失败! 状态码: {response.status_code}")
        return []
    
    return response.json()

def analyze_and_save(issues):
    if not issues:
        print("没有数据，停止分析。")
        return

    data_list = []
    
    for issue in issues:
        if "pull_request" in issue:
            continue
            
        created_at = datetime.strptime(issue['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        closed_at = datetime.strptime(issue['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
        duration_hours = (closed_at - created_at).total_seconds() / 3600
        
        data_list.append({
            "id": issue['number'],
            "title": issue['title'],
            "created_at": created_at,
            "closed_at": closed_at,
            "duration_hours": duration_hours
        })

    df = pd.DataFrame(data_list)
    
    csv_path = os.path.join(DATA_DIR, "flask_bugs.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"数据已保存到: {csv_path}")

    print(f"平均解决时间: {df['duration_hours'].mean():.2f} 小时")
    
    plt.figure(figsize=(10, 6))
    plt.hist(df['duration_hours'], bins=20, color='skyblue', edgecolor='black')
    plt.title('Distribution of Time Taken to Fix Bugs in Flask (Recent 100)')
    plt.xlabel('Hours to Fix')
    plt.ylabel('Number of Bugs')
    plt.grid(axis='y', alpha=0.75)
    
    fig_path = os.path.join(FIG_DIR, "bug_fix_duration.png")
    plt.savefig(fig_path)
    print(f"图表已保存到: {fig_path}")

if __name__ == "__main__":
    issues_data = fetch_bugs()
    analyze_and_save(issues_data)