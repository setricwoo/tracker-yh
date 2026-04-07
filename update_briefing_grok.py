#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美以伊冲突每日简报 - AI API 自动更新脚本（仅更新内容，不修改布局）
支持：Grok官方API、OpenAI格式中转、自定义中转服务等
"""

import json
import os
import sys
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# ============ 配置区域 - 请在此处修改 ============
CONFIG = {
    # API密钥（必填）
    "api_key": "sk-9XSaf4XwU4DefoKqpuZWVZ5OrZbzmw6YsksHaqo7VcDw3ZF1",
    
    # API类型选择（必填）
    # 可选值："grok" | "openai" | "custom"
    "api_type": "openai",

    # API基础URL（根据中转服务修改）
    "base_url": "https://api.vectorengine.ai/v1",

    # 模型名称（根据中转服务修改）
    "model": "grok-4.2",

    # 其他参数
    "max_tokens": 50000,  # 大token以支持深度长文输出
    "temperature": 0.4,
    "briefing_file": "briefing.html",
}

# ============ 高级配置（一般不需要修改） ============
CUSTOM_HEADERS = {}

def get_api_config():
    """获取API配置，支持从环境变量覆盖"""
    config = CONFIG.copy()

    if os.environ.get("AI_API_KEY"):
        config["api_key"] = os.environ.get("AI_API_KEY")

    if os.environ.get("AI_BASE_URL"):
        config["base_url"] = os.environ.get("AI_BASE_URL")

    if os.environ.get("AI_MODEL"):
        config["model"] = os.environ.get("AI_MODEL")

    # 构建完整URL
    config["api_url"] = f"{config['base_url']}/chat/completions"

    return config

def get_today_info():
    """获取今日信息"""
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")

    conflict_start = datetime(2026, 2, 28)
    conflict_day = (today - conflict_start).days + 1

    blockade_start = datetime(2026, 3, 2)
    blockade_day = (today - blockade_start).days + 1

    return {
        "date": date_str,
        "conflict_day": conflict_day,
        "blockade_day": max(0, blockade_day),
        "today_iso": today.strftime("%Y-%m-%d")
    }

def call_api(config, system_prompt, user_prompt):
    """调用API"""
    if not config["api_key"]:
        print("[错误] 未设置API密钥")
        return None

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
        **CUSTOM_HEADERS
    }

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"]
    }

    try:
        print(f"[信息] 正在调用API...")
        print(f"[信息] 服务类型: {config['api_type']}")
        print(f"[信息] 模型: {config['model']}")
        print("[信息] 这可能需要30-60秒，请耐心等待...")

        response = requests.post(
            config["api_url"],
            headers=headers,
            json=payload,
            timeout=180
        )

        if response.status_code == 429:
            print(f"[错误] API请求频率限制(HTTP 429)，请稍后重试")
            return None
        elif response.status_code != 200:
            print(f"[错误] API返回错误: HTTP {response.status_code}")
            print(f"[错误] 响应内容: {response.text[:500]}")
            return None

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
        elif "content" in result:
            content = result["content"]
        else:
            print(f"[错误] 无法解析API响应格式")
            return None

        if "usage" in result:
            usage = result["usage"]
            print(f"[信息] Token使用: 输入={usage.get('prompt_tokens', 0)}, 输出={usage.get('completion_tokens', 0)}")

        return content

    except requests.exceptions.Timeout:
        print("[错误] API请求超时")
        return None
    except Exception as e:
        print(f"[错误] API调用失败: {e}")
        return None

def extract_json_from_text(text):
    """从文本中提取JSON"""
    if not text or not text.strip():
        print("[错误] API返回内容为空")
        return None

    text = text.strip()

    try:
        # 尝试匹配```json ... ```
        if "```json" in text:
            match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text)
            if match:
                return json.loads(match.group(1))

        # 尝试匹配``` ... ```
        if "```" in text:
            match = re.search(r'```\s*(\{[\s\S]*?\})\s*```', text)
            if match:
                return json.loads(match.group(1))

        # 尝试直接找JSON对象
        match = re.search(r'(\{[\s\S]*\})', text)
        if match:
            return json.loads(match.group(1))

        # 最后尝试直接解析
        return json.loads(text)

    except json.JSONDecodeError as e:
        print(f"[错误] JSON解析失败: {e}")
        print("[调试] 响应内容长度:", len(text))
        print("[调试] 响应内容前500字符:")
        try:
            print(text[:500])
        except:
            print("(内容包含特殊字符，无法显示)")
        return None

def generate_briefing_with_ai(config, info):
    """使用AI API生成简报内容"""

    system_prompt = """你是华泰固收研究所的中东地缘政治首席分析师，拥有20年研究经验，曾在国际顶级智库任职，多次准确预测中东局势演变。

你的核心能力：
1. 数据严谨性：对每一个数字负责，不确定必标注，错误必纠正
2. 信息全面性：多源交叉验证，不遗漏关键信息，善于归纳整合
3. 分析深度：透过表象看本质，识别关键变量，预判演变路径
4. 战略视野：将具体事件置于全球政治经济格局中分析

你的思考方法论（必须在分析中体现）：
1. 层层追问：
   - 发生了什么？（事实层）
   - 为什么发生？（动因层）
   - 会导致什么？（影响层）
   - 还有什么可能？（情景层）

2. 多维度交叉验证：
   - 政治维度：各方战略意图、国内政治约束
   - 军事维度：实力对比、战术选择、升级路径
   - 经济维度：成本收益、资源约束、市场反应
   - 外交维度：联盟关系、第三方影响、国际法

3. 历史对照：
   - 类似历史情境的启示
   - 关键差异点的识别
   - 教训与误判案例

4. 市场逻辑：
   - 投行和机构的共识与分歧
   - 定价的有效性和偏差
   - 风险溢价的变化机制

写作要求：
- 使用专业术语但保持可读性
- 论证逻辑严密，结论有据可依
- 不回避不确定性，但给出概率判断
- 提供可操作的行动建议

【输出格式 - 必须严格遵守】
1. 必须输出有效的JSON格式
2. 不要在JSON之外添加任何解释性文字
3. 所有内容都必须包含在JSON结构内
4. 深度分析的四个子模块内容要完整展开，确保字数达标
5. JSON结构：
{
  "summary": "简报摘要（200字以内）",
  "conflict_progress": [
  {"title": "美以联军最新军事行动", "content": "3月X日XX时间...详细描述...", "type": "military"},
  {"title": "伊朗反击动态", "content": "3月X日XX时间...详细描述...", "type": "military"},
  {"title": "关键设施损毁情况", "content": "3月X日XX时间...详细描述...", "type": "damage"},
  {"title": "各方官方表态", "content": "3月X日XX时间...详细描述...", "type": "statements"},
  {"title": "市场与国际反应", "content": "3月X日XX时间...详细描述...", "type": "reaction"}
  // 根据过去24小时实际进展，动态增减条目，总字数1500+
],
  "positions": {"us": "...", "israel": "...", "iran": "...", "others": "..."},
  "timeline": [{"time": "...", "event": "...", "type": "..."}, ...],
  "market_data": {"oil": "...", "equity": "...", "bond": "...", "fx": "...", "volatility": "..."},
  "bank_views": "投行观点汇总（至少5家，包含目标价、持续时间、判断逻辑、交易建议、风险提示）",
  "analysis": {
    "geopolitical": "地缘政治深度分析（必须500-600字，充分展开论证）",
    "outlook": "后续进展预判（必须400-500字，包含情景分析、时间节点、信号清单）",
    "impact": "全球经济影响分析（必须500-600字，包含能源、通胀、供应链、中国影响）",
    "strategy": "投资策略建议（必须400-500字，包含固收、大宗商品、外汇、综合配置）"
  },
  "watch_points": ["关注要点1", "关注要点2", ...],
  "news": [{"title": "...", "source": "...", "url": "...", "summary": "..."}, ...]
}"""

    user_prompt = f"""请生成{info['date']}（美以伊冲突第{info['conflict_day']}天）的每日简报。

【当前背景】
- 日期：{info['date']}（今天）
- 冲突天数：第{info['conflict_day']}天（2026年2月28日开始）
- 霍尔木兹封锁：第{info['blockade_day']}天（3月2日开始）
- 当前态势：布伦特原油已突破100美元/桶，伊朗向沙特发射导弹，冲突开始外溢，全球能源市场面临供应危机

【今日重点关注 - 必须在简报中详细分析】
1. **伊朗总统表态**：伊朗总统称伊方愿在诉求满足前提下结束战争，这是伊朗首次释放明确停火意愿
2. **特朗普最新声明**：特朗普表示即使霍尔木兹海峡仍关闭也愿结束战争，称将在两到三周内结束伊朗战事
3. **美军航母部署**：美军"布什"号航母正部署至中东地区，军事压力持续升级
4. 请在分析中重点讨论这些最新动态对冲突走向的影响

=================================================================
【第一部分：金融市场数据 - 必须准确核实】
=================================================================
请仔细核对以下数据，确保准确。如无法确认，请明确标注"约"或"据XX报道称"：

1. 原油市场（必须包含）：
   - 布伦特原油：当前价格（美元/桶）、日内涨跌（美元和百分比）、较上周涨跌
   - WTI原油：当前价格、日内涨跌、较上周涨跌
   - 数据来源：ICE、NYMEX等

2. 全球股市（必须包含）：
   - 美股：标普500指数点位及涨跌、道琼斯指数、纳斯达克指数
   - 欧洲：斯托克600指数、英国富时100、德国DAX
   - 亚洲：日经225、恒生指数、上证综指
   - 注：请标注是实时数据还是收盘数据

3. 债券市场（必须包含）：
   - 美国国债：10年期收益率、2年期收益率、收益率曲线变化
   - 德国国债10年期收益率
   - 避险资产走势（黄金、美债需求）

4. 外汇市场（必须包含）：
   - 美元指数（DXY）点位及变化
   - 欧元/美元、美元/日元、英镑/美元走势
   - 新兴市场货币（土耳其里拉等）表现

5. 波动率与风险指标：
   - VIX恐慌指数当前水平及变化
   - 原油波动率（OVX）

=================================================================
【第二部分：冲突最新进展 - 过去24小时内，必须1500字以上】
=================================================================
【时间范围】
- 只展现过去24小时内的最新进展（从当前时间往前推24小时）
- 过时的信息不要重复列举
- 在进展描述文字中标注具体发生时间（如"3月7日晚间"、"3月8日凌晨"、"3月8日上午"等）

【字数要求 - 强制】
- 总字数必须达到1500字以上
- 充分展开，详细描述，不能简单罗列

【信息源 - 必须全网搜索】
- ISW (Institute for the Study of War): https://understandingwar.org/research/middle-east/iran-update
  * ISW每日更新两次（Evening Special Report + 常规更新）
  * 提供最权威的战场态势、打击目标坐标、兵力部署细节、损毁评估
  * 必须查看最新Evening Special Report获取准确信息
- 半岛电视台 (Al Jazeera): 实时新闻、现场画面、各方反应
- 路透社 (Reuters): 官方声明、外交动态、军事动向
- CNN/BBC/Fox News: 美国官方表态、军事专家分析
- Twitter/X: 实时战场视频、当地目击者报告

【输出格式 - 完全灵活条目】
冲突进展条目数量：根据过去24小时内最重要、最新的进展动态决定，通常6-12条。

【内容组织原则】
1. 灵活优先：不强制从固定条目中选择，根据当前市场讨论最多的热点动态调整
2. 按重要性排序：军事打击 > 外交表态 > 设施损毁 > 海峡封锁 > 其他重要动态
3. 合并同类事件：同一主题的事件放在同一条目内，按时间顺序描述
4. 时间标注：在正文里标注具体时间（如"3月7日晚间"、"3月8日凌晨3点"等）
5. 注意：不需要包含全球市场反应（后面有专门的市场分析部分）

【参考条目类型（根据最新情况灵活选择，不限于以下）】
- 美以联军最新军事行动（打击目标、规模、效果）
- 伊朗反击行动（导弹/无人机袭击、目标、拦截情况）
- 关键设施损毁评估（能源设施、军事设施、产能损失）
- 各方官方表态（美、以、伊、海湾国家、国际组织的最新立场）
- 霍尔木兹海峡封锁情况（通航量、滞留船只、航运公司动态、保险费变化）
- 军事部署变化（美军航母位置、以色列空军出动、伊朗导弹阵地转移）
- 人员伤亡与平民影响（各方伤亡统计、难民流动、人道主义危机）
- 外交斡旋进展（谈判尝试、第三方调解、联合国动向）
- 代理人动态（真主党、胡塞武装、伊拉克民兵的活动）
- 伊朗内部动态（领导层变动、国内反应、抗议活动）
- 伊朗导弹能力评估（剩余库存、发射器数量、生产能力、消耗速度）
- 代理人网络动态（黎巴嫩真主党动员情况、也门胡塞红海行动、伊拉克民兵活动）
- 核设施相关动态（伊朗核设施安全状况、国际原子能机构表态）
- 能源市场直接影响（产能损失、替代路线、保险变化）
- 人道主义与难民危机（平民伤亡、跨境难民、援助困难）

【如果有关于战争结束、战争加剧等新闻，请优先分析信息的准确性、可行性和未来前景，若影响较大，请优先展示】

【小标题命名规则】
- 小标题不要包含固定日期
- 根据内容核心提炼标题，简洁明了，突出核心事件
- 示例："以色列打击德黑兰能源设施"、"伊朗导弹袭击海湾国家"、"霍尔木兹海峡通航量骤降"

【每个条目必须包含 - 确保字数达标】
- 小标题：概括核心事件（不含日期）
- 正文详细描述（必须包含）：
  * 具体发生时间（精确到小时更佳，如"3月7日22:00"）
  * 地点（城市、设施名称）
  * 数量和规模（战机数量、导弹数量、涉及人员）
  * 直接效果（损毁程度、人员伤亡、市场反应）
  * 背景分析或影响评估（至少1-2句话）
- 字数：每条200-300字，宁可详细不要简略

【示例条目格式】
标题：美以联军扩大打击伊朗能源设施
内容：3月7日晚间至8日凌晨，美以联军对伊朗德黑兰周边油库和炼油设施发动多轮打击（当地时间3月7日22:00-3月8日04:00）。目标包括Shahran油库、Tehran炼油厂等关键设施，出动F-35战机与巡航导弹。3月8日早间卫星图像显示多处起火，产能损失约15-20万桶/日。此举标志冲突从纯军事目标向经济基础设施升级，意在切断伊朗战争资金来源，加速其财政崩溃。
类型：military

=================================================================
【第三部分：关键时间线 - 筛选影响走向的关键事件】
=================================================================
要求：
1. 优先最近72小时的最新进展
2. 但必须是真正影响冲突走向的关键节点
3. 筛选标准：
   - 导致局势重大升级的事件
   - 对全球能源市场产生实质影响的事件
   - 改变各方战略态势的事件
   - 国际反应发生重大转变的节点
4. 数量：8-12个关键事件
5. 按时间倒序排列（最新的在前）
6. 格式：时间 + 核心事件 + 影响评估
7. 标注重要性（critical/normal）

=================================================================
【第四部分：深度分析 - 资深研究者视角】
=================================================================
请以华泰固收研究所首席地缘政治分析师的身份，展开系统性深度分析。

要求：深入论证，逻辑严密，结论有据可依，不回避不确定性。

【子模块1：地缘政治深度分析】
请涵盖以下维度：

1. 冲突根本逻辑：
   - 美伊70年恩怨演变（从1953年政变到伊核协议破裂）
   - 核问题核心矛盾（浓缩铀丰度、突破时间、国际制裁）
   - 代理人战争模式（黎巴嫩真主党、也门胡塞、伊拉克民兵网络）

2. 关键变量识别：
   - 伊朗导弹库存量估算（公开情报显示约3000-5000枚，包括短程/中程/远程分类）
   - 海峡封锁可持续性（经济成本、国际反应、军事压力三维度分析）
   - 第三方介入意愿（真主党全面动员可能性、胡塞武装红海策应能力）

3. 各方战略意图与底线：
   - 美国：防止伊朗拥核时间表、重塑中东亲美秩序、维护石油美元结算体系
   - 以色列：消除生存威胁（伊朗高层多次威胁"抹平以色列"）、扩大战略纵深、巩固地区军事霸权
   - 伊朗：政权生存优先、核计划是政权合法性来源、地区什叶派影响力网络

4. 误判风险评估：
   - 历史案例对比（2003伊拉克战争：美低估游击战、高估速胜；2011利比亚：干预后乱局）
   - 当前误判可能性（美以高估伊朗崩溃速度、伊朗高估国际干预意愿）
   - 最坏情景推演（海峡长期中断6个月以上、伊朗政权更迭引发内战、核设施遭袭后辐射泄漏）

5. 外交维度分析：
   - 中国：能源安全关切但避免直接卷入，主要发挥经济影响力
   - 欧盟：内部分裂（法国强硬、德国谨慎、希腊等国依赖伊朗石油）
   - 海湾国家：沙特/阿联酋左右为难（安全靠美国、经济靠石油出口、地理上受伊朗威胁）

【子模块2：后续进展预判 - 基于市场预期】
要求：仔细搜索投行、机构、分析师的最新观点，确保情景分析符合当前市场预期，不要与市场共识偏离。不需要标注具体概率数字。

【基准情景（市场主流预期）】
- 描述当前市场普遍预期的冲突发展路径
- 包括持续时间、升级/降级可能性、关键变量
- 参考投行研报、分析师共识、期货市场定价

【乐观情景（如有积极信号）】
- 仅在市场出现积极信号时描述（如外交突破、停火谈判、缓和表态）
- 包括促成因素和可能结果
- 注明市场对此的预期程度

【悲观情景（如有更严重担忧）】
- 仅在市场出现更严重担忧时描述（如地面战风险、全面战争、第三方介入）
- 包括触发因素和可能后果
- 注明市场对此的定价程度

【市场预期参考来源】
- 高盛、摩根士丹利、摩根大通、花旗、美银等投行最新研报
- 彭博、路透分析师调查
- 期货市场（原油、黄金、VIX）定价隐含预期
- 期权市场波动率 skew 反映的风险偏好

3. 触发局势变化的信号清单（80-100字）：
   【降级信号】海峡船舶恢复通行量>50%、伊朗官方发布求和声明、美以暂停打击48小时以上
   【升级信号】美军地面部队调动至科威特/卡塔尔、伊朗导弹袭击造成以色列平民大规模伤亡、伊朗宣布退出NPT（核不扩散条约）
   【转折信号】伊朗最高领袖健康传闻、伊朗国内爆发大规模反战游行、沙特与伊朗秘密接触被披露

【子模块3：全球经济影响分析 - 必须500-600字】

1. 能源市场结构性影响（150-180字）：
   - 霍尔木兹海峡战略价值量化：日运输量约2000万桶石油（占全球海运石油35%）、LNG约3000万吨/年
   - 替代路线成本：绕道好望角增加航程约6000海里、运费上涨30-40%、运输时间延长12-15天
   - 供需缺口测算：当前已中断约1500万桶/日，若持续1个月=全球减少4.5亿桶供应（相当于全球5天消费量）
   - 长期油价中枢：即使冲突结束，"霍尔木兹风险溢价"将永久性纳入油价，中枢从70美元上移至75-80美元

2. 全球通胀与货币政策冲击（120-150字）：
   - 传导机制：油价上涨→运输成本上升（占总成本10-15%）→制造业成本上升→消费品价格上涨
   - 时间滞后：运输成本1个月内传导、能源账单2-3个月传导、工资-物价螺旋6个月以上
   - 央行困境：美联储（通胀回升vs经济放缓）、欧央行（能源依赖度高）、日央行（输入性通胀加剧）
   - 滞胀对比：1973年石油危机（油价涨3倍）、1979年伊朗革命（油价涨2倍）、当前情景（若持续3个月，油价可能翻倍）

3. 供应链与贸易影响（100-120字）：
   - 航运成本：上海-鹿特丹航线运费已上涨50%，集装箱船绕行成本增加200万美元/航次
   - 亚洲制造业：中国（进口依赖度75%）、日本（99%）、韩国（100%），能源成本占制造业成本15-20%
   - 特定行业：航空燃油成本占航司运营成本30%（票价将上涨20-30%）、化工行业（乙烯/丙烯成本上升）、物流业（陆运成本跟涨）

4. 中国经济影响（120-150字）：
   - 进口成本：中国日均进口原油约1100万桶，油价每涨10美元=日增成本1.1亿美元、年增约400亿美元
   - 通胀压力：CPI能源权重约3%，油价涨50%将推高CPI约1.5个百分点，压缩货币政策空间
   - 人民币汇率：进口支付增加→外汇需求上升→人民币贬值压力，但避险需求可能部分抵消
   - 外汇储备：按1100万桶/日、每桶涨30美元计算，年额外支出约1200亿美元（占外储3.5%）
   - 一带一路风险：中伊25年合作协议执行受阻、中巴经济走廊安全威胁上升、中东基建项目保险成本飙升

【子模块4：投资策略建议】

1. 固定收益策略：
   - 久期调整：缩短至3-7年（避免长端利率上行风险），减少长久期美债敞口
   - 信用债：减配高收益债（HYG/JNK，违约风险上升）、增配投资级（LQD）；减持中东主权债（卡塔尔/沙特风险溢价上升）
   - 地域配置：美债40%（避险）、德债30%（欧央鸽派）、日债10%（避险）、新兴市场债20%（仅限投资级）
   - 操作目标：美10年期收益率4.0%以下逐步减仓、4.5%以上加仓；设定止损于收益率突破5.0%

2. 大宗商品策略：
   - 原油：Brent目标90-110美元区间，当前92美元附近可分批建仓（30%仓位），突破85美元加仓至50%，止损设于75美元
   - 黄金：目标3000-3200美元/盎司，与油价90天相关系数约0.6，同步上涨概率高，配置组合10-15%
   - 天然气：美国Henry Hub与欧洲TTF价差扩大套利（当前价差约5美元/MMBtu），亚洲LNG现货溢价交易
   - 操作方式：期货远月合约（避免展期成本）、买入看涨期权（风险有限）、能源股（XLE/OIH，杠杆效应）

3. 外汇策略：
   - EUR/USD：看空至1.05（欧洲能源依赖度高、经济受冲击大），止损1.08
   - USD/JPY：看多至155（避险需求+日央行鸽派），止损148
   - USD/CNY：看多至7.35（中国进口成本上升+资本外流压力），但央行干预风险存在
   - 新兴市场：减持TRY（土耳其高通胀+能源进口）、ZAR（南非原油进口）、BRL（依赖石油出口但风险情绪恶化）
   - 避险货币：CHF（传统避险）、JPY（套息交易平仓需求）配置各5%

4. 综合配置建议：
   - 风险资产:避险资产 = 40%:60%（平时通常为60:40）
   - 动态调整触发：若VIX突破40且持续3天，风险资产降至30%；若油价回落至80美元以下且海峡恢复，可增配风险资产至50%
   - 现金比例：维持20%（平时10%），等待局势明朗后加仓
   - 对冲工具：买入VIX看涨期权（行权价35）、买入原油看跌期权（行权价80，保护多头头寸）

关于情景分析：
- 如果难以准确预测，可以不写
- 如果要写，必须与当前市场主流预期保持一致
- 明确标注概率和触发条件

=================================================================
【第五部分：投行研报观点 - 尽可能多搜索】
=================================================================
请搜索并汇总近3-5日内主要海外投行的研报观点。

必须覆盖的投行（至少5家）：
- 高盛（Goldman Sachs）
- 摩根士丹利（Morgan Stanley）
- 摩根大通（J.P. Morgan）
- 花旗（Citi）
- 美银证券（BofA Securities）
- 瑞银（UBS）、巴克莱（Barclays）等（如有）

每家投行的观点请包含：
1. 研报发布日期（确认是近几日的）
2. 对油价的最新目标价预测
3. 对冲突持续时间的判断
4. 对全球经济/市场影响的评估
5. 推荐的交易策略
6. 特别观点/风险提示

如果某家投行近日无相关研报，请标注"近几日未见更新"。

=================================================================
【第六部分：最新新闻】
=================================================================
列出5-8条今日重要新闻，包含标题、来源、链接、摘要。

=================================================================
【强制输出格式要求 - 必须遵守】
=================================================================

请直接输出以下JSON（纯文本，无markdown标记）：

{{
  "summary": "200字以内核心摘要",
  "conflict_progress": [{{"title": "", "content": "", "type": ""}}],
  "positions": {{"us": "", "israel": "", "iran": "", "others": ""}},
  "timeline": [{{"time": "", "event": "", "type": ""}}],
  "market_data": {{"oil": "", "equity": "", "bond": "", "fx": "", "volatility": ""}},
  "bank_views": "投行观点汇总（详细）",
  "analysis": {{
    "geopolitical": "地缘政治深度分析（约500字）",
    "outlook": "后续进展预判（约500字）",
    "impact": "全球经济影响（约500字）",
    "strategy": "投资策略（约500字）"
  }},
  "watch_points": ["要点1", "要点2"],
  "news": [{{"title": "", "source": "", "url": "", "summary": ""}}]
}}

总字数要求：
- 全文约4000-5000字
- 其中深度分析部分至少2000字
- 投行观点部分至少500字

质量要求：
1. 金融数据准确，不确定的标注来源
2. 冲突进展全面，不遗漏重要信息
3. 分析有深度，体现专业视角
4. 逻辑清晰，论证有力
5. 建议具体可操作"""

    content = call_api(config, system_prompt, user_prompt)
    if not content:
        return None

    data = extract_json_from_text(content)
    if data:
        data["date"] = info["date"]
        data["conflict_day"] = info["conflict_day"]
        data["blockade_day"] = info["blockade_day"]
        return data

    return None

def generate_content_html(data, info):
    """生成内容HTML（仅内容部分，不包含head和body标签）"""
    
    # 冲突进展
    progress_html = ""
    for item in data.get("conflict_progress", []):
        type_class = item.get("type", "normal")
        progress_html += f'<div class="highlight-box {type_class}"><h5>{item.get("title", "")}</h5><p>{item.get("content", "")}</p></div>'
    
    # 各方表态
    positions = data.get("positions", {})
    positions_html = "<h4>各方最新表态</h4><ul>"
    if "us" in positions: positions_html += f'<li><strong>🇺🇸 美国：</strong>{positions["us"]}</li>'
    if "israel" in positions: positions_html += f'<li><strong>🇮🇱 以色列：</strong>{positions["israel"]}</li>'
    if "iran" in positions: positions_html += f'<li><strong>🇮🇷 伊朗：</strong>{positions["iran"]}</li>'
    if "others" in positions: positions_html += f'<li><strong>🌍 国际社会：</strong>{positions["others"]}</li>'
    positions_html += "</ul>"
    
    # 时间线
    timeline_items = data.get("timeline", [])
    mid = len(timeline_items) // 2 + len(timeline_items) % 2
    left_col = timeline_items[:mid]
    right_col = timeline_items[mid:]
    
    def make_timeline_html(items):
        html = ""
        for item in items:
            type_class = item.get("type", "normal")
            html += f'<div class="timeline-item {type_class}"><div class="timeline-time">{item.get("time", "")}</div><div class="timeline-content">{item.get("event", "")}</div></div>'
        return html
    
    timeline_html = f'<div class="timeline-two-col"><div class="timeline-col">{make_timeline_html(left_col)}</div><div class="timeline-col">{make_timeline_html(right_col)}</div></div>'
    
    # 市场数据
    market_data = data.get("market_data", {})
    market_html = '<div class="market-grid">'
    if "oil" in market_data:
        market_html += f'<div class="market-card"><h5>🛢️ 原油</h5><p>{market_data["oil"]}</p></div>'
    if "equity" in market_data:
        market_html += f'<div class="market-card"><h5>📈 股市</h5><p>{market_data["equity"]}</p></div>'
    if "bond" in market_data:
        market_html += f'<div class="market-card"><h5>📉 债市</h5><p>{market_data["bond"]}</p></div>'
    if "fx" in market_data:
        market_html += f'<div class="market-card"><h5>💱 外汇</h5><p>{market_data["fx"]}</p></div>'
    if "volatility" in market_data:
        market_html += f'<div class="market-card"><h5>⚡ 波动率</h5><p>{market_data["volatility"]}</p></div>'
    market_html += "</div>"
    
    # 投行观点
    bank_views = data.get("bank_views", "")
    bank_html = f'<div class="highlight-box"><h5>🏦 投行观点汇总</h5><p>{bank_views}</p></div>' if bank_views else ""
    
    # 深度分析
    analysis = data.get("analysis", {})
    analysis_html = ""
    if "geopolitical" in analysis:
        analysis_html += f'<h4>🌍 地缘政治深度分析</h4><p>{analysis["geopolitical"]}</p>'
    if "outlook" in analysis:
        analysis_html += f'<h4>🔮 后续进展预判</h4><p>{analysis["outlook"]}</p>'
    if "impact" in analysis:
        analysis_html += f'<h4>💥 全球经济影响</h4><p>{analysis["impact"]}</p>'
    if "strategy" in analysis:
        analysis_html += f'<div class="highlight-box"><h5>💡 投资策略建议</h5><p>{analysis["strategy"]}</p></div>'
    
    # 关注要点
    watch_points = data.get("watch_points", [])
    watch_html = "<h4>📌 关键关注要点</h4><ul>"
    for point in watch_points:
        watch_html += f'<li>{point}</li>'
    watch_html += "</ul>"
    
    # 新闻
    news_html = ""
    for item in data.get("news", []):
        news_html += f'<a href="{item.get("url", "#")}" target="_blank" class="news-item"><div class="news-title">{item.get("title", "")}</div><div class="news-source">{item.get("source", "")} · {info["date"]}</div><div class="news-summary">{item.get("summary", "")}</div></a>'
    
    # 构建完整内容HTML
    html = f'''<div class="container">
        <div class="briefing-header">
            <h2>📰 美以伊冲突每日简报 ({info['date']})</h2>
            <p class="summary">{data.get("summary", "")}</p>
        </div>

        <div class="section">
            <h3>📍 冲突最新进展</h3>
            {progress_html}
            {positions_html}
        </div>

        <div class="section">
            <h3>⏱️ 关键时间线</h3>
            {timeline_html}
        </div>

        <div class="section">
            <h3>🔍 深度分析</h3>
            {analysis_html}
            {watch_html}
        </div>

        <div class="section">
            <h3>📊 市场影响分析</h3>
            {market_html}
            {bank_html}
        </div>

        <div class="section">
            <h3>📰 最新新闻</h3>
            <div class="news-list">{news_html}</div>
        </div>

        <div class="footer">数据来源：路透社、彭博社、半岛电视台、财联社、新华社等 | 仅供参考，不构成投资建议</div>
    </div>'''
    
    return html

def update_html_content(file_path, content_html, info):
    """更新HTML文件中的内容（保留原有布局和样式）"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_html = f.read()
    except FileNotFoundError:
        print(f"[错误] 文件不存在: {file_path}")
        return False
    
    # 更新header-right中的日期
    updated_html = re.sub(
        r'<div class="header-right">.*?</div>',
        f'<div class="header-right">更新时间: {info["date"]}</div>',
        original_html
    )
    
    # 替换container部分（从<div class="container">到</body>之前）
    pattern = r'<div class="container">.*?</div>\s*<div class="footer">.*?</div>\s*</div>'
    
    if re.search(pattern, updated_html, re.DOTALL):
        # 如果找到旧的container结构，替换它
        updated_html = re.sub(pattern, content_html.strip(), updated_html, flags=re.DOTALL)
    else:
        # 尝试另一种模式：从<div class="container">到</body>
        pattern2 = r'<div class="container">.*?</body>'
        if re.search(pattern2, updated_html, re.DOTALL):
            updated_html = re.sub(pattern2, content_html.strip() + '\n</body>', updated_html, flags=re.DOTALL)
        else:
            print("[警告] 无法找到内容区域，尝试备用方案")
            # 备用：直接在</body>前插入
            updated_html = updated_html.replace('</body>', content_html.strip() + '\n</body>')
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("美以伊冲突每日简报 - AI API 更新工具")
    print("特点：仅更新内容，保留页面布局")
    print("=" * 60)
    print()
    
    config = get_api_config()
    info = get_today_info()
    
    print(f"[日期] {info['date']}")
    print(f"[冲突] 第{info['conflict_day']}天")
    print(f"[封锁] 第{info['blockade_day']}天")
    print()
    
    # 生成简报内容
    data = generate_briefing_with_ai(config, info)
    
    if not data:
        print("\n[失败] 无法生成简报")
        return 1
    
    print("\n[成功] 简报内容生成完成")
    
    # 生成内容HTML
    print("\n[任务2/2] 正在更新网页文件...")
    content_html = generate_content_html(data, info)
    
    # 更新HTML文件
    if update_html_content(config["briefing_file"], content_html, info):
        print(f"[成功] 已更新: {config['briefing_file']}")
    else:
        print(f"[失败] 无法更新: {config['briefing_file']}")
        return 1
    
    print("\n" + "=" * 60)
    print("简报更新完成!")
    print(f"文件位置: {config['briefing_file']}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
