"""Dimension 17 · 舆情与大V — 真实 web search (雪球 / 股吧 / 知乎 / 小红书)."""
from __future__ import annotations

import json
import sys

from lib import data_sources as ds
from lib.market_router import parse_ticker
from lib.web_search import search


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    basic = ds.fetch_basic(ti)
    name = basic.get("name") or ti.code

    # Query each platform separately
    platforms = {
        "xueqiu": f"site:xueqiu.com {name}",
        "guba": f"site:guba.eastmoney.com {name}",
        "zhihu": f"知乎 {name} 股票 分析",
        "weibo": f"微博 {name} 股票",
        "xiaohongshu": f"小红书 {name} 股票",
        "big_v": f"{name} 大V 分析",
    }

    snippets: dict[str, list] = {}
    platform_hit = {}
    for key, q in platforms.items():
        res = search(q, max_results=4)
        valid = [r for r in res if "error" not in r]
        snippets[key] = [
            {"title": r.get("title", "")[:80], "body": r.get("body", "")[:200], "url": r.get("url", "")}
            for r in valid[:3]
        ]
        platform_hit[key] = len(valid)

    # Positive/negative sentiment analysis
    all_bodies = []
    for platform_snips in snippets.values():
        for s in platform_snips:
            all_bodies.append(s.get("body", ""))
    text = " ".join(all_bodies).lower()

    positive_kws = ["看好", "强势", "上涨", "涨停", "突破", "利好", "龙头", "加仓", "买入"]
    negative_kws = ["看空", "下跌", "亏损", "利空", "减仓", "卖出", "割肉", "杀跌"]
    pos = sum(1 for kw in positive_kws if kw in text)
    neg = sum(1 for kw in negative_kws if kw in text)
    total = pos + neg if (pos + neg) > 0 else 1
    positive_pct = round(pos / total * 100, 0)

    # Heat gauge (0-100) based on total platform hits
    total_hits = sum(platform_hit.values())
    heat = min(100, total_hits * 8 + pos * 2)

    # Big V level detection
    big_v_text = " ".join(s.get("body", "") for s in snippets.get("big_v", []))
    big_v_count = sum(1 for kw in ["万粉", "百万", "博主", "专家"] if kw in big_v_text)

    return {
        "ticker": ti.full,
        "data": {
            "xueqiu_heat": f"热度 {heat}",
            "thermometer_value": heat,
            "guba_volume": f"{platform_hit.get('guba', 0)} 条结果",
            "big_v_mentions": f"{big_v_count} 位大V提及" if big_v_count else "—",
            "positive_pct": f"{positive_pct}%",
            "sentiment_label": "乐观" if positive_pct > 60 else "悲观" if positive_pct < 40 else "中性",
            "platform_snippets": snippets,
            "platform_hits": platform_hit,
            "total_mentions": total_hits,
        },
        "source": "web_search:ddgs (多平台 site: query)",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))
