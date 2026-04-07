# 中东地缘研究观点数据更新流程

## 概述
本流程用于收集智库和投行关于伊朗战争、霍尔木兹海峡、油价等中东地缘政治主题的研究观点，生成HTML展示页面。

---

## 数据流程图（两步流程）

```
┌─────────────────────────┐         ┌─────────────────────────────────────┐
│    Step 1: 数据采集      │   ──→   │       Step 2: AI筛选+HTML生成        │
│  update_research_data.py │         │        Kimi直接处理并输出            │
└─────────────────────────┘         └─────────────────────────────────────┘
            ↓                                                   ↓
  data/research_raw_data.json                           research.html
      （用户复制给Kimi）                              （Kimi直接生成）
```

**流程说明**：
1. **Step 1**: 运行脚本抓取智库RSS和投行/财经媒体搜索数据
2. **Step 2**: 将抓取的数据复制给Kimi，Kimi根据筛选标准处理并直接生成 `research.html`

---

## Step 1: 数据采集

### 运行脚本
```bash
python scripts/update_research_data.py
```

### 功能说明
1. **抓取智库RSS**（12个来源）
   - 美国：Brookings, CSIS, CFR, PIIE, Carnegie, RAND, Atlantic Council
   - 欧洲：Chatham House, ECFR, GMF
   - 国际组织：IMF, BIS

2. **搜索投行研报**（DuckDuckGo搜索，无需API key）
   - **Tier 1**: Goldman Sachs, Morgan Stanley, JPMorgan, Citi, BofA
   - **Tier 2**: Deutsche Bank, Barclays, UBS, Credit Suisse
   - **Tier 3**: HSBC, SocGen, Nomura, Macquarie
   - **Tier 4**: Bloomberg, Reuters, FT, WSJ, CNBC, MarketWatch 报道的投行观点
   - **Tier 5**: Hormuz, Iran war, Brent/WTI 等主题搜索
   - 搜索时间范围：**最近一个月**，确保获取最新研报

### 输出文件
- `data/research_raw_data.json` - 原始数据（典型数据量：300-400条）

---

## Step 2: AI筛选处理（由Kimi处理）

### 操作步骤

#### 1. 准备输入数据
打开 `data/research_raw_data.json`，复制整个文件内容。

#### 2. 发送给Kimi
将复制的内容粘贴到对话框，并附上指令：
> 请根据 research.md 中的筛选标准处理这些数据，生成 research.html

---

### 给Kimi的筛选指令（复制使用）

```
我是专业的地缘政治与能源市场研究员。请处理以下研究数据，筛选出与"伊朗战争、霍尔木兹海峡、油价"高度相关的内容，并生成 research.html。

## 输入数据
[粘贴 data/research_raw_data.json 的内容]

## 筛选标准

### 必须保留（满足任一）
- 标题或摘要包含：Iran war, Hormuz Strait, oil supply, oil price, energy security, Middle East conflict
- 内容与伊朗战争对全球能源市场影响直接相关
- 涉及霍尔木兹海峡关闭、油价波动、能源供应链冲击
- **投行研报**：Goldman Sachs, Morgan Stanley, JPMorgan等投行的油价预测、能源展望
- **财经媒体报道**：Bloomberg, Reuters, FT, WSJ等关于投行观点的报道

### 必须排除
- 印度、乌克兰、匈牙利、非洲、孟加拉国等地区内容
- 气候变化、网络安全、AI监管、纯政治话题
- 纯军事战术分析（无能源/经济影响维度）
- 书籍评论、人物访谈
- 与中东/能源无关的通用经济分析

### 去重与提炼规则（重要）

#### 1. 同一机构去重
- **同一投行**（如JPMorgan、Goldman Sachs）的多个条目，如果讨论同一主题（如霍尔木兹供应中断），**只保留最新的一条**
- 如果同一投行有不同主题（如油价预测 vs 供应链分析），可以保留2-3条，但要确保观点有实质性差异

#### 2. 日期相近去重（7天内）
- 发布日期在7天内的相似内容，视为同一批次研报
- 保留信息最完整、观点最明确的一条
- 其他相似条目删除

#### 3. 内容相似性去重
- **标题相似度>70%** 视为重复
- **摘要核心观点相同**（如都是"上调油价预测至$85"）视为重复
- **来源不同但内容相同**（如Reuters报道Goldman观点 vs Goldman官网），优先保留原始投行来源

#### 4. 提炼原则
- 对于重复信息，**合并提炼**成一条高质量条目
- 保留：最新日期 + 最完整数据 + 最明确观点
- 删除：过时日期 + 碎片化信息 + 模糊表述

**示例**：
- JPMorgan 3月20日："油价可能上涨" 
- JPMorgan 3月22日："因霍尔木兹中断，上调Brent预测至$90"
→ **保留3月22日条目，删除3月20日**

## 处理要求

1. **筛选**：只保留与 Iran war / Hormuz / oil / energy supply 直接相关的内容
2. **去重提炼**：按上述规则去除重复，合并相似观点
3. **分类**：
   - think_tank = 智库研究
   - investment_bank = 投行研报
   - news = 财经媒体报道
   - institution = 国际组织
4. **翻译**：标题和摘要翻译成中文（简洁准确）
5. **标记情绪**：
   - bullish = 看涨油价/乐观预期/供应缓解
   - bearish = 看跌油价/风险警示/供应冲击担忧
   - neutral = 客观分析/平衡观点
6. **打分**：relevance_score 1-5（5=直接相关，如霍尔木兹/伊朗战争）
7. **排序**：按相关度降序排列
8. **数量控制**：最终保留 **40-60条** 高质量、无重复的观点

## 输出要求

处理完成后，**直接生成 research.html 文件**，包含：
- 筛选后的条目（通常50-80条）
- 卡片式布局
- 机构筛选功能（智库/投行/媒体/国际组织）
- 情绪标签显示
- 响应式设计

使用以下HTML模板结构：
- 头部导航栏（链接到index.html, briefing.html等）
- 统计卡片（总观点数、来源机构数、智库/投行/媒体数量）
- 筛选栏（按类型筛选、按机构筛选）
- 观点卡片网格布局
- 页脚更新日期
```

#### 3. Kimi直接生成
Kimi会：
1. 处理数据（筛选、翻译、标记）
2. 直接输出完整的 `research.html` 文件内容
3. 你保存为 `research.html` 即可

---

## 完整执行流程

```bash
# Step 1: 数据采集
python scripts/update_research_data.py

# Step 2: AI筛选处理（Kimi直接生成HTML）
# 1. 打开 data/research_raw_data.json，复制内容
# 2. 粘贴到Kimi对话框，并附上指令：
#    "请根据 research.md 筛选标准处理，生成 research.html"
# 3. Kimi直接输出完整的 research.html，保存即可
```

---

## 数据源配置

### 智库RSS源（THINK_TANK_SOURCES）
| 英文名 | 中文名 | RSS地址 |
|--------|--------|---------|
| Brookings Institution | 布鲁金斯学会 | https://www.brookings.edu/feed/ |
| CSIS | 战略与国际研究中心 | https://www.csis.org/rss.xml |
| CFR | 外交关系委员会 | https://www.cfr.org/rss.xml |
| PIIE | 彼得森国际经济研究所 | https://www.piie.com/rss.xml |
| Carnegie Endowment | 卡内基国际和平基金会 | https://carnegieendowment.org/rss.xml |
| RAND Corporation | 兰德公司 | https://www.rand.org/rss.xml |
| Atlantic Council | 大西洋理事会 | https://www.atlanticcouncil.org/feed/ |
| Chatham House | 查塔姆研究所 | https://www.chathamhouse.org/feed |
| ECFR | 欧洲外交关系委员会 | https://ecfr.eu/feed/ |
| GMF | 德国马歇尔基金会 | https://www.gmfus.org/rss.xml |
| IMF | 国际货币基金组织 | https://www.imf.org/en/Publications/RSS |
| BIS | 国际清算银行 | https://www.bis.org/doclist/bis_fsi_publs.rss |

### 投行研报搜索（IB_RESEARCH_SEARCHES）

| 优先级 | 类型 | 搜索关键词 |
|--------|------|-----------|
| **P1** | Goldman Sachs | Goldman Sachs oil price forecast brent 2025 |
| **P1** | Morgan Stanley | Morgan Stanley energy outlook oil forecast |
| **P1** | JPMorgan | JPMorgan oil supply disruption forecast |
| **P1** | Citi | Citi commodity outlook oil price target |
| **P1** | Bank of America | Bank of America energy outlook oil forecast |
| **P2** | Deutsche Bank | Deutsche Bank oil price forecast commodity |
| **P2** | Barclays | Barclays oil price target energy research |
| **P2** | UBS | UBS commodity outlook oil forecast |
| **P2** | Credit Suisse | Credit Suisse oil market outlook |
| **P3** | HSBC | HSBC oil price forecast commodity |
| **P3** | Societe Generale | Societe Generale oil forecast energy |
| **P3** | Nomura | Nomura oil price forecast energy |
| **P3** | Macquarie | Macquarie commodity outlook oil |
| **P1** | Bloomberg/Goldman | Bloomberg Goldman Sachs oil price forecast |
| **P1** | Bloomberg | Bloomberg analyst oil price target |
| **P1** | Reuters | Reuters investment bank oil forecast |
| **P1** | Reuters | Reuters analyst oil price middle east |
| **P1** | FT | Financial Times oil price forecast analyst |
| **P1** | WSJ | Wall Street Journal energy analysts forecast |
| **P2** | CNBC | CNBC oil price forecast analyst |
| **P2** | MarketWatch | MarketWatch oil forecast investment bank |
| **P1** | 主题搜索 | Hormuz Strait oil supply analyst forecast |
| **P1** | 主题搜索 | Iran war oil supply disruption analyst |
| **P1** | 主题搜索 | Middle East oil supply risk forecast |
| **P1** | 主题搜索 | Brent crude price forecast 2025 |
| **P1** | 主题搜索 | WTI oil price target investment bank |
| **P2** | 主题搜索 | oil price outlook geopolitical risk |

**统计**：共27个搜索任务，覆盖15家投行+6家财经媒体+6个主题搜索

**搜索时间范围**：最近一个月（timelimit='m'）

---

## 文件结构

```
scripts/
├── update_research_data.py      # Step 1: 数据采集脚本
└── generate_research_html.py    # 备用：HTML生成脚本（Kimi处理失败时使用）

data/
└── research_raw_data.json       # 原始数据（Step 1输出，Step 2输入）

research.html                    # 最终展示页面（Step 2直接生成）
research.md                      # 本说明文档
```

---

## 更新频率建议

| 频率 | 操作 |
|------|------|
| 每日 | 检查RSS更新，如有重大事件（如霍尔木兹关闭升级）立即更新 |
| 每周 | 完整执行两步流程：1) 运行数据采集脚本 → 2) 交给Kimi处理生成HTML |
| 每月 | 检查RSS源可用性，调整搜索关键词 |

---

## 常见问题

### Q: 投行研报搜索不到？
A: 检查以下几点：
1. 确保 `duckduckgo-search` 已安装：`pip install duckduckgo-search`
2. 搜索时间范围已设为最近一个月（timelimit='m'）
3. 如长期无结果，可能需要更换搜索源或使用付费API（如SerpAPI）

### Q: RSS抓取为空？
A: 检查RSS地址是否有效：
```bash
curl -I https://www.brookings.edu/feed/
```
部分RSS可能需要特殊Headers。

### Q: AI处理token超限？
A: 如果entries超过300条，分批处理：
- 第一批：think_tank_entries + ib_search_results[0:100]
- 第二批：ib_search_results[100:200]
- 合并输出

### Q: 想添加新数据源？
A: 编辑 `update_research_data.py`：
- 添加RSS源：修改 `THINK_TANK_SOURCES` 列表
- 添加搜索：修改 `IB_RESEARCH_SEARCHES` 列表

---

*文档版本：2026-04-06*
*搜索配置：27个任务，覆盖15家投行+6家财经媒体*


---

## 附录D：智能去重与日期提取（新增）

### 去重执行流程（由Kimi或Python脚本执行）

```
原始数据 (315条)
    ↓
Step 1: 相关性筛选 → 202条 (score >= 3)
    ↓
Step 2: 机构内去重 → 144条 (7天内+标题相似度>60%)
    ↓
Step 3: 跨来源去重 → 60条 (标题相似度>65%)
    ↓
最终输出
```

### 日期提取规则

研报实际日期应从以下位置提取（按优先级）：

1. **Summary中的日期**（最高优先级）
   - 格式: "Mar 13, 2026 · ..."
   - 格式: "Mar 27, 2026 · ..."
   - 格式: "5 days ago · ..."

2. **Title中的日期**
   - 如: "Goldman raises 2026 Brent forecast (Mar 2026)"

3. **Pub_date**（保底）
   - 抓取日期，非研报实际日期

**提取后的日期用于**：
- HTML卡片显示日期
- 按日期从新到旧排序

### Python去重代码参考

```python
from difflib import SequenceMatcher
from datetime import datetime, timedelta

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Step 1: 按机构分组去重
grouped = {}
for item in entries:
    source = item['source']
    if source not in grouped:
        grouped[source] = []
    grouped[source].append(item)

# Step 2: 机构内去重（7天内+相似标题）
unique_entries = []
for source, items in grouped.items():
    items.sort(key=lambda x: x['date'], reverse=True)  # 从新到旧
    
    kept = []
    for item in items:
        is_dup = False
        for existing in kept:
            date_diff = abs((item['date'] - existing['date']).days)
            if date_diff <= 7:
                if similar(item['title'], existing['title']) > 0.6:
                    is_dup = True
                    break
                # 核心观点相同（都是预测油价）
                if 'forecast' in item['title'].lower() and 'forecast' in existing['title'].lower():
                    is_dup = True
                    break
        if not is_dup:
            kept.append(item)
    unique_entries.extend(kept)

# Step 3: 跨来源去重（不同媒体报道同一事件）
final_entries = []
for item in sorted(unique_entries, key=lambda x: x['relevance'], reverse=True):
    is_dup = False
    for existing in final_entries:
        if similar(item['title'], existing['title']) > 0.65:
            is_dup = True
            break
        # 同一事件（如都是Barclays的85美元预测）
        if '85' in item['title'] and '85' in existing['title']:
            is_dup = True
            break
    if not is_dup:
        final_entries.append(item)
```

### HTML排序要求

生成HTML时必须：
1. **按研报日期从新到旧排序**（不是抓取日期）
2. **显示研报实际日期**（不是pub_date）
3. **数量控制在40-60条**，确保高质量无重复

---

## 附录E：后续更新说明（新增）

### 搜索时间范围

首次运行后，后续更新应将搜索时间范围调整为**最近72小时/一周**：

```python
# update_research_data.py 中
timelimit = 'w'  # 'w'=最近一周(约72h+), 'd'=24h, 'm'=1月
```

- **首次运行**: `'m'` (月) - 获取历史数据
- **后续更新**: `'w'` (周) - 获取最近72小时左右的新研报

### 更新频率建议（更新后）

| 频率 | 操作 |
|------|------|
| 每日 | 如有重大事件（如霍尔木兹关闭升级），立即运行脚本更新 |
| 每周 | 常规更新：运行脚本（搜索最近72h）→ Kimi处理 → 生成HTML |
| 每月 | 检查RSS源可用性，调整搜索关键词 |

### 文件保留清单

保留文件：
- `scripts/update_research_data.py` - 数据采集（已优化为72h搜索）
- `scripts/generate_research_html.py` - HTML生成（按日期排序）
- `data/research_raw_data.json` - 原始抓取数据
- `data/research_deduped.json` - 去重后数据
- `research.html` - 最终展示页面
- `research.md` - 本文档

删除文件（测试用）：
- `research_ai_input.json`
- `research_filtered.json`
- `thinktank_insights_summary.json`
- `generate_html.py`
- `generate_deduped_html.py`
- `process_research_ai.py`

---

*附录更新时间：2026-04-06*
*更新内容：智能去重逻辑、日期提取规则、72h搜索配置*


---

## 附录F：翻译步骤说明（新增）

### 最终输出要求：全部中文呈现

数据处理完成后，生成HTML时必须：

1. **标题翻译**
   - 英文标题 → 简洁准确的中文标题
   - 示例："Barclays raises 2026 Brent forecast to $85" → "巴克莱上调2026年布伦特油价预测至85美元"

2. **摘要翻译**
   - 英文摘要 → 80-150字中文摘要
   - 保留关键数据（如$85、1400万桶等）
   - 示例："Barclays on Friday raised its 2026 Brent crude forecast to $85 per barrel..." → "巴克莱因霍尔木兹海峡供应中断，将2026年布伦特原油价格预测上调至每桶85美元。"

3. **来源名称**
   - 保留英文原名
   - 可选添加中文备注（如"高盛(Goldman Sachs)"）

4. **日期格式**
   - 保持YYYY-MM-DD格式
   - 提取研报实际日期（非抓取日期）

### 翻译质量要求

- **准确**：专业术语正确（Brent→布伦特，Hormuz→霍尔木兹）
- **简洁**：标题不超过25字，摘要不超过150字
- **一致**：同一机构/术语统一翻译

### 已翻译条目示例

| 原文标题 | 中文标题 | 中文摘要 |
|---------|---------|---------|
| Barclays raises 2026 Brent forecast to $85 | 巴克莱上调2026年布伦特油价预测至85美元 | 巴克莱因霍尔木兹海峡供应中断，将2026年布伦特原油价格预测上调至每桶85美元。 |
| Macquarie flags 40% risk probability as Iran war chokes | 麦格理：油价或达200美元（风险概率40%） | 麦格理警告，若伊朗冲突持续至6月且霍尔木兹海峡保持关闭，原油价格可能攀升至每桶200美元。 |
| How the Iran war could shift energy policies | 伊朗战争如何改变全球能源政策 | 霍尔木兹海峡关闭引发燃料短缺和能源成本飙升，同时也为能源生产国带来新机遇。 |

---

*附录更新时间：2026-04-06*
