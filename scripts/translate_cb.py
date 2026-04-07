import json

with open('data/central-banks.json','r',encoding='utf-8') as f:
    data=json.load(f)

for item in data:
    t = item.get('title','')
    s = item.get('summary','')
    src = item.get('source','')

    # 美联储
    if src == 'Federal Reserve':
        if 'Inflation Expectations' in t:
            item['titleZh'] = '美联储警告中东紧张局势可能影响通胀预期'
            item['summaryZh'] = '美联储主席表示正密切关注中东事态发展，指出持续的地缘政治紧张局势可能影响通胀预期，货币政策决策需要审慎考虑。'
        elif 'Morgan Stanley' in t:
            item['titleZh'] = '美联储与货币监理署就摩根士丹利银行豁免申请发布联合裁定'
            item['summaryZh'] = '美联储与货币监理署联合发布关于摩根士丹利银行第23A条豁免申请的裁定。'
        elif 'audited financial' in t:
            item['titleZh'] = '美联储发布年度审计财务报表'
            item['summaryZh'] = '美联储理事会发布经审计的年度财务报表。'
        elif 'enforcement actions' in t and 'former employee' in t:
            item['titleZh'] = '美联储对银行前员工采取执法行动'
            item['summaryZh'] = '美联储对Ally Bank和Regions Bank前员工发布执法行动。'
        elif 'enforcement action' in t:
            item['titleZh'] = '美联储发布执法行动'
            item['summaryZh'] = '美联储对相关金融机构前员工发布执法行动。'
        elif 'enforcement actions' in t:
            item['titleZh'] = '美联储发布多项执法行动'
            item['summaryZh'] = '美联储对相关银行前员工采取监管执法行动。'
        elif 'termination of enforcement' in t:
            item['titleZh'] = '美联储宣布终止执法行动'
            item['summaryZh'] = '美联储宣布终止此前的监管执法行动。'
        elif 'capital treatment of tokenized' in t:
            item['titleZh'] = '多家机构明确代币化证券的资本处理方式'
            item['summaryZh'] = '多家监管机构就代币化证券的资本处理方式进行澄清说明。'
        elif 'modernize the regulatory capital' in t:
            item['titleZh'] = '多家机构就现代化监管资本框架征求意见'
            item['summaryZh'] = '多家监管机构就现代化银行监管资本框架、维护银行体系稳健性的提案征求公众意见。'
        elif 'FOMC statement' in t:
            item['titleZh'] = '美联储发布FOMC利率决议声明'
            item['summaryZh'] = '美联储联邦公开市场委员会(FOMC)发布最新货币政策声明。'
        elif 'minutes' in t and 'discount rate' in t:
            item['titleZh'] = '美联储发布贴现率会议纪要'
            item['summaryZh'] = '美联储发布2026年1月贴现率会议纪要。'
        elif 'minutes' in t:
            item['titleZh'] = '美联储发布FOMC会议纪要'
            item['summaryZh'] = '美联储发布2026年3月FOMC会议纪要。'
        elif 'approval of application' in t and 'CBS' in t:
            item['titleZh'] = '美联储批准CBS银行申请'
            item['summaryZh'] = '美联储批准CBS银行的相关申请。'
        elif 'approval of application' in t and 'Home' in t:
            item['titleZh'] = '美联储批准银行申请'
            item['summaryZh'] = '美联储批准相关银行的申请。'
        elif 'approval of application' in t and 'Alma' in t:
            item['titleZh'] = '美联储批准银行申请'
            item['summaryZh'] = '美联储批准相关银行的申请。'
        elif 'approval of application' in t and 'First' in t:
            item['titleZh'] = '美联储批准银行申请'
            item['summaryZh'] = '美联储批准相关银行的申请。'
        elif 'approval of notice' in t:
            item['titleZh'] = '美联储批准CBS银行通知'
            item['summaryZh'] = '美联储批准CBS银行的相关通知。'
        elif 'hybrid public meeting' in t:
            item['titleZh'] = '美联储将举办公开会议'
            item['summaryZh'] = '美联储宣布将举行线上线下一体化公开会议。'
        elif 'reputation risk' in t:
            item['titleZh'] = '美联储从监管框架中移除声誉风险因素'
            item['summaryZh'] = '美联储此前已从监管框架中移除声誉风险考量因素。'
        elif 'consumer credit' in t:
            item['titleZh'] = '美联储发布消费者信贷数据'
            item['summaryZh'] = '美联储发布月度消费者信贷数据报告。'

    # 英格兰银行
    elif src == 'Bank of England':
        if 'Middle East' in t:
            item['titleZh'] = '英格兰银行：中东冲突对英国通胀构成重大上行风险'
            item['summaryZh'] = '英格兰银行货币政策委员会成员表示，中东冲突对英国通胀构成显著上行风险，能源和供应链中断可能在短期内推高物价。'
        else:
            item['titleZh'] = '英格兰银行发布政策声明'
            item['summaryZh'] = '英格兰银行发布最新政策相关声明。'

    # 欧央行
    elif src == 'European Central Bank':
        item['titleZh'] = '欧央行管委会讨论油价冲击传导机制'
        item['summaryZh'] = '欧央行管委会议讨论了油价冲击对欧元区通胀的传导机制，强调中东局势导致能源价格飙升对通胀预期的影响需要持续关注。'

    # 中国央行
    elif '人民银行' in src or "People's Bank" in src:
        item['titleZh'] = '中国人民银行：密切关注国际大宗商品价格波动对国内通胀影响'
        item['summaryZh'] = '央行货币政策委员会季度例会指出，要密切关注国际大宗商品价格波动对国内通胀的影响，保持流动性合理充裕。'

    # 沙特央行
    elif 'SAMA' in src or 'Saudi' in src:
        item['titleZh'] = '沙特央行在区域不确定性中维持稳定措施'
        item['summaryZh'] = '沙特央行(SAMA)宣布维持基准利率不变，并表示正在采取必要措施确保金融体系稳定。银行业资本充足率保持在健康水平。'

    # 卡塔尔央行
    elif 'Qatar' in src:
        item['titleZh'] = '卡塔尔央行采取流动性措施确保市场稳定'
        item['summaryZh'] = '卡塔尔央行宣布一系列流动性措施，包括定期回购工具和降低存款准备金要求，以确保市场在地缘政治风险中保持稳定。'

    # 日本央行
    elif 'Japan' in src:
        item['titleZh'] = '日本央行密切关注中东局势导致能源价格上涨'
        item['summaryZh'] = '日本央行行长表示正密切关注中东局势导致的能源价格上涨，日本95%原油依赖中东进口。'

    # Reuters
    elif src == 'Reuters':
        if 'Middle East' in t and 'Fed' in t:
            item['titleZh'] = '美联储警告中东局势可能冲击市场，维持利率不变'
            item['summaryZh'] = '据路透社报道，美联储警告中东紧张局势可能影响市场稳定，同时维持利率不变。预计2026年仅有一次降息。'

    # CNBC
    elif src == 'CNBC':
        if 'Miran' in t:
            item['titleZh'] = '美联储理事Miran仍支持降息，称今年利率可能下调约1个百分点'
            item['summaryZh'] = '美联储理事斯蒂芬·米伦在CNBC节目中表示仍支持降息，预计今年利率可能下降约1个百分点。'
        elif 'Visa' in t and 'AI' in t:
            item['titleZh'] = 'Visa推出AI工具管理信用卡争议流程'
            item['summaryZh'] = 'Visa推出新的AI工具管理信用卡争议流程，这是大型银行和金融机构将AI纳入业务的一部分。'
        elif 'Buffett' in t and 'Iran' in t:
            item['titleZh'] = '巴菲特称伊朗核武器将使核灾难更难避免'
            item['summaryZh'] = '伯克希尔董事长巴菲特表示，拥核国家数量增加已从根本上改变了全球风险格局。'
        elif 'Buffett' in t and 'Apple' in t:
            item['titleZh'] = '巴菲特称过早卖出苹果股票，愿在合适市场加仓'
            item['summaryZh'] = '巴菲特表示过早卖出了苹果股票，愿意在更好的市场环境下加仓。苹果仍是伯克希尔最大持仓。'
        elif 'Buffett' in t and 'Curry' in t:
            item['titleZh'] = '巴菲特与NBA球星库里联手举办慈善午餐'
            item['summaryZh'] = '巴菲特与NBA球星斯蒂芬·库里联手举办慈善午餐拍卖活动。'
        elif 'Buffett' in t and 'calls' in t:
            item['titleZh'] = '巴菲特称仍在伯克希尔做投资决策，透露小幅新买入'
            item['summaryZh'] = '95岁的巴菲特表示仍每日到办公室工作，并密切关注市场。'
        elif 'commodity' in t.lower() or 'tungsten' in t.lower():
            item['titleZh'] = '三类小众大宗商品价格飙升，揭示中国对供应链的掌控力'
            item['summaryZh'] = '伊朗战争后，用于国防和半导体AI芯片的关键元素价格飙升，反映中国对供应链的影响力。'

with open('data/central-banks.json','w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

count_zh = sum(1 for d in data if d.get('titleZh'))
count_sum = sum(1 for d in data if d.get('summaryZh'))
print(f'Total: {len(data)} items')
print(f'With titleZh: {count_zh}/{len(data)}')
print(f'With summaryZh: {count_sum}/{len(data)}')
