#!/usr/bin/env python3
"""
海峡通行数据更新脚本
整合金十数据抓取、历史CSV读取、统一数据生成
"""

import asyncio
import json
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

WORKDIR = Path(__file__).parent.resolve()
DATA_FILE = WORKDIR / "strait_data.json"
JIN10_DATA_FILE = WORKDIR / "jin10_strait_data.json"
HISTORY_CSV = WORKDIR / "历史.csv"
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


async def fetch_jin10_data():
    """抓取金十期货霍尔木兹海峡数据（含视频）"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        result = {
            "updated": datetime.now(BEIJING_TZ).strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "金十数据",
            "url": "https://qihuo.jin10.com/topic/strait_of_hormuz.html",
            "industry_pressure": {},
            "ship_counts": {},
            "snapshot_url": None  # 实时快照图片
        }
        
        try:
            print("正在访问金十期货霍尔木兹海峡页面...")
            url = "https://qihuo.jin10.com/topic/strait_of_hormuz.html"
            
            # 增加超时时间到60秒
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=60000)
                if response and response.status != 200:
                    print(f"页面访问失败: HTTP {response.status}")
                    return None
                print(f"页面加载成功: HTTP {response.status}")
            except Exception as e:
                print(f"页面加载超时(60s): {e}")
                print("继续尝试提取已加载的数据...")
            
            # 等待JS渲染
            print("等待页面渲染...")
            await asyncio.sleep(10)
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 1. 提取行业通行压力系数
            print("\n提取行业通行压力系数...")
            
            # 从页面结构中提取
            pressure_data = await page.evaluate(r'''
                () => {
                    const result = { total: null, categories: [] };
                    const bodyText = document.body.innerText || '';
                    
                    // 方法1: 专门查找"行业通行压力系数"标题后面的数字
                    // 金十页面上压力系数是大字体显示，在标题后面
                    const match = bodyText.match(/行业通行压力系数\D*(\d+\.?\d*)%/);
                    if (match) {
                        result.total = parseFloat(match[1]);
                    }
                    
                    // 方法2: 如果没找到，尝试在"压力系数"附近查找最大的百分比
                    if (!result.total) {
                        const pressureSection = bodyText.match(/压力系数[\s\S]{0,500}/);
                        if (pressureSection) {
                            const allPercents = pressureSection[0].match(/(\d+\.?\d*)%/g);
                            if (allPercents) {
                                // 取最大的一个（通常综合压力是最大的）
                                let maxVal = 0;
                                for (let p of allPercents) {
                                    const val = parseFloat(p);
                                    if (val > maxVal && val <= 100) maxVal = val;
                                }
                                if (maxVal > 0) result.total = maxVal;
                            }
                        }
                    }
                    
                    // 提取各品类数据 - 甲醇、原油、LPG、LNG、化肥、铝
                    // 注意：正则按优先级排序，先匹配特定模式，再匹配通用模式
                    const categoryPatterns = [
                        {key: 'methanol', name: '甲醇', pattern: /甲醇[\s\w]*?(\d+\.?\d*)%/},
                        {key: 'oil', name: '原油及成品油', pattern: /原油(?:及成品油)?[\s\w]*?(\d+\.?\d*)%/},
                        {key: 'lpg', name: '液化石油气/LPG', pattern: /(?:液化石油气|LPG)[^%]*?(\d+\.?\d*)%/},
                        {key: 'lng', name: '液化天然气/LNG', pattern: /(?:液化天然气|LNG)[^%]*?(\d+\.?\d*)%/},
                        {key: 'fertilizer', name: '化肥', pattern: /(?:化肥|尿素|磷肥|钾肥)[^%]*?(\d+\.?\d*)%/},
                        {key: 'aluminum', name: '铝材', pattern: /(?:铝材|铝及铝制品|铝制品|原铝)[^%]*?(\d+\.?\d*)%/}
                    ];
                    
                    for (let cat of categoryPatterns) {
                        const match = bodyText.match(cat.pattern);
                        if (match) {
                            // 取第一个非空的捕获组
                            const value = match[1] ? parseFloat(match[1]) : (match[2] ? parseFloat(match[2]) : null);
                            if (value !== null) {
                                result.categories.push({
                                    key: cat.key,
                                    name: cat.name,
                                    value: value
                                });
                            }
                        }
                    }
                    
                    return result;
                }
            ''')
            
            if pressure_data.get('total'):
                result["industry_pressure"]["total"] = pressure_data["total"]
                print(f"  综合通行压力系数: {pressure_data['total']}%")
            
            seen = set()
            for cat in pressure_data.get('categories', []):
                if cat['key'] not in seen:
                    seen.add(cat['key'])
                    result["industry_pressure"][cat['key']] = {
                        "name": cat['name'],
                        "value": cat['value']
                    }
                    print(f"  {cat['name']}: {cat['value']}%")
            
            # 2. 提取船只数量统计
            print("\n提取船只数量统计...")
            ship_data = await page.evaluate(r"""
                () => {
                    const result = {
                        yesterday_passed: 0,  // 昨日通过
                        hormuz_passing: 0,    // 正在通过（当前通过）
                        sailing: 0,           // 航行中
                        anchored: 0,          // 锚泊/停靠
                        total_in_area: 0      // 海域内总数
                    };
                    
                    const bodyText = document.body.innerText || '';
                    
                    // 方法1: 查找"当前通过霍尔木兹海峡" - 这是左侧大数字
                    const currentMatch = bodyText.match(/当前通过霍尔木兹海峡[\s\S]*?(\d+)\s*艘/);
                    if (currentMatch) {
                        result.hormuz_passing = parseInt(currentMatch[1]);
                    }
                    
                    // 方法2: 从左侧卡片提取
                    const cards = document.querySelectorAll('.card, [class*="card"]');
                    for (let card of cards) {
                        const text = card.textContent || '';
                        
                        // 当前通过霍尔木兹海峡
                        if (text.includes('当前通过') && text.includes('霍尔木兹')) {
                            const match = text.match(/(\d+)\s*艘/);
                            if (match) {
                                result.hormuz_passing = parseInt(match[1]);
                            }
                        }
                        
                        // 阿曼湾与波斯湾海域内
                        if (text.includes('阿曼湾') && text.includes('波斯湾')) {
                            // 提取大数字（通常是3,089这种格式）
                            const bigNumMatch = text.match(/(\d{1,3}(?:,\d{3})+)\s*艘/);
                            if (bigNumMatch) {
                                result.total_in_area = parseInt(bigNumMatch[1].replace(/,/g, ''));
                            }
                        }
                        
                        // 航行中 - 速度≥1节
                        if (text.includes('航行中')) {
                            const match = text.match(/航行中[^\d]*(\d{1,3}(?:,\d{3})*)\s*艘/);
                            if (match) result.sailing = parseInt(match[1].replace(/,/g, ''));
                        }
                        
                        // 锚泊/停靠 - 速度<1节
                        if (text.includes('锚泊') || text.includes('停靠')) {
                            const match = text.match(/(?:锚泊|停靠)[^\d]*(\d{1,3}(?:,\d{3})*)\s*艘/);
                            if (match) result.anchored = parseInt(match[1].replace(/,/g, ''));
                        }
                    }
                    
                    // 方法3: 从整个页面文本提取（如果上面的方法没找到）
                    if (result.hormuz_passing === 0) {
                        // 查找"5艘"前面有"当前通过"的
                        const match = bodyText.match(/当前通过[\s\S]{0,100}?(\d+)\s*艘/);
                        if (match) result.hormuz_passing = parseInt(match[1]);
                    }
                    
                    if (result.total_in_area === 0) {
                        const match = bodyText.match(/阿曼湾与波斯湾海域内[\s\S]{0,100}?(\d{1,3}(?:,\d{3})*)\s*艘/);
                        if (match) result.total_in_area = parseInt(match[1].replace(/,/g, ''));
                    }
                    
                    if (result.sailing === 0) {
                        // 更灵活的匹配：航行中 + 数字 + 艘
                        const patterns = [
                            /航行中[\s\S]{0,50}?(\d{1,3}(?:,\d{3})*)\s*艘/,
                            /速度[≥>=\s]*1[\s]*节[\s\S]{0,30}?(\d{1,3}(?:,\d{3})*)\s*艘/,
                            /航行中[^\d]{0,20}(\d{1,3}(?:,\d{3})*)/
                        ];
                        for (let pattern of patterns) {
                            const match = bodyText.match(pattern);
                            if (match) {
                                result.sailing = parseInt(match[1].replace(/,/g, ''));
                                break;
                            }
                        }
                    }
                    
                    if (result.anchored === 0) {
                        // 更灵活的匹配：锚泊/停靠 + 数字 + 艘
                        const patterns = [
                            /锚泊[\/\s]*停靠[\s\S]{0,50}?(\d{1,3}(?:,\d{3})*)\s*艘/,
                            /速度[<\s]*1[\s]*节[\s\S]{0,30}?(\d{1,3}(?:,\d{3})*)\s*艘/,
                            /锚泊[^\d]{0,20}(\d{1,3}(?:,\d{3})*)/
                        ];
                        for (let pattern of patterns) {
                            const match = bodyText.match(pattern);
                            if (match) {
                                result.anchored = parseInt(match[1].replace(/,/g, ''));
                                break;
                            }
                        }
                    }
                    
                    // 如果航行中和锚泊有数据，计算总数
                    if (result.sailing > 0 && result.anchored > 0) {
                        result.calculated_total = result.sailing + result.anchored;
                    }
                    
                    return result;
                }
            """)
            
            result["ship_counts"] = ship_data
            print(f"  昨日通过: {ship_data.get('yesterday_passed', 'N/A')}艘")
            print(f"  正在通过: {ship_data.get('hormuz_passing', 'N/A')}艘")
            print(f"  航行中: {ship_data.get('sailing', 'N/A')}艘")
            print(f"  锚泊/停靠: {ship_data.get('anchored', 'N/A')}艘")
            print(f"  海域内总数: {ship_data.get('total_in_area', ship_data.get('calculated_total', 'N/A'))}艘")
            
            # 3. 提取实时快照图片URL
            print("\n提取实时快照图片...")
            snapshot_data = await page.evaluate("""
                () => {
                    // 方法1: 查找data-v-开头的金十特定组件中的图片
                    const jin10Images = document.querySelectorAll('[class*="snapshot"] img, [class*="map"] img, [data-v-] img');
                    for (let img of jin10Images) {
                        if (img.src && img.src.startsWith('http') && 
                            (img.src.includes('jin10') || img.src.includes('snapshot') || img.src.includes('map'))) {
                            return { url: img.src, type: 'jin10_component' };
                        }
                    }
                    
                    // 方法2: 查找所有图片，筛选可能的海峡地图
                    const allImages = document.querySelectorAll('img');
                    for (let img of allImages) {
                        if (img.src && img.src.startsWith('http')) {
                            const alt = (img.alt || '').toLowerCase();
                            const src = img.src.toLowerCase();
                            if (alt.includes('海峡') || alt.includes('map') || alt.includes('hormuz') ||
                                src.includes('strait') || src.includes('hormuz') || src.includes('map')) {
                                return { url: img.src, type: 'map_image' };
                            }
                        }
                    }
                    
                    // 方法3: 查找背景图片
                    const elements = document.querySelectorAll('*');
                    for (let el of elements) {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage.includes('url(')) {
                            const urlMatch = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/);
                            if (urlMatch && urlMatch[1].startsWith('http')) {
                                return { url: urlMatch[1], type: 'background' };
                            }
                        }
                    }
                    
                    return null;
                }
            """)
            
            if snapshot_data and snapshot_data.get('url'):
                result["snapshot_url"] = snapshot_data["url"]
                print(f"  找到快照: {snapshot_data['url'][:80]}...")
            else:
                print("  未找到快照图片")
            
            return result
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            await browser.close()


def read_history_csv():
    """读取历史CSV文件，返回图表数据"""
    print("\n读取历史CSV数据...")
    
    data = {
        "dates": [],
        "ship_counts": [],  # 艘次
        "tonnages": []      # 载重吨
    }
    
    try:
        # 尝试不同编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(HISTORY_CSV, 'r', encoding=encoding, newline='') as f:
                    content = f.read()
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"  错误: 无法读取CSV文件")
            return None
        
        # 解析CSV
        lines = content.strip().split('\n')
        reader = csv.reader(lines)
        
        # 跳过表头
        header = next(reader, None)
        print(f"  表头: {header}")
        
        for row in reader:
            if len(row) >= 3:
                try:
                    date_str = row[0].strip()
                    ships = int(row[1].strip())
                    tonnage = int(row[2].strip())
                    
                    data["dates"].append(date_str)
                    data["ship_counts"].append(ships)
                    data["tonnages"].append(tonnage)
                except (ValueError, IndexError):
                    continue
        
        print(f"  读取了 {len(data['dates'])} 条记录")
        if data['dates']:
            print(f"  最新记录: {data['dates'][-1]} - {data['ship_counts'][-1]}艘, {data['tonnages'][-1]}吨")
        
        return data
        
    except Exception as e:
        print(f"  读取CSV错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def merge_and_save_data(jin10_data, history_data):
    """合并数据并保存为 strait_data.json"""
    print("\n合并数据并保存...")

    # 从历史CSV数据中读取昨日通过数
    if history_data and history_data.get("ship_counts") and len(history_data["ship_counts"]) > 0:
        yesterday_count = history_data["ship_counts"][-1]  # 最新的一条记录作为昨日数据
        print(f"  从历史CSV读取昨日通过数: {yesterday_count}艘")

        # 确保 ship_counts 存在
        if jin10_data and "ship_counts" not in jin10_data:
            jin10_data["ship_counts"] = {}

        # 将昨日通过数添加到 ship_counts 中
        if jin10_data:
            jin10_data["ship_counts"]["yesterday_passed"] = yesterday_count

    # 构建统一的数据结构
    merged = {
        "updated": datetime.now(BEIJING_TZ).strftime("%Y-%m-%dT%H:%M:%S"),
        "source": {
            "jin10": "金十数据",
            "history": "历史.csv"
        },
        "jin10": jin10_data or {},
        "history": history_data or {}
    }

    # 保存到 jin10_strait_data.json（原始金十数据，已包含昨日通过数）
    if jin10_data:
        with open(JIN10_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(jin10_data, f, ensure_ascii=False, indent=2)
        print(f"  已保存: {JIN10_DATA_FILE}")
    
    # 保存到 strait_data.json（统一数据）
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {DATA_FILE}")
    
    return merged


def embed_data_to_html(jin10_data, history_data=None):
    """将金十数据和历史CSV数据嵌入到index.html中"""
    print("\n嵌入数据到index.html...")
    
    if not jin10_data:
        print("  无数据可嵌入")
        return
    
    # 从历史CSV数据中读取昨日通过数
    if history_data and history_data.get("ship_counts") and len(history_data["ship_counts"]) > 0:
        yesterday_count = history_data["ship_counts"][-1]  # 最新的一条记录作为昨日数据
        print(f"  从历史CSV读取昨日通过数: {yesterday_count}艘")
        
        # 确保 ship_counts 存在
        if "ship_counts" not in jin10_data:
            jin10_data["ship_counts"] = {}
        
        # 将昨日通过数添加到 ship_counts 中
        jin10_data["ship_counts"]["yesterday_passed"] = yesterday_count
    
    tracking_file = WORKDIR / "index.html"
    if not tracking_file.exists():
        print(f"  错误: 找不到 {tracking_file}")
        return
    
    with open(tracking_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 准备嵌入的数据
    industry_pressure = jin10_data.get("industry_pressure", {})
    ship_counts = jin10_data.get("ship_counts", {})
    
    # 构建嵌入的JavaScript代码
    embed_script = f'''
<!-- 金十数据嵌入 (自动更新于 {datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")}) -->
<script id="jin10-embedded-data">
const JIN10_STRAIT_DATA = {json.dumps(jin10_data, ensure_ascii=False, indent=2)};

// 页面加载时自动填充数据
document.addEventListener('DOMContentLoaded', function() {{
    fillJin10Data(JIN10_STRAIT_DATA);
}});

function fillJin10Data(data) {{
    if (!data) return;
    
    // ========== 1. 船只实时通行状态 ==========
    const shipStatusSection = document.getElementById('jin10-ship-status-section');
    if (shipStatusSection) {{
        shipStatusSection.style.display = 'block';
        
        // 当前通过霍尔木兹海峡
        if (data.ship_counts) {{
            if (data.ship_counts.hormuz_passing !== undefined) {{
                document.getElementById('jin10-hormuz-passing').textContent = data.ship_counts.hormuz_passing;
            }} else if (data.ship_counts.hormuz) {{
                document.getElementById('jin10-hormuz-passing').textContent = data.ship_counts.hormuz;
            }}
            
            // 海域内总船舶数
            if (data.ship_counts.total_in_area > 0) {{
                document.getElementById('jin10-total-ships').textContent = data.ship_counts.total_in_area.toLocaleString();
            }} else if (data.ship_counts.calculated_total > 0) {{
                document.getElementById('jin10-total-ships').textContent = data.ship_counts.calculated_total.toLocaleString();
            }}
            
            // 航行中 vs 锚泊/停靠
            if (data.ship_counts.sailing !== undefined) {{
                document.getElementById('jin10-sailing').textContent = data.ship_counts.sailing.toLocaleString() + '艘';
            }}
            if (data.ship_counts.anchored !== undefined) {{
                document.getElementById('jin10-anchored').textContent = data.ship_counts.anchored.toLocaleString() + '艘';
            }}
            
            // 昨日通过海峡数据（来自CSV历史数据）
            if (data.ship_counts.yesterday_passed !== undefined) {{
                const yesterdayEl = document.getElementById('jin10-yesterday-passed');
                if (yesterdayEl) {{
                    yesterdayEl.textContent = data.ship_counts.yesterday_passed;
                }}
            }}
        }}
        
        // 更新时间
        if (data.updated) {{
            const updateTimeEl = document.getElementById('jin10-ship-update-time');
            if (updateTimeEl) {{
                updateTimeEl.textContent = data.updated.slice(0, 16).replace('T', ' ');
            }}
        }}
    }}
    
    // ========== 2. 行业通行压力系数 ==========
    const pressureSection = document.getElementById('jin10-pressure-section');
    if (pressureSection && data.industry_pressure) {{
        pressureSection.style.display = 'block';
        
        // 更新综合通行压力系数
        if (data.industry_pressure.total) {{
            const totalPressure = data.industry_pressure.total;
            document.getElementById('jin10-total-pressure').textContent = totalPressure;
            
            // 更新压力等级标签
            const levelEl = document.getElementById('jin10-pressure-level');
            if (levelEl) {{
                if (totalPressure >= 95) {{
                    levelEl.textContent = '极高风险';
                    levelEl.style.background = '#cf1322';
                }} else if (totalPressure >= 80) {{
                    levelEl.textContent = '高风险';
                    levelEl.style.background = '#cf1322';
                }} else if (totalPressure >= 60) {{
                    levelEl.textContent = '中等风险';
                    levelEl.style.background = '#fa8c16';
                }} else {{
                    levelEl.textContent = '低风险';
                    levelEl.style.background = '#52c41a';
                }}
            }}
        }}
        
        // 更新各品类数据
        const categoryMap = {{
            'oil': 'jin10-oil',
            'lng': 'jin10-lng',
            'lpg': 'jin10-lpg',
            'fertilizer': 'jin10-fertilizer',
            'aluminum': 'jin10-aluminum',
            'methanol': 'jin10-methanol'
        }};
        
        for (const [key, elementId] of Object.entries(categoryMap)) {{
            if (data.industry_pressure[key]) {{
                const value = data.industry_pressure[key].value;
                const el = document.getElementById(elementId);
                if (el) el.textContent = value;
                
                // 更新进度条
                const barEl = document.getElementById(elementId + '-bar');
                if (barEl) barEl.style.width = value + '%';
            }}
        }}
    }}
}}
</script>'''
    
    # 检查是否已有嵌入数据
    if '<script id="jin10-embedded-data">' in content:
        # 替换现有嵌入数据 - 只替换 script 标签及其内容
        pattern = r'<script id="jin10-embedded-data">.*?</script>'
        content = re.sub(pattern, embed_script.strip(), content, flags=re.DOTALL)
        print("  已替换现有嵌入数据")
    elif '<!-- 金十数据入口 -->' in content:
        # 在入口位置插入新数据
        content = content.replace('<!-- 金十数据入口 -->', embed_script + '\n<!-- 金十数据入口 -->')
        print("  已嵌入数据到HTML")
    else:
        # 在</body>前插入
        content = content.replace('</body>', embed_script + '\n</body>')
        print("  已嵌入数据到页面底部")

    # 同时嵌入历史CSV数据到图表（如果有的话）
    if history_data and history_data.get("dates"):
        print("  嵌入历史CSV数据到图表...")
        
        # 构建CSV数据的JavaScript数组
        csv_js_data = []
        for i, date in enumerate(history_data["dates"]):
            ships = history_data["ship_counts"][i] if i < len(history_data["ship_counts"]) else 0
            tonnage = history_data["tonnages"][i] if i < len(history_data["tonnages"]) else 0
            csv_js_data.append(f"{{date: '{date}', ships: {ships}, dwt: {tonnage}}}")
        
        csv_data_js = "const CSV_HISTORY_DATA = [\n            " + ",\n            ".join(csv_js_data) + "\n        ];"
        
        # 检查是否已有CSV数据嵌入
        if 'const CSV_HISTORY_DATA' in content:
            # 替换现有数据
            content = re.sub(
                r'const CSV_HISTORY_DATA = \[.*?\];',
                csv_data_js,
                content,
                flags=re.DOTALL
            )
            print("    已替换现有CSV历史数据")
        else:
            # 在trafficChart脚本前插入
            if 'const ctx = document.getElementById(\'trafficChart\')' in content:
                content = content.replace(
                    'const ctx = document.getElementById(\'trafficChart\')',
                    csv_data_js + '\n\n        const ctx = document.getElementById(\'trafficChart\')'
                )
                print("    已嵌入CSV历史数据")
        
        # 替换硬编码的realData数组为CSV数据
        if 'const CSV_HISTORY_DATA' in content:
            content = content.replace(
                '// 真实数据（来自船视宝',
                '// 历史数据来自CSV文件（自动更新）\n        // 原始数据来自船视宝'
            )
            # 将 realData 数组引用改为使用 CSV_HISTORY_DATA
            content = re.sub(
                r'const realData = \[.*?\];',
                'const realData = CSV_HISTORY_DATA;',
                content,
                flags=re.DOTALL
            )
            print("    图表将使用CSV数据替代硬编码数据")
    
    with open(tracking_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  已保存: {tracking_file}")


async def main():
    print("=" * 60)
    print("海峡通行数据更新")
    print(f"北京时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 抓取金十数据
    jin10_data = await fetch_jin10_data()
    
    # 2. 读取历史CSV
    history_data = read_history_csv()
    
    # 3. 合并并保存
    merged_data = merge_and_save_data(jin10_data, history_data)
    
    # 4. 嵌入数据到HTML（包括金十数据和CSV历史数据）
    embed_data_to_html(jin10_data, history_data)
    
    print("\n" + "=" * 60)
    print("更新完成")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
