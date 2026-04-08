#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Polymarket获取数据并保存到JSON文件
HTML页面会自动从JSON文件加载数据，不需要重新生成HTML
"""

import requests
import json
import time
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Any

# Polymarket APIs
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# 事件slug列表
EVENT_SLUGS = [
    "trump-announces-end-of-military-operations-against-iran-by",
    "us-x-iran-ceasefire-by",
    "avg-of-ships-transiting-strait-of-hormuz-end-of-april",
    "strait-of-hormuz-traffic-returns-to-normal-by-april-30",
    "what-price-will-wti-hit-in-april-2026",
    "cl-hit-jun-2026",
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://polymarket.com",
    "Referer": "https://polymarket.com/",
}

# 颜色配置 - 使用鲜明可见的颜色
COLORS = {
    "blue": "#2563eb",      # 鲜明蓝色
    "indigo": "#4f46e5",    # 鲜明紫色
    "slate": "#0ea5e9",     # 改用青色（更可见）
    "teal": "#10b981",      # 鲜明绿色
    "emerald": "#059669",   # 深绿色
    "sky": "#f59e0b",       # 改用橙色（更可见）
    "amber": "#f97316",     # 橙色
    "rose": "#e11d48",      # 玫红色
}


def get_event_by_slug(slug: str, max_retries: int = 2) -> Dict:
    """通过slug获取事件数据，带重试机制"""
    url = f"{GAMMA_API}/events"
    params = {"slug": slug, "_s": "slug"}

    for attempt in range(max_retries):
        try:
            time.sleep(0.3)  # 减少延迟
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                event = data[0]
                event_id = event.get("id")
                if event_id:
                    time.sleep(0.2)  # 减少延迟
                    detail_url = f"{GAMMA_API}/events/{event_id}"
                    detail_resp = requests.get(detail_url, headers=HEADERS, timeout=15)
                    if detail_resp.status_code == 200:
                        return detail_resp.json()
                return event
            return {}
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  获取失败 {slug} (尝试 {attempt+1}/{max_retries}): {e}")
                time.sleep(1)  # 失败后等待
            else:
                print(f"  获取事件失败 {slug}: {e}")
                return {}


def get_price_history(token_id: str, interval: str = "all", max_retries: int = 1) -> List[Dict]:
    """获取价格历史数据，带重试机制"""
    url = f"{CLOB_API}/prices-history"
    params = {"market": token_id, "interval": interval}

    for attempt in range(max_retries):
        try:
            time.sleep(0.1)  # 减少延迟
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("history", [])
        except:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            # 尝试其他interval
            for alt_interval in ["max", "1d"]:
                try:
                    params["interval"] = alt_interval
                    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("history", [])
                except:
                    pass
            return []


def parse_json_field(field) -> List:
    """解析JSON字段"""
    if isinstance(field, str):
        try:
            return json.loads(field)
        except:
            return []
    elif isinstance(field, list):
        return field
    return []


def fetch_all_events_data() -> Dict:
    """获取所有事件数据"""
    # 尝试加载之前保存的数据
    prev_data = {}
    try:
        if os.path.exists("data/polymarket_data.json"):
            with open("data/polymarket_data.json", "r", encoding="utf-8") as f:
                saved = json.load(f)
                prev_data = saved.get("events", {})
    except:
        pass

    all_data = {}

    for slug in EVENT_SLUGS:
        print(f"获取: {slug}")
        event = get_event_by_slug(slug)
        if not event:
            # 如果获取失败，使用之前保存的数据
            if slug in prev_data:
                print(f"  使用缓存数据")
                all_data[slug] = prev_data[slug]
            continue

        event_id = event.get("id")
        event_title = event.get("title", "")
        markets = event.get("markets", [])

        markets_data = []
        for m in markets:
            question = m.get("question", "")
            outcomes = parse_json_field(m.get("outcomes"))
            outcome_prices = parse_json_field(m.get("outcomePrices"))
            clob_token_ids = parse_json_field(m.get("clobTokenIds"))
            volume = m.get("volume", "0")

            market_info = {
                "question": question,
                "outcomes": {},
                "volume": volume,
                "closed": m.get("closed", False),
            }

            for i, outcome_name in enumerate(outcomes):
                token_id = clob_token_ids[i] if i < len(clob_token_ids) else ""
                current_price = 0.0
                if i < len(outcome_prices):
                    try:
                        current_price = float(outcome_prices[i])
                    except:
                        pass

                # 获取价格历史
                price_history = []
                if token_id and not m.get("closed", False):
                    history = get_price_history(token_id)
                    for h in history:
                        try:
                            ts = h.get("t", 0)
                            price = h.get("p", 0)
                            beijing_tz = ZoneInfo("Asia/Shanghai")
                            dt = datetime.fromtimestamp(ts, tz=beijing_tz)
                            price_history.append({
                                "time": dt.strftime('%m-%d %H:%M'),
                                "timestamp": ts,
                                "price": round(price * 100, 2)
                            })
                        except:
                            pass
                    # 移除多余延迟

                market_info["outcomes"][outcome_name] = {
                    "currentPrice": round(current_price * 100, 2),
                    "priceHistory": price_history
                }

            markets_data.append(market_info)

        all_data[slug] = {
            "title": event_title,
            "markets": markets_data
        }

    return all_data


def generate_html(data: Dict) -> str:
    """生成完整的HTML页面"""
    beijing_tz = ZoneInfo("Asia/Shanghai")
    update_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>【华泰固收】中东地缘跟踪 - Polymarket预测市场</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #1e293b; }
        .chart-container { position: relative; height: 300px; width: 100%; }
        .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .positive { color: #059669; }
        .negative { color: #dc2626; }
        /* 统一导航栏样式 */
        .header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            color: white;
            padding: 12px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header-main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-left h1 {
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
        }
        .header-center {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .nav-btn {
            color: rgba(255,255,255,0.85);
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            transition: all 0.2s;
            white-space: nowrap;
        }
        .nav-btn:hover {
            background: rgba(255,255,255,0.15);
            color: white;
        }
        .nav-btn.active {
            background: rgba(255,255,255,0.2);
            color: white;
            font-weight: 500;
        }
        .header-right {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.7);
            white-space: nowrap;
        }
        /* 手机端适配 */
        @media (max-width: 768px) {
            .header-main { flex-wrap: wrap; padding: 4px 8px; gap: 4px; position: relative; }
            .header-left { position: relative; left: auto; width: 100%; text-align: left; order: 1; }
            .header h1 { font-size: 0.9rem; white-space: nowrap; margin: 0; padding: 2px 0; }
            .header-center-wrapper { 
                order: 2; 
                width: 100%; 
                display: flex; 
                align-items: center; 
                position: relative;
                margin-top: 2px;
            }
            .header-center { 
                flex: 1;
                justify-content: flex-start; 
                gap: 4px; 
                flex-wrap: nowrap; 
                overflow-x: auto; 
                -webkit-overflow-scrolling: touch; 
                scrollbar-width: none; 
                position: relative; 
                padding: 0 4px; 
            }
            .header-center::-webkit-scrollbar { display: none; }
            .nav-btn { padding: 4px 8px; font-size: 0.7rem; white-space: nowrap; flex: 0 0 auto; text-align: center; }
            .header-right { display: none; }
            .chart-container { height: 220px; }
            /* 移动端字体大小调整 */
            .text-3xl { font-size: 1.5rem !important; }
            .text-2xl { font-size: 1.25rem !important; }
            .text-xl { font-size: 1.1rem !important; }
            .text-lg { font-size: 1rem !important; }
            .text-base { font-size: 0.9rem !important; }
            .text-sm { font-size: 0.8rem !important; }
            .p-6 { padding: 1rem !important; }
            .py-8 { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            .mb-8 { margin-bottom: 1rem !important; }
            .gap-6 { gap: 1rem !important; }
            /* 移动端滚动箭头 */
            .nav-arrow {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 20px;
                height: 28px;
                background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
                color: rgba(255,255,255,0.7);
                font-size: 12px;
                cursor: pointer;
                flex-shrink: 0;
                z-index: 10;
            }
            .nav-arrow.hidden { display: none; }
        }
        @media (min-width: 769px) {
            .nav-arrow { display: none !important; }
            .header-center-wrapper { display: contents; }
        }
        @media (max-width: 480px) {
            .header-main { padding: 6px 8px; gap: 6px; }
            .header h1 { font-size: 0.9rem; }
            .header-center { gap: 4px; }
            .nav-btn { padding: 5px 8px; font-size: 0.7rem; min-width: 70px; max-width: 100px; }
            .header-right { display: none; }
        }
    </style>
</head>
<body class="min-h-screen">
    <div class="header">
        <div class="header-main">
            <div class="header-left">
                <h1>【华泰固收】中东地缘跟踪</h1>
            </div>
            <div class="header-center-wrapper">
                <div class="nav-arrow nav-arrow-left" id="navArrowLeft">◀</div>
                <div class="header-center" id="navCenter">
                    <a href="index.html" class="nav-btn">海峡跟踪</a>
                    <a href="polymarket.html" class="nav-btn active">Polymarket</a>
                    <a href="data-tracking.html" class="nav-btn">全球市场</a>
                    <a href="war-situation.html" class="nav-btn">战局形势</a>
                    <a href="news.html" class="nav-btn">实时新闻</a>
                    <a href="briefing.html" class="nav-btn">每日简报</a>
                    <a href="oil-chart.html" class="nav-btn">原油图谱</a>
                </div>
                <div class="nav-arrow nav-arrow-right" id="navArrowRight">▶</div>
            </div>
        </div>
    </div>
    <script>
        // 移动端导航滚动箭头控制
        (function() {
            var navCenter = document.getElementById('navCenter');
            var arrowLeft = document.getElementById('navArrowLeft');
            var arrowRight = document.getElementById('navArrowRight');
            if (!navCenter || !arrowLeft || !arrowRight) return;
            
            function updateArrows() {
                var scrollLeft = navCenter.scrollLeft;
                var scrollWidth = navCenter.scrollWidth;
                var clientWidth = navCenter.clientWidth;
                var canScrollLeft = scrollLeft > 5;
                var canScrollRight = scrollLeft < scrollWidth - clientWidth - 5;
                
                arrowLeft.classList.toggle('hidden', !canScrollLeft);
                arrowRight.classList.toggle('hidden', !canScrollRight);
            }
            
            arrowLeft.addEventListener('click', function() {
                navCenter.scrollBy({ left: -100, behavior: 'smooth' });
            });
            arrowRight.addEventListener('click', function() {
                navCenter.scrollBy({ left: 100, behavior: 'smooth' });
            });
            
            navCenter.addEventListener('scroll', updateArrows, { passive: true });
            window.addEventListener('resize', updateArrows, { passive: true });
            window.addEventListener('pageshow', updateArrows);
            
            // 初始化
            setTimeout(updateArrows, 100);
            setTimeout(updateArrows, 500);
        })();
    </script>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-slate-800 mb-2">伊朗相关预测市场追踪</h1>
            <p class="text-slate-500">基于 Polymarket 实时数据</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
'''

    # 图表计数器
    chart_idx = 0

    # 1. 特朗普宣布结束军事行动
    trump_data = data.get("trump-announces-end-of-military-operations-against-iran-by", {})
    html += generate_event_card(trump_data, "特朗普宣布结束对伊朗军事行动", "不同截止日期的概率预测",
                                 ["April 7th", "April 15th", "April 30th", "June 30th"],
                                 ["blue", "indigo", "teal", "sky"], chart_idx)
    chart_idx += 1

    # 2. 美伊停火
    ceasefire_data = data.get("us-x-iran-ceasefire-by", {})
    html += generate_event_card(ceasefire_data, "美伊停火时间", "不同截止日期的概率预测",
                                 ["April 30", "May 31", "June 30", "December 31"],
                                 ["blue", "indigo", "teal", "sky"], chart_idx)
    chart_idx += 1

    # 3. 霍尔木兹海峡船舶数量
    ships_data = data.get("avg-of-ships-transiting-strait-of-hormuz-end-of-april", {})
    html += generate_ships_card(ships_data, chart_idx)
    chart_idx += 1

    # 4. 霍尔木兹海峡恢复正常
    normal_data = data.get("strait-of-hormuz-traffic-returns-to-normal-by-april-30", {})
    html += generate_simple_card(normal_data, "霍尔木兹海峡恢复正常", "4月30日前恢复正常的概率",
                                  chart_idx, "indigo")
    chart_idx += 1

    # 5. 4月原油价格
    oil_april_data = data.get("what-price-will-wti-hit-in-april-2026", {})
    html += generate_oil_card(oil_april_data, "4月原油价格预测", "WTI期货价格4月底前触碰概率",
                               chart_idx)
    chart_idx += 1

    # 6. 6月原油价格
    oil_june_data = data.get("cl-hit-jun-2026", {})
    html += generate_oil_card(oil_june_data, "6月原油价格预测", "CL期货价格6月底前触碰概率",
                               chart_idx)
    chart_idx += 1

    html += '''
        </div>
    </div>

    <footer class="bg-white border-t border-slate-200 mt-12 py-6">
        <div class="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm">
            <p>数据来源: Polymarket | 仅供信息参考，不构成投资建议</p>
        </div>
    </footer>
</body>
</html>
'''
    return html


def generate_event_card(event_data: Dict, title: str, subtitle: str,
                        date_labels: List[str], colors: List[str], chart_idx: int) -> str:
    """生成事件卡片HTML"""
    markets = event_data.get("markets", [])

    # 查找匹配的市场
    matched_markets = []
    for label in date_labels:
        for m in markets:
            q = m.get("question", "").lower()
            if label.lower() in q and not m.get("closed", False):
                matched_markets.append({"label": label, "market": m})
                break

    if not matched_markets:
        return ""

    # 生成概率显示
    prob_html = '<div class="grid grid-cols-2 gap-2 mb-4">\n'
    color_list = list(COLORS.values())
    datasets = []
    all_times = set()

    for i, item in enumerate(matched_markets):
        label = item["label"]
        m = item["market"]
        outcomes = m.get("outcomes", {})
        yes_price = outcomes.get("Yes", {}).get("currentPrice", 0)
        volume = float(m.get("volume", 0))
        volume_str = f"${int(volume/1000)}K" if volume > 0 else ""

        color = color_list[i % len(color_list)]
        prob_html += f'''            <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full" style="background-color: {color}"></div>
                <span class="text-sm text-slate-700">{label}:</span>
                <span class="text-lg font-bold" style="color: {color}">{yes_price}%</span>
                <span class="text-xs text-slate-500">({volume_str})</span>
            </div>\n'''

        # 收集历史数据
        history = outcomes.get("Yes", {}).get("priceHistory", [])
        data_points = {}
        for h in history:
            t = h["time"]
            all_times.add(t)
            data_points[t] = h["price"]

        datasets.append({
            "label": label,
            "data": data_points,
            "color": color
        })

    prob_html += '        </div>\n'

    # 排序时间点
    sorted_times = sorted(list(all_times))
    labels_json = json.dumps(sorted_times)

    # 生成数据集
    chart_datasets = []
    for ds in datasets:
        data_arr = [ds["data"].get(t, None) for t in sorted_times]
        chart_datasets.append({
            "label": ds["label"],
            "data": data_arr,
            "borderColor": ds["color"],
            "backgroundColor": ds["color"] + "1a",
            "borderWidth": 2,
            "fill": False,
            "tension": 0.4,
            "pointRadius": 0,
            "pointHoverRadius": 4
        })

    chart_id = f"chart_{chart_idx}"

    html = f'''            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-1">{title}</h2>
                <p class="text-sm text-slate-600 mb-4">{subtitle}</p>

                {prob_html}

                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('{chart_id}'), {{
                    type: 'line',
                    data: {{
                        labels: {labels_json},
                        datasets: {json.dumps(chart_datasets)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ intersect: false, mode: 'index' }},
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#334155', font: {{ size: 11 }} }} }}
                        }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b', maxTicksLimit: 10 }} }},
                            y: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b' }} }}
                        }}
                    }}
                }});
            </script>
'''
    return html


def generate_ships_card(ships_data: Dict, chart_idx: int) -> str:
    """生成船舶数量卡片 - 选取概率最高的6个区间，显示为线图"""
    markets = ships_data.get("markets", [])

    # 收集所有市场数据（包含历史）
    all_markets = []
    for m in markets:
        q = m.get("question", "")
        outcomes = m.get("outcomes", {})
        yes_price = outcomes.get("Yes", {}).get("currentPrice", 0)
        history = outcomes.get("Yes", {}).get("priceHistory", [])

        # 提取区间标签
        import re
        match = re.search(r'between (\d+) and (\d+)', q.lower())
        if match:
            label = f"{match.group(1)}-{match.group(2)}"
        elif "60 or more" in q.lower():
            label = "60+"
        else:
            continue

        all_markets.append({
            "label": label,
            "price": yes_price,
            "history": history
        })

    if not all_markets:
        return ""

    # 按概率排序，取最高的6个
    all_markets.sort(key=lambda x: x["price"], reverse=True)
    top_markets = all_markets[:6]

    color_list = list(COLORS.values())

    # 生成概率显示
    prob_html = '<div class="grid grid-cols-3 gap-2 mb-4">\n'
    for i, m in enumerate(top_markets):
        color = color_list[i % len(color_list)]
        prob_html += f'''            <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full" style="background-color: {color}"></div>
                <span class="text-sm text-slate-700">{m["label"]}:</span>
                <span class="text-lg font-bold" style="color: {color}">{m["price"]}%</span>
            </div>\n'''
    prob_html += '        </div>\n'

    # 收集所有时间点
    all_times = set()
    for m in top_markets:
        for h in m["history"]:
            all_times.add(h["time"])

    sorted_times = sorted(list(all_times))

    # 生成数据集
    chart_datasets = []
    for i, m in enumerate(top_markets):
        color = color_list[i % len(color_list)]
        data_points = {}
        for h in m["history"]:
            data_points[h["time"]] = h["price"]

        data_arr = [data_points.get(t, None) for t in sorted_times]
        chart_datasets.append({
            "label": m["label"],
            "data": data_arr,
            "borderColor": color,
            "backgroundColor": color + "1a",
            "borderWidth": 2,
            "fill": False,
            "tension": 0.4,
            "pointRadius": 0,
            "pointHoverRadius": 4
        })

    chart_id = f"chart_{chart_idx}"

    html = f'''            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-1">4月霍尔木兹海峡船舶数量</h2>
                <p class="text-sm text-slate-600 mb-4">平均每日通过船舶数量的概率分布 (Top 6)</p>

                {prob_html}

                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('{chart_id}'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(sorted_times)},
                        datasets: {json.dumps(chart_datasets)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ intersect: false, mode: 'index' }},
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#334155', font: {{ size: 11 }} }} }}
                        }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b', maxTicksLimit: 10 }} }},
                            y: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b' }} }}
                        }}
                    }}
                }});
            </script>
'''
    return html


def generate_simple_card(event_data: Dict, title: str, subtitle: str,
                         chart_idx: int, color_name: str) -> str:
    """生成简单Yes/No卡片"""
    markets = event_data.get("markets", [])
    if not markets:
        return ""

    m = markets[0]
    outcomes = m.get("outcomes", {})
    yes_price = outcomes.get("Yes", {}).get("currentPrice", 0)
    no_price = outcomes.get("No", {}).get("currentPrice", 100 - yes_price)

    history = outcomes.get("Yes", {}).get("priceHistory", [])
    labels = [h["time"] for h in history]
    data = [h["price"] for h in history]

    color = COLORS.get(color_name, COLORS["blue"])
    chart_id = f"chart_{chart_idx}"

    html = f'''            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-1">{title}</h2>
                <p class="text-sm text-slate-600 mb-4">{subtitle}</p>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="text-center p-4 bg-slate-100 rounded-lg border border-slate-200">
                        <div class="text-3xl font-bold" style="color: {color}">{yes_price}%</div>
                        <div class="text-sm text-slate-500 mt-1">Yes</div>
                    </div>
                    <div class="text-center p-4 bg-slate-100 rounded-lg border border-slate-200">
                        <div class="text-3xl font-bold text-slate-600">{no_price}%</div>
                        <div class="text-sm text-slate-500 mt-1">No</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('{chart_id}'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: 'Yes (%)',
                            data: {json.dumps(data)},
                            borderColor: '{color}',
                            backgroundColor: '{color}' + '1a',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.4,
                            pointRadius: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b', maxTicksLimit: 10 }} }},
                            y: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b' }} }}
                        }}
                    }}
                }});
            </script>
'''
    return html


def generate_oil_card(oil_data: Dict, title: str, subtitle: str,
                      chart_idx: int) -> str:
    """生成原油价格卡片 - 选取概率最高的6个价格，显示为线图"""
    markets = oil_data.get("markets", [])

    # 收集所有价格数据（包含历史）
    all_prices = []
    for m in markets:
        q = m.get("question", "")
        outcomes = m.get("outcomes", {})
        yes_price = outcomes.get("Yes", {}).get("currentPrice", 0)
        history = outcomes.get("Yes", {}).get("priceHistory", [])

        # 提取价格
        import re
        match = re.search(r'\$(\d+)', q)
        if match:
            price_label = f"${match.group(1)}"
            # 排除已确定的价格（100%或0%）
            if 0 < yes_price < 100:
                all_prices.append({
                    "label": price_label,
                    "price": yes_price,
                    "history": history
                })

    if not all_prices:
        return ""

    # 按概率排序，取最高的6个
    all_prices.sort(key=lambda x: x["price"], reverse=True)
    top_prices = all_prices[:6]

    color_list = list(COLORS.values())

    # 生成概率显示
    prob_html = '<div class="grid grid-cols-3 gap-2 mb-4">\n'
    for i, p in enumerate(top_prices):
        color = color_list[i % len(color_list)]
        prob_html += f'''            <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full" style="background-color: {color}"></div>
                <span class="text-sm text-slate-700">{p["label"]}:</span>
                <span class="text-lg font-bold" style="color: {color}">{p["price"]}%</span>
            </div>\n'''
    prob_html += '        </div>\n'

    # 收集所有时间点
    all_times = set()
    for p in top_prices:
        for h in p["history"]:
            all_times.add(h["time"])

    sorted_times = sorted(list(all_times))

    # 生成数据集
    chart_datasets = []
    for i, p in enumerate(top_prices):
        color = color_list[i % len(color_list)]
        data_points = {}
        for h in p["history"]:
            data_points[h["time"]] = h["price"]

        data_arr = [data_points.get(t, None) for t in sorted_times]
        chart_datasets.append({
            "label": p["label"],
            "data": data_arr,
            "borderColor": color,
            "backgroundColor": color + "1a",
            "borderWidth": 2,
            "fill": False,
            "tension": 0.4,
            "pointRadius": 0,
            "pointHoverRadius": 4
        })

    chart_id = f"chart_{chart_idx}"

    html = f'''            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-1">{title}</h2>
                <p class="text-sm text-slate-600 mb-4">{subtitle} (Top 6)</p>

                {prob_html}

                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('{chart_id}'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(sorted_times)},
                        datasets: {json.dumps(chart_datasets)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ intersect: false, mode: 'index' }},
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#334155', font: {{ size: 11 }} }} }}
                        }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b', maxTicksLimit: 10 }} }},
                            y: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5, drawBorder: false }}, ticks: {{ color: '#64748b' }} }}
                        }}
                    }}
                }});
            </script>
'''
    return html


def generate_party_card(event_data: Dict, title: str, subtitle: str, chart_idx: int) -> str:
    """生成党派预测卡片（用于中期选举）"""
    markets = event_data.get("markets", [])
    if not markets:
        return ""

    m = markets[0]
    outcomes = m.get("outcomes", {})

    # 找到Republican/Democrat或类似键
    rep_key = next((k for k in outcomes if "repub" in k.lower() or "republican" in k.lower()), None)
    dem_key = next((k for k in outcomes if "demo" in k.lower() or "democrat" in k.lower()), None)
    if not rep_key or not dem_key:
        keys = list(outcomes.keys())
        if len(keys) >= 2:
            rep_key, dem_key = keys[0], keys[1]
        else:
            return ""

    rep_price = outcomes[rep_key].get("currentPrice", 0)
    dem_price = outcomes[dem_key].get("currentPrice", 0)
    rep_history = outcomes[rep_key].get("priceHistory", [])
    dem_history = outcomes[dem_key].get("priceHistory", [])

    all_times = set(h["time"] for h in rep_history) | set(h["time"] for h in dem_history)
    sorted_times = sorted(list(all_times))

    rep_pts = {h["time"]: h["price"] for h in rep_history}
    dem_pts = {h["time"]: h["price"] for h in dem_history}

    chart_id = f"chart_{chart_idx}"
    rep_color = COLORS["rose"]
    dem_color = COLORS["blue"]

    html = f'''            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-semibold text-slate-800 mb-1">{title}</h2>
                <p class="text-sm text-slate-600 mb-4">{subtitle}</p>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="text-center p-4 bg-slate-100 rounded-lg border border-slate-200">
                        <div class="text-3xl font-bold" style="color: {rep_color}">{rep_price}%</div>
                        <div class="text-sm text-slate-500 mt-1">共和党</div>
                    </div>
                    <div class="text-center p-4 bg-slate-100 rounded-lg border border-slate-200">
                        <div class="text-3xl font-bold" style="color: {dem_color}">{dem_price}%</div>
                        <div class="text-sm text-slate-500 mt-1">民主党</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('{chart_id}'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(sorted_times)},
                        datasets: [
                            {{
                                label: '共和党 (%)',
                                data: {json.dumps([rep_pts.get(t) for t in sorted_times])},
                                borderColor: '{rep_color}',
                                backgroundColor: '{rep_color}1a',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.4,
                                pointRadius: 0
                            }},
                            {{
                                label: '民主党 (%)',
                                data: {json.dumps([dem_pts.get(t) for t in sorted_times])},
                                borderColor: '{dem_color}',
                                backgroundColor: '{dem_color}1a',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.4,
                                pointRadius: 0
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'top', labels: {{ color: '#334155', font: {{ size: 11 }} }} }} }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5 }}, ticks: {{ color: '#64748b', maxTicksLimit: 10 }} }},
                            y: {{ grid: {{ color: 'rgba(100, 116, 139, 0.2)', lineWidth: 0.5 }}, ticks: {{ color: '#64748b' }} }}
                        }}
                    }}
                }});
            </script>
'''
    return html


def main():
    print("="*60)
    print("Polymarket 数据更新器")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    try:
        # 获取数据
        print("\n正在获取Polymarket数据...")
        data = fetch_all_events_data()

        # 保存JSON数据到data目录
        json_filename = "data/polymarket_data.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({"fetchedAt": datetime.now().isoformat(), "events": data}, f, ensure_ascii=False, indent=2)
        print(f"数据已保存: {json_filename}")
        print("HTML页面会自动从JSON文件加载数据，无需重新生成HTML")

        print("\n" + "="*60)
        print("完成!")
        print("="*60)
        return 0
    except Exception as e:
        print(f"\n[错误] 更新失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n不标记为失败，继续执行")
        return 0


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
