# 📊 Stock Deep Analyzer · 个股深度分析引擎

> Float Future · ALPHA TERMINAL · **v2.0.0**
>
> **AI 驱动 · 22 维数据 × 51 位大佬量化评委 × 17 种机构级分析方法 · 杀猪盘检测 · Bloomberg 风格 HTML 报告**

---

## ✨ 这是什么

一个 Claude Code 插件，让 Claude 变成一位**首席股票分析师**。一句话分析任意 A 股 / 港股 / 美股：

```
> /analyze-stock 水晶光电
> /dcf 600519
> /initiate 002273
> /ic-memo AAPL
```

Claude 会按 **6 个 Task** 完成一次完整深度分析：

1. **Task 1** · 22 维数据采集 (财报 / K线 / 估值 / 龙虎榜 / 资金面 / 政策 / 情绪 / 杀猪盘…)
2. **Task 1.5** · 机构级建模 (DCF / Comps / LBO / 3-Statement / IC Memo / Porter 五力 / 催化剂日历…)
3. **Task 2** · 22 维打分 + Claude 亲写的定性评语
4. **Task 3** · 51 位大佬量化评委裁决 (180 条规则引擎)
5. **Task 4** · Claude 主导的叙事合成 (多空辩论 + 估值三角验证 + 买入区间)
6. **Task 5** · 生成 Bloomberg 风格报告

输出产物：
- `full-report.html` · Bloomberg 风格 16:9 专业仪表盘 (~600 KB 自包含)
- `full-report-standalone.html` · 内嵌所有资源的离线版
- `share-card.png` · 1080×1920 朋友圈竖图战报
- `war-report.png` · 1920×1080 微信群横图
- `one-liner.txt` · 一句话摘要

---

## 🎯 v2.0 新增：机构级分析层

基于 **[anthropics/financial-services-plugins](https://github.com/anthropics/financial-services-plugins)** 的方法论，本插件新增 **17 种机构级分析方法**：

### 📐 估值建模 (5 种)

| 方法 | 产物 | 命令 |
|---|---|---|
| **DCF** (2-stage + Gordon Growth) | WACC 分解 + 10 年 FCF 预测 + 5×5 敏感性表 | `/dcf` |
| **Comps** 同行对标 | PE / PB / PS / EV-EBITDA 分位分析 + 隐含目标价 | `/comps` |
| **3-Statement** 预测 | 5 年 IS / BS / CF 联动 | `/initiate` |
| **Quick LBO** | PE 买方 IRR / MOIC 交叉验证 | `/lbo` |
| **Merger Model** | 并购增厚 / 摊薄分析 | (内部调用) |

### 📑 研究工作流产物 (7 种)

| 方法 | 描述 | 命令 |
|---|---|---|
| **Initiating Coverage** | 机构首次覆盖报告 (6 章节 · JPM/GS/MS 格式) | `/initiate` |
| **Earnings Analysis** | 财报 beat/miss 解读 + 投资逻辑影响 | `/earnings` |
| **Catalyst Calendar** | 未来 60 天事件日历 + 影响分级 | `/catalysts` |
| **Thesis Tracker** | 投资逻辑 5 支柱运行跟踪 | `/thesis` |
| **Morning Note** | 晨报简讯 | (内部) |
| **Idea Screen** | 5 套量化筛选 (value/growth/quality/gulp/short) | `/screen` |
| **Sector Overview** | 行业综述 | (内部) |

### 🏛️ 深度决策方法 (6 种)

| 方法 | 描述 | 命令 |
|---|---|---|
| **IC Memo** | 投委会备忘录 8 章节 + 三情景回报 | `/ic-memo` |
| **Unit Economics** | LTV/CAC 或毛利瀑布 | (内部) |
| **Value Creation Plan** | EBITDA 桥 + 5 大杠杆 | (内部) |
| **DD Checklist** | 5 工作流 21 项尽调清单 | `/dd` |
| **Porter 5 Forces + BCG** | 竞争格局结构化分析 | (内部) |
| **Portfolio Rebalance** | 组合漂移分析 | (内部) |

---

## 🧠 51 位投资大佬量化评委

每位大佬有明确的 **量化规则集**（`lib/investor_criteria.py` 共 **180 条规则**），每条建议必须击中具体规则：

- **巴菲特** · 7 条 · ROE 连续 5Y>15% / 净利率>15% / 负债率<50% / FCF+ / 护城河≥24 / PE 中位数以下 / 5Y 分红
- **格雷厄姆** · 6 条 · PE<15 · PB<1.5 · PE×PB<22.5 (22.5 定律) · 流动比>2 · 连续 6Y 盈利 · 现净资产 20% 以上
- **段永平** · 4 条 · 三问法 (Stop Doing / 看 10 年能否看懂 / 是否本分生意)
- **赵老哥** · 5 条 · 龙虎榜活跃 · Stage 2 动量 · 板块龙头 · 涨幅榜位置 · 两板之后
- ... (51 人 × 180 规则)

每次裁决输出：
```json
{
  "investor_id": "buffett",
  "score": 62,
  "signal": "neutral",
  "headline": "观望：护城河 27/40 可见；但 ROE 5 年最低 6.7%，达标率仅 0/5",
  "pass_rules": [{"name": "资产负债率 < 50%", "msg": "资产负债率 30% 保守", "weight": 3}],
  "fail_rules": [{"name": "ROE 连续 5 年 > 15%", "msg": "...", "weight": 5}],
  "rationale": "✅ 符合标准...\n❌ 未达标准..."
}
```

---

## 🎭 流派分布

| 组 | 人数 | 代表 |
|---|---|---|
| **A · 经典价值** | 6 | 巴菲特 / 格雷厄姆 / 费雪 / 芒格 / 邓普顿 / 卡拉曼 |
| **B · 成长投资** | 4 | 林奇 / 欧奈尔 / 蒂尔 / 木头姐 |
| **C · 宏观对冲** | 5 | 索罗斯 / 达里奥 / 马克斯 / 德鲁肯米勒 / 罗伯逊 |
| **D · 技术趋势** | 4 | 利弗莫尔 / 米内尔维尼 / 达瓦斯 / 江恩 |
| **E · 中国价投** | 6 | 段永平 / 张坤 / 朱少醒 / 谢治宇 / 冯柳 / 邓晓峰 |
| **F · A 股游资** | 23 | 章盟主 / 赵老哥 / 佛山无影脚 / 炒股养家 / 北京炒家 / 鑫多多 ... |
| **G · 量化系统** | 3 | 西蒙斯 / 索普 / 大卫·肖 |

## 🏗️ 架构

```
stock-deep-analyzer/
├── .claude-plugin/
│   ├── plugin.json              # 插件元数据 + 命令清单
│   └── marketplace.json         # Marketplace 发布配置
├── commands/                    # 14 个 slash commands
│   ├── analyze-stock.md         #   /analyze-stock
│   ├── quick-scan.md            #   /quick-scan
│   ├── panel-only.md            #   /panel-only
│   ├── scan-trap.md             #   /scan-trap
│   ├── dcf.md                   #   /dcf
│   ├── comps.md                 #   /comps
│   ├── lbo.md                   #   /lbo
│   ├── initiate.md              #   /initiate
│   ├── earnings.md              #   /earnings
│   ├── catalysts.md             #   /catalysts
│   ├── thesis.md                #   /thesis
│   ├── screen.md                #   /screen
│   ├── ic-memo.md               #   /ic-memo
│   └── dd.md                    #   /dd
├── skills/
│   ├── deep-analysis/           # ★ 主工作流 (6 Task)
│   │   ├── SKILL.md             # Claude 的分析师手册 (v2.0)
│   │   ├── references/
│   │   │   ├── task1-data-collection.md
│   │   │   ├── task1.5-institutional-modeling.md  # ★ 新增
│   │   │   ├── task2-dimension-scoring.md
│   │   │   ├── task3-investor-panel.md
│   │   │   ├── task4-synthesis.md
│   │   │   ├── task5-report-assembly.md
│   │   │   └── fin-methods/              # ★ 17 种方法论
│   │   │       └── README.md
│   │   ├── assets/
│   │   │   ├── report-template.html      # Bloomberg 风格模板
│   │   │   ├── avatars/{51}.svg          # 51 张像素头像
│   │   │   ├── data-contracts.md
│   │   │   └── quality-checklist.md
│   │   └── scripts/
│   │       ├── lib/
│   │       │   ├── data_sources.py       # 多源 fallback (5+ hosts)
│   │       │   ├── cache.py              # 分层 TTL 缓存
│   │       │   ├── market_router.py      # A/H/U 路由
│   │       │   ├── seat_db.py            # 22 位游资席位
│   │       │   ├── investor_db.py        # 51 人元数据
│   │       │   ├── investor_personas.py  # 51 × 270 条真实原话
│   │       │   ├── investor_criteria.py  # ★ 180 条量化规则
│   │       │   ├── investor_evaluator.py # ★ 规则引擎
│   │       │   ├── stock_features.py     # ★ 108 标准化特征
│   │       │   ├── data_integrity.py     # ★ 100% 覆盖度校验
│   │       │   ├── fin_models.py         # ★ DCF/Comps/3-Stmt/LBO/Merger
│   │       │   ├── research_workflow.py  # ★ 7 种研究产物
│   │       │   ├── deep_analysis_methods.py # ★ 6 种 PE/IB/WM 方法
│   │       │   └── web_search.py         # ddgs 封装 + 12h 缓存
│   │       ├── fetch_*.py                # 22 个维度 fetcher
│   │       ├── compute_deep_methods.py   # ★ dim 20/21/22 生成
│   │       ├── run_real_test.py          # ★ 6-Task 主流水线
│   │       ├── assemble_report.py        # HTML 装配 (~2000 行)
│   │       ├── inline_assets.py          # 自包含 HTML
│   │       ├── render_share_card.py      # 朋友圈 PNG
│   │       └── render_war_report.py      # 战报 PNG
│   ├── investor-panel/
│   ├── lhb-analyzer/
│   └── trap-detector/
├── README.md
└── requirements.txt
```

---

## 📦 安装

### 1. 安装插件

```bash
# 在 Claude Code 里
/plugin marketplace add /path/to/stock-deep-analyzer
/plugin install stock-deep-analyzer@float-future-stock-analyzer
```

或直接 git clone：
```bash
git clone https://github.com/float-future/stock-deep-analyzer
cd stock-deep-analyzer
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
playwright install chromium  # 用于 PNG 渲染
```

### 3. 启动

```bash
# 在 Claude Code 会话里
/analyze-stock 水晶光电

# 或直接跑 Python 流水线（调试用）
python skills/deep-analysis/scripts/run_real_test.py 002273.SZ
```

---

## 🚀 用法示例

### 完整深度分析 (6 Task · 约 5-8 分钟)

```
/analyze-stock 水晶光电
/analyze-stock 002273
/analyze-stock 00700.HK
/analyze-stock AAPL
```

### 只跑 DCF 估值

```
/dcf 600519
```
输出：WACC 分解 / 10 年 FCF / 终值 / 内在价值 / 5×5 敏感性表 / 安全边际

### 只跑同行对标

```
/comps 002273
```
输出：同行池 / PE/PB 分位 / 中位数隐含价 / 估值结论

### 机构首次覆盖报告

```
/initiate 600519
```
输出：推荐评级 / 目标价 / 投资论点 / 估值桥 / 核心风险 / 财务快照

### 投委会备忘录

```
/ic-memo 002273
```
输出：8 章节 IC Memo · Bull/Base/Bear 三情景回报 · Top 3 风险+缓解

### 催化剂日历

```
/catalysts 002273
```
输出：未来 60 天事件时间线 · 高/中/低影响分级

### 30 秒速判

```
/quick-scan 002273
```
仅跑核心维度 + Top 10 投资者，不生成 PNG。

### 只看投票

```
/panel-only 600519
```

### 杀猪盘排查

```
/scan-trap 002273
/scan-trap 朋友推荐我买这只票
```

---

## 🧠 Claude 是分析师，不是脚本运行器

本插件的核心设计原则（写在 `skills/deep-analysis/SKILL.md` 里）：

> **Claude 不是脚本的搬运工** — 不要只把 `cat xxx.json` 往报告里贴。
> **Claude 是分析师** — 读原始数据 + 量化结果，然后用判断串起一个有冲突感、有洞察的叙事。

脚本负责算数，Claude 负责：
- **假设审查** (Task 1.5) — 默认 DCF 用 stage1=10%, beta=1.0，但半导体公司应该用 22% / 1.4
- **定性评语** (Task 2) — 每个维度写 1-2 句"数据背后的故事"
- **叙事合成** (Task 4) — 多空辩论、估值三角、买入区间、金句
- **金句审查** (Task 5) — punchline 必须有冲突感 + 引用具体数字

---

## 📚 17 种方法论详细参考

完整方法论文档见 `skills/deep-analysis/references/fin-methods/README.md`，列出了每种方法的：
- Python 模块路径
- 源 SKILL.md (Anthropic 官方)
- A 股落地参数（rf / ERP / 税率 / 终值 g）
- 输入 / 输出 schema

---

## 🔧 数据源矩阵

全部免费、零 API key，多层 fallback：

| 维度 | 主数据源 | Fallback 链 |
|---|---|---|
| 实时行情 / PE / 市值 | push2.eastmoney.com | xueqiu → qt.gtimg.cn → sina → baidu |
| 财报历史 | akshare `stock_financial_em` | 雪球 f10 |
| K线 / 技术指标 | akshare `stock_zh_a_hist` | yfinance |
| 估值分位 | akshare `stock_zh_valuation_baidu` | 手算 |
| 龙虎榜 | akshare `stock_lhb_detail_em` | 东财 |
| 事件 / 研报 / 公告 | akshare `stock_research_report_em` + `stock_zh_a_disclosure_report_cninfo` | ths |
| 港股 | akshare `stock_hk_*` | yfinance |
| 美股 | yfinance | akshare `stock_us_hist` |
| 宏观 / 政策 / 原材料 / 杀猪盘 / 舆情 | **ddgs web search** (多站点 query) | — |

---

## 📊 水晶光电 (002273.SZ) 实测输出样例

```
[████████████████████] 100% · v2.0 新流水线已完成

🔢 数据完整性: 100% · 18/18 关键字段 · 0 缺失

📐 Task 1.5 · 机构级建模:
  DCF  · WACC 6.96% · 内在价值 ¥20.73 · 安全边际 -28.6% · 🟠 略微高估
  LBO  · IRR 21.7% · MOIC 2.67x · 🟢 PE 买方可赚 20%+
  Comps · 待同行补全
  3-Stmt · Y5 营收 82.4 亿 · 净利 12.1 亿

🏛️ 首次覆盖: 减持 (Underperform) · 目标价 ¥20.73 · 空间 -28.6%
📋 IC Memo: ⚪ 观望 (HOLD)
⚔️ Porter: BCG Dog · 行业吸引力 50%
📋 DD Checklist: 48% 自动命中 · 11 项待人工复核
📅 催化剂: 未来 30 天 1 个高影响事件

🎭 51 位评委:
  看多 26 · 中性 15 · 看空 10 · 平均 64.9 分
  巴菲特  · 62 · neutral · 观望：护城河 27/40 可见；但 ROE 5 年最低 6.7%，达标率仅 0/5
  格雷厄姆 · 44 · neutral · 观望：连续 6 年盈利；但 PE 35.055 高于 15
  卡拉曼  ·  0 · bearish · 看空核心：无 30% 安全边际

💥 Great Divide (需 Claude 合成):
  "DCF 说高估 28%，但 LBO 说 PE 仍能赚 21% IRR —
   市场把光学行业增速定得比 PE 基金更悲观。"

→ reports/002273.SZ_20260415/full-report-standalone.html (531 KB)
```

---

## ⚠️ 免责声明

本工具由 AI 模型基于公开信息生成报告，所有数据通过开源库与 web search 获取，**可能存在滞后或误差**。

报告中的评分、建议、模拟评语**均为算法模拟**，不代表任何真实投资者的实际观点。

**本工具不构成任何投资建议**，投资者应独立判断并承担投资风险。

---

## 🪪 License

MIT — 但请尊重数据源各自的使用条款（akshare / yfinance / 雪球 / 东方财富）。

---

Generated with ❤️ by Float Future · v2.0.0 · O.o
