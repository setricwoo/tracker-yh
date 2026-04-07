#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从research_deduped.json生成research.html
按研报日期从新到旧排序，提取实际研报日期
"""

import json
import re
from datetime import datetime
from collections import Counter

def extract_report_date(entry):
    """
    从summary或title中提取研报实际日期
    返回: (日期字符串, 排序用的datetime对象)
    """
    summary = entry.get('summary', '')
    title = entry.get('title', '')
    text = summary + ' ' + title
    
    # 尝试匹配各种日期格式
    patterns = [
        # "Mar 13, 2026" 或 "Mar 13, 2026 ·"
        r'([A-Z][a-z]{2})\s+(\d{1,2}),?\s+(202\d)',
        # "Mar 27, 2026" 格式
        r'([A-Z][a-z]{2})\s+(\d{1,2}),\s+(202\d)',
        # "5 days ago" - 需要特殊处理
        r'(\d+)\s+days?\s+ago',
        # "Mar 2026"
        r'([A-Z][a-z]{2})\s+(202\d)',
    ]
    
    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    # 尝试提取具体日期
    for pattern in patterns[:3]:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                month_str, day, year = match.groups()
                month = months.get(month_str, 1)
                try:
                    return f"{year}-{month:02d}-{int(day):02d}", datetime(int(year), month, int(day))
                except:
                    pass
            elif len(match.groups()) == 1:
                # "X days ago"
                days = int(match.groups()[0])
                date = datetime.now() - __import__('datetime').timedelta(days=days)
                return date.strftime("%Y-%m-%d"), date
    
    # 如果提取失败，使用pub_date（截取日期部分）
    pub_date = entry.get('pub_date', '')
    if pub_date:
        try:
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00').replace('+00:00', ''))
            return dt.strftime("%Y-%m-%d"), dt
        except:
            pass
    
    return "2026-04-06", datetime(2026, 4, 6)

# 读取去重后数据
with open('data/research_deduped.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data['entries']

# 提取日期并排序（从新到旧）
for entry in entries:
    date_str, date_obj = extract_report_date(entry)
    entry['report_date'] = date_str
    entry['date_obj'] = date_obj

entries.sort(key=lambda x: x['date_obj'], reverse=True)

# HTML模板
HTML_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>【华泰固收】中东地缘跟踪 - 智库&投行研究观点</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.6;}
        .header {background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);color: white;padding: 12px 0;box-shadow: 0 2px 8px rgba(0,0,0,0.1);position: sticky;top: 0;z-index: 100;}
        .header-main {max-width: 1400px;margin: 0 auto;padding: 0 20px;display: flex;justify-content: center;align-items: center;position: relative;}
        .header-left {position: absolute; left: 20px;}
        .header-left h1 {font-size: 1.1rem; font-weight: 600; margin: 0;}
        .header-center {display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;}
        .nav-btn {color: rgba(255,255,255,0.85);text-decoration: none;padding: 6px 12px;border-radius: 6px;font-size: 0.85rem;transition: all 0.2s;white-space: nowrap;}
        .nav-btn:hover {background: rgba(255,255,255,0.15); color: white;}
        .nav-btn.active {background: rgba(255,255,255,0.2); color: white; font-weight: 500;}
        .header-right {font-size: 0.75rem; color: rgba(255,255,255,0.7); white-space: nowrap; position: absolute; right: 20px;}
        .container{max-width:1200px;margin:0 auto;padding:24px 20px;}
        .page-header {background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);color: white;padding: 32px 24px;border-radius: 12px;margin-bottom: 24px;text-align: center;}
        .page-header h2 {font-size: 1.6rem; margin-bottom: 8px;}
        .page-header p {font-size: 0.95rem; opacity: 0.9;}
        .dedup-badge {display: inline-block;background: rgba(255,255,255,0.2);padding: 4px 12px;border-radius: 20px;font-size: 0.8rem;margin-top: 8px;}
        .stats-grid {display: grid;grid-template-columns: repeat(4, 1fr);gap: 16px;margin-bottom: 24px;}
        .stat-card {background: #fff;border-radius: 12px;padding: 20px;text-align: center;box-shadow: 0 1px 3px rgba(0,0,0,0.08);border: 1px solid #e2e8f0;}
        .stat-number {font-size: 2rem; font-weight: 700; color: #1e3a5f;}
        .stat-label {font-size: 0.85rem; color: #64748b; margin-top: 4px;}
        .filter-bar {background: #fff;border-radius: 12px;padding: 16px 20px;margin-bottom: 20px;box-shadow: 0 1px 3px rgba(0,0,0,0.08);border: 1px solid #e2e8f0;}
        .filter-group {display: flex; align-items: center; gap: 10px; flex-wrap: wrap;}
        .filter-label {font-size: 0.9rem; color: #64748b; font-weight: 500;}
        .filter-btn {padding: 6px 16px;border: 1px solid #e2e8f0;background: #f8fafc;border-radius: 20px;font-size: 0.85rem;cursor: pointer;transition: all 0.2s;color: #475569;}
        .filter-btn:hover {background: #e2e8f0;}
        .filter-btn.active {background: #1e3a5f; color: white; border-color: #1e3a5f;}
        .institution-tabs {display: flex;gap: 8px;margin-bottom: 24px;flex-wrap: wrap;}
        .inst-tab {padding: 8px 16px;background: #fff;border: 1px solid #e2e8f0;border-radius: 8px;cursor: pointer;font-size: 0.9rem;transition: all 0.2s;display: flex;align-items: center;gap: 6px;}
        .inst-tab:hover {background: #f1f5f9;}
        .inst-tab.active {background: #1e3a5f; color: white; border-color: #1e3a5f;}
        .inst-tab .badge {background: #e2e8f0;color: #475569;padding: 2px 8px;border-radius: 12px;font-size: 0.75rem;}
        .inst-tab.active .badge {background: rgba(255,255,255,0.2); color: white;}
        .insights-grid {display: grid;grid-template-columns: repeat(2, 1fr);gap: 20px;}
        .insight-card {background: #fff;border-radius: 12px;padding: 20px;box-shadow: 0 1px 3px rgba(0,0,0,0.08);border: 1px solid #e2e8f0;transition: all 0.2s;display: flex;flex-direction: column;}
        .insight-card:hover {box-shadow: 0 4px 12px rgba(0,0,0,0.1);transform: translateY(-2px);}
        .insight-header {display: flex;justify-content: space-between;align-items: flex-start;margin-bottom: 12px;}
        .institution-info {display: flex;align-items: center;gap: 12px;flex: 1;min-width: 0;}
        .institution-logo {width: 40px;height: 40px;border-radius: 8px;display: flex;align-items: center;justify-content: center;font-weight: 700;font-size: 0.75rem;color: white;flex-shrink: 0;}
        .institution-detail {min-width: 0;flex: 1;}
        .institution-name {font-weight: 600;color: #1e293b;font-size: 0.95rem;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;}
        .institution-type {font-size: 0.8rem;color: #64748b;}
        .insight-date {font-size: 0.8rem;color: #94a3b8;flex-shrink: 0;margin-left: 8px;}
        .insight-title {font-size: 1.05rem;font-weight: 600;color: #1e40af;margin-bottom: 12px;line-height: 1.5;}
        .insight-keypoints {background: #f8fafc;border-radius: 8px;padding: 12px 16px;margin-bottom: 12px;flex: 1;}
        .insight-keypoints h5 {font-size: 0.8rem;color: #1e40af;margin-bottom: 8px;font-weight: 600;}
        .insight-keypoints ul {padding-left: 16px;margin: 0;}
        .insight-keypoints li {font-size: 0.9rem;color: #475569;margin-bottom: 4px;line-height: 1.5;}
        .insight-footer {display: flex;justify-content: space-between;align-items: center;padding-top: 12px;border-top: 1px solid #e2e8f0;margin-top: auto;}
        .sentiment-tag {padding: 4px 12px;border-radius: 20px;font-size: 0.8rem;font-weight: 500;}
        .sentiment-bullish {background: #dcfce7; color: #166534;}
        .sentiment-bearish {background: #fee2e2; color: #991b1b;}
        .sentiment-neutral {background: #f1f5f9; color: #475569;}
        .read-more {color: #1e40af;text-decoration: none;font-size: 0.9rem;font-weight: 500;}
        .read-more:hover {text-decoration: underline;}
        @media (max-width: 768px) {.header-main {flex-wrap: wrap; padding: 8px;}.header-left {position: relative; left: auto; width: 100%; margin-bottom: 8px;}.header-center {overflow-x: auto; flex-wrap: nowrap; justify-content: flex-start; padding: 0;}.header-right {display: none;}.stats-grid {grid-template-columns: repeat(2, 1fr);}.insights-grid {grid-template-columns: 1fr;}.institution-tabs {flex-wrap: nowrap; overflow-x: auto;}.institution-name {font-size: 0.85rem;}}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-main">
            <div class="header-left"><h1>【华泰固收】中东地缘跟踪</h1></div>
            <div class="header-center">
                <a href="index.html" class="nav-btn">首页</a>
                <a href="briefing.html" class="nav-btn">每日简报</a>
                <a href="war-situation.html" class="nav-btn">战况追踪</a>
                <a href="oil-chart.html" class="nav-btn">油价跟踪</a>
                <a href="research.html" class="nav-btn active">研究观点</a>
                <a href="polymarket.html" class="nav-btn">Polymarket</a>
            </div>
            <div class="header-right">更新时间: 2026-04-06</div>
        </div>
    </header>

    <div class="container">
        <div class="page-header">
            <h2>智库 & 投行研究观点</h2>
            <p>聚焦伊朗战争、霍尔木兹海峡、油价等中东地缘政治主题</p>
            <span class="dedup-badge">AI去重处理：从315条精选至60条核心观点 | 按研报日期排序</span>
        </div>
'''

# 统计
source_counts = Counter(e['source'] for e in entries)
total = len(entries)
tt_count = sum(1 for e in entries if e['source_type'] == 'think_tank')
ib_count = sum(1 for e in entries if e['source_type'] == 'investment_bank')
news_count = sum(1 for e in entries if e['source_type'] == 'news')

stats_html = f'''
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-number">{total}</div><div class="stat-label">核心观点</div></div>
            <div class="stat-card"><div class="stat-number">{len(source_counts)}</div><div class="stat-label">来源机构</div></div>
            <div class="stat-card"><div class="stat-number">{tt_count}</div><div class="stat-label">智库</div></div>
            <div class="stat-card"><div class="stat-number">{ib_count + news_count}</div><div class="stat-label">投行&媒体</div></div>
        </div>

        <div class="filter-bar">
            <div class="filter-group">
                <span class="filter-label">类型筛选:</span>
                <button class="filter-btn active" data-type="all">全部</button>
                <button class="filter-btn" data-type="investment_bank">投资银行</button>
                <button class="filter-btn" data-type="news">财经媒体</button>
                <button class="filter-btn" data-type="think_tank">智库</button>
            </div>
        </div>

        <div class="institution-tabs">
            <button class="inst-tab active" data-source="all">全部<span class="badge">{total}</span></button>
'''

for src, count in source_counts.most_common(12):
    short = src[:15] + '...' if len(src) > 15 else src
    stats_html += f'            <button class="inst-tab" data-source="{src}">{short}<span class="badge">{count}</span></button>\n'

stats_html += '        </div>\n\n        <div class="insights-grid" id="insightsGrid">\n'

# 翻译和情绪映射
TITLE_MAP = {
    'barclays raises': ('巴克莱上调2026年布伦特油价预测至85美元', 'bullish'),
    'goldman raises': ('高盛因史上最大供应冲击上调油价预测', 'bullish'),
    'goldman sachs oil price': ('高盛油价预测与能源展望', 'bullish'),
    'macquarie': ('麦格理：油价或达200美元（风险概率40%）', 'bullish'),
    'oil price to hit $250': ('油价或突破250-370美元', 'bullish'),
    'oil at $200': ('油价200美元？麦格理警告40%风险概率', 'bullish'),
    'iran war pushes': ('伊朗战争推动油价预测创纪录上调', 'bullish'),
    'iran war shock': ('伊朗战争冲击推动油价预测大幅上调', 'bullish'),
    'brokerages hike': ('多家投行上调油价预测', 'bullish'),
    'jpmorgan': ('摩根大通油市展望与供应分析', 'neutral'),
    'morgan stanley': ('摩根士丹利能源展望', 'neutral'),
    'bank of america': ('美银能源展望与油价预测', 'bullish'),
    'how the iran war could shift': ('伊朗战争如何改变全球能源政策', 'neutral'),
    'will the iran war redraw': ('伊朗战争会重绘全球能源版图吗', 'neutral'),
    'us-iran war': ('美伊战争对油气市场影响', 'bearish'),
    'oil supply disruption': ('石油供应中断风险分析', 'bearish'),
    'strait of hormuz': ('霍尔木兹海峡供应风险', 'bearish'),
}

COLORS = {
    'Goldman Sachs': '#7399C6', 'Morgan Stanley': '#003087', 'JPMorgan': '#003B70',
    'Citi': '#003B70', 'Bank of America': '#012169', 'Barclays': '#00aeef',
    'Deutsche Bank': '#0018a8', 'UBS': '#e60000', 'Credit Suisse': '#1e3a5f',
    'HSBC': '#db0011', 'Societe Generale': '#e50278', 'Nomura': '#c41e3a',
    'Macquarie': '#00838f', 'Reuters': '#fb8023', 'Bloomberg': '#2800d7',
    'Bloomberg/Goldman': '#2800d7', 'CNBC': '#1d5f6e', 'Atlantic Council': '#1e3a5f',
    'ECFR': '#003B5C', 'GMF': '#1e40af', 'BIS': '#1e3a5f', 'Analysts': '#64748b',
    'Investment Banks': '#1e3a5f', 'MarketWatch': '#567384'
}

SHORTS = {
    'Goldman Sachs': 'GS', 'Morgan Stanley': 'MS', 'JPMorgan': 'JPM', 'Citi': 'Citi',
    'Bank of America': 'BofA', 'Barclays': 'BARC', 'Deutsche Bank': 'DB', 'UBS': 'UBS',
    'Credit Suisse': 'CS', 'HSBC': 'HSBC', 'Societe Generale': 'SG', 'Nomura': 'NOM',
    'Macquarie': 'MQG', 'Reuters': 'RTRS', 'Bloomberg': 'BLOOM', 'Bloomberg/Goldman': 'BG',
    'CNBC': 'CNBC', 'Atlantic Council': 'AC', 'ECFR': 'ECFR', 'GMF': 'GMF',
    'BIS': 'BIS', 'Analysts': 'ANL', 'Investment Banks': 'IB', 'MarketWatch': 'MW'
}

def get_card(entry):
    source = entry['source']
    title = entry['title']
    summary = entry.get('summary', '')
    date = entry.get('report_date', '')  # 使用研报日期
    link = entry['link']
    stype = entry.get('source_type', 'other')
    
    color = COLORS.get(source, '#64748b')
    short = SHORTS.get(source, source[:3].upper())
    
    # 匹配翻译
    title_zh = title
    sentiment = 'neutral'
    for key, (zh, sent) in TITLE_MAP.items():
        if key.lower() in title.lower():
            title_zh = zh
            sentiment = sent
            break
    
    # 清理摘要
    clean = re.sub(r'<[^>]+>', ' ', summary).replace('\n', ' ').strip()
    if len(clean) > 200:
        clean = clean[:200] + '...'
    
    sent_class = {'bullish': 'sentiment-bullish', 'bearish': 'sentiment-bearish'}.get(sentiment, 'sentiment-neutral')
    sent_text = {'bullish': '看多', 'bearish': '看空'}.get(sentiment, '中性')
    
    return f'''<div class="insight-card" data-type="{stype}" data-source="{source}">
    <div class="insight-header">
        <div class="institution-info">
            <div class="institution-logo" style="background: {color}">{short}</div>
            <div class="institution-detail">
                <div class="institution-name">{source}</div>
                <div class="institution-type">{stype.replace('_', ' ').title()}</div>
            </div>
        </div>
        <div class="insight-date">{date}</div>
    </div>
    <h4 class="insight-title">{title_zh}</h4>
    <div class="insight-keypoints">
        <h5>核心要点</h5>
        <ul><li>{clean}</li></ul>
    </div>
    <div class="insight-footer">
        <span class="sentiment-tag {sent_class}">{sent_text}</span>
        <a href="{link}" class="read-more" target="_blank">查看原文 →</a>
    </div>
</div>'''

cards = [get_card(e) for e in entries]
cards_html = '\n'.join(cards)

HTML_FOOT = '''
        </div>
    </div>

    <script>
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                filterCards();
            });
        });

        document.querySelectorAll('.inst-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('.inst-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                filterCards();
            });
        });

        function filterCards() {
            const typeFilter = document.querySelector('.filter-btn.active')?.dataset.type || 'all';
            const sourceFilter = document.querySelector('.inst-tab.active')?.dataset.source || 'all';
            
            document.querySelectorAll('.insight-card').forEach(card => {
                const type = card.dataset.type;
                const source = card.dataset.source;
                
                const typeMatch = typeFilter === 'all' || type === typeFilter;
                const sourceMatch = sourceFilter === 'all' || source === sourceFilter;
                
                card.style.display = typeMatch && sourceMatch ? 'flex' : 'none';
            });
        }
    </script>
</body>
</html>'''

with open('research.html', 'w', encoding='utf-8') as f:
    f.write(HTML_HEAD + stats_html + cards_html + HTML_FOOT)

print(f'Generated research.html with {len(entries)} entries')
print(f'Sorted by report date (newest first)')
print('Top 5 sources:', dict(source_counts.most_common(5)))
