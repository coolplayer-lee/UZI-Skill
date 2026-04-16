"""Rule engine executor — turns (investor_id, features) into a quantified verdict.

Every investor's evaluation is traceable to the specific rules in
`investor_criteria.INVESTOR_RULES[investor_id]`. No fuzzy templates.

Output schema:
    {
        "investor_id": "buffett",
        "score": 0-100,                     # weighted rule pass rate
        "signal": "bullish"|"bearish"|"neutral",
        "confidence": 0-100,                # coverage-adjusted confidence
        "weight_pass": int,                 # sum of weights of passed rules
        "weight_total": int,                # sum of all rule weights
        "pass_rules": [{rule_id, name, weight, msg}, ...],
        "fail_rules": [{rule_id, name, weight, msg}, ...],
        "headline": "1-sentence summary citing top hit/miss",
        "rationale": "multi-line detailed reasoning",
    }
"""
from __future__ import annotations

from typing import Any

from lib.investor_criteria import INVESTOR_RULES, Rule


# ────────────────────────────────────────────────────────────────
# Signal thresholds
# ────────────────────────────────────────────────────────────────
BULLISH_THRESHOLD = 65   # score ≥ 65 → bullish
BEARISH_THRESHOLD = 35   # score < 35 → bearish


def _fmt_msg(template: str, features: dict) -> str:
    """Format a rule's pass_msg / fail_msg with feature values.

    Gracefully handles missing keys — unknown placeholders stay as literals.
    """
    if not template:
        return ""
    try:
        return template.format(**features)
    except (KeyError, IndexError, ValueError):
        # Fall back: strip unresolved placeholders
        try:
            # replace missing keys with "?"
            safe = {k: features.get(k, "?") for k in _extract_keys(template)}
            return template.format(**safe)
        except Exception:
            return template


def _extract_keys(template: str) -> list[str]:
    import re
    return re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)", template)


def _safe_check(rule: Rule, features: dict) -> bool:
    """Run rule.check guarded against exceptions (missing features, type errors)."""
    try:
        return bool(rule.check(features))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def evaluate(investor_id: str, features: dict) -> dict:
    """Evaluate one investor against one stock's features."""
    rules: list[Rule] = INVESTOR_RULES.get(investor_id, [])
    if not rules:
        return _unknown_result(investor_id)

    pass_list: list[dict] = []
    fail_list: list[dict] = []
    weight_pass = 0
    weight_total = 0

    for rule in rules:
        weight_total += rule.weight
        if _safe_check(rule, features):
            weight_pass += rule.weight
            pass_list.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "weight": rule.weight,
                "msg": _fmt_msg(rule.pass_msg or rule.name, features),
            })
        else:
            fail_list.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "weight": rule.weight,
                "msg": _fmt_msg(rule.fail_msg or f"未达{rule.name}", features),
            })

    # Score: weighted pass rate
    score = round((weight_pass / weight_total) * 100, 1) if weight_total else 0.0

    # Signal determination
    if score >= BULLISH_THRESHOLD:
        signal = "bullish"
    elif score < BEARISH_THRESHOLD:
        signal = "bearish"
    else:
        signal = "neutral"

    # Confidence — more rules = higher confidence; penalize tiny criteria sets
    n_rules = len(rules)
    base_conf = min(100, 50 + n_rules * 8)  # 2 rules → 66, 5 rules → 90, 7+ → 100
    # pull confidence toward the score's extremeness
    extremeness = abs(score - 50) * 0.6  # 0-30
    confidence = round(min(100, base_conf * 0.6 + 40 + extremeness * 0.4), 0)

    # Sort rules by weight desc for display
    pass_list.sort(key=lambda r: -r["weight"])
    fail_list.sort(key=lambda r: -r["weight"])

    headline = _build_headline(signal, pass_list, fail_list)
    rationale = _build_rationale(signal, pass_list, fail_list)

    return {
        "investor_id": investor_id,
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "weight_pass": weight_pass,
        "weight_total": weight_total,
        "pass_count": len(pass_list),
        "fail_count": len(fail_list),
        "pass_rules": pass_list,
        "fail_rules": fail_list,
        "headline": headline,
        "rationale": rationale,
    }


def _build_headline(signal: str, pass_list: list, fail_list: list) -> str:
    """One-sentence takeaway citing the top rule."""
    if signal == "bullish" and pass_list:
        top = pass_list[0]
        return f"看多核心：{top['msg']}"
    if signal == "bearish" and fail_list:
        top = fail_list[0]
        return f"看空核心：{top['msg']}"
    # neutral — cite most important passed + most important failed
    if pass_list and fail_list:
        return f"观望：{pass_list[0]['msg']}；但 {fail_list[0]['msg']}"
    if pass_list:
        return f"中性：{pass_list[0]['msg']}"
    if fail_list:
        return f"中性：{fail_list[0]['msg']}"
    return "数据不足，暂无判断"


def _build_rationale(signal: str, pass_list: list, fail_list: list) -> str:
    """Multi-line detailed reasoning with bullet points."""
    lines: list[str] = []

    if pass_list:
        lines.append("✅ 符合标准：")
        for r in pass_list[:4]:
            lines.append(f"  • [权{r['weight']}] {r['msg']}")

    if fail_list:
        lines.append("❌ 未达标准：")
        for r in fail_list[:4]:
            lines.append(f"  • [权{r['weight']}] {r['msg']}")

    return "\n".join(lines) if lines else "无有效规则命中"


def _unknown_result(investor_id: str) -> dict:
    return {
        "investor_id": investor_id,
        "score": 50.0,
        "signal": "neutral",
        "confidence": 30,
        "weight_pass": 0,
        "weight_total": 0,
        "pass_count": 0,
        "fail_count": 0,
        "pass_rules": [],
        "fail_rules": [],
        "headline": "该投资者暂无量化评估规则",
        "rationale": "此投资者未配置规则库，使用默认中性判断。",
    }


def evaluate_all(features: dict) -> dict[str, dict]:
    """Evaluate all 51 investors at once."""
    return {inv_id: evaluate(inv_id, features) for inv_id in INVESTOR_RULES}


def panel_summary(results: dict[str, dict]) -> dict:
    """Aggregate all investor verdicts into a consensus panel view."""
    if not results:
        return {"bullish": 0, "bearish": 0, "neutral": 0, "avg_score": 50.0}

    bullish = sum(1 for r in results.values() if r["signal"] == "bullish")
    bearish = sum(1 for r in results.values() if r["signal"] == "bearish")
    neutral = sum(1 for r in results.values() if r["signal"] == "neutral")
    avg_score = round(sum(r["score"] for r in results.values()) / len(results), 1)
    avg_conf = round(sum(r["confidence"] for r in results.values()) / len(results), 0)

    # Top 3 most bullish & most bearish (by score)
    sorted_bull = sorted(results.items(), key=lambda kv: -kv[1]["score"])[:5]
    sorted_bear = sorted(results.items(), key=lambda kv: kv[1]["score"])[:5]

    return {
        "total": len(results),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "avg_score": avg_score,
        "avg_confidence": avg_conf,
        "bullish_pct": round(bullish / len(results) * 100, 0),
        "bearish_pct": round(bearish / len(results) * 100, 0),
        "top_bulls": [{"id": k, "score": v["score"], "headline": v["headline"]} for k, v in sorted_bull],
        "top_bears": [{"id": k, "score": v["score"], "headline": v["headline"]} for k, v in sorted_bear],
    }


if __name__ == "__main__":
    import json
    # Sanity check with synthetic features
    test_features = {
        "roe_5y_above_15": 5,
        "roe_5y_min": 18.2,
        "net_margin": 22.5,
        "debt_ratio": 35,
        "fcf_positive": True,
        "fcf_margin": 12.0,
        "moat_total": 32,
        "pe": 18.5,
        "pe_quantile_5y": 45,
        "pb": 3.2,
        "pe_x_pb": 59.2,
        "dividend_5y": True,
        "safety_margin": 15.0,
        "dcf_intrinsic_yi": 800,
        "market_cap_yi": 700,
        "stage_num": 2,
        "ma_bull_aligned": True,
        "pct_from_60d_high": -5.0,
        "rev_growth_3y": 18.0,
        "eps_growth_3y": 25.0,
    }
    result = evaluate("buffett", test_features)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n--- Panel summary ---")
    all_res = evaluate_all(test_features)
    print(json.dumps(panel_summary(all_res), ensure_ascii=False, indent=2))
