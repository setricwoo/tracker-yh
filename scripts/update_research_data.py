#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究数据抓取脚本 - 优化版投行研报抓取
精简但高效的搜索策略
"""

import json
import os
import hashlib
import re
from datetime import datetime, timedelta
import feedparser
import time

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("[WARN] duckduckgo-search not installed, search will be skipped")

# 智库RSS配置
THINK_TANK_SOURCES = [
    {"name": "Brookings Institution", "name_zh": "布鲁金斯学会", "rss": "https://www.brookings.edu/feed/", "region": "us", "type": "think_tank"},
    {"name": "CSIS", "name_zh": "战略与国际研究中心", "rss": "https://www.csis.org/rss.xml", "region": "us", "type": "think_tank"},
    {"name": "CFR", "name_zh": "外交关系委员会", "rss": "https://www.cfr.org/rss.xml", "region": "us", "type": "think_tank"},
    {"name": "PIIE", "name_zh": "彼得森国际经济研究所", "rss": "https://www.piie.com/rss.xml", "region": "us", "type": "think_tank"},
    {"name": "Carnegie Endowment", "name_zh": "卡内基国际和平基金会", "rss": "https://carnegieendowment.org/rss.xml", "region": "us", "type": "think_tank"},
    {"name": "RAND Corporation", "name_zh": "兰德公司", "rss": "https://www.rand.org/rss.xml", "region": "us", "type": "think_tank"},
    {"name": "Atlantic Council", "name_zh": "大西洋理事会", "rss": "https://www.atlanticcouncil.org/feed/", "region": "us", "type": "think_tank"},
    {"name": "Chatham House", "name_zh": "查塔姆研究所", "rss": "https://www.chathamhouse.org/feed", "region": "eu", "type": "think_tank"},
    {"name": "ECFR", "name_zh": "欧洲外交关系委员会", "rss": "https://ecfr.eu/feed/", "region": "eu", "type": "think_tank"},
    {"name": "GMF", "name_zh": "德国马歇尔基金会", "rss": "https://www.gmfus.org/rss.xml", "region": "eu", "type": "think_tank"},
    {"name": "IMF", "name_zh": "国际货币基金组织", "rss": "https://www.imf.org/en/Publications/RSS", "region": "global", "type": "institution"},
    {"name": "BIS", "name_zh": "国际清算银行", "rss": "https://www.bis.org/doclist/bis_fsi_publs.rss", "region": "global", "type": "institution"},
]

# ==========================================
# 投行研报搜索配置 - 精简高效版
# ==========================================

IB_RESEARCH_SEARCHES = [
    # Tier 1: 顶级投行 - 官网+媒体报道
    {"query": "Goldman Sachs oil price forecast brent 2025", "source": "Goldman Sachs", "source_zh": "高盛", "priority": 1},
    {"query": "Morgan Stanley energy outlook oil forecast", "source": "Morgan Stanley", "source_zh": "大摩", "priority": 1},
    {"query": "JPMorgan oil supply disruption forecast", "source": "JPMorgan", "source_zh": "小摩", "priority": 1},
    {"query": "Citi commodity outlook oil price target", "source": "Citi", "source_zh": "花旗", "priority": 1},
    {"query": "Bank of America energy outlook oil forecast", "source": "Bank of America", "source_zh": "美银", "priority": 1},
    
    # Tier 2: 欧洲投行
    {"query": "Deutsche Bank oil price forecast commodity", "source": "Deutsche Bank", "source_zh": "德银", "priority": 2},
    {"query": "Barclays oil price target energy research", "source": "Barclays", "source_zh": "巴克莱", "priority": 2},
    {"query": "UBS commodity outlook oil forecast", "source": "UBS", "source_zh": "瑞银", "priority": 2},
    {"query": "Credit Suisse oil market outlook", "source": "Credit Suisse", "source_zh": "瑞信", "priority": 2},
    
    # Tier 3: 其他重要投行
    {"query": "HSBC oil price forecast commodity", "source": "HSBC", "source_zh": "汇丰", "priority": 3},
    {"query": "Societe Generale oil forecast energy", "source": "Societe Generale", "source_zh": "法兴", "priority": 3},
    {"query": "Nomura oil price forecast energy", "source": "Nomura", "source_zh": "野村", "priority": 3},
    {"query": "Macquarie commodity outlook oil", "source": "Macquarie", "source_zh": "麦格理", "priority": 3},
    
    # Tier 4: 财经媒体报道的投行观点
    {"query": "Bloomberg Goldman Sachs oil price forecast", "source": "Bloomberg/Goldman", "source_zh": "彭博/高盛", "priority": 1},
    {"query": "Bloomberg analyst oil price target", "source": "Bloomberg", "source_zh": "彭博", "priority": 1},
    {"query": "Reuters investment bank oil forecast", "source": "Reuters", "source_zh": "路透", "priority": 1},
    {"query": "Reuters analyst oil price middle east", "source": "Reuters", "source_zh": "路透", "priority": 1},
    {"query": "Financial Times oil price forecast analyst", "source": "FT", "source_zh": "金融时报", "priority": 1},
    {"query": "Wall Street Journal energy analysts forecast", "source": "WSJ", "source_zh": "华尔街日报", "priority": 1},
    {"query": "CNBC oil price forecast analyst", "source": "CNBC", "source_zh": "CNBC", "priority": 2},
    {"query": "MarketWatch oil forecast investment bank", "source": "MarketWatch", "source_zh": "MarketWatch", "priority": 2},
    
    # Tier 5: 特定主题搜索
    {"query": "Hormuz Strait oil supply analyst forecast", "source": "Analysts", "source_zh": "分析师", "priority": 1},
    {"query": "Iran war oil supply disruption analyst", "source": "Analysts", "source_zh": "分析师", "priority": 1},
    {"query": "Middle East oil supply risk forecast", "source": "Analysts", "source_zh": "分析师", "priority": 1},
    {"query": "Brent crude price forecast 2025", "source": "Analysts", "source_zh": "分析师", "priority": 1},
    {"query": "WTI oil price target investment bank", "source": "Investment Banks", "source_zh": "投行", "priority": 1},
    {"query": "oil price outlook geopolitical risk", "source": "Analysts", "source_zh": "分析师", "priority": 2},
    
    # Tier 6: 关键智库研究（通过搜索获取，RSS内容不匹配）
    # 国际金融组织
    {"query": "IMF Iran war oil supply Middle East 2025", "source": "IMF", "source_zh": "国际货币基金组织", "priority": 1},
    {"query": "IMF World Bank Iran conflict energy shock", "source": "IMF", "source_zh": "国际货币基金组织", "priority": 1},
    {"query": "IMF Middle East oil supply disruption forecast", "source": "IMF", "source_zh": "国际货币基金组织", "priority": 1},
    {"query": "BIS Iran war oil supply financial stability", "source": "BIS", "source_zh": "国际清算银行", "priority": 1},
    {"query": "BIS energy supply shock commodity prices", "source": "BIS", "source_zh": "国际清算银行", "priority": 1},
    {"query": "World Bank Iran war oil Middle East economy", "source": "World Bank", "source_zh": "世界银行", "priority": 1},
    
    # 美国经济智库
    {"query": "PIIE Peterson Institute Iran oil sanctions", "source": "PIIE", "source_zh": "彼得森国际经济研究所", "priority": 1},
    {"query": "PIIE oil price Middle East supply shock 2025", "source": "PIIE", "source_zh": "彼得森国际经济研究所", "priority": 1},
    {"query": "Brookings Institution Iran war oil Middle East", "source": "Brookings", "source_zh": "布鲁金斯学会", "priority": 1},
    {"query": "Brookings energy security Hormuz Strait", "source": "Brookings", "source_zh": "布鲁金斯学会", "priority": 1},
    
    # 安全/战略智库
    {"query": "CSIS energy security Iran Hormuz Strait", "source": "CSIS", "source_zh": "战略与国际研究中心", "priority": 1},
    {"query": "CSIS Middle East oil supply chain disruption", "source": "CSIS", "source_zh": "战略与国际研究中心", "priority": 1},
    {"query": "CFR Iran war oil price energy outlook", "source": "CFR", "source_zh": "外交关系委员会", "priority": 1},
    {"query": "CFR Council Foreign Relations Hormuz oil", "source": "CFR", "source_zh": "外交关系委员会", "priority": 1},
    {"query": "RAND Corporation Iran energy security", "source": "RAND", "source_zh": "兰德公司", "priority": 1},
    {"query": "Carnegie Endowment Iran oil Middle East war", "source": "Carnegie", "source_zh": "卡内基国际和平基金会", "priority": 1},
    {"query": "Chatham House Hormuz oil Middle East", "source": "Chatham House", "source_zh": "查塔姆研究所", "priority": 1},
    
    # IEA国际能源署
    {"query": "IEA International Energy Agency Iran oil supply", "source": "IEA", "source_zh": "国际能源署", "priority": 1},
    {"query": "IEA Hormuz Strait oil disruption forecast", "source": "IEA", "source_zh": "国际能源署", "priority": 1},
]

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def parse_date(entry):
    """解析日期"""
    for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if hasattr(entry, field) and getattr(entry, field):
            return datetime(*getattr(entry, field)[:6])
    return None

def generate_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def fetch_rss_source(source, days=15):
    """抓取单个RSS源"""
    log(f"[RSS] {source['name_zh']}")
    
    try:
        feed = feedparser.parse(source['rss'])
        entries = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for entry in feed.entries:
            entry_date = parse_date(entry)
            if entry_date and entry_date < cutoff:
                continue
            
            item = {
                "id": generate_id(f"{source['name']}_{entry.get('title', '')}"),
                "title": entry.get('title', ''),
                "summary": entry.get('summary', '') or entry.get('description', ''),
                "link": entry.get('link', ''),
                "pub_date": entry_date.isoformat() if entry_date else datetime.now().isoformat(),
                "source": source['name'],
                "source_zh": source['name_zh'],
                "source_type": source['type'],
                "region": source['region'],
                "fetch_method": "rss"
            }
            entries.append(item)
        
        log(f"  OK {len(entries)} entries")
        return entries
        
    except Exception as e:
        log(f"  ERR {e}")
        return []

def fetch_all_rss(days=15):
    """抓取所有RSS"""
    all_entries = []
    for source in THINK_TANK_SOURCES:
        entries = fetch_rss_source(source, days)
        all_entries.extend(entries)
    return all_entries

def search_investment_banks(max_results=8):
    """
    搜索投行研报 - 后续更新使用（最近72小时/一周）
    首次运行可能需要调整为'w'(周)或'm'(月)以获取足够数据
    """
    if not DDGS_AVAILABLE:
        log("[WARN] Search skipped - duckduckgo-search not available")
        return []
    
    log(f"\n[Search] Starting IB research search (recent 72h/1w)...")
    log(f"[Search] Total tasks: {len(IB_RESEARCH_SEARCHES)}")
    all_results = []
    
    # 时间范围: 'd'=24h, 'w'=1周, 'm'=1月
    # 为获取足够数据，使用'w'(周)或'm'(月)
    timelimit = 'w'  # 最近一周
    
    try:
        with DDGS() as ddgs:
            for i, task in enumerate(IB_RESEARCH_SEARCHES, 1):
                query = task["query"]
                source = task["source"]
                priority = task["priority"]
                
                log(f"[{i}/{len(IB_RESEARCH_SEARCHES)}] [P{priority}] {source}: {query[:45]}...")
                
                try:
                    # 使用周时间范围（约72小时）
                    results = list(ddgs.text(query, max_results=max_results, timelimit=timelimit))
                    
                    for r in results:
                        # 提取域名
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', r['href'])
                        domain = domain_match.group(1) if domain_match else "unknown"
                        
                        item = {
                            "id": generate_id(f"search_{r['title']}"),
                            "title": r['title'],
                            "summary": r['body'][:500] if len(r['body']) > 500 else r['body'],
                            "link": r['href'],
                            "pub_date": datetime.now().isoformat(),
                            "source": source,
                            "source_zh": task["source_zh"],
                            "source_type": "investment_bank" if "Bloomberg" not in source and "Reuters" not in source and "FT" not in source and "WSJ" not in source and "CNBC" not in source and "MarketWatch" not in source else "news",
                            "region": "us",
                            "fetch_method": "search",
                            "search_query": query,
                            "priority": priority,
                            "domain": domain
                        }
                        all_results.append(item)
                    
                    log(f"  OK {len(results)} results")
                    
                    # 短暂延迟
                    time.sleep(0.3)
                    
                except Exception as e:
                    log(f"  ERR {str(e)[:50]}")
                    continue
                
    except Exception as e:
        log(f"[ERR] Search failed: {e}")
    
    # 去重（基于链接）
    seen_links = set()
    unique_results = []
    for item in all_results:
        if item['link'] not in seen_links:
            seen_links.add(item['link'])
            unique_results.append(item)
    
    log(f"[Search] Total unique: {len(unique_results)} (from {len(all_results)} raw)")
    return unique_results

def save_raw_data(think_tank_entries, search_results):
    """保存原始数据"""
    output = {
        "fetch_time": datetime.now().isoformat(),
        "date_range": {
            "from": (datetime.now() - timedelta(days=15)).isoformat(),
            "to": datetime.now().isoformat()
        },
        "think_tank_entries": think_tank_entries,
        "ib_search_results": search_results,
        "total_raw_entries": len(think_tank_entries) + len(search_results),
        "search_summary": {
            "search_tasks": len(IB_RESEARCH_SEARCHES),
            "total_results": len(search_results)
        }
    }
    
    os.makedirs("data", exist_ok=True)
    filepath = "data/research_raw_data.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    log(f"\n[Saved] {filepath}")
    log(f"  - Think tank: {len(think_tank_entries)}")
    log(f"  - IB/News: {len(search_results)}")
    
    return filepath

def main():
    log("="*60)
    log("Research Data Fetcher - Optimized IB Search")
    log("="*60)
    
    # 1. 抓取智库RSS
    log("\n[Step 1] Fetching think tank RSS...")
    think_tank_entries = fetch_all_rss(days=15)
    
    # 2. 搜索投行研报
    log("\n[Step 2] Searching IB research...")
    search_results = search_investment_banks(max_results=8)
    
    # 3. 保存
    log("\n[Step 3] Saving...")
    filepath = save_raw_data(think_tank_entries, search_results)
    
    log("\n" + "="*60)
    log(f"Complete! Total: {len(think_tank_entries) + len(search_results)}")
    log("="*60)

if __name__ == "__main__":
    main()
