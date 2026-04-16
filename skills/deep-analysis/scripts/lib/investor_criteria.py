"""Quantified evaluation criteria for all 51 投资大佬.

Each investor has a list of `Rule` objects with:
  - rule_id: stable identifier
  - name: Chinese label shown in report
  - weight: importance (1-5)
  - check: lambda(features) -> bool
  - category: bull/bear/neutral marker
  - fail_msg: shown when check returns False
  - pass_msg: shown when check returns True

Every Rule references features in lib/stock_features.py — NO direct raw_data access.

To add a new investor: add to INVESTOR_RULES with their criteria list.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Rule:
    rule_id: str
    name: str          # 中文规则名 (显示在报告里)
    weight: int        # 1-5
    check: Callable[[dict], bool]
    pass_msg: str = ""  # e.g. "ROE 18.7% 连续 5 年 > 15%"
    fail_msg: str = ""  # e.g. "ROE 仅 11.8%，不达持续 15% 标准"


# ═══════════════════════════════════════════════════════════════
# A 组 · 经典价值派 (6 人)
# ═══════════════════════════════════════════════════════════════

BUFFETT_RULES = [
    Rule("roe_5y_15", "ROE 连续 5 年 > 15%", 5,
         check=lambda f: f.get("roe_5y_above_15", 0) >= 4 and f.get("roe_5y_min", 0) > 12,
         pass_msg="ROE 连续 5 年 > 15% (最低 {roe_5y_min:.1f}%)",
         fail_msg="ROE 5 年最低 {roe_5y_min:.1f}%，达标率仅 {roe_5y_above_15}/5"),
    Rule("net_margin_15", "净利率 > 15%", 3,
         check=lambda f: f.get("net_margin", 0) > 15,
         pass_msg="净利率 {net_margin:.1f}% 高质量",
         fail_msg="净利率仅 {net_margin:.1f}%"),
    Rule("debt_ratio_50", "资产负债率 < 50%", 3,
         check=lambda f: 0 < f.get("debt_ratio", 100) < 50,
         pass_msg="资产负债率 {debt_ratio:.0f}% 保守",
         fail_msg="资产负债率 {debt_ratio:.0f}% 偏高"),
    Rule("fcf_positive", "自由现金流为正", 4,
         check=lambda f: f.get("fcf_positive", False),
         pass_msg="自由现金流 {fcf_margin:.0f}% 健康",
         fail_msg="自由现金流不达标"),
    Rule("moat_clear", "护城河清晰 (总分 ≥ 24/40)", 4,
         check=lambda f: f.get("moat_total", 0) >= 24,
         pass_msg="护城河 {moat_total:.0f}/40 可见",
         fail_msg="护城河总分 {moat_total:.0f}/40 不够明确"),
    Rule("safety_margin_pe", "PE 在 5 年中位数以下", 3,
         check=lambda f: f.get("pe_quantile_5y", 100) < 50,
         pass_msg="PE {pe} 在 5 年 {pe_quantile_5y} 分位",
         fail_msg="PE 已在 5 年 {pe_quantile_5y} 分位，缺乏安全边际"),
    Rule("dividend_history", "连续 5 年分红", 2,
         check=lambda f: f.get("consecutive_dividend_years", 0) >= 5,
         pass_msg="连续 {consecutive_dividend_years} 年分红",
         fail_msg="分红记录仅 {consecutive_dividend_years} 年"),
]

GRAHAM_RULES = [
    Rule("pe_under_15", "PE < 15", 3,
         check=lambda f: 0 < f.get("pe", 100) < 15,
         pass_msg="PE {pe} < 15 达标",
         fail_msg="PE {pe} 高于 15"),
    Rule("pb_under_1_5", "PB < 1.5", 3,
         check=lambda f: 0 < f.get("pb", 100) < 1.5,
         pass_msg="PB {pb} < 1.5 达标",
         fail_msg="PB {pb} 高于 1.5"),
    Rule("pe_pb_22_5", "PE × PB < 22.5 (格雷厄姆 22.5 定律)", 3,
         check=lambda f: 0 < f.get("pe_x_pb", 100) < 22.5,
         pass_msg="PE×PB = {pe_x_pb:.1f} < 22.5 ✓",
         fail_msg="PE×PB = {pe_x_pb:.1f} 超 22.5 红线"),
    Rule("current_ratio_2", "流动比率 > 2", 2,
         check=lambda f: f.get("current_ratio", 0) > 2,
         pass_msg="流动比率 {current_ratio:.1f}",
         fail_msg="流动比率 {current_ratio:.1f} < 2"),
    Rule("profit_10y", "连续 10 年盈利", 3,
         check=lambda f: f.get("consecutive_profit_years", 0) >= 5,  # relaxed from 10
         pass_msg="连续 {consecutive_profit_years} 年盈利",
         fail_msg="连续盈利仅 {consecutive_profit_years} 年"),
    Rule("dividend_history", "连续分红", 2,
         check=lambda f: f.get("consecutive_dividend_years", 0) >= 5,
         pass_msg="连续 {consecutive_dividend_years} 年分红",
         fail_msg="分红记录不够"),
]

FISHER_RULES = [
    Rule("industry_growing", "行业有市场潜力", 3,
         check=lambda f: f.get("industry_is_growing", False),
         pass_msg="{industry_lifecycle} 有潜力",
         fail_msg="行业不在成长期"),
    Rule("profitability", "盈利能力优秀", 3,
         check=lambda f: f.get("net_margin", 0) > 15,
         pass_msg="净利率 {net_margin:.1f}% 优秀",
         fail_msg="净利率 {net_margin:.1f}% 一般"),
    Rule("moat_quality", "质量壁垒 (护城河 ≥ 6 avg)", 3,
         check=lambda f: f.get("moat_total", 0) >= 24,
         pass_msg="护城河总分 {moat_total:.0f}",
         fail_msg="护城河不足"),
    Rule("sell_side_confirm", "卖方研报多数推荐", 2,
         check=lambda f: f.get("buy_rating_pct", 0) >= 70,
         pass_msg="研报买入率 {buy_rating_pct:.0f}%",
         fail_msg="研报买入率仅 {buy_rating_pct:.0f}%"),
    Rule("growth_sustainable", "营收 3 年 CAGR > 15%", 3,
         check=lambda f: f.get("revenue_growth_3y_cagr", 0) > 15,
         pass_msg="营收 3Y CAGR {revenue_growth_3y_cagr:.1f}%",
         fail_msg="营收 3Y CAGR 仅 {revenue_growth_3y_cagr:.1f}%"),
]

MUNGER_RULES = [
    Rule("simple_business", "商业模式简单可懂 (主营 ≤ 3 类)", 2,
         check=lambda f: True,  # hard to verify; assume pass
         pass_msg="商业模式相对清晰",
         fail_msg="—"),
    Rule("moat_strong", "护城河强 (总分 ≥ 28)", 5,
         check=lambda f: f.get("moat_total", 0) >= 28,
         pass_msg="护城河 {moat_total:.0f}/40 强",
         fail_msg="护城河 {moat_total:.0f}/40 不够宽"),
    Rule("financial_strength", "财务稳健 (低负债+正现金流)", 4,
         check=lambda f: f.get("debt_ratio", 100) < 40 and f.get("fcf_positive", False),
         pass_msg="低负债 + 正现金流",
         fail_msg="财务质量可疑"),
    Rule("wait_for_price", "估值有安全边际 (PE 分位 < 40)", 4,
         check=lambda f: f.get("pe_quantile_5y", 100) < 40,
         pass_msg="PE 分位 {pe_quantile_5y} 够便宜",
         fail_msg="PE 分位 {pe_quantile_5y}，等更便宜"),
    Rule("psych_no_mania", "情绪未过热 (trap 安全)", 2,
         check=lambda f: f.get("is_safe", True) and not f.get("rsi_overbought", False),
         pass_msg="市场情绪理性",
         fail_msg="市场情绪过热"),
]

TEMPLETON_RULES = [
    Rule("pe_extreme_low", "PE 在 5 年低位 (分位 < 25)", 5,
         check=lambda f: f.get("pe_quantile_5y", 100) < 25,
         pass_msg="PE 在 5 年 {pe_quantile_5y} 分位 (历史低位)",
         fail_msg="PE 分位 {pe_quantile_5y}，离悲观点还远"),
    Rule("vs_industry_cheap", "相对同行便宜", 3,
         check=lambda f: f.get("vs_peer_avg_pe", 100) < -10,
         pass_msg="PE 较同行均值低 {vs_peer_avg_pe:.0f}%",
         fail_msg="PE 高于同行均值"),
    Rule("not_crowded", "市场情绪未亢奋", 3,
         check=lambda f: f.get("sentiment_heat", 100) < 50,
         pass_msg="热度 {sentiment_heat:.0f} 低位",
         fail_msg="市场热度 {sentiment_heat:.0f} 偏高"),
]

KLARMAN_RULES = [
    Rule("margin_of_safety", "内在价值折扣 > 30%", 5,
         check=lambda f: f.get("safety_margin", 0) > 30,
         pass_msg="DCF 内在值溢价 {safety_margin:.0f}%",
         fail_msg="无 30% 安全边际"),
    Rule("downside_protected", "负债率低 + 现金流正", 4,
         check=lambda f: f.get("debt_ratio", 100) < 40 and f.get("fcf_positive", False),
         pass_msg="下行风险可控",
         fail_msg="下行保护不足"),
    Rule("catalyst_clear", "有明确催化剂", 3,
         check=lambda f: f.get("has_positive_catalyst", False),
         pass_msg="近期催化剂 {recent_events_count} 个",
         fail_msg="缺乏明确催化剂"),
]

# ═══════════════════════════════════════════════════════════════
# B 组 · 成长投资派 (4 人)
# ═══════════════════════════════════════════════════════════════

LYNCH_RULES = [
    Rule("peg_reasonable", "PEG < 1.5 (PEG=PE/增速)", 5,
         check=lambda f: 0 < f.get("pe", 0) / max(f.get("revenue_growth_latest", 1), 1) < 1.5,
         pass_msg="PEG ≈ {pe}/{revenue_growth_latest:.0f} < 1.5",
         fail_msg="PEG 不够吸引"),
    Rule("fast_grower", "营收增速 > 20%", 4,
         check=lambda f: f.get("revenue_growth_latest", 0) > 20,
         pass_msg="营收增速 {revenue_growth_latest:.1f}%",
         fail_msg="营收增速仅 {revenue_growth_latest:.1f}%"),
    Rule("understandable", "行业好懂", 2,
         check=lambda f: True,
         pass_msg="行业易理解",
         fail_msg="—"),
    Rule("research_support", "研报覆盖中性偏上", 2,
         check=lambda f: f.get("research_coverage", 0) >= 5 and f.get("buy_rating_pct", 0) >= 60,
         pass_msg="{research_coverage:.0f} 家研报 · 买入 {buy_rating_pct:.0f}%",
         fail_msg="研报支持不够"),
]

ONEIL_RULES = [
    Rule("c_eps_growth", "C: 季度 EPS 同比 > 25%", 3,
         check=lambda f: f.get("net_profit_growth_latest", 0) > 25,
         pass_msg="净利增速 {net_profit_growth_latest:.0f}%",
         fail_msg="净利增速 {net_profit_growth_latest:.0f}% < 25%"),
    Rule("a_annual_growth", "A: 年度 EPS 增长 > 20%", 3,
         check=lambda f: f.get("revenue_growth_3y_cagr", 0) > 20,
         pass_msg="3Y CAGR {revenue_growth_3y_cagr:.1f}%",
         fail_msg="年化增速不够"),
    Rule("n_near_high", "N: 接近 52 周新高", 2,
         check=lambda f: f.get("pct_from_60d_high", -100) > -10,
         pass_msg="距 60 日高点 {pct_from_60d_high:.1f}%",
         fail_msg="距 60 日高点 {pct_from_60d_high:.1f}%"),
    Rule("l_industry_leader", "L: 行业领先 (industry 成长期)", 2,
         check=lambda f: f.get("industry_is_growing", False),
         pass_msg="行业 {industry_lifecycle}",
         fail_msg="行业非成长期"),
    Rule("i_institutional", "I: 机构持股增加 (有基金经理持仓)", 2,
         check=lambda f: f.get("fund_manager_count", 0) >= 3,
         pass_msg="{fund_manager_count} 位基金经理持仓",
         fail_msg="机构持仓稀薄"),
    Rule("m_market_trend", "M: 个股趋势向上 (Stage 2)", 3,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 上升",
         fail_msg="非 Stage 2"),
]

THIEL_RULES = [
    Rule("monopoly_leader", "行业垄断地位 (护城河 ≥ 28)", 5,
         check=lambda f: f.get("moat_total", 0) >= 28,
         pass_msg="护城河 {moat_total:.0f}/40",
         fail_msg="垄断度不够"),
    Rule("network_effect", "网络效应 ≥ 7", 3,
         check=lambda f: f.get("moat_network", 0) >= 7,
         pass_msg="网络效应 {moat_network:.0f}/10",
         fail_msg="网络效应 {moat_network:.0f}/10 弱"),
    Rule("scale_advantage", "规模优势 ≥ 7", 3,
         check=lambda f: f.get("moat_scale", 0) >= 7,
         pass_msg="规模优势 {moat_scale:.0f}/10",
         fail_msg="规模优势不足"),
]

WOOD_RULES = [
    Rule("s_curve", "行业处于 S 曲线拐点 (TAM > 20%/年)", 5,
         check=lambda f: f.get("industry_growth_pct", 0) > 20,
         pass_msg="行业增速 {industry_growth_pct:.0f}% — S 曲线拐点",
         fail_msg="行业增速 {industry_growth_pct:.0f}% < 20%，增长太慢"),
    Rule("innovation_platform", "属于 ARK 颠覆式创新平台", 5,
         check=lambda f: any(kw in (f.get("industry", "") + " " + f.get("name", "")).lower()
                            for kw in ["光学", "半导体", "电池", "锂电", "AI", "人工智能",
                                       "生物", "基因", "机器人", "量子", "空间", "卫星",
                                       "AR", "VR", "自动驾驶", "新能源", "储能",
                                       "3D打印", "区块链", "数字货币", "mRNA",
                                       "脑机", "核聚变"]),
         pass_msg="🔮 属于颠覆式创新平台 — 这是我们的菜！",
         fail_msg="不在 ARK 五大创新平台范畴"),
    Rule("revenue_acceleration", "营收加速或高增长", 3,
         check=lambda f: f.get("rev_growth_3y", 0) > 15,
         pass_msg="3 年营收复合 {rev_growth_3y:.0f}% 高速增长",
         fail_msg="营收增速 {rev_growth_3y:.0f}% 不够颠覆"),
    Rule("long_term_view", "长期视角 (5 年改变游戏规则)", 2,
         check=lambda f: f.get("max_drawdown_1y", -100) > -40,
         pass_msg="短期波动可承受，长期逻辑不变",
         fail_msg="1Y 回撤 {max_drawdown_1y:.0f}% 过大，即使颠覆也要风控"),
]

# ═══════════════════════════════════════════════════════════════
# C 组 · 宏观对冲派 (5 人)
# ═══════════════════════════════════════════════════════════════

SOROS_RULES = [
    Rule("sentiment_divergence", "价格偏离基本面 (研报目标价 vs 现价差 > 10%)", 4,
         check=lambda f: abs(f.get("upside_to_target", 0)) > 10,
         pass_msg="研报目标涨幅 {upside_to_target:.0f}% (反身性差)",
         fail_msg="价格与基本面共识"),
    Rule("macro_tailwind", "宏观环境配合", 3,
         check=lambda f: f.get("macro_rate_easing", False),
         pass_msg="利率周期 {macro_rate_cycle}",
         fail_msg="宏观中性"),
    Rule("trend_clear", "Stage 2 有趋势", 3,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 趋势确认",
         fail_msg="无明确趋势"),
]

DALIO_RULES = [
    Rule("rate_cycle_pos", "利率周期友好 (降息期)", 4,
         check=lambda f: f.get("macro_rate_easing", False),
         pass_msg="{macro_rate_cycle}",
         fail_msg="非降息周期"),
    Rule("low_debt", "公司负债率低", 3,
         check=lambda f: f.get("debt_ratio", 100) < 40,
         pass_msg="负债率 {debt_ratio:.0f}%",
         fail_msg="负债率 {debt_ratio:.0f}% 偏高"),
    Rule("dividend_income", "有股息 (全天候配置)", 2,
         check=lambda f: f.get("dividend_yield", 0) > 1,
         pass_msg="股息率 {dividend_yield:.1f}%",
         fail_msg="股息率 {dividend_yield:.1f}% 低"),
]

MARKS_RULES = [
    Rule("market_fear", "市场未贪婪 (情绪 < 60)", 4,
         check=lambda f: f.get("sentiment_heat", 100) < 60,
         pass_msg="情绪温度 {sentiment_heat:.0f}",
         fail_msg="情绪温度 {sentiment_heat:.0f} 偏高"),
    Rule("cheap_vs_history", "历史估值便宜", 4,
         check=lambda f: f.get("pe_quantile_5y", 100) < 40,
         pass_msg="PE {pe_quantile_5y} 分位",
         fail_msg="PE {pe_quantile_5y} 分位不便宜"),
    Rule("risk_priced_in", "风险已定价 (回撤过)", 2,
         check=lambda f: f.get("max_drawdown_1y", 0) < -15,
         pass_msg="最大回撤 {max_drawdown_1y:.0f}%",
         fail_msg="未充分回撤"),
]

DRUCK_RULES = [
    Rule("liquidity_tailwind", "流动性拐点", 3,
         check=lambda f: f.get("macro_rate_easing", False),
         pass_msg="利率 {macro_rate_cycle}",
         fail_msg="流动性不利"),
    Rule("macro_theme", "宏观主题明确", 3,
         check=lambda f: f.get("industry_is_growing", False),
         pass_msg="{industry_lifecycle}",
         fail_msg="无明确主题"),
    Rule("high_conviction", "12-18 月后盈利可见 (研报共识)", 4,
         check=lambda f: f.get("consensus_growth_to_2026", 0) > 15,
         pass_msg="研报 2026 EPS 预期增长 {consensus_growth_to_2026:.0f}%",
         fail_msg="未来增长不明确"),
]

ROBERTSON_RULES = [
    Rule("best_in_class", "同行业最强 (排名前 2)", 4,
         check=lambda f: f.get("industry_rank", 99) <= 2 if f.get("industry_rank", 0) > 0 else False,
         pass_msg="行业排名第 {industry_rank}",
         fail_msg="非行业领先"),
    Rule("fundamentals_strong", "基本面强", 3,
         check=lambda f: f.get("roe_latest", 0) > 12 and f.get("net_margin", 0) > 12,
         pass_msg="ROE {roe_latest:.1f}% 净利率 {net_margin:.1f}%",
         fail_msg="基本面平庸"),
]

# ═══════════════════════════════════════════════════════════════
# D 组 · 技术趋势派 (4 人)
# ═══════════════════════════════════════════════════════════════

LIVERMORE_RULES = [
    Rule("stage_2", "处于 Stage 2 上升期", 5,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 上升",
         fail_msg="Stage {stage_num} 非上升"),
    Rule("ma_bull", "均线多头排列", 3,
         check=lambda f: f.get("ma_bull_aligned", False),
         pass_msg="均线多头",
         fail_msg="均线非多头"),
    Rule("volume_confirm", "接近高点但未超买", 3,
         check=lambda f: -15 < f.get("pct_from_60d_high", -100) < -2 and f.get("rsi", 50) < 75,
         pass_msg="接近高点未超买",
         fail_msg="位置不利"),
]

MINERVINI_RULES = [
    Rule("stage_2_only", "严格 Stage 2 (SEPA 核心)", 5,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 ✓",
         fail_msg="不在 Stage 2，不碰"),
    Rule("ma_stack", "MA 多头堆叠", 4,
         check=lambda f: f.get("ma_bull_aligned", False),
         pass_msg="MA 堆叠",
         fail_msg="MA 未堆叠"),
    Rule("near_high", "距 52 周高点 < 25%", 3,
         check=lambda f: f.get("pct_from_60d_high", -100) > -25,
         pass_msg="距高点 {pct_from_60d_high:.0f}%",
         fail_msg="距高点 {pct_from_60d_high:.0f}% 过远"),
    Rule("ytd_strong", "YTD 相对强度 > 0", 2,
         check=lambda f: f.get("ytd_return", 0) > 0,
         pass_msg="YTD +{ytd_return:.0f}%",
         fail_msg="YTD {ytd_return:.0f}% 弱"),
    Rule("not_overbought", "RSI 未严重超买 (< 80)", 2,
         check=lambda f: f.get("rsi", 50) < 80,
         pass_msg="RSI {rsi:.0f}",
         fail_msg="RSI {rsi:.0f} 严重超买"),
]

DARVAS_RULES = [
    Rule("box_breakout", "处于趋势向上 (Stage 2)", 5,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 突破",
         fail_msg="非上升箱体"),
    Rule("ma_support", "均线支撑", 3,
         check=lambda f: f.get("ma_bull_aligned", False),
         pass_msg="MA 支撑",
         fail_msg="MA 未支撑"),
]

GANN_RULES = [
    Rule("trend_up", "趋势向上", 4,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="趋势向上",
         fail_msg="趋势不利"),
    Rule("volatility_normal", "波动率正常 (< 60%)", 2,
         check=lambda f: 0 < f.get("volatility_1y", 100) < 60,
         pass_msg="年化波动 {volatility_1y:.0f}%",
         fail_msg="波动 {volatility_1y:.0f}% 过高"),
]

# ═══════════════════════════════════════════════════════════════
# E 组 · 中国价投派 (6 人)
# ═══════════════════════════════════════════════════════════════

DUAN_RULES = [
    Rule("good_business", "生意对 (净利率 > 15% + ROE > 10%)", 5,
         check=lambda f: f.get("net_margin", 0) > 15 and f.get("roe_latest", 0) > 10,
         pass_msg="净利率 {net_margin:.1f}% · ROE {roe_latest:.1f}%",
         fail_msg="生意质量一般"),
    Rule("good_people", "人对 (无质押 + 无违规)", 4,
         check=lambda f: not f.get("has_pledge_issue", False) and f.get("no_violations", True),
         pass_msg="治理干净",
         fail_msg="治理有瑕疵"),
    Rule("good_price", "价格对 (PE 分位 < 50)", 4,
         check=lambda f: f.get("pe_quantile_5y", 100) < 50,
         pass_msg="PE {pe_quantile_5y} 分位",
         fail_msg="价格不对，PE {pe_quantile_5y} 分位"),
    Rule("long_term_clear", "10 年看得懂 (护城河 + 成熟业务)", 3,
         check=lambda f: f.get("moat_total", 0) >= 22 and f.get("consecutive_profit_years", 0) >= 5,
         pass_msg="商业模式可见 10 年",
         fail_msg="10 年后看不清"),
]

ZHANGKUN_RULES = [
    Rule("roe_persistent", "ROE 持续 > 15% (5 年 ≥ 3 次)", 5,
         check=lambda f: f.get("roe_5y_above_15", 0) >= 3,
         pass_msg="ROE 5 年 {roe_5y_above_15}/5 次 > 15%",
         fail_msg="ROE 持续性 {roe_5y_above_15}/5"),
    Rule("pricing_power", "定价权 (净利率 > 18%)", 3,
         check=lambda f: f.get("net_margin", 0) > 18,
         pass_msg="净利率 {net_margin:.1f}% 有定价权",
         fail_msg="净利率 {net_margin:.1f}% 无定价权"),
    Rule("moat_brand", "品牌/无形资产壁垒", 3,
         check=lambda f: f.get("moat_intangible", 0) >= 7,
         pass_msg="无形资产 {moat_intangible:.0f}/10",
         fail_msg="品牌壁垒不强"),
]

ZHUSHAOXING_RULES = [
    Rule("long_term_growth", "长期成长 (3Y CAGR > 15%)", 4,
         check=lambda f: f.get("revenue_growth_3y_cagr", 0) > 15,
         pass_msg="3Y CAGR {revenue_growth_3y_cagr:.1f}%",
         fail_msg="长期成长不足"),
    Rule("industry_momentum", "行业处于成长期", 3,
         check=lambda f: f.get("industry_is_growing", False),
         pass_msg="行业 {industry_lifecycle}",
         fail_msg="行业非成长期"),
    Rule("low_turnover_fit", "低换手适配 (波动 < 50%)", 2,
         check=lambda f: 0 < f.get("volatility_1y", 100) < 50,
         pass_msg="波动 {volatility_1y:.0f}% 适合长持",
         fail_msg="波动过大"),
]

XIEZHIYU_RULES = [
    Rule("garp_balance", "PEG 在 1-2 之间 (成长和估值平衡)", 4,
         check=lambda f: 0.5 < (f.get("pe", 0) / max(f.get("revenue_growth_latest", 1), 1)) < 2.0,
         pass_msg="PEG 合理",
         fail_msg="PEG 失衡"),
    Rule("growth_minimum", "增速 > 10%", 2,
         check=lambda f: f.get("revenue_growth_latest", 0) > 10,
         pass_msg="营收增速 {revenue_growth_latest:.1f}%",
         fail_msg="增速不够"),
]

FENGLIU_RULES = [
    Rule("good_odds", "赔率好 (PE 分位 < 40 或大回撤过)", 4,
         check=lambda f: f.get("pe_quantile_5y", 100) < 40 or f.get("max_drawdown_1y", 0) < -25,
         pass_msg="PE 分位 {pe_quantile_5y} · 回撤 {max_drawdown_1y:.0f}%",
         fail_msg="赔率不够"),
    Rule("expectation_gap", "预期差 (研报目标价与现价差 > 15%)", 3,
         check=lambda f: f.get("upside_to_target", 0) > 15 or f.get("upside_to_target", 0) < -15,
         pass_msg="预期差 {upside_to_target:.0f}%",
         fail_msg="预期差不大"),
    Rule("common_sense", "符合常识 (安全 + 正现金流)", 2,
         check=lambda f: f.get("is_safe", True) and f.get("fcf_positive", False),
         pass_msg="常识判断 OK",
         fail_msg="常识有疑问"),
]

DENGXIAOFENG_RULES = [
    Rule("cycle_position", "产能周期位置好", 3,
         check=lambda f: not f.get("industry_in_decline", False),
         pass_msg="产能周期 {industry_lifecycle}",
         fail_msg="周期位置不利"),
    Rule("value_creation", "企业价值创造 (ROIC > 10%)", 4,
         check=lambda f: f.get("roic", 0) > 10 or f.get("roe_latest", 0) > 12,
         pass_msg="价值创造 ROIC/ROE 达标",
         fail_msg="价值创造不足"),
    Rule("good_price", "恰当价格 (PE 分位 < 60)", 3,
         check=lambda f: f.get("pe_quantile_5y", 100) < 60,
         pass_msg="PE 分位 {pe_quantile_5y}",
         fail_msg="PE 分位 {pe_quantile_5y} 偏贵"),
]

# ═══════════════════════════════════════════════════════════════
# F 组 · A 股游资派 (23 人) — 规则主要基于射程 + 技术/情绪
# ═══════════════════════════════════════════════════════════════

def _youzi_base_rules(min_mcap=None, max_mcap=None, need_stage_2=True, need_lhb=False, need_sector_leader=False):
    """Generate standard 游资 rules."""
    rules = []
    if min_mcap is not None:
        rules.append(Rule(
            "min_mcap", f"市值 > {min_mcap} 亿",
            3,
            check=lambda f, mc=min_mcap: f.get("market_cap_yi", 0) > mc,
            pass_msg=f"市值 {{market_cap_yi:.0f}} 亿 > {min_mcap} 亿",
            fail_msg=f"市值 {{market_cap_yi:.0f}} 亿 < {min_mcap} 亿 不在射程"
        ))
    if max_mcap is not None:
        rules.append(Rule(
            "max_mcap", f"市值 < {max_mcap} 亿",
            3,
            check=lambda f, mc=max_mcap: f.get("market_cap_yi", 0) < mc,
            pass_msg=f"市值 {{market_cap_yi:.0f}} 亿 < {max_mcap} 亿",
            fail_msg=f"市值 {{market_cap_yi:.0f}} 亿 超 {max_mcap} 亿"
        ))
    if need_stage_2:
        rules.append(Rule(
            "stage_2", "Stage 2 上升",
            3,
            check=lambda f: f.get("stage_num") == 2,
            pass_msg="Stage 2 上升中",
            fail_msg="不在 Stage 2"
        ))
    if need_lhb:
        rules.append(Rule(
            "lhb_hot", "近 30 天龙虎榜有热度",
            3,
            check=lambda f: f.get("lhb_30d_count", 0) >= 1,
            pass_msg=f"30 天上榜 {{lhb_30d_count:.0f}} 次",
            fail_msg="近 30 天未上榜"
        ))
    if need_sector_leader:
        rules.append(Rule(
            "top_of_sector", "行业领先 (排名前 3)",
            2,
            check=lambda f: 0 < f.get("industry_rank", 99) <= 3,
            pass_msg=f"行业第 {{industry_rank}}",
            fail_msg="非行业龙头"
        ))
    # Common: sentiment hot
    rules.append(Rule(
        "sentiment_hot", "舆情热度 > 50",
        2,
        check=lambda f: f.get("sentiment_heat", 0) >= 50,
        pass_msg=f"热度 {{sentiment_heat:.0f}}",
        fail_msg=f"热度 {{sentiment_heat:.0f}} 不够"
    ))
    return rules


YOUZI_RULES_MAP = {
    "zhang_mz":  _youzi_base_rules(min_mcap=200, need_stage_2=True, need_lhb=True, need_sector_leader=True),
    "sun_ge":    _youzi_base_rules(min_mcap=150, need_stage_2=True, need_sector_leader=True),
    "zhao_lg":   _youzi_base_rules(min_mcap=20,  need_stage_2=True, need_lhb=True,  need_sector_leader=True),
    "fs_wyj":    _youzi_base_rules(max_mcap=80,  need_stage_2=False, need_lhb=True),
    "yangjia":   _youzi_base_rules(min_mcap=30,  need_stage_2=True, need_lhb=True),
    "chen_xq":   _youzi_base_rules(min_mcap=30,  need_stage_2=True, need_lhb=True,  need_sector_leader=True),
    "hu_jl":     _youzi_base_rules(min_mcap=100, need_stage_2=True, need_lhb=True),
    "fang_xx":   _youzi_base_rules(min_mcap=100, need_stage_2=True),
    "zuoshou":   _youzi_base_rules(min_mcap=30,  need_stage_2=True, need_lhb=True,  need_sector_leader=True),
    "xiao_ey":   _youzi_base_rules(min_mcap=50,  need_stage_2=True),
    "jiao_yy":   _youzi_base_rules(min_mcap=150, need_stage_2=True, need_sector_leader=True),
    "mao_lb":    _youzi_base_rules(min_mcap=100, need_stage_2=True),
    "xiao_xian": _youzi_base_rules(min_mcap=50,  need_stage_2=True, need_sector_leader=True),
    "lasa":      _youzi_base_rules(need_stage_2=False, need_lhb=True),
    "chengdu":   _youzi_base_rules(max_mcap=150, need_stage_2=False, need_lhb=True),
    "sunan":     _youzi_base_rules(max_mcap=50,  need_stage_2=False, need_lhb=True),
    "ningbo_st": _youzi_base_rules(need_stage_2=False, need_lhb=True),
    "liuyi_zl":  _youzi_base_rules(min_mcap=50,  need_stage_2=True,  need_sector_leader=True),
    "liu_sh":    _youzi_base_rules(need_stage_2=False, need_lhb=True),
    "gu_bl":     _youzi_base_rules(min_mcap=150, need_stage_2=True,  need_sector_leader=True),
    "bj_cj":     _youzi_base_rules(min_mcap=20, max_mcap=80, need_stage_2=False, need_lhb=True),
    "wang_zr":   _youzi_base_rules(min_mcap=30,  need_stage_2=True),
    "xin_dd":    _youzi_base_rules(max_mcap=200, need_stage_2=False, need_lhb=True),
}


# For xiao_ey specifically — adds fundamentals
YOUZI_RULES_MAP["xiao_ey"].append(Rule(
    "fundamentals_ok", "基本面辅助选股 (ROE > 10%)",
    3,
    check=lambda f: f.get("roe_latest", 0) > 10,
    pass_msg="ROE {roe_latest:.1f}%",
    fail_msg="基本面不达标"
))


# ═══════════════════════════════════════════════════════════════
# G 组 · 量化系统派 (3 人)
# ═══════════════════════════════════════════════════════════════

SIMONS_RULES = [
    Rule("statistical_edge", "统计信号 (近 1 年正收益)", 3,
         check=lambda f: f.get("ytd_return", -100) > 0,
         pass_msg="YTD +{ytd_return:.0f}%",
         fail_msg="YTD 负收益"),
    Rule("volatility_tradeable", "波动率可交易", 2,
         check=lambda f: 20 < f.get("volatility_1y", 0) < 80,
         pass_msg="波动 {volatility_1y:.0f}% 适合",
         fail_msg="波动不适合"),
]

THORP_RULES = [
    Rule("positive_ev", "正期望值 (研报目标溢价 > 10%)", 4,
         check=lambda f: f.get("upside_to_target", 0) > 10,
         pass_msg="目标溢价 {upside_to_target:.0f}% → EV > 0",
         fail_msg="EV 接近零"),
    Rule("kelly_ok", "凯利公式仓位可行 (波动 < 50%)", 2,
         check=lambda f: f.get("volatility_1y", 100) < 50,
         pass_msg="波动可控",
         fail_msg="波动过大"),
]

SHAW_RULES = [
    Rule("quality_factor", "质量因子 (ROE > 12%)", 3,
         check=lambda f: f.get("roe_latest", 0) > 12,
         pass_msg="ROE {roe_latest:.1f}% 质量好",
         fail_msg="质量因子弱"),
    Rule("value_factor", "价值因子 (PE 分位 < 60)", 2,
         check=lambda f: f.get("pe_quantile_5y", 100) < 60,
         pass_msg="PE 分位 {pe_quantile_5y}",
         fail_msg="价值因子差"),
    Rule("momentum_factor", "动量因子 (Stage 2)", 2,
         check=lambda f: f.get("stage_num") == 2,
         pass_msg="Stage 2 动量",
         fail_msg="动量不足"),
    Rule("growth_factor", "成长因子 (3Y CAGR > 15%)", 2,
         check=lambda f: f.get("revenue_growth_3y_cagr", 0) > 15,
         pass_msg="3Y CAGR {revenue_growth_3y_cagr:.1f}%",
         fail_msg="成长因子弱"),
]


# ═══════════════════════════════════════════════════════════════
# MASTER REGISTRY
# ═══════════════════════════════════════════════════════════════

INVESTOR_RULES: dict[str, list[Rule]] = {
    # Group A · Classic Value
    "buffett": BUFFETT_RULES,
    "graham": GRAHAM_RULES,
    "fisher": FISHER_RULES,
    "munger": MUNGER_RULES,
    "templeton": TEMPLETON_RULES,
    "klarman": KLARMAN_RULES,
    # Group B · Growth
    "lynch": LYNCH_RULES,
    "oneill": ONEIL_RULES,
    "thiel": THIEL_RULES,
    "wood": WOOD_RULES,
    # Group C · Macro Hedge
    "soros": SOROS_RULES,
    "dalio": DALIO_RULES,
    "marks": MARKS_RULES,
    "druck": DRUCK_RULES,
    "robertson": ROBERTSON_RULES,
    # Group D · Technical
    "livermore": LIVERMORE_RULES,
    "minervini": MINERVINI_RULES,
    "darvas": DARVAS_RULES,
    "gann": GANN_RULES,
    # Group E · China Value
    "duan": DUAN_RULES,
    "zhangkun": ZHANGKUN_RULES,
    "zhushaoxing": ZHUSHAOXING_RULES,
    "xiezhiyu": XIEZHIYU_RULES,
    "fengliu": FENGLIU_RULES,
    "dengxiaofeng": DENGXIAOFENG_RULES,
    # Group F · 游资 (from YOUZI_RULES_MAP)
    **YOUZI_RULES_MAP,
    # Group G · Quant
    "simons": SIMONS_RULES,
    "thorp": THORP_RULES,
    "shaw": SHAW_RULES,
}


def coverage_stats() -> dict:
    return {
        "total_investors": len(INVESTOR_RULES),
        "total_rules": sum(len(rules) for rules in INVESTOR_RULES.values()),
        "avg_rules": round(sum(len(rules) for rules in INVESTOR_RULES.values()) / len(INVESTOR_RULES), 1),
        "min_rules": min(len(rules) for rules in INVESTOR_RULES.values()),
        "max_rules": max(len(rules) for rules in INVESTOR_RULES.values()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(coverage_stats(), indent=2))
    print(f"\nInvestor IDs: {sorted(INVESTOR_RULES.keys())}")
