#!/usr/bin/env python3
"""
从金十数据获取快照，生成延时视频
- 通过Playwright访问金十页面拦截API获取快照
- 取最近48张快照
- 按时间从旧到新排序
- 每张图片添加日期时间水印
- 生成约10秒的视频（5fps）
- 固定文件名: strait_timelapse_jin10.mp4
"""

import json
import urllib.request
import io
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 配置
JIN10_URL = "https://qihuo.jin10.com/topic/strait_of_hormuz.html"
OUTPUT_FILE = "strait_timelapse_jin10.mp4"
MAX_FRAMES = 48
TARGET_DURATION = 10  # 目标时长（秒）
MAX_RETRIES = 3  # 最大重试次数

async def fetch_snapshots():
    """通过Playwright访问金十页面，拦截API获取快照数据"""
    print("[1/3] 获取金十快照数据...")

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"      尝试 {attempt}/{MAX_RETRIES}...")
        api_results = {}

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()

                # 拦截 _vir_107 API 响应（快照数据）
                async def handle_response(response):
                    url = response.url
                    if "_vir_107" in url and "mp-api.jin10.com" in url:
                        try:
                            body = await response.json()
                            api_results["_vir_107"] = body
                            print(f"      [拦截] _vir_107 API - {len(body.get('data', []))} 张快照")
                        except Exception as e:
                            print(f"      [警告] 解析API失败: {e}")

                page.on("response", handle_response)

                print(f"      访问: {JIN10_URL}")
                try:
                    await page.goto(JIN10_URL, wait_until="domcontentloaded", timeout=45000)
                except PlaywrightTimeout:
                    print("      [警告] 页面加载超时，继续等待API...")

                # 等待API响应（最多30秒）
                for _ in range(60):
                    if "_vir_107" in api_results:
                        break
                    await asyncio.sleep(0.5)

                await context.close()
                await browser.close()

            if "_vir_107" in api_results:
                snapshots = api_results["_vir_107"].get("data", [])
                if snapshots:
                    print(f"      成功获取 {len(snapshots)} 张快照")
                    return snapshots
                else:
                    print("      [警告] API返回空数据")
            else:
                print("      [警告] 未拦截到 _vir_107 API")

        except Exception as e:
            print(f"      [错误] {e}")

        if attempt < MAX_RETRIES:
            print("      等待5秒后重试...")
            await asyncio.sleep(5)

    print("      [失败] 所有尝试均未成功获取快照数据")
    return []

def parse_date(snap):
    """解析快照日期"""
    return datetime.strptime(snap['date'], '%Y-%m-%d %H:%M:%S')

def add_datetime_watermark(img_array, date_str):
    """在图片上添加日期时间水印

    Args:
        img_array: numpy数组格式的图片
        date_str: 日期时间字符串，如 '2026-03-31 10:00'

    Returns:
        添加水印后的numpy数组图片
    """
    # 转换为PIL Image
    img = Image.fromarray(img_array)

    # 图片尺寸
    width, height = img.size

    # 格式化日期时间显示 (去掉秒)
    display_text = date_str[:16].replace('-', '/').replace(' ', ' ')

    # 尝试加载字体，失败则使用默认字体
    font_size = max(20, int(height * 0.035))  # 字体大小根据图片高度调整
    font = None
    font_paths = [
        "arial.ttf",  # Windows
        "C:/Windows/Fonts/arial.ttf",  # Windows绝对路径
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Ubuntu (GitHub Actions)
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Ubuntu备用
    ]
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    # 创建RGBA模式的图层用于绘制
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 创建透明图层
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 计算文字位置（右下角，留出边距）
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    margin = 15
    x = width - text_width - margin
    y = height - text_height - margin - 5

    # 绘制半透明黑色背景
    padding = 8
    bg_box = [
        x - padding,
        y - padding,
        x + text_width + padding,
        y + text_height + padding
    ]
    draw.rectangle(bg_box, fill=(0, 0, 0, 180))

    # 绘制白色文字
    draw.text((x, y), display_text, fill=(255, 255, 255, 255), font=font)

    # 合并图层
    img = Image.alpha_composite(img, overlay)

    # 转换回RGB模式（视频需要）
    background = Image.new('RGB', img.size, (0, 0, 0))
    background.paste(img, mask=img.split()[3])

    return np.array(background)

def download_and_generate_video(snapshots):
    """下载图片并生成视频"""
    print("[2/3] 下载快照图片...")

    # 按日期排序（旧→新）
    sorted_snaps = sorted(snapshots, key=parse_date)

    # 取最近48张
    recent = sorted_snaps[-MAX_FRAMES:] if len(sorted_snaps) >= MAX_FRAMES else sorted_snaps
    print(f"      取最近 {len(recent)} 张")
    print(f"      时间范围: {recent[0]['date']} -> {recent[-1]['date']}")

    # 下载图片
    images = []
    for i, snap in enumerate(recent):
        url = snap['url']
        date_str = snap['date']
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                img_data = resp.read()

            # 从内存读取图片
            img = imageio.imread(io.BytesIO(img_data))

            # 添加日期时间水印
            img_with_watermark = add_datetime_watermark(img, date_str)
            images.append(img_with_watermark)
            print(f"      [{i+1}/{len(recent)}] {snap['date']} OK")

        except Exception as e:
            print(f"      [{i+1}/{len(recent)}] {snap['date']} FAIL ({e})")

    if len(images) < 3:
        print(f"[错误] 可用帧数不足({len(images)})，无法生成视频")
        return False

    # 根据帧数动态计算fps，使视频时长约10秒
    fps = max(1, round(len(images) / TARGET_DURATION))
    duration = len(images) / fps

    print(f"[3/3] 生成视频 ({len(images)} 帧, {fps}fps, ~{duration:.0f}秒)...")

    # 生成视频
    imageio.mimwrite(
        OUTPUT_FILE,
        images,
        fps=fps,
        codec='libx264',
        pixelformat='yuv420p'
    )

    size_mb = Path(OUTPUT_FILE).stat().st_size / 1024 / 1024

    print(f"\n[DONE] 视频生成成功!")
    print(f"       文件: {OUTPUT_FILE}")
    print(f"       大小: {size_mb:.1f} MB")
    print(f"       时长: ~{duration:.0f}秒")
    print(f"       帧数: {len(images)} 帧")

    return True

async def async_main():
    print("=" * 50)
    print("  金十数据延时视频生成器")
    print("=" * 50)
    print()

    try:
        snapshots = await fetch_snapshots()
        if not snapshots:
            print("\n[FAILED] 未能获取快照数据，请检查网络或稍后重试")
            return False

        success = download_and_generate_video(snapshots)
        return success

    except Exception as e:
        print(f"[错误] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    return asyncio.run(async_main())

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
