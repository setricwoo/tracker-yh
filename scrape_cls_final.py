"""
使用 Playwright 爬取财联社中东冲突专题新闻
来源: https://www.cls.cn/subject/10986
"""
from playwright.sync_api import sync_playwright
import json
import re
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

def try_api_fetch():
    """尝试通过API获取新闻数据"""
    try:
        # 财联社API端点（通过网页分析得到）
        url = "https://www.cls.cn/v3/SubjectHomeArticles"
        params = {
            "subjectId": "10986",
            "page": "1",
            "size": "50"
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.cls.cn/subject/10986',
            'Accept': 'application/json'
        }
        
        print(f"请求API: {url}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200 and data.get('data', {}).get('articles'):
                articles = data['data']['articles']
                news_list = []
                for item in articles:
                    try:
                        title = item.get('title', '')
                        content = item.get('content', '')
                        # 提取时间
                        time_str = item.get('time', '')
                        if not time_str:
                            continue
                            
                        # 转换时间格式（统一转换为北京时间）
                        try:
                            beijing_tz = ZoneInfo("Asia/Shanghai")
                            if time_str.isdigit():
                                # 时间戳转换为北京时间
                                dt = datetime.fromtimestamp(int(time_str), tz=beijing_tz)
                            else:
                                # 字符串时间直接解析为北京时间
                                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M').replace(tzinfo=beijing_tz)
                            time_formatted = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            time_formatted = time_str
                        
                        news_list.append({
                            'id': str(len(news_list) + 1),
                            'title': title[:120],
                            'summary': content[:500] if content else title[:500],
                            'time': time_formatted,
                            'url': f"https://www.cls.cn/detail/{item.get('id', '')}",
                            'category': categorize(title)
                        })
                    except Exception as e:
                        continue
                
                if news_list:
                    print(f"API获取成功: {len(news_list)} 条")
                    return news_list
    except Exception as e:
        print(f"API获取失败: {e}")
    
    return None

def scrape_news():
    """爬取财联社新闻"""
    print("开始爬取财联社新闻...")
    
    # 首先尝试直接通过HTTP请求获取API数据（更快，更少依赖浏览器）
    print("尝试通过API获取新闻...")
    api_news = try_api_fetch()
    if api_news:
        print(f"API获取成功，共 {len(api_news)} 条新闻")
        return api_news
    
    print("API获取失败，使用Playwright浏览器抓取...")
    
    with sync_playwright() as p:
        # 启动浏览器，增加更多参数避免检测
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        page.set_default_timeout(60000)  # 增加到60秒
        
        try:
            # 访问页面
            print("正在访问 https://www.cls.cn/subject/10986")
            page.goto("https://www.cls.cn/subject/10986", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            print(f"页面标题: {page.title()}")
            
            # 截图保存用于调试
            try:
                page.screenshot(path='debug_screenshot.png', full_page=True)
                print("已保存调试截图: debug_screenshot.png")
            except Exception as e:
                print(f"截图失败: {e}")
            
            # 检查页面是否加载成功
            if "中东冲突" not in page.title() and "财联社" not in page.title():
                print(f"[警告] 页面标题异常: {page.title()}")
            
            # 点击"加载更多"
            print("点击加载更多...")
            load_more_count = 0
            max_clicks = 15  # 减少点击次数，避免超时
            
            while load_more_count < max_clicks:
                load_more_selectors = [
                    'text=加载更多',
                    'text=查看更多',
                    '.load-more',
                    '[class*="load-more"]',
                    'button:has-text("更多")',
                ]
                
                found_button = None
                for selector in load_more_selectors:
                    try:
                        button = page.query_selector(selector)
                        if button and button.is_visible():
                            found_button = button
                            print(f"  找到加载按钮: {selector}")
                            break
                    except:
                        continue
                
                if not found_button:
                    print("  未找到更多按钮，停止加载")
                    break
                
                try:
                    found_button.scroll_into_view_if_needed()
                    page.wait_for_timeout(800)
                    
                    links_before = len(page.query_selector_all('a[href*="/detail/"]'))
                    found_button.click()
                    load_more_count += 1
                    print(f"  点击第 {load_more_count} 次")
                    
                    page.wait_for_timeout(2500)
                    
                    links_after = len(page.query_selector_all('a[href*="/detail/"]'))
                    print(f"    链接数: {links_before} -> {links_after}")
                    
                    if links_after <= links_before:
                        print("    没有新增内容，停止加载")
                        break
                    
                    if links_after >= 200:  # 降低上限
                        print("    达到上限，停止加载")
                        break
                        
                except Exception as e:
                    print(f"    点击失败: {e}")
                    break
            
            # 提取新闻
            print("\n提取新闻数据...")
            news_list = []
            seen_urls = set()
            
            # 方法1: 通过时间元素找到对应的新闻
            time_elements = page.query_selector_all('[class*="time"], [class*="999"], time')
            print(f"找到 {len(time_elements)} 个时间元素")
            
            for time_el in time_elements[:200]:  # 增加处理数量
                try:
                    time_text = time_el.inner_text().strip()
                    
                    # 跳过空文本
                    if not time_text:
                        continue
                    
                    # 检查是否包含时间格式 (更宽松的检查)
                    if not re.search(r'\d{1,4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}:\d{2}', time_text):
                        continue
                    
                    time_str = extract_time(time_text)
                    if not time_str:
                        continue
                    
                    # 向上查找父元素
                    parent = time_el.query_selector('xpath=..')
                    if not parent:
                        continue
                    
                    # 在父元素中查找链接
                    link = parent.query_selector('a[href*="/detail/"]')
                    
                    # 如果没找到，尝试祖父元素
                    if not link:
                        grandparent = parent.query_selector('xpath=..')
                        if grandparent:
                            link = grandparent.query_selector('a[href*="/detail/"]')
                    
                    if not link:
                        continue
                    
                    # 获取标题
                    title = link.inner_text().strip().split('\n')[0]
                    if not title or len(title) < 5:
                        continue
                    
                    href = link.get_attribute('href') or ''
                    if not href or href in seen_urls:
                        continue
                    
                    # 获取摘要
                    summary = extract_summary(parent, title)
                    
                    # 清理财联社前缀
                    title = clean_cls_prefix(title)
                    summary = clean_cls_prefix(summary)
                    
                    seen_urls.add(href)
                    news_list.append({
                        'id': str(len(news_list) + 1),
                        'title': title[:120],
                        'summary': summary[:500],
                        'time': time_str,
                        'url': 'https://www.cls.cn' + href if not href.startswith('http') else href,
                        'category': categorize(title)
                    })
                    
                    if len(news_list) >= 200:
                        print("  达到新闻数量上限(200条)，停止提取")
                        break
                        
                except Exception as e:
                    continue
            
            browser.close()
            
            print(f"\n成功提取 {len(news_list)} 条新闻")
            for n in news_list[:5]:
                print(f"  [{n['time']}] {n['title'][:40]}...")
            
            return news_list
            
        except Exception as e:
            print(f"[错误] 爬取过程出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                browser.close()
            except:
                pass
            return []

def extract_summary(parent, title):
    """提取摘要"""
    summary = ''
    try:
        # 从父元素获取文本
        parent_text = parent.inner_text().strip()
        if title in parent_text:
            summary_part = parent_text.replace(title, '').strip()
            summary = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', '', summary_part).strip()
        
        # 尝试查找摘要元素
        if not summary or len(summary) < 10:
            summary_el = parent.query_selector('[class*="content"], [class*="summary"], p')
            if summary_el:
                summary = summary_el.inner_text().strip()
        
        # 提取】之后的内容
        if '】' in summary:
            summary = summary.split('】', 1)[1].strip()
    except:
        pass
    
    # 如果没有摘要，使用标题
    if not summary:
        if '】' in title:
            summary = title.split('】', 1)[1].strip()
        else:
            summary = title
    
    return summary

def clean_cls_prefix(text):
    """去除财联社前缀"""
    if not text:
        return text
    pattern = r'^财联社\d{1,2}月\d{1,2}日电[，,\s]*'
    return re.sub(pattern, '', text.strip())

def extract_time(text):
    """提取时间 - 支持多种格式"""
    if not text:
        return ''
    
    # 格式1: 2026-03-19 08:47
    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', text)
    if match:
        return match.group(1)
    
    # 格式2: 03-19 08:47 (没有年份，假设为当前年)
    match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', text)
    if match:
        current_year = datetime.now().year
        return f"{current_year}-{match.group(1)}"
    
    # 格式3: 2026/03/19 08:47 (使用斜杠)
    match = re.search(r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})', text)
    if match:
        return match.group(1).replace('/', '-')
    
    # 格式4: 03/19 08:47 (使用斜杠，没有年份)
    match = re.search(r'(\d{2}/\d{2}\s+\d{2}:\d{2})', text)
    if match:
        current_year = datetime.now().year
        return f"{current_year}-{match.group(1).replace('/', '-')}"
    
    return ''

def categorize(text):
    """分类新闻"""
    text = (text or '').lower()
    if any(k in text for k in ['海峡', '霍尔木兹', '航运', '油轮', '船舶', '港口', '海运', '航道']):
        return 'shipping'
    if any(k in text for k in ['石油', '原油', '天然气', '能源', 'opec', '油价', '产量', '供应']):
        return 'energy'
    if any(k in text for k in ['外交', '谈判', '会谈', '制裁', '联合国', '欧盟', '协议', '停火']):
        return 'diplomacy'
    return 'military'

def load_existing_news():
    """加载现有新闻"""
    try:
        with open('news.html', 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'const CLS_NEWS_DATA = (\[.*?\]);', content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"读取现有新闻失败: {e}")
    return []

def merge_news(existing_news, new_news):
    """合并新闻"""
    existing_urls = {item['url']: item for item in existing_news}
    added_count = 0
    for item in new_news:
        if item['url'] not in existing_urls:
            existing_urls[item['url']] = item
            added_count += 1
    merged = list(existing_urls.values())
    merged.sort(key=lambda x: x['time'], reverse=True)
    for i, item in enumerate(merged, 1):
        item['id'] = str(i)
    return merged, added_count

def update_html(news_list):
    """更新HTML"""
    if not news_list:
        print("没有新闻数据可更新")
        return 0, 0, 0
    
    existing_news = load_existing_news()
    existing_count = len(existing_news)
    print(f"现有新闻: {existing_count} 条")
    
    merged_news, added_count = merge_news(existing_news, news_list)
    total_count = len(merged_news)
    
    with open('news.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新新闻数据
    news_json = json.dumps(merged_news, ensure_ascii=False, indent=4)
    content = re.sub(r'const CLS_NEWS_DATA = \[.*?\];', f'const CLS_NEWS_DATA = {news_json};', content, flags=re.DOTALL)
    
    # 更新右上角时间戳（使用北京时间）
    beijing_tz = ZoneInfo("Asia/Shanghai")
    current_date = datetime.now(beijing_tz).strftime('%Y年%m月%d日')
    current_time_full = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 尝试匹配不同格式的时间戳
    content = re.sub(r'更新时间: \d{4}年\d{1,2}月\d{1,2}日', f'更新时间: {current_date}', content)
    
    with open('news.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n[统计] 原有: {existing_count} 条 | 新增: {added_count} 条 | 现有: {total_count} 条")
    print(f"[时间戳] 已更新为: {current_date} ({current_time_full} 北京时间)")
    print(f"[文件已写入] news.html")
    return existing_count, added_count, total_count

def main():
    beijing_tz = ZoneInfo("Asia/Shanghai")
    print("="*50)
    print(f"财联社新闻爬虫 - {datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')}")
    print("="*50)
    
    try:
        news_list = scrape_news()
        if news_list:
            existing, added, total = update_html(news_list)
            print(f"\n[RESULT] existing={existing} added={added} total={total}")
            print("\n完成!")
            return 0
        else:
            print("\n未能获取新闻，但不标记为失败")
            return 0
    except Exception as e:
        print(f"\n[错误] 发生异常: {e}")
        import traceback
        traceback.print_exc()
        print("\n不标记为失败，继续执行")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
