"""
金十数据央行快讯抓取脚本 v3
直接搜索"美联储""欧央行"等关键词，提取所有相关快讯
识别、去重、总结交给AI完成
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import quote

# 搜索关键词
SEARCH_KEYWORDS = [
    "美联储", "欧央行", "欧洲央行", "日本央行", "日央行",
    "英格兰银行", "英国央行", "英央行", "人民银行",
    "鲍威尔", "拉加德", "植田和男", "贝利", "潘功胜",
]

# 用于前端过滤的央行关键词
CB_KEYWORDS = [
    "美联储", "Fed", "FOMC",
    "欧央行", "ECB", "欧洲央行",
    "日本央行", "BoJ", "日银",
    "英格兰银行", "BoE", "英国央行",
    "人民银行", "PBoC", "中国央行",
]


def clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()


async def search_jin10(page, keyword: str, max_pages: int = 3) -> List[Dict]:
    """搜索金十，拦截API响应"""
    items = []
    seen = set()

    async def on_response(response):
        if "search" in response.url or "flash" in response.url:
            try:
                data = await response.json()
                if isinstance(data, dict):
                    raw = data.get("data", {}).get("list", []) or data.get("data", [])
                    if isinstance(raw, list):
                        for r in raw:
                            rid = r.get("id", "")
                            if rid and rid not in seen:
                                seen.add(rid)
                                items.append(r)
            except:
                pass

    page.on("response", on_response)

    for pg in range(1, max_pages + 1):
        offset = (pg - 1) * 20
        url = f"https://search.jin10.com/?page={pg}&type=flash&order=1&keyword={quote(keyword)}&offset={offset}&vip=&basic_mode="
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await asyncio.sleep(0.5)
        except:
            break
        if len(items) < offset:
            break

    return items


def load_existing(path: str) -> tuple:
    """读取已有数据，返回 (items列表, 最新时间戳)"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        if items:
            times = [i.get("time", "") for i in items if i.get("time")]
            latest = max(times) if times else ""
        else:
            latest = ""
        return items, latest
    except (FileNotFoundError, json.JSONDecodeError):
        return [], ""


async def main_async():
    from playwright.async_api import async_playwright
    import sys

    out_path = "d:/python_code/跟踪网页2/data/jin10_cb_for_ai.json"

    # 增量逻辑：读取已有数据，从最新时间戳开始抓取
    existing_items, latest_time = load_existing(out_path)

    if latest_time:
        cutoff = datetime.strptime(latest_time[:19], "%Y-%m-%d %H:%M:%S")
        mode = f"增量（从 {latest_time[:16]} 起）"
    else:
        days = 7 if "--week" in sys.argv else 30
        cutoff = datetime.now() - timedelta(days=days)
        mode = "近一周" if days == 7 else "近一个月"

    print("=" * 60)
    print(f"  金十数据央行快讯抓取器 v3")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  范围: {mode} | 关键词: {len(SEARCH_KEYWORDS)} 个")
    print(f"  已有数据: {len(existing_items)} 条")
    print("=" * 60 + "\n")

    all_items = []
    seen_ids = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        for kw in SEARCH_KEYWORDS:
            print(f"  搜索: {kw}", end="")
            items = await search_jin10(page, kw, max_pages=3)
            new = 0
            for item in items:
                iid = item.get("id", "")
                if iid in seen_ids:
                    continue
                seen_ids.add(iid)

                content = item.get("data", {}).get("content", "") if "data" in item else item.get("content", "")
                time_str = item.get("time", "") or item.get("data", {}).get("time", "")
                source = item.get("data", {}).get("source", "") if "data" in item else ""
                if not content:
                    continue

                # 时间过滤
                if time_str:
                    try:
                        t = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        if t < cutoff:
                            continue
                    except:
                        pass

                all_items.append({
                    "id": iid,
                    "time": time_str,
                    "content": clean_html(content),
                    "source": source or "金十数据",
                    "important": item.get("important", 0) == 1,
                    "link": f"https://www.jin10.com/flash/{iid}"
                })
                new += 1
            print(f" -> {new} 条")

        await browser.close()

    # 按时间倒序
    all_items.sort(key=lambda x: x.get("time", ""), reverse=True)

    # 合并：用ID去重，新数据优先
    merged_map = {}
    for item in existing_items:
        merged_map[item.get("id", "")] = item
    for item in all_items:
        merged_map[item.get("id", "")] = item

    merged_items = sorted(merged_map.values(), key=lambda x: x.get("time", ""), reverse=True)
    new_count = len(all_items)

    result = {
        "fetchTime": datetime.now().isoformat(),
        "range": mode,
        "cutoff": cutoff.strftime("%Y-%m-%d"),
        "totalItems": len(merged_items),
        "newItems": new_count,
        "keywords": SEARCH_KEYWORDS,
        "items": merged_items
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  本次新增: {new_count} 条")
    print(f"  合并总计: {len(merged_items)} 条")
    print(f"  已保存: {out_path}")
    print(f"{'=' * 60}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
