# 中东地缘跟踪器全量更新提示词

## 执行前准备
1. 确保所有Python依赖已安装
2. 确保`全球市场.xlsx`文件已更新到最新数据
3. 确保GitHub仓库已配置

---

## 1. 海峡跟踪网页 (index.html) 更新

### 上方数据更新
```bash
python update_strait_data.py
python generate_timelapse_video.py
```

### 下方供应链跟踪
**参考文件**: `scripts/SUPPLY_CHAIN_PROMPT.md`
- 读取该文件中的更新逻辑和提示词
- 更新index.html中的供应链跟踪部分

---

## 2. 全球市场 & 经济数据网页更新

```bash
python update_data_from_excel.py
```

**更新内容**:
- `data-tracking.html` - 全球市场数据（商品价格、流动性、股市、债市、总览）
- `eco-track.html` - 各国经济数据（美国、欧元区、日本、英国等8国）

**数据源**: `全球市场.xlsx`

---

## 3. 战局形势网页 (war-situation.html) 更新

### 步骤1：获取最新报告
1. 访问 https://understandingwar.org/
2. 搜索最新的 Iran Update Special Report（伊朗特别更新报告）
3. 提取报告全文和所有图片链接

### 步骤2：翻译处理（手动翻译，不使用脚本）
**必须完整翻译的内容**:
- ✅ Key Takeaways（关键要点）- 全部保留翻译
- ✅ 所有图表/地图 - 全部保留
- ✅ 图表对应的正文内容 - 翻译使用

### 步骤3：更新网页
- 保留war-situation.html原有结构
- 替换为最新翻译内容
- 确保图片链接正确（使用原始URL或下载到本地）

---

## 4. 每日简报网页 (briefing.html) 更新

**参考文件**: `BRIEFING_UPDATE_PROMPT.md`
- 按照该文件中的更新流程执行
- 生成新的简报内容
- 更新briefing.html和briefing_data.json

---

## 5. 实时新闻网页 (news.html) 更新

```bash
python scrape_cls_final.py
```

**更新内容**:
- 抓取财联社最新新闻
- 更新news.html的新闻列表

---

## 6. 央行表态网页 (central-bank-tracker.html) 更新

**参考文件**: `scripts/AI_PROCESS_PROMPT.md`
- 读取该文件中的AI处理流程
- 更新央行表态数据
- 更新central-bank-tracker.html

---

## 7. 研究视点网页 (research.html) 更新

**参考文件**: `research.md`
- 读取research.md中的研究内容
- 更新research.html

---

## 8. Polymarket网页 (polymarket.html) 更新

```bash
python update_polymarket_html.py
```

**更新内容**:
- 抓取Polymarket中东相关预测市场数据
- 保存到 `data/polymarket_data.json`
- polymarket.html 会自动从JSON加载数据，无需重新生成HTML

---

## 9. 海湾原油图谱网页 (oil-chart.html) 更新

### 更新要求：
1. **使用全网搜索功能**搜索以下国家能源设施相关新闻：
   - 沙特阿拉伯
   - 伊朗
   - 伊拉克
   - 阿联酋
   - 科威特
   - 卡塔尔
   - 阿曼
   - 巴林

2. **时间范围**: 近72小时内的最新信息

3. **更新规则**:
   - ✅ 添加新增的新闻
   - ✅ 保留旧的新闻（不要删除）
   - ❌ 内容大体相同的重复新闻不重复添加
   - 📅 按时间从新到早排序

### 更新位置：
oil-chart.html中"各国最新动态"部分

---

## 10. 推送到GitHub

```bash
# 添加所有更改
git add .

# 提交更新
git commit -m "update: 全量数据更新 [日期]"

# 推送到远程
git push origin main
```

---

## 更新检查清单

- [ ] index.html - 海峡跟踪数据已更新
- [ ] index.html - 供应链跟踪已更新
- [ ] data-tracking.html - 全球市场数据已更新
- [ ] eco-track.html - 经济数据已更新
- [ ] war-situation.html - ISW战局报告已翻译更新
- [ ] briefing.html - 每日简报已更新
- [ ] news.html - 实时新闻已更新
- [ ] central-bank-tracker.html - 央行表态已更新
- [ ] research.html - 研究视点已更新
- [ ] polymarket.html - 预测市场数据已更新
- [ ] oil-chart.html - 海湾原油动态已更新
- [ ] GitHub推送已完成

---

## 执行顺序建议

```
步骤1: 数据收集
  ├── 执行 update_data_from_excel.py
  ├── 执行 scrape_cls_final.py
  ├── 执行 update_strait_data.py
  └── 搜索oil-chart需要的各国新闻

步骤2: AI处理
  ├── 处理briefing更新
  ├── 处理央行表态更新
  ├── 处理war-situation翻译
  └── 处理research更新

步骤3: 生成视频
  └── 执行 generate_timelapse_video.py

步骤4: 验证检查
  └── 检查所有网页显示正常

步骤5: 提交推送
  └── git commit & push
```

---

## 注意事项

1. **war-situation.html**: 必须手动翻译，确保中文流畅准确
2. **oil-chart.html**: 只添加新新闻，不删除旧新闻
3. **Excel文件**: 确保`全球市场.xlsx`已更新到最新数据后再运行脚本
4. **图片链接**: war-situation中的图片如无法显示，需下载到本地或替换为可用链接
5. **Git提交**: 提交信息建议包含更新日期和主要内容
