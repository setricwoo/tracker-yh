#!/usr/bin/env python3
"""
Update data-tracking.html with latest data from 全球市场.xlsx
Only updates data, does not change page layout or structure
"""

import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path

def extract_commodity_groups(df):
    """Extract commodity data grouped by category, including inflation data"""
    names = df.iloc[1, :].tolist()
    units = df.iloc[3, :].tolist()
    sources = df.iloc[5, :].tolist()
    
    commodities = []
    
    # Read all columns including inflation data (cols 13, 14)
    for col_idx in range(1, min(15, len(df.columns))):  # Changed from 14 to 15
        name = names[col_idx] if col_idx < len(names) else f'商品{col_idx}'
        unit = units[col_idx] if col_idx < len(units) else ''
        source = sources[col_idx] if col_idx < len(sources) else ''
        
        if pd.isna(name) or name == '':
            continue
        
        # Skip financial condition index
        if '金融状况' in str(name):
            continue
        
        dates = []
        values = []
        
        for row_idx in range(6, len(df)):
            date_val = df.iloc[row_idx, 0]
            price_val = df.iloc[row_idx, col_idx]
            
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(price_val) and isinstance(price_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(price_val), 2))
        
        # Reverse to chronological order
        dates.reverse()
        values.reverse()
        
        # Keep up to 10 years of data for long-term analysis
        if len(values) > 3650:
            dates = dates[-3650:]
            values = values[-3650:]
        
        if len(values) > 0:
            commodities.append({
                'name': str(name),
                'unit': str(unit) if pd.notna(unit) else '',
                'source': str(source) if pd.notna(source) else '',
                'dates': dates,
                'values': values
            })
    
    # Group commodities
    groups = {
        'oil': {'name': '原油价格', 'unit': '美元/桶', 'items': []},
        'gas': {'name': '天然气价格', 'unit': '', 'items': []},
        'naphtha_lpg': {'name': '石脑油与LPG', 'unit': '', 'items': []},
        'methanol_ethylene': {'name': '甲醇与乙烯', 'unit': '', 'items': []},
        'aluminum_urea': {'name': '铝与尿素', 'unit': '', 'items': []},
        'grains': {'name': '大豆与小麦', 'unit': '', 'items': []},
        'inflation': {'name': '盈亏平衡通胀率', 'unit': '%', 'items': []}  # New group for inflation
    }
    
    for comm in commodities:
        name = comm['name']
        if '盈亏平衡通胀' in name or '通胀' in name:
            groups['inflation']['items'].append(comm)
        elif '原油' in name or '布伦特' in name or 'WTI' in name:
            groups['oil']['items'].append(comm)
        elif '天然气' in name or ('气' in name and '通胀' not in name):
            groups['gas']['items'].append(comm)
        elif '石脑油' in name:
            groups['naphtha_lpg']['items'].append(comm)
        elif 'LPG' in name or '液化石油' in name:
            groups['naphtha_lpg']['items'].append(comm)
        elif '甲醇' in name:
            groups['methanol_ethylene']['items'].append(comm)
        elif '乙烯' in name:
            groups['methanol_ethylene']['items'].append(comm)
        elif '铝' in name and 'LME' in name:
            groups['aluminum_urea']['items'].append(comm)
        elif '尿素' in name:
            groups['aluminum_urea']['items'].append(comm)
        elif '大豆' in name:
            groups['grains']['items'].append(comm)
        elif '小麦' in name:
            groups['grains']['items'].append(comm)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if len(v['items']) > 0}

def extract_liquidity_indicators(df):
    """Extract liquidity indicators with units from Excel row 2"""
    names = df.iloc[1, :].tolist()
    units = df.iloc[2, :].tolist()  # 单位在第3行（index 2）
    indicators = []

    for col_idx in range(1, min(12, len(df.columns))):
        name = names[col_idx] if col_idx < len(names) else f'指标{col_idx}'
        unit = units[col_idx] if col_idx < len(units) else ''

        if pd.isna(name) or name == '' or 'Unnamed' in str(name):
            continue

        # Skip excluded items
        if '沙特' in str(name) or '美元兑沙特' in str(name):
            continue
        if '全球股市隐含波动率' in str(name) and ('VIX' not in str(name) and 'VSTOXX' not in str(name)):
            continue

        dates = []
        values = []

        for row_idx in range(3, len(df)):  # 数据从第4行（index 3）开始
            date_val = df.iloc[row_idx, 0]
            data_val = df.iloc[row_idx, col_idx]

            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(data_val) and isinstance(data_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(data_val), 4))

        # Reverse to chronological order
        dates.reverse()
        values.reverse()

        if len(values) > 0:
            indicators.append({
                'name': str(name),
                'unit': str(unit) if pd.notna(unit) and unit else '',
                'dates': dates,
                'values': values
            })

    return indicators


def extract_financial_data(df):
    """Extract financial market data (stocks, bonds, etc.)

    全球市场sheet结构：
    - Row 0: "Wind"
    - Row 1: 指标名称
    - Row 2: 更新日期
    - Row 3-28985: 数据（最新在前，日期递减）
    - Row 28986+: 重复数据（跳过）
    """
    names = df.iloc[1, :].tolist() if len(df) > 1 else []

    stocks = {}
    bonds = {}

    # 找到日期开始递增的位置（重复数据的开始）
    cutoff_row = len(df)
    prev_date = None
    for i in range(3, len(df)):
        d = df.iloc[i, 0]
        if isinstance(d, datetime):
            if prev_date and d > prev_date:
                cutoff_row = i
                break
            prev_date = d

    print(f"  [INFO] Financial data cutoff at row {cutoff_row}")

    for col_idx in range(1, len(df.columns)):
        name = names[col_idx] if col_idx < len(names) else f'指标{col_idx}'

        if pd.isna(name) or name == '' or 'Unnamed' in str(name):
            continue

        dates = []
        values = []

        # 只读取到cutoff_row，避免重复数据
        for row_idx in range(3, cutoff_row):
            date_val = df.iloc[row_idx, 0]
            data_val = df.iloc[row_idx, col_idx]

            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(data_val) and isinstance(data_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(data_val), 2))

        # 数据在Excel中是最新在前，需要反转为时间顺序（旧→新）
        dates.reverse()
        values.reverse()

        if len(values) > 0:
            # Determine if stock or bond based on name
            name_str = str(name)
            data_obj = {
                'name': name_str,
                'unit': '',
                'dates': dates,
                'values': values,
                'latest': values[-1] if values else None,  # 最新值在最后一位（反转后）
                'latest_date': dates[-1] if dates else None
            }

            # Classify as stock or bond
            if any(kw in name_str for kw in ['国债', '美债', '收益率', '债券']):
                key = f'bond_{col_idx}'
                bonds[key] = data_obj
            else:
                key = f'stock_{col_idx}'
                stocks[key] = data_obj

    return {'stocks': stocks, 'bonds': bonds}


def extract_bond_data(df):
    """Extract global bond market data from 全球债市 sheet
    
    全球债市sheet结构：
    - Row 0: "Wind"
    - Row 1: 指标名称
    - Row 2: 数据（最新在前，日期递减）
    """
    names = df.iloc[1, :].tolist() if len(df) > 1 else []
    
    bonds = {}
    
    # 找到日期开始递增的位置（重复数据的开始）
    cutoff_row = len(df)
    prev_date = None
    for i in range(2, len(df)):
        d = df.iloc[i, 0]
        if isinstance(d, datetime):
            if prev_date and d > prev_date:
                cutoff_row = i
                break
            prev_date = d
    
    print(f"  [INFO] Bond data cutoff at row {cutoff_row}")
    
    for col_idx in range(1, len(df.columns)):
        name = names[col_idx] if col_idx < len(names) else f'指标{col_idx}'
        
        if pd.isna(name) or name == '' or 'Unnamed' in str(name):
            continue
        
        dates = []
        values = []
        
        # 只读取到cutoff_row，避免重复数据
        for row_idx in range(2, cutoff_row):
            date_val = df.iloc[row_idx, 0]
            data_val = df.iloc[row_idx, col_idx]
            
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(data_val) and isinstance(data_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(data_val), 2))
        
        # 数据在Excel中是最新在前，需要反转为时间顺序（旧→新）
        dates.reverse()
        values.reverse()
        
        if len(values) > 0:
            name_str = str(name)
            # 提取国家/地区信息
            country = '其他'
            if '美国' in name_str or '美债' in name_str:
                country = '美国'
            elif '中国' in name_str or '中债' in name_str:
                country = '中国'
            elif '德国' in name_str or '德债' in name_str:
                country = '德国'
            elif '英国' in name_str or '英债' in name_str:
                country = '英国'
            elif '日本' in name_str or '日债' in name_str:
                country = '日本'
            elif '法国' in name_str or '法债' in name_str:
                country = '法国'
            elif '意大利' in name_str:
                country = '意大利'
            elif '印度' in name_str:
                country = '印度'
            elif '越南' in name_str:
                country = '越南'
            elif '巴西' in name_str:
                country = '巴西'
            elif '南非' in name_str:
                country = '南非'
            
            bonds[f'bond_{col_idx}'] = {
                'name': name_str,
                'country': country,
                'unit': '%',
                'dates': dates,
                'values': values,
                'latest': values[-1] if values else None,
                'latest_date': dates[-1] if dates else None
            }
    
    return bonds


def extract_country_economy_data(df, country_name):
    """Extract country economy data
    
    各国经济sheet结构：
    - Row 0: "Wind"
    - Row 1: 指标名称
    - Row 2+: 数据（最新在前，日期递减）
    """
    names = df.iloc[1, :].tolist() if len(df) > 1 else []
    
    indicators = {}
    
    # 找到日期开始递增的位置（重复数据的开始）
    cutoff_row = len(df)
    prev_date = None
    for i in range(2, len(df)):
        d = df.iloc[i, 0]
        if isinstance(d, datetime):
            if prev_date and d > prev_date:
                cutoff_row = i
                break
            prev_date = d
    
    for col_idx in range(1, len(df.columns)):
        name = names[col_idx] if col_idx < len(names) else f'指标{col_idx}'
        
        if pd.isna(name) or name == '' or 'Unnamed' in str(name):
            continue
        
        dates = []
        values = []
        
        # 只读取到cutoff_row，避免重复数据
        for row_idx in range(2, cutoff_row):
            date_val = df.iloc[row_idx, 0]
            data_val = df.iloc[row_idx, col_idx]
            
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(data_val) and isinstance(data_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(data_val), 2))
        
        # 数据在Excel中是最新在前，需要反转为时间顺序（旧→新）
        dates.reverse()
        values.reverse()
        
        if len(values) > 0:
            indicators[f'indicator_{col_idx}'] = {
                'name': str(name),
                'country': country_name,
                'dates': dates,
                'values': values,
                'latest': values[-1] if values else None,
                'latest_date': dates[-1] if dates else None
            }
    
    return indicators


def extract_overview_data(df_commodity, df_liquidity, df_market, df_bond):
    """Extract overview data for dashboard table
    
    总览表格包含以下指标：
    - 原油: 布伦特、WTI、阿曼、迪拜、俄罗斯
    - 贵金属: 现货黄金、现货白银
    - 工业金属: LME铜、LME铝
    - 化工品: 乙二醇、PTA、乙烯、聚乙烯
    - 集运: INE集运指数
    - 权益市场: 标普500、纳斯达克、日经225、韩国综合指数
    - 债券市场: 10年期美债、2年期美债
    - 波动率: VIX指数
    """
    overview = {
        'categories': [
            {
                'name': '原油',
                'items': []
            },
            {
                'name': '贵金属',
                'items': []
            },
            {
                'name': '工业金属',
                'items': []
            },
            {
                'name': '相关化工品',
                'items': []
            },
            {
                'name': '集运',
                'items': []
            },
            {
                'name': '权益市场',
                'items': []
            },
            {
                'name': '债券市场',
                'items': []
            },
            {
                'name': '波动率指数',
                'items': []
            }
        ]
    }
    
    # Helper function to calculate change percentage
    def calc_change_pct(values, days=1):
        if len(values) < days + 1:
            return None
        current = values[-1]
        previous = values[-(days + 1)]
        if previous == 0:
            return None
        return round((current - previous) / previous * 100, 2)
    
    # Helper function to extract latest value and changes
    def extract_indicator_data(df, row_start, col_idx, name, unit=''):
        """Extract indicator data from dataframe"""
        dates = []
        values = []
        
        # Find cutoff row
        cutoff_row = len(df)
        prev_date = None
        for i in range(row_start, len(df)):
            d = df.iloc[i, 0]
            if isinstance(d, datetime):
                if prev_date and d > prev_date:
                    cutoff_row = i
                    break
                prev_date = d
        
        # Extract data
        for row_idx in range(row_start, cutoff_row):
            date_val = df.iloc[row_idx, 0]
            data_val = df.iloc[row_idx, col_idx]
            
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
                if pd.notna(data_val) and isinstance(data_val, (int, float)):
                    dates.append(date_str)
                    values.append(round(float(data_val), 2))
        
        dates.reverse()
        values.reverse()
        
        if len(values) == 0:
            return None
        
        return {
            'name': name,
            'unit': unit,
            'latest': values[-1],
            'latest_date': dates[-1] if dates else '',
            'change_1d': calc_change_pct(values, 1),
            'change_since_conflict': calc_change_pct(values, 30),  # Approx 1 month
            'values': values[-30:]  # Last 30 days for sparkline
        }
    
    # 1. 提取原油价格 (商品价格sheet)
    if df_commodity is not None and len(df_commodity) > 6:
        # 布伦特原油 (列1)
        data = extract_indicator_data(df_commodity, 6, 1, '布伦特原油', '美元/桶')
        if data:
            overview['categories'][0]['items'].append(data)
        
        # WTI原油 (列2)
        data = extract_indicator_data(df_commodity, 6, 2, 'WTI', '美元/桶')
        if data:
            overview['categories'][0]['items'].append(data)
        
        # 原油现货(阿曼) (列17)
        if len(df_commodity.columns) > 17:
            data = extract_indicator_data(df_commodity, 6, 17, '原油现货价格(阿曼)', '美元/桶')
            if data:
                overview['categories'][0]['items'].append(data)
        
        # 原油现货(迪拜) (列18)
        if len(df_commodity.columns) > 18:
            data = extract_indicator_data(df_commodity, 6, 18, '原油现货价格(迪拜)', '美元/桶')
            if data:
                overview['categories'][0]['items'].append(data)
        
        # 原油现货(俄罗斯) (列19)
        if len(df_commodity.columns) > 19:
            data = extract_indicator_data(df_commodity, 6, 19, '原油现货价格(俄罗斯)', '美元/桶')
            if data:
                overview['categories'][0]['items'].append(data)
        
        # 现货黄金 (列20)
        if len(df_commodity.columns) > 20:
            data = extract_indicator_data(df_commodity, 6, 20, '现货黄金', '美元/盎司')
            if data:
                overview['categories'][1]['items'].append(data)
        
        # 现货白银 (列21)
        if len(df_commodity.columns) > 21:
            data = extract_indicator_data(df_commodity, 6, 21, '现货白银', '美元/盎司')
            if data:
                overview['categories'][1]['items'].append(data)
        
        # LME铜 (列22)
        if len(df_commodity.columns) > 22:
            data = extract_indicator_data(df_commodity, 6, 22, 'LME铜', '美元/吨')
            if data:
                overview['categories'][2]['items'].append(data)
        
        # LME铝 (列9)
        data = extract_indicator_data(df_commodity, 6, 9, 'LME铝', '美元/吨')
        if data:
            overview['categories'][2]['items'].append(data)
        
        # 乙二醇 (列23)
        if len(df_commodity.columns) > 23:
            data = extract_indicator_data(df_commodity, 6, 23, '乙二醇', '元/吨')
            if data:
                overview['categories'][3]['items'].append(data)
        
        # PTA (列24)
        if len(df_commodity.columns) > 24:
            data = extract_indicator_data(df_commodity, 6, 24, '精对苯二甲酸(PTA)', '元/吨')
            if data:
                overview['categories'][3]['items'].append(data)
        
        # 乙烯 (列8)
        data = extract_indicator_data(df_commodity, 6, 8, '乙烯', '美元/吨')
        if data:
            overview['categories'][3]['items'].append(data)
        
        # 聚乙烯/LLDPE (列25)
        if len(df_commodity.columns) > 25:
            data = extract_indicator_data(df_commodity, 6, 25, '聚乙烯', '元/吨')
            if data:
                overview['categories'][3]['items'].append(data)
        
        # INE集运指数(欧线) (列26)
        if len(df_commodity.columns) > 26:
            data = extract_indicator_data(df_commodity, 6, 26, 'INE集运指数(欧线)', '点')
            if data:
                overview['categories'][4]['items'].append(data)
    
    # 2. 提取权益市场数据 (全球市场sheet)
    if df_market is not None and len(df_market) > 2:
        # 标普500 (列1)
        data = extract_indicator_data(df_market, 2, 1, '标普500', '点')
        if data:
            overview['categories'][5]['items'].append(data)
        
        # 纳斯达克 (列2)
        data = extract_indicator_data(df_market, 2, 2, '纳斯达克', '点')
        if data:
            overview['categories'][5]['items'].append(data)
        
        # 日经225 (列5)
        if len(df_market.columns) > 5:
            data = extract_indicator_data(df_market, 2, 5, '日经225', '点')
            if data:
                overview['categories'][5]['items'].append(data)
        
        # 韩国综合指数 (列6)
        if len(df_market.columns) > 6:
            data = extract_indicator_data(df_market, 2, 6, '韩国综合指数', '点')
            if data:
                overview['categories'][5]['items'].append(data)
    
    # 3. 提取债券市场数据 (全球债市sheet)
    if df_bond is not None and len(df_bond) > 2:
        # 10年期美债 (列1)
        data = extract_indicator_data(df_bond, 2, 1, '10年期美债', '%')
        if data:
            # Convert to BP for changes
            if data['change_1d'] is not None:
                data['change_1d'] = round(data['change_1d'] * 100, 0)
            if data['change_since_conflict'] is not None:
                data['change_since_conflict'] = round(data['change_since_conflict'] * 100, 0)
            data['unit'] = 'BP'
            overview['categories'][6]['items'].append(data)
        
        # 2年期美债 (列2)
        if len(df_bond.columns) > 2:
            data = extract_indicator_data(df_bond, 2, 2, '2年期美债', '%')
            if data:
                if data['change_1d'] is not None:
                    data['change_1d'] = round(data['change_1d'] * 100, 0)
                if data['change_since_conflict'] is not None:
                    data['change_since_conflict'] = round(data['change_since_conflict'] * 100, 0)
                data['unit'] = 'BP'
                overview['categories'][6]['items'].append(data)
    
    # 4. 提取VIX指数 (流动性sheet)
    if df_liquidity is not None and len(df_liquidity) > 3:
        # VIX (列2)
        if len(df_liquidity.columns) > 2:
            data = extract_indicator_data(df_liquidity, 3, 2, 'VIX指数', '')
            if data:
                overview['categories'][7]['items'].append(data)
    
    # Remove empty categories
    overview['categories'] = [c for c in overview['categories'] if len(c['items']) > 0]
    
    return overview

def update_html_data():
    """Update data in HTML file"""
    excel_path = '全球市场.xlsx'
    html_path = 'data-tracking.html'
    json_path = 'data/excel_history.json'
    eco_json_path = 'data/eco_data.json'
    
    print(f"Reading {excel_path}...")
    
    # Read Excel data
    try:
        df_commodity = pd.read_excel(excel_path, sheet_name=0, header=None)
        commodity_groups = extract_commodity_groups(df_commodity)
        print(f"[OK] Extracted {sum(len(g['items']) for g in commodity_groups.values())} commodities in {len(commodity_groups)} groups")
    except Exception as e:
        print(f"[ERROR] Error reading commodity sheet: {e}")
        return False
    
    try:
        df_liquidity = pd.read_excel(excel_path, sheet_name=1, header=None)
        liquidity_data = extract_liquidity_indicators(df_liquidity)
        print(f"[OK] Extracted {len(liquidity_data)} liquidity indicators")
    except Exception as e:
        print(f"[ERROR] Error reading liquidity sheet: {e}")
        return False
    
    # Read financial market data (third sheet)
    try:
        df_financial = pd.read_excel(excel_path, sheet_name=2, header=None)
        financial_data = extract_financial_data(df_financial)
        print(f"[OK] Extracted {len(financial_data['stocks'])} stocks and {len(financial_data['bonds'])} bonds")
    except Exception as e:
        print(f"[WARNING] Error reading financial sheet: {e}")
        financial_data = {'stocks': {}, 'bonds': {}}
    
    # Read global bond market data (fourth sheet - 全球债市)
    try:
        df_bond = pd.read_excel(excel_path, sheet_name=3, header=None)
        bond_data = extract_bond_data(df_bond)
        print(f"[OK] Extracted {len(bond_data)} global bond indicators")
    except Exception as e:
        print(f"[WARNING] Error reading bond sheet: {e}")
        bond_data = {}
    
    # Extract overview data for dashboard
    try:
        overview_data = extract_overview_data(df_commodity, df_liquidity, df_financial, df_bond)
        total_items = sum(len(c['items']) for c in overview_data['categories'])
        print(f"[OK] Extracted {total_items} overview indicators in {len(overview_data['categories'])} categories")
    except Exception as e:
        print(f"[WARNING] Error extracting overview data: {e}")
        overview_data = {'categories': []}
    
    # Prepare data object for data-tracking
    data = {
        'updated': datetime.now().isoformat(),
        'source': '全球市场.xlsx',
        'commodity_groups': commodity_groups,
        'liquidity': liquidity_data,
        'financial': financial_data,
        'bonds': bond_data,
        'overview': overview_data
    }
    
    # Convert to JSON string
    js_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    # Step 1: Write to separate JSON file
    try:
        Path('data').mkdir(exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(js_data)
        print(f"[OK] Data written to {json_path} ({len(js_data)/1024:.1f} KB)")
    except Exception as e:
        print(f"[ERROR] Failed to write JSON file: {e}")
        return False
    
    # Step 2: Update HTML to use fetch instead of embedded data
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace embedded STATIC_EXCEL_DATA with null (data will be loaded via fetch)
    pattern = r'let STATIC_EXCEL_DATA = \{.*?\};'
    replacement = 'let STATIC_EXCEL_DATA = null; // 数据将通过 fetch 加载'
    
    if re.search(pattern, html_content, re.DOTALL):
        html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
        print(f"[OK] Updated {html_path} to use external JSON")
    else:
        # Check if already using null (maybe already converted)
        if 'STATIC_EXCEL_DATA = null' in html_content:
            print(f"[OK] {html_path} already using external JSON")
        else:
            print(f"[WARNING] STATIC_EXCEL_DATA pattern not found, may need manual check")
    
    # Write back HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Step 3: Extract and save country economy data for eco-track.html
    try:
        country_sheets = [
            (5, '美国'),
            (6, '欧元区'),
            (7, '日本'),
            (8, '英国'),
            (9, '新加坡'),
            (10, '泰国'),
            (11, '越南'),
            (12, '澳大利亚')
        ]
        
        eco_data = {
            'updated': datetime.now().isoformat(),
            'countries': {}
        }
        
        for sheet_idx, country_name in country_sheets:
            try:
                df_country = pd.read_excel(excel_path, sheet_name=sheet_idx, header=None)
                country_indicators = extract_country_economy_data(df_country, country_name)
                if country_indicators:
                    eco_data['countries'][country_name] = country_indicators
                    print(f"[OK] Extracted {len(country_indicators)} indicators for {country_name}")
            except Exception as e:
                print(f"[WARNING] Error reading {country_name} sheet: {e}")
        
        # Write eco data to JSON
        eco_js_data = json.dumps(eco_data, ensure_ascii=False, separators=(',', ':'))
        with open(eco_json_path, 'w', encoding='utf-8') as f:
            f.write(eco_js_data)
        print(f"[OK] Economy data written to {eco_json_path} ({len(eco_js_data)/1024:.1f} KB)")
    except Exception as e:
        print(f"[WARNING] Error extracting economy data: {e}")
    
    print(f"\n[DONE] Data update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"       JSON: {json_path}")
    print(f"       HTML: {html_path}")
    return True

if __name__ == '__main__':
    success = update_html_data()
    exit(0 if success else 1)
