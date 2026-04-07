"""
CME FedWatch Tool 数据抓取脚本
通过QuikStrike iframe内部点击Probabilities，提取利率概率表
输出: data/fedwatch.json
"""
import asyncio, json, sys, io
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def parse_table(table):
    """将原始表格数据转为fedwatch.json格式"""
    if not table or len(table) < 2:
        return None

    headers = table[0]
    rate_ranges = headers[1:]  # ["200-225", "225-250", ...]

    meetings = []
    for row in table[1:]:
        meeting_date = row[0]
        all_probs = {}
        max_prob_val = 0
        max_rate = ""

        for i, rate in enumerate(rate_ranges):
            val = row[i + 1] if i + 1 < len(row) else "0.0%"
            val = val.strip() if val else "0.0%"
            if not val.endswith('%'):
                val = "0.0%"
            all_probs[rate] = val
            num = float(val.replace('%', ''))
            if num > max_prob_val:
                max_prob_val = num
                max_rate = rate

        # Determine action
        current_rate = "350-375"  # current target rate range
        if max_rate == current_rate:
            action = "维持不变"
        elif rate_ranges.index(max_rate) < rate_ranges.index(current_rate):
            diff = rate_ranges.index(current_rate) - rate_ranges.index(max_rate)
            action = f"降息{diff * 25}bp"
        else:
            diff = rate_ranges.index(max_rate) - rate_ranges.index(current_rate)
            action = f"加息{diff * 25}bp"

        meetings.append({
            "meetingDate": meeting_date,
            "maxProbability": round(max_prob_val, 1),
            "targetRate": max_rate,
            "action": action,
            "allProbs": all_probs
        })

    return meetings


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,
            args=['--disable-blink-features=AutomationControlled'])
        ctx = await browser.new_context(viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = await ctx.new_page()

        print("[1] Loading CME FedWatch page...")
        try:
            await page.goto(
                "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
                wait_until='networkidle', timeout=90000)
        except:
            print("    timeout (OK)")

        await asyncio.sleep(5)

        # Close popups
        for s in ['button:has-text("Accept")', 'button:has-text("Accept all")', '[aria-label="Close"]']:
            try:
                if await page.locator(s).count() > 0:
                    await page.locator(s).first.click(timeout=2000)
                    await asyncio.sleep(1)
            except:
                pass

        # Scroll to load iframe
        for y in [300, 600, 900]:
            await page.evaluate(f"window.scrollTo(0,{y})")
            await asyncio.sleep(2)

        # Find QuikStrike iframe
        print("[2] Finding QuikStrike iframe...")
        qs = None
        for frame in page.frames:
            if 'quikstrike' in frame.url:
                qs = frame
                break
        if not qs:
            await asyncio.sleep(10)
            for frame in page.frames:
                if 'quikstrike' in frame.url:
                    qs = frame
                    break
        if not qs:
            print("[FAIL] QuikStrike iframe not found")
            await browser.close()
            return

        await asyncio.sleep(8)

        # Click Probabilities in iframe sidebar
        print("[3] Clicking Probabilities...")
        try:
            loc = qs.locator('text=Probabilities').first
            await loc.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            await loc.click(timeout=10000)
            print("    Clicked!")
        except Exception as e:
            print(f"    Failed: {e}")
            await browser.close()
            return

        await asyncio.sleep(5)

        # Extract probability table
        print("[4] Extracting table data...")
        tables = await qs.evaluate("""() => {
            const r = [];
            document.querySelectorAll('table').forEach(table => {
                const rows = [];
                table.querySelectorAll('tr').forEach(tr => {
                    const cells = [];
                    tr.querySelectorAll('th,td').forEach(td => cells.push(td.textContent.trim()));
                    if (cells.length > 2) rows.push(cells);
                });
                if (rows.length > 1) r.push(rows);
            });
            return r;
        }""")

        # Find the probability table (has "Meeting Date" header)
        prob_table = None
        for t in tables:
            if t and t[0] and 'Meeting Date' in t[0]:
                prob_table = t
                break

        if not prob_table:
            print("[FAIL] Probability table not found")
            await browser.close()
            return

        print(f"    Found table: {len(prob_table)} rows")

        # Parse and save
        meetings = parse_table(prob_table)
        output = {
            "fetchTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "CME FedWatch Tool",
            "sourceUrl": "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
            "currentTargetRate": "350-375bp (3.50%-3.75%)",
            "probabilities": meetings
        }

        out_path = DATA / "fedwatch.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"[5] Saved to fedwatch.json ({len(meetings)} meetings)")

        # Also save screenshot
        await page.screenshot(path=str(DATA / "fedwatch_screenshot.png"), full_page=False)
        print("[Done]")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
