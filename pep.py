#!/usr/bin/env python
# coding: utf-8

import requests, bs4, graphviz
import time

class PEPEntry:
    def __init__(self, status, ID, title, href, authors, versions):
        self.status = status
        self.ID = ID
        self.title = title
        self.href = href
        self.created = self.extract_date(href)
        self.authors = self.split_authors(authors)
        self.versions = versions

    def split_authors(self, authors):
        if not authors:
            return []
        authors = authors.replace(", Jr.", " Jr.")
        if ";" in authors:
            return [a.strip() for a in authors.split(";")]
        return authors.split(", ")

    def extract_date(self, href):
        url = f"https://peps.python.org/numerical/{href}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                return ""
            dom = bs4.BeautifulSoup(res.text, 'html.parser')
            created = dom.find(string="Created")
            if created:
                date = created.find_next("dd").get_text()
                return date
            return ""
        except:
            return ""

def count_pep_status(entries):
    status_counts = {}
    for entry in entries:
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
    return status_counts

def create_author_graph(entries):
    graph = graphviz.Graph()
    edge_set = set()
    
    for entry in entries:
        length = len(entry.authors)
        for i in range(length):
            a1 = entry.authors[i]
            for j in range(i+1, length):
                a2 = entry.authors[j]
                if (a1, a2) in edge_set or (a2, a1) in edge_set:
                    continue
                graph.edge(a1, a2)
                edge_set.add((a1, a2))
    
    return graph

if __name__ == "__main__":
    url = "https://peps.python.org/numerical/"
    res = requests.get(url)
    
    if res.status_code == 200:
        dom = bs4.BeautifulSoup(res.text, 'html.parser')
        entries = []
        
        for tr in dom.find("table").find("tbody").find_all("tr")[:10]:
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue
            status = tds[0].get_text()
            ID = tds[1].get_text()
            title = tds[2].get_text()
            href = tds[2].find("a").get("href")
            authors = tds[3].get_text()
            versions = tds[4].get_text()
            
            entry = PEPEntry(status, ID, title, href, authors, versions)
            entries.append(entry)
        
        # 显示统计信息
        stats = count_pep_status(entries)
        print(f"总共获取 {len(entries)} 个PEP")
        print(f"状态分布: {stats}")
        
        # 生成作者合作图
        graph = create_author_graph(entries)
        print(f"\n作者合作图已生成，共 {len(graph.edges)} 条边")
        print(graph.source[:200] + "...")
        
        # 输出前3个PEP的信息
        print("\n前3个PEP信息:")
        for entry in entries[:3]:
            print(f"PEP {entry.ID}: {entry.title}")
            print(f"  状态: {entry.status}, 作者: {entry.authors}")
            if entry.created:
                print(f"  创建日期: {entry.created}")
    else:
        print(f"请求失败，状态码: {res.status_code}")