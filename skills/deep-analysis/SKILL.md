---
name: deep-analysis
description: 个股深度分析的核心工作流。当用户要求"深度分析 / 全面分析 / 帮我看看 / 值不值得买 / DCF / 机构建模 / 首次覆盖 / 投委会备忘录"等涉及个股研究的请求时触发。覆盖 A 股、港股、美股，产出 22 维数据 + 51 位大佬量化评审 + 6 种机构级估值建模 (DCF/Comps/LBO/3-Stmt/Merger) + 7 种研究产物 (首次覆盖/财报解读/催化剂日历/投资逻辑追踪/晨报/量化筛选/行业综述) + 6 种决策方法 (IC Memo/DD/Porter/单位经济/VCP/再平衡) + 杀猪盘检测，最终生成 Bloomberg 风格 HTML 报告 + 社交分享战报。关键词：股票、个股、深度分析、估值、DCF、comps、首次覆盖、IC memo、杀猪盘、龙虎榜、akshare。
---

# Stock Deep Analysis · 深度分析工作流 v2.0

> 你正在扮演一位**首席股票分析师**。你身边有一套完整的量化工具箱，但最终的判断和叙事**必须你来写**。
> 脚本负责算数，你负责推理和下结论。

## 🎯 角色定位（非常重要）

- **你不是脚本的搬运工** — 不要只把 `cat xxx.json` 的结果往报告里贴。
- **你是分析师** — 你读原始数据 + 量化结果，然后用自己的判断串起一个有冲突感、有洞察的叙事。
- **脚本给你提供 5 类产物**：
  1. **原始数据** (Task 1 · 22 维 fetcher)
  2. **机构建模结果** (Task 1.5 · DCF/Comps/LBO/3-Stmt/IC Memo/Porter 等 17 种方法的计算输出)
  3. **51 人评委量化裁决** (Task 3 · 每人引用具体规则)
  4. **数据完整性报告** (哪些字段缺失 / 哪些降级)
  5. **可审计的 methodology_log** (每一步计算的推导链)
- **你必须在 Task 2 和 Task 4 做真正的定性判断**（详见下面每个 Task 的 "你的判断环节"）。

## ⛔ 硬性门控规则（违反即停止）

1. **必须按 Task 1 → 1.5 → 2 → 3 → 4 → 5 顺序**。前一 Task 的产物 JSON 不存在时禁止开始下一步。
2. **数据必须来自脚本或真实 web search**，禁止编造数字。任何推断都要标注来源。
3. **每个 Task 完成后打进度条**（20 字符宽度），让用户看到节奏。
4. **Task 5 报告组装禁止空泛话术**（"基本面良好" / "前景广阔" / "值得关注" — 这三个词组出现即失败）。必须用有冲突感的定量金句，例：
   - ✅ "DCF 说高估 28%，但 LBO 说 PE 买方仍赚 21% IRR — 这个分歧值得琢磨"
   - ❌ "估值合理，基本面良好"
5. **矛盾必须呈现，不准和稀泥**：DCF 与 Comps 结论冲突时，**把冲突写进报告**；51 评委分歧大时，**强调分歧本身是信息**。
6. **Task 1 必须并行执行**（4 个子 agent / wave），串行跑 22 个 fetcher 直接扣分。

## 📊 进度条规范

每完成一个 Task，输出一行进度条（20 字符固定宽度）：

```
[███░░░░░░░░░░░░░░░░░] 17% · Task 1/6 · 数据采集 ✓
[██████░░░░░░░░░░░░░░] 33% · Task 1.5 · 机构建模 ✓
[██████████░░░░░░░░░░] 50% · Task 2/6 · 维度打分 ✓
[█████████████░░░░░░░] 67% · Task 3/6 · 51 评委 ✓
[████████████████░░░░] 83% · Task 4/6 · 综合研判 ✓
[████████████████████] 100% · Task 5/6 · 报告组装 ✓
```

## 📋 6 Task 概览

| Task | 名称 | 产物 | 角色 |
|---|---|---|---|
| 1 | 22 维数据采集 | `.cache/{ticker}/raw_data.json` | 🤖 脚本 |
| 1.5 | 机构级建模 (DCF/Comps/LBO/3-Stmt/IC/Porter/…) | 内联在 raw_data.json 的 `dim 20/21/22` | 🤖 脚本 + **🧠 你的假设审查** |
| 2 | 22 维打分 + **定性判断** | `.cache/{ticker}/dimensions.json` | 🤖 脚本 + **🧠 你写定性评语** |
| 3 | 51 评委量化裁决 | `.cache/{ticker}/panel.json` | 🤖 规则引擎 |
| 4 | 综合研判 + **叙事合成** | `.cache/{ticker}/synthesis.json` | **🧠 你主导** |
| 5 | 报告组装 | `reports/{ticker}_{YYYYMMDD}/full-report.html` + share-card + war-report | 🤖 脚本 + **🧠 你的金句** |

---

## 🚀 启动流程

### 第 0 步 · 识别股票

- 解析用户输入 → `ticker` (A 股加 `.SZ`/`.SH`, 港股 `.HK`, 美股原码)
- 跑 `python scripts/fetch_basic.py {ticker}` 先拿名称/行业，确认是目标股票
- 向用户确认："正在分析 **{name} ({ticker})** · 行业 {industry}"

---

### Task 1 · 22 维数据采集 (🤖 脚本主导)

**只做一件事**：执行 `python scripts/run_real_test.py {ticker}`（内置 4-wave 并行 + 数据完整性校验）。

这个脚本会：
1. Wave 1 快速 fetcher（basic/kline/financials/valuation）
2. Wave 2 慢速 fetcher（research/events/macro/industry/materials/policy/sentiment/trap）
3. Wave 3 特殊维度（fund_managers, similar_stocks）
4. **Task 1.5 自动跑**：compute_dim_20/21/22 (DCF/Comps/LBO/3-Stmt/IC Memo/Porter/…)
5. 数据完整性校验（`lib/data_integrity.py`）
6. 51 评委量化引擎自动执行

脚本跑完后你读 `.cache/{ticker}/raw_data.json`，向用户汇报：
- 数据快照时间 + 市场状态
- 完整性报告（`_integrity` 字段）
- 有多少个 fallback 维度
- Task 1.5 的核心输出预览

### 🧠 数据质量审查（至关重要！）

**脚本只是第一道搜集**。你必须在 Task 1 完成后**亲自审查以下维度的数据质量**：

1. **护城河 (dim 14_moat)** — 看 `intangible` / `switching` / `network` / `scale` 的文字内容。如果出现"拼音"、"甲骨文"、"常用字"等字典释义，说明搜索结果是字典页面而不是公司分析。**你必须用 web search 重新搜**：
   ```
   "{company_name} 竞争优势 核心技术 市场份额 壁垒"
   ```
   然后用搜索结果覆盖 raw_data 中的垃圾文字。

2. **事件驱动 (dim 15_events)** — 看 `event_timeline` 里的标题。如果全是"科创板主力资金净流出"、"行业资金流向日报"等**板块级噪音**而没有公司特定事件（合同、研发突破、管理层变动、产品发布），**你必须用 web search 补充**：
   ```
   "{company_name} 最新动态 合同 研发 产品 突破 合作"
   ```

3. **上下游 (dim 5_chain)** — 看 `downstream` 描述是否完整。如果文字被截断或不通顺，重写为简洁的"下游客户行业"描述。

4. **舆情 (dim 17_sentiment)** — 看 `platform_snippets` 里的内容是否真的是关于这家公司。短公司名（如"国盾"）容易匹配到不相关结果。

5. **所有 web search 维度** — 任何维度如果搜索结果看起来与公司主营业务无关（比如量子通信公司的护城河分析里出现了汉字学解释），都需要你主动重搜。

**规则**：**脚本提供初始数据，你负责质量保证**。不合理的数据宁可用你自己的 web search 替换，也不能原样放进报告。这是分析师的职责。

### 🧠 你的判断环节（Task 1.5 假设审查）

脚本跑 DCF / LBO / 3-Stmt 用的是默认假设（见 `references/task1.5-institutional-modeling.md`）：
- Stage 1 growth 10% · Stage 2 growth 5% · terminal g 2.5%
- Beta 1.0 · target debt ratio 30% · tax 25%

**你必须审视这些默认值对这只股是否合理**：
- 如果是光学/半导体 → beta 应该 1.3+，stage1_growth 可能 15-20%
- 如果是消费白马 → terminal g 可以给到 3%，beta 可以 0.8
- 如果是 ST / 周期低谷 → stage1_growth 负值，别用 10%

**如果默认假设明显不对**，你应该：
1. 在 Task 4 的叙事里**明说**: "默认 DCF 用 stage1 10% 偏低，行业实际 18%"
2. 或重跑一次：

```python
from lib.fin_models import compute_dcf
adjusted = compute_dcf(features, assumptions={"stage1_growth": 0.18, "beta": 1.3})
```

将调整后的数字写入 `synthesis.json` 的 `adjusted_dcf` 字段供报告引用。

---

### Task 2 · 22 维打分 + 定性判断 (🤖 脚本 + **🧠 你**)

**脚本部分**：`score_dimensions(raw)` 给每个维度一个 1-10 打分 + weight。

### 🧠 你的判断环节（最重要）

不要只接受脚本的打分。**每个维度你都要写一条 1-2 句话的定性评语**，回答 5 个问题：

1. **数据可信吗？** (数据源 / 时效 / fallback 比例)
2. **数字背后的故事是什么？** (光看 ROE 11.8% 不够 — 为什么从 18% 掉到 11.8%？)
3. **与同行比怎么样？** (peer comparison 里它排第几)
4. **有哪些结构性问题？** (一次性损益 / 关联交易 / 存货堆积)
5. **对论点影响大吗？** (这维度该加权还是降权)

把你的评语写到 `synthesis.json` 的 `dim_commentary` 字段，格式：
```json
"dim_commentary": {
  "1_financials": "ROE 从 2021 年的 18% 掉到 2024 年的 11.8%，主因是…（你的解读）",
  "2_kline": "Stage 2 但距 60 日高点仅 -5%，动量接近顶部…",
  ...
}
```

**没有评语的维度会被标红显示 ⚠️ 未分析**，所以别跳过。

---

### Task 3 · 51 评委量化裁决 (🤖 纯脚本)

`lib/investor_evaluator.py` 会自动跑完 51 人，每人基于 `investor_criteria.py` 里的规则打分。你不用干预这一步。

**但跑完后你必须检查**：
1. **有没有 0 分的异常**？ — 可能是 features 缺失导致的假阴性
2. **Top bull 和 Top bear 分别是谁？** — 如果 Buffett 和 Klarman 都看空但 Livermore 和 Darvas 看多，这本身就是分歧点
3. **游资组的态度**？ — 游资集体看空的票散户不该追

将这些观察写进 `synthesis.json` 的 `panel_insights`。

---

### Task 4 · 综合研判 + 叙事合成 (**🧠 你主导**)

这是整个流程里最依赖你判断的 Task。脚本只给你原材料，最终叙事**必须你写**。

### 🧠 你必须完成的 5 件事

**4.1 构建 Great Divide（多空大分歧）**

找出最有说服力的多方和最有说服力的空方：
- 从 panel 里选 bull 得分最高 + bear 得分最低的两人
- 读他们的 `pass_rules` 和 `fail_rules`
- 让他们"辩论" 3 轮（每轮 2 句话），**引用具体数字**

**4.2 写 3 条核心结论**

用 "但是" 结构，不要和稀泥：
- ✅ "ROE 连续 6 年盈利但从未破 15%，典型的长期平庸。" — 有定论
- ❌ "ROE 有起伏，需要观察。" — 废话

**4.3 估值三角验证**

- DCF 说什么？（dim 20）
- Comps 说什么？
- LBO 说什么？
- 三者**冲突时**，写出冲突并给出你的解读

**4.4 催化剂 + 风险排序**

- 从 dim 21 `catalyst_calendar` 取未来 60 天高影响事件
- 按概率 × 影响度排序 Top 3 催化剂
- 再挑 Top 3 风险（来自 dim 22 IC Memo 的 risks_mitigants）

**4.5 四派系买入区间**

给出 4 个有说服力的价位：
- **价值派**：DCF 内在价 × 0.85 （要 15% 安全边际）
- **成长派**：3 年 EPS × 中位数 PE
- **技术派**：60 日均线附近 或 Stage 2 起涨点
- **游资派**：龙虎榜集中区间

每个价位**必须附一句解释**。

### 写入

以上 5 件事全部写入 `synthesis.json`。脚本里有 `generate_synthesis()` 会生成 stub，但**默认是程序化的**。你要在 stub 基础上**重写**这几个关键字段。

---

### Task 5 · 报告组装 (🤖 脚本 + **🧠 你的金句**)

**脚本部分**：
```bash
python scripts/assemble_report.py {ticker}
python scripts/inline_assets.py {ticker}      # 生成自包含 HTML
python scripts/render_share_card.py {ticker}  # 朋友圈 PNG
python scripts/render_war_report.py {ticker}  # 战报 PNG
```

### 🧠 你的金句审查

在调 assemble_report 之前，**检查一遍** `synthesis.json` 中这 5 个字段：

| 字段 | 检查点 |
|---|---|
| `great_divide.punchline` | 是不是一句能传播的话？有冲突感吗？引用数字了吗？ |
| `dashboard.core_conclusion` | 1-2 句结论，必须有定论 |
| `debate.rounds[*].bull_say / bear_say` | 每轮必须引用具体数字 |
| `buy_zones.*.rationale` | 每个价位必须给出计算逻辑（不能只写"基于技术面"） |
| `risks[*]` | 风险必须具体到数字 / 事件 |

任何一个字段没达标，**直接重写**后再调脚本。

### 完成验证

生成的 HTML 报告打开必须满足：
- 无 console error
- 22 维深度卡全部出现（包含新增的 dim 20/21/22）
- 51 评委聊天室 + 审判席都渲染
- Great Divide punchline 不为空
- 杀猪盘等级显示
- 文件大小 > 400 KB（低于说明有大段缺失）

---

## 🎛️ 模式选择

| 触发 | 行为 |
|---|---|
| 默认 | 完整 6 Task |
| `/quick-scan` | 只跑 dim 0/1/2/10/18 + Top 10 投资者，跳过 dim 21/22 |
| `/panel-only` | 跳过 Task 2, 只输出 51 评委 + synthesis |
| `/scan-trap` | 只跑 dim 18 (杀猪盘)，不调评审团 |
| `/dcf` | 只跑 DCF 估值单独输出 |
| `/comps` | 只跑同行对标 |
| `/initiate` | 完整 6 Task + 强制生成机构首次覆盖章节 |
| `/ic-memo` | 完整 6 Task + 强制生成 IC Memo 8 章节 |
| `/catalysts` | 完整 Task + 重点展示催化剂日历 |
| `/thesis` | 只跑 thesis_tracker 单独输出 |
| `/screen` | 跑 5 套量化筛选 |
| `/dd` | 跑 DD 清单 |

## 📁 数据契约 & 文件路径

| 文件 | 谁写 | 谁读 |
|---|---|---|
| `.cache/{ticker}/raw_data.json` | Task 1/1.5 脚本 | Task 2-5 + 你 |
| `.cache/{ticker}/dimensions.json` | Task 2 脚本 + 你的 `dim_commentary` | Task 4-5 |
| `.cache/{ticker}/panel.json` | Task 3 规则引擎 | Task 4-5 |
| `.cache/{ticker}/synthesis.json` | **你主导写** | Task 5 |
| `reports/{ticker}_{date}/full-report.html` | Task 5 脚本 | 用户 |
| `reports/{ticker}_{date}/full-report-standalone.html` | inline_assets.py | 用户分享 |
| `reports/{ticker}_{date}/share-card.png` | render_share_card | 朋友圈 |
| `reports/{ticker}_{date}/war-report.png` | render_war_report | 战报 |
| `reports/{ticker}_{date}/one-liner.txt` | assemble 副产 | 快速摘要 |

详细 schema 见 `assets/data-contracts.md`。

## 🔧 工具箱速查

### 估值建模
- `lib.fin_models.compute_dcf(features, assumptions)` — DCF + WACC + 5×5 敏感性
- `lib.fin_models.build_comps_table(target, peers)` — 同行对标
- `lib.fin_models.project_three_stmt(features, assumptions)` — 5 年 IS/BS/CF
- `lib.fin_models.quick_lbo(features, ...)` — PE 买方视角 IRR 测试
- `lib.fin_models.accretion_dilution(acquirer, target, ...)` — 并购增厚/摊薄

### 研究工作流
- `lib.research_workflow.build_initiating_coverage(...)` — 机构首次覆盖
- `lib.research_workflow.build_earnings_analysis(...)` — beat/miss 解读
- `lib.research_workflow.build_catalyst_calendar(...)` — 催化剂日历
- `lib.research_workflow.build_thesis_tracker(...)` — 投资逻辑追踪
- `lib.research_workflow.build_morning_note(...)` — 晨报
- `lib.research_workflow.run_idea_screen(features, style)` — 5 套量化筛选 (value/growth/quality/gulp/short)
- `lib.research_workflow.build_sector_overview(...)` — 行业综述

### 深度决策
- `lib.deep_analysis_methods.build_ic_memo(...)` — 投委会备忘录 8 章
- `lib.deep_analysis_methods.build_unit_economics(...)` — LTV/CAC 或毛利拆解
- `lib.deep_analysis_methods.build_value_creation_plan(...)` — EBITDA 桥
- `lib.deep_analysis_methods.build_dd_checklist(...)` — 5 工作流 21 项 DD
- `lib.deep_analysis_methods.build_competitive_analysis(...)` — Porter 5 Forces + BCG
- `lib.deep_analysis_methods.build_portfolio_rebalance(...)` — 组合再平衡

### 量化评委 / 规则引擎
- `lib.stock_features.extract_features(raw, dims)` — 108 标准化特征
- `lib.investor_criteria.INVESTOR_RULES` — 51 人 180 条规则
- `lib.investor_evaluator.evaluate(investor_id, features)` — 单人裁决
- `lib.investor_evaluator.evaluate_all(features)` — 51 人批量
- `lib.investor_evaluator.panel_summary(results)` — panel 汇总

### 数据质量
- `lib.data_integrity.validate(raw)` — 100% 覆盖度校验器

## 📚 详细参考文档

- `references/task1-data-collection.md` — 22 维 fetcher 清单 + 并行策略
- `references/task1.5-institutional-modeling.md` — **DCF/Comps/LBO 默认参数与 A 股适配**（重要！）
- `references/task2-dimension-scoring.md` — 打分规则
- `references/task3-investor-panel.md` — 51 评委规则
- `references/task4-synthesis.md` — 叙事合成规范
- `references/task5-report-assembly.md` — 报告组装
- `references/fin-methods/README.md` — 17 种机构方法论索引
- `assets/data-contracts.md` — 所有 JSON schema
- `assets/quality-checklist.md` — 完成前的 checklist

## ✅ 完成定义

- 5 个 JSON 产物全部落地
- `raw_data.json` 完整性覆盖 ≥ 90%
- `dim_commentary` 至少覆盖 15/22 维度
- `synthesis.json` 中 punchline / core_conclusion / debate.rounds / buy_zones / risks 都由你亲自写
- HTML 报告打开无 console error
- 金句里包含具体数字
- 杀猪盘等级始终显示

---

**现在开始**：从第 0 步识别股票开始。记住 — **你是分析师，不是脚本运行器。**
