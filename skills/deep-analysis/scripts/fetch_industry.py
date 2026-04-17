"""Dimension 7 · 行业景气度 — 使用 cninfo 行业 PE 聚合数据（绕过 push2）."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

import akshare as ak  # type: ignore
from lib.market_router import parse_ticker
from lib.industry_mapping import resolve_csrc_industry


# Industry → (growth %, TAM 亿, penetration %, lifecycle stage)
# Hardcoded domain knowledge for common industries (fallback when no API)
INDUSTRY_ESTIMATES: dict[str, dict] = {
    "光学光电子": {
        "growth": "+30%/年",
        "tam": "¥420 亿",
        "penetration": "12%",
        "lifecycle": "成长期",
        "note": "AR/VR + 车载光学 + iPhone 相机模组驱动",
    },
    "半导体": {
        "growth": "+18%/年",
        "tam": "¥7800 亿",
        "penetration": "国产化率 15%",
        "lifecycle": "成长期",
        "note": "国产替代 + AI 算力需求",
    },
    "医药生物": {
        "growth": "+10%/年",
        "tam": "¥3.2 万亿",
        "penetration": "—",
        "lifecycle": "成熟期",
        "note": "集采降价 + 创新药放量博弈",
    },
    "电池": {
        "growth": "+22%/年",
        "tam": "¥1.8 万亿",
        "penetration": "电车 38%",
        "lifecycle": "成长期",
        "note": "动力电池 + 储能双驱动",
    },
    "白酒": {
        "growth": "+6%/年",
        "tam": "¥7500 亿",
        "penetration": "—",
        "lifecycle": "成熟期",
        "note": "次高端分化 + 名酒企稳",
    },
    "银行": {
        "growth": "+4%/年",
        "tam": "—",
        "penetration": "—",
        "lifecycle": "成熟期",
        "note": "净息差收窄 + 红利防御属性",
    },
    "钢铁": {
        "growth": "-2%/年",
        "tam": "—",
        "penetration": "—",
        "lifecycle": "衰退期",
        "note": "供给侧 + 需求下行",
    },
}


def _best_industry_match(industry: str) -> dict:
    if not industry:
        return {}
    for key, val in INDUSTRY_ESTIMATES.items():
        if key in industry or industry in key or industry[:2] in key:
            return val
    return {}


def _cninfo_industry_metrics(industry_name: str) -> dict:
    """Pull industry aggregated PE from cninfo — works on this network."""
    if not industry_name:
        return {}
    today = datetime.now()
    for i in range(1, 8):
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = ak.stock_industry_pe_ratio_cninfo(
                symbol="证监会行业分类", date=d
            )
            if df is None or df.empty:
                continue
            # v2.8.3 · 用语义映射代替 str.contains(industry[:2]) —— 旧版对"工业金属"
            # 等前缀高碰撞的申万行业会误命中"农副食品加工业"
            row = resolve_csrc_industry(industry_name, df)
            if row is None:
                continue
            pe_col = next((c for c in df.columns if "市盈率" in c and "加权" in c), None)
            return {
                "industry_name_match": str(row.get("行业名称", "")),
                "company_count": int(row.get("公司数量", 0)) if "公司数量" in df.columns else None,
                "total_mcap_yi": float(row.get("总市值-静态", 0)) if "总市值-静态" in df.columns else None,
                "net_profit_yi": float(row.get("净利润-静态", 0)) if "净利润-静态" in df.columns else None,
                "industry_pe_weighted": float(row[pe_col]) if pe_col else None,
                "industry_pe_median": float(row.get("静态市盈率-中位数", 0)) if "静态市盈率-中位数" in df.columns else None,
                "data_date": d,
            }
        except Exception:
            continue
    return {}


def main(industry: str) -> dict:
    # Lookup industry estimates
    est = _best_industry_match(industry)

    # Get cninfo aggregated metrics
    cninfo_metrics = _cninfo_industry_metrics(industry)

    return {
        "data": {
            "industry": industry,
            "growth": est.get("growth", "—"),
            "tam": est.get("tam", "—"),
            "penetration": est.get("penetration", "—"),
            "lifecycle": est.get("lifecycle", "—"),
            "note": est.get("note", ""),
            "cninfo_metrics": cninfo_metrics,
            "total_companies": cninfo_metrics.get("company_count"),
            "industry_pe_weighted": cninfo_metrics.get("industry_pe_weighted"),
            "needs_web_search": not bool(est),
            "web_search_queries": [
                f"{industry} 行业景气度 2026",
                f"{industry} 市场规模 TAM",
                f"{industry} 渗透率 提升空间",
            ] if not est else [],
        },
        "source": "cninfo:stock_industry_pe_ratio + INDUSTRY_ESTIMATES + web_search",
        "fallback": not bool(cninfo_metrics),
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "光学光电子"
    print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))
