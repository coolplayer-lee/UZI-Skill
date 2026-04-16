"""Dimension 13 · 政策与监管 — 真实 web search 拉取行业政策."""
from __future__ import annotations

import json
import sys
from datetime import datetime

from lib.web_search import search


def main(industry: str = "综合") -> dict:
    year = datetime.now().year
    queries = {
        "policy_dir": f"{year} {industry} 国家政策 扶持 利好",
        "subsidy": f"{year} {industry} 政府补贴 税收优惠",
        "monitoring": f"{year} {industry} 监管 合规 风险",
        "anti_trust": f"{year} {industry} 反垄断 调查",
    }
    snippets: dict[str, list] = {}
    sentiment_map: dict[str, str] = {}

    for key, q in queries.items():
        res = search(q, max_results=4)
        valid = [r for r in res if "error" not in r]
        snippets[key] = [
            {"title": r.get("title", "")[:80], "body": r.get("body", "")[:200], "url": r.get("url", "")}
            for r in valid[:3]
        ]

        # Heuristic sentiment per category
        text = " ".join(r.get("body", "") for r in valid)
        pos_kws = ["扶持", "支持", "鼓励", "补贴", "优惠", "免税", "专项", "利好"]
        neg_kws = ["处罚", "罚款", "违规", "禁止", "限制", "收紧", "调查", "约谈"]
        pos = sum(1 for kw in pos_kws if kw in text)
        neg = sum(1 for kw in neg_kws if kw in text)

        if pos > neg + 1:
            sentiment_map[key] = "积极"
        elif neg > pos + 1:
            sentiment_map[key] = "收紧"
        elif pos == 0 and neg == 0:
            sentiment_map[key] = "—"
        else:
            sentiment_map[key] = "中性"

    return {
        "data": {
            "policy_dir": sentiment_map.get("policy_dir", "—"),
            "subsidy": sentiment_map.get("subsidy", "—"),
            "monitoring": sentiment_map.get("monitoring", "—"),
            "anti_trust": sentiment_map.get("anti_trust", "—"),
            "snippets": snippets,
            "year": year,
            "industry": industry,
        },
        "source": "web_search:ddgs + keyword sentiment",
        "fallback": False,
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "光学光电子"
    print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))
