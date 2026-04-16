"""Post-Task-1 data integrity validator.

After Task 1 (raw data collection) finishes, run `validate(raw)` to check
that all critical fields used by downstream rules are populated. Returns a
report with missing/fallback dimensions and a `critical_missing` flag.

If critical_missing is True, the caller should retry the affected fetchers
or mark the report with a warning banner.
"""
from __future__ import annotations

from typing import Any


# (dim_key, data_path, label, critical)
# data_path is a dotted path into dim["data"][...]
CRITICAL_CHECKS = [
    # Dimension 0 · Basic
    ("0_basic",        "name",               "公司名称",         True),
    ("0_basic",        "price",              "当前股价",         True),
    ("0_basic",        "industry",           "所属行业",         True),
    ("0_basic",        "market_cap",         "总市值",           True),
    ("0_basic",        "pe_ttm",             "PE-TTM",           False),
    ("0_basic",        "pb",                 "PB",               False),

    # Dimension 1 · Financials
    ("1_financials",   "roe_history",        "ROE 历史",         True),
    ("1_financials",   "revenue_history",    "营收历史",         False),
    ("1_financials",   "net_profit_history", "净利历史",         False),
    ("1_financials",   "financial_health",   "财务健康度",        False),

    # Dimension 2 · Kline
    ("2_kline",        "stage",              "K 线阶段",         True),
    ("2_kline",        "ma_align",           "均线多空",         False),
    ("2_kline",        "macd",               "MACD",             False),

    # Dimension 10 · Valuation
    ("10_valuation",   "pe",                 "PE",               False),
    ("10_valuation",   "pe_quantile",        "PE 5 年分位",       False),
    ("10_valuation",   "pb_quantile",        "PB 5 年分位",       False),

    # Dimension 7 · Industry
    ("7_industry",     "growth",             "行业增速",          False),

    # Dimension 14 · Moat
    ("14_moat",        "scores",             "护城河评分",        False),
]

# Fetchers that provide qualitative enrichment — should have any data at all
# Keys must match the actual dim keys used by run_real_test.collect_raw_data
ENRICHMENT_DIMS = [
    ("3_macro",     "宏观周期"),
    ("4_peers",     "同业对标"),
    ("5_chain",     "上下游"),
    ("6_research",  "券商研报"),
    ("7_industry",  "行业景气"),
    ("8_materials", "原材料"),
    ("9_futures",   "期货关联"),
    ("11_governance", "治理/减持"),
    ("12_capital_flow", "北向/两融"),
    ("13_policy",   "政策环境"),
    ("14_moat",     "护城河"),
    ("15_events",   "事件驱动"),
    ("16_lhb",      "龙虎榜/游资"),
    ("17_sentiment","大V舆情"),
    ("18_trap",     "杀猪盘"),
    ("19_contests", "实盘比赛"),
]


def _get(obj: dict, path: str) -> Any:
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() in ("", "—", "-", "N/A", "None", "0", "0.0"):
        return True
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True
    return False


def validate(raw: dict) -> dict:
    """Validate raw data. Returns:
        {
            "ok": bool,
            "critical_missing": bool,
            "missing_critical": [...],      # list of missing critical fields
            "missing_optional": [...],
            "missing_enrichment": [...],    # dims with no data at all
            "fallback_dims": [...],         # dims flagged fallback=True
            "coverage_pct": 0-100,
        }
    """
    dims = raw.get("dimensions", {}) or {}

    missing_critical: list[dict] = []
    missing_optional: list[dict] = []
    total_checks = 0
    passed_checks = 0

    for dim_key, path, label, critical in CRITICAL_CHECKS:
        total_checks += 1
        dim = dims.get(dim_key) or {}
        data = dim.get("data") or {}
        value = _get(data, path)
        if _is_missing(value):
            entry = {"dim": dim_key, "path": path, "label": label}
            if critical:
                missing_critical.append(entry)
            else:
                missing_optional.append(entry)
        else:
            passed_checks += 1

    # Enrichment coverage
    missing_enrichment: list[dict] = []
    for dim_key, label in ENRICHMENT_DIMS:
        dim = dims.get(dim_key) or {}
        data = dim.get("data") or {}
        # Check if the dim has any non-empty string/list/number in its values
        has_content = False
        for v in data.values() if isinstance(data, dict) else []:
            if not _is_missing(v):
                has_content = True
                break
        if not has_content:
            missing_enrichment.append({"dim": dim_key, "label": label})

    # Fallback dim detection
    fallback_dims = [
        {"dim": k, "reason": (v or {}).get("fallback_reason", "unknown")}
        for k, v in dims.items()
        if isinstance(v, dict) and v.get("fallback") is True
    ]

    coverage_pct = round(passed_checks / total_checks * 100, 0) if total_checks else 0

    critical_missing = len(missing_critical) > 0
    return {
        "ok": not critical_missing and len(missing_enrichment) < 7,
        "critical_missing": critical_missing,
        "missing_critical": missing_critical,
        "missing_optional": missing_optional,
        "missing_enrichment": missing_enrichment,
        "fallback_dims": fallback_dims,
        "coverage_pct": coverage_pct,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
    }


def format_report(report: dict) -> str:
    """Human-readable integrity report for console output."""
    lines: list[str] = []
    status = "✅ OK" if report["ok"] else ("🔴 CRITICAL" if report["critical_missing"] else "🟡 WARNING")
    lines.append(f"[data_integrity] {status} coverage={report['coverage_pct']}% ({report['passed_checks']}/{report['total_checks']})")

    if report["missing_critical"]:
        lines.append(f"  🔴 critical missing ({len(report['missing_critical'])}):")
        for m in report["missing_critical"]:
            lines.append(f"     - {m['label']} ({m['dim']}.{m['path']})")

    if report["missing_optional"]:
        lines.append(f"  🟡 optional missing ({len(report['missing_optional'])}):")
        for m in report["missing_optional"][:8]:
            lines.append(f"     - {m['label']} ({m['dim']}.{m['path']})")

    if report["missing_enrichment"]:
        labels = ", ".join(m["label"] for m in report["missing_enrichment"])
        lines.append(f"  🟡 enrichment dims empty ({len(report['missing_enrichment'])}): {labels}")

    if report["fallback_dims"]:
        labels = ", ".join(f["dim"] for f in report["fallback_dims"])
        lines.append(f"  ⚠️  fallback dims: {labels}")

    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import sys
    # Optional — validate a saved raw JSON file
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        report = validate(raw)
        print(format_report(report))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Usage: python -m lib.data_integrity <raw.json>")
