# 每日简报更新Prompt

## 任务目标
更新 `briefing.html` 网页内容，展示美以伊冲突的最新进展。

## 更新频率
每日更新一次，建议在北京时间上午9-10点执行。

---

## 执行步骤

### Step 1: 搜索最新信息（近36小时）

使用Web Search工具搜索以下关键词，获取**2026年4月X日-4月X日**（近36小时）的最新新闻：

#### 1.1 战局进展搜索
```
"Israel Iran war [当前日期] latest"
"US strikes Iran [当前日期]"
"IDF Iran missile attack [当前日期]"
"Iran missile intercepted Israel [当前日期]"
```

#### 1.2 各方表态搜索
```
"Trump Iran deadline [当前日期]"
"Trump Hormuz Strait [当前日期]"
"Iran Supreme Leader Khamenei statement [当前日期]"
"Saudi Arabia Iran war statement [当前日期]"
"UAE Iran conflict statement [当前日期]"
```

#### 1.3 海峡通行搜索
```
"Strait of Hormuz shipping [当前日期]"
"Hormuz Strait tanker [当前日期]"
"Qatar LNG Hormuz [当前日期]"
"Hormuz transit ships [当前日期]"
```

#### 1.4 供应链搜索
```
"Middle East supply chain disruption [当前日期]"
"Aluminum price LME Hormuz [当前日期]"
"LNG shortage India Iran war [当前日期]"
"Fertilizer supply Middle East [当前日期]"
"Supply chain pressure index [当前日期]"
```

#### 1.5 投行观点搜索
```
"Goldman Sachs oil price Iran [当前日期]"
"JP Morgan Dimon Iran war inflation [当前日期]"
"Morgan Stanley Middle East war [当前日期]"
"Oil price forecast investment bank [当前日期]"
```

---

### Step 2: 整理搜索结果

将搜索到的信息按以下5个板块分类整理：

#### 板块1: 战局进展（Military Progress）
- 美以联军对伊朗的打击行动
- 伊朗的反击（导弹、无人机等）
- 军事设施损毁情况
- 人员伤亡情况

**格式示例：**
```
标题: 美以联军空袭伊朗XX炼油厂
时间: 2026-04-XX XX:XX
内容: 详细描述打击行动...
来源: Reuters/CNN/WSJ
```

#### 板块2: 各方表态（Statements）
- **美国/特朗普**: 最后期限、威胁、谈判立场
- **伊朗/最高领袖**: 封锁海峡立场、报复威胁、谈判条件
- **沙特/阿联酋**: 对冲突的立场、能源政策表态
- **中国/俄罗斯/欧盟**: 外交立场（如有）

**格式示例：**
```
国家: 🇺🇸 美国/特朗普
时间: 2026-04-XX
表态: "周二将是发电厂日..."
来源: CNN/NBC News
```

#### 板块3: 海峡通行情况（Strait Status）
- 当日/近24小时通航船只数量
- 封锁持续时间（天数）
- 重要事件（如LNG船掉头、战争险保费变化）
- 伊朗对通行政策的调整

**关键数据：**
- 通航量变化（如"周末21艘船通过，为3月初以来最高"）
- 战争险保费涨幅
- 航运公司绕行情况

#### 板块4: 全球供应链（Supply Chain）
- **铝业**: LME铝价、EGA/Alba等产能损失
- **化肥**: 价格涨幅、供应短缺
- **LNG/能源**: 卡塔尔出口、印度短缺
- **供应链指数**: 纽约联储供应链压力指数等

**格式示例：**
```
行业: 铝业
事件: 阿联酋EGA工厂需12个月恢复
影响: LME铝价突破3500美元/吨
```

#### 板块5: 海外投行讨论（Investment Banks）
- **摩根大通**: Jamie Dimon观点、油价预测
- **高盛**: 油价目标、经济影响评估
- **摩根士丹利**: 投资建议、风险评估
- **其他**: 花旗、美银、瑞银等

**格式示例：**
```
机构: 摩根大通
发言人: Jamie Dimon
观点: 战争是不确定性领域，若霍尔木兹关闭至5月中旬油价或达150美元
来源: Greenwich Time/CNN
```

---

### Step 3: 生成完整HTML代码

**根据Step 2整理的数据，直接生成完整的HTML代码。**

请使用以下HTML模板，将整理好的数据填入对应位置：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>【华泰固收】中东地缘跟踪 - 美以伊冲突每日简报</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.8;}
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
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .header-left {
            position: absolute;
            left: 20px;
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
        .container{max-width:900px;margin:0 auto;padding:24px 20px;}
        .briefing-header{background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);border:1px solid #f59e0b;border-radius:12px;padding:24px;margin-bottom:24px;}
        .briefing-header h2{color:#92400e;font-size:1.4rem;margin-bottom:12px;}
        .briefing-header .summary{color:#78350f;font-size:0.95rem;line-height:1.8;}
        .section{background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.08);border:1px solid #e2e8f0;}
        .section h3{color:#1e40af;font-size:1.15rem;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid #e2e8f0;}
        .section p{color:#475569;font-size:0.95rem;margin-bottom:12px;text-align:justify;}
        .section ul{padding-left:20px;margin-bottom:12px;}
        .section li{color:#475569;font-size:0.95rem;margin-bottom:8px;}
        .highlight-box{background:#eff6ff;border-left:4px solid #3b82f6;padding:16px;border-radius:0 8px 8px 0;margin:16px 0;}
        .highlight-box.critical{background:#fef2f2;border-left-color:#dc2626;}
        .highlight-box.warning{background:#fffbeb;border-left-color:#f59e0b;}
        .highlight-box.statements{background:#f0fdf4;border-left-color:#16a34a;}
        .highlight-box h5{color:#1e40af;font-size:0.95rem;margin-bottom:10px;}
        .highlight-box.critical h5{color:#dc2626;}
        .highlight-box.warning h5{color:#b45309;}
        .highlight-box.statements h5{color:#166534;}
        .market-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:16px 0;}
        .market-card{background:#f8fafc;border-radius:8px;padding:16px;border:1px solid #e2e8f0;}
        .market-card h5{color:#1e40af;font-size:0.9rem;margin-bottom:8px;}
        .market-card p{color:#475569;font-size:0.85rem;margin:0;}
        .footer{text-align:center;padding:24px;color:#64748b;font-size:0.8rem;border-top:1px solid #e2e8f0;margin-top:40px;}
        @media (max-width: 768px) {
            .market-grid{grid-template-columns:repeat(2,1fr);}
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-main">
            <div class="header-left">
                <h1>【华泰固收】中东地缘跟踪</h1>
            </div>
            <div class="header-center">
                <a href="index.html" class="nav-btn">海峡跟踪</a>
                <a href="polymarket.html" class="nav-btn">Polymarket</a>
                <a href="data-tracking.html" class="nav-btn">全球市场</a>
                <a href="war-situation.html" class="nav-btn">战局形势</a>
                <a href="news.html" class="nav-btn">实时新闻</a>
                <a href="briefing.html" class="nav-btn active">每日简报</a>
                <a href="oil-chart.html" class="nav-btn">原油图谱</a>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- 标题区 -->
        <div class="briefing-header">
            <h2>每日简报 ([日期])</h2>
            <p class="summary">冲突第[X]天，霍尔木兹封锁第[X]天。[一句话总结当日关键动态]</p>
        </div>

        <!-- 1. 战局进展 -->
        <div class="section">
            <h3>战局进展</h3>
            <!-- 填入2-4条战局进展 -->
        </div>

        <!-- 2. 各方表态 -->
        <div class="section">
            <h3>各方最新表态</h3>
            <!-- 填入3-4条各方表态 -->
        </div>

        <!-- 3. 海峡通行情况 -->
        <div class="section">
            <h3>霍尔木兹海峡通行情况</h3>
            <!-- 填入海峡通行数据 -->
        </div>

        <!-- 4. 全球供应链 -->
        <div class="section">
            <h3>全球供应链影响</h3>
            <!-- 填入3-4条供应链信息 -->
        </div>

        <!-- 5. 海外投行讨论 -->
        <div class="section">
            <h3>海外投行观点</h3>
            <!-- 填入3-4条投行观点 -->
        </div>

        <!-- 市场数据 -->
        <div class="section">
            <h3>市场数据速览</h3>
            <div class="market-grid">
                <div class="market-card"><h5>布伦特原油</h5><p>[价格]</p></div>
                <div class="market-card"><h5>WTI原油</h5><p>[价格]</p></div>
                <div class="market-card"><h5>标普500</h5><p>[点数]</p></div>
                <div class="market-card"><h5>纳斯达克</h5><p>[点数]</p></div>
                <div class="market-card"><h5>VIX波动率</h5><p>[数值]</p></div>
                <div class="market-card"><h5>美元指数</h5><p>[数值]</p></div>
            </div>
        </div>

        <div class="footer">数据来源：路透社、彭博社、半岛电视台、CNN、华尔街日报等 | 仅供参考，不构成投资建议</div>
    </div>
</body>
</html>
```

---

### Step 4: 输出要求

**请直接输出完整的HTML代码**，格式如下：

```
=== 每日简报更新完成 ===

日期: 2026-04-XX
冲突第X天，封锁第X天

板块统计:
- 战局进展: X条
- 各方表态: X条
- 海峡通行: X个关键事件
- 供应链: X个行业
- 投行观点: X家机构

=== 完整HTML代码 ===

[直接输出完整的HTML代码，可直接复制粘贴到briefing.html文件中]

=== 使用说明 ===
1. 复制上方HTML代码
2. 粘贴到 briefing.html 文件中（覆盖原有内容）
3. 保存文件
4. 在浏览器中打开验证显示效果
```

---

### Step 5: 验证清单

输出HTML前请确认：
- [ ] 日期和冲突/封锁天数正确
- [ ] 5个板块都有内容（各2-4条）
- [ ] 信息来源标注清晰
- [ ] 市场数据准确（油价、股市、汇率）
- [ ] HTML格式正确，无语法错误
- [ ] 样式与之前保持一致

---

## 内容规范

### 信息筛选原则
1. **时效性**: 只保留近36小时（1.5天）内的信息
2. **准确性**: 优先采用Reuters、Bloomberg、CNN、WSJ等权威媒体
3. **相关性**: 排除纯猜测、未证实消息、重复旧闻
4. **完整性**: 包含时间、地点、事件、影响、来源五要素

### 内容排除清单
❌ 不要包含：
- 超过48小时的旧闻
- 无明确来源的传闻
- 纯市场价格预测（无实际事件支撑）
- 重复已在昨日简报中的内容

✅ 必须包含：
- 特朗普/伊朗最高领袖的最新表态
- 霍尔木兹海峡通航数据变化
- 投行对油价/经济的最新观点
- 供应链中断的具体案例

---

## 网页结构说明

新版简报网页包含5个板块：

```html
1. ⚔️ 战局进展        - 军事行动、打击与反击
2. 🎙️ 各方表态        - 特朗普、伊朗、沙特等立场
3. 🚢 海峡通行情况    - 通航数据、封锁状态
4. 📦 全球供应链      - 铝业、化肥、LNG等行业影响
5. 🏦 海外投行观点    - 摩根大通、高盛等机构分析
+ 📊 市场数据速览     - 油价、股市、汇率等
```

---

## 示例输出

更新后的简报应类似：

```
📰 美以伊冲突每日简报 (2026-04-07)
冲突第39天，霍尔木兹封锁第37天

⚔️ 战局进展
- 美以联军空袭阿巴丹炼油厂（4月6日 22:30）
- 伊朗导弹反击全部被拦截（4月7日 04:20）
- 以军空袭德黑兰三座机场（4月6日）

🎙️ 各方表态
- 🇺🇸 特朗普：设定周二晚8点最后期限，威胁打击发电厂和桥梁
- 🇮🇷 伊朗最高领袖：将继续封锁海峡，1300万人报名牺牲生命运动
- 🇸🇦 沙特/阿联酋：拦截7枚导弹，敦促安理会采取行动

🚢 海峡通行情况
- 状态：部分松动但仍受限
- 通航：周末21艘船通过，为3月初以来最高
- 事件：首艘LNG船穿越、卡塔尔油轮掉头、战争险保费飙升450%

📦 全球供应链
- 铝业：LME铝价突破3500美元，EGA需12个月恢复
- 化肥：以色列价格飙升180%，全球粮食市场受冲击
- LNG：卡塔尔出口受阻，印度严重短缺
- 供应链指数：升至0.68，为2023年来最高

🏦 海外投行观点
- 摩根大通Dimon：若霍尔木兹关闭至5月中旬，油价或达150美元
- 高盛：冲突将持续6-8周，全球经济增速下修0.4%
- 摩根士丹利：油价中枢90-105美元，建议增配黄金ETF

📊 市场数据
- 布伦特原油：110美元/桶 (+4.5%)
- WTI原油：113.50美元/桶 (+5.2%)
- 标普500：5185点 (-1.3%)
```

---

## 自动化建议

如需进一步优化，可考虑：
1. 使用定时任务每日自动执行此Prompt
2. 将搜索结果缓存到JSON文件供脚本读取
3. 添加邮件/消息通知，更新完成后提醒审核

---

## HTML内容填写格式示例

### 战局进展板块格式：
```html
<div class="section">
    <h3>战局进展</h3>
    <div class="highlight-box military">
        <h5>美以联军空袭伊朗XX炼油厂</h5>
        <p><strong>时间：</strong>4月X日 XX:XX | <strong>来源：</strong>Reuters</p>
        <p>详细描述打击行动、损毁情况、人员伤亡...</p>
    </div>
    <div class="highlight-box military">
        <h5>伊朗导弹反击全部被拦截</h5>
        <p><strong>时间：</strong>4月X日 XX:XX | <strong>来源：</strong>CNN</p>
        <p>详细描述反击行动、拦截情况...</p>
    </div>
</div>
```

### 各方表态板块格式：
```html
<div class="section">
    <h3>各方最新表态</h3>
    <div class="highlight-box statements">
        <h5>美国/特朗普</h5>
        <p><strong>时间：</strong>4月X日 | <strong>来源：</strong>CNN/NBC</p>
        <p>具体表态内容，包括最后期限、威胁等...</p>
    </div>
    <div class="highlight-box statements">
        <h5>伊朗/最高领袖</h5>
        <p><strong>时间：</strong>4月X日 | <strong>来源：</strong>ISW</p>
        <p>具体表态内容，包括封锁立场、报复威胁等...</p>
    </div>
</div>
```

### 海峡通行板块格式：
```html
<div class="section">
    <h3>霍尔木兹海峡通行情况</h3>
    <div class="highlight-box warning">
        <h5>海峡通行状态</h5>
        <p><strong>当前状态：</strong>部分松动但仍受限 | <strong>封锁天数：</strong>第X天</p>
        <p><strong>通行数据：</strong>周末X艘船通过...</p>
        <p><strong>关键事件：</strong></p>
        <ul>
            <li>事件1...</li>
            <li>事件2...</li>
            <li>事件3...</li>
        </ul>
        <p><strong>影响评估：</strong>具体影响...</p>
    </div>
</div>
```

### 供应链板块格式：
```html
<div class="section">
    <h3>全球供应链影响</h3>
    <div class="highlight-box">
        <h5>铝业</h5>
        <p><strong>事件：</strong>阿联酋EGA工厂遭袭...</p>
        <p><strong>影响：</strong>LME铝价突破3500美元...</p>
    </div>
    <div class="highlight-box">
        <h5>化肥</h5>
        <p><strong>事件：</strong>以色列化肥价格飙升...</p>
        <p><strong>影响：</strong>全球粮食市场受冲击...</p>
    </div>
</div>
```

### 投行观点板块格式：
```html
<div class="section">
    <h3>海外投行观点</h3>
    <div class="highlight-box">
        <h5>摩根大通 (JP Morgan)</h5>
        <p><strong>发言人：</strong>CEO Jamie Dimon</p>
        <p>具体观点内容...</p>
        <p style="font-size:0.8rem;color:#64748b;">来源：Greenwich Time/CNN</p>
    </div>
    <div class="highlight-box">
        <h5>高盛 (Goldman Sachs)</h5>
        <p>具体观点内容...</p>
        <p style="font-size:0.8rem;color:#64748b;">来源：CNBC</p>
    </div>
</div>
```

---

## 执行前确认清单

**执行此Prompt前，请确认：**
1. [ ] 当前日期和冲突/封锁天数（冲突天数累加，封锁天数累加）
2. [ ] Web Search工具可用
3. [ ] 搜索日期范围设置为近36小时
4. [ ] 输出格式为可直接复制粘贴的完整HTML代码

---

## 输出示例

最终输出应如下所示：

```
=== 每日简报更新完成 ===

日期: 2026-04-07
冲突第39天，封锁第37天

板块统计:
- 战局进展: 3条
- 各方表态: 3条  
- 海峡通行: 5个关键事件
- 供应链: 4个行业
- 投行观点: 4家机构

=== 完整HTML代码 ===

<!DOCTYPE html>
<html lang="zh-CN">
...（完整的HTML代码）...
</html>

=== 使用说明 ===
1. 复制上方HTML代码
2. 粘贴到 briefing.html 文件中（覆盖原有内容）
3. 保存文件
4. 在浏览器中打开验证显示效果
```
