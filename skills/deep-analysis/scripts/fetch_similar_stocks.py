"""NEW Fetcher · 相似股推荐 — 硬编码同行 + 真实行情对比.

策略:
1. 按 industry 在 INDUSTRY_PEERS 里查到同行列表
2. 对每只同行股，调用 fetch_basic 拿 name/price/pe/market_cap (复用各种 fallback)
3. 如果 industry 不在硬编码表里，返回空（可后续加 stock_info_a_code_name 关键词搜索）

无需 push2 blocked 的 stock_board_industry_cons_em。
"""
from __future__ import annotations

import json
import sys

from lib import data_sources as ds
from lib.market_router import parse_ticker


# Industry → peer stock codes (top 4-6 by market cap)
INDUSTRY_PEERS: dict[str, list[tuple[str, str]]] = {
    "光学光电子": [
        ("002273", "水晶光电"),
        ("002281", "光迅科技"),
        ("300433", "蓝思科技"),
        ("688127", "蓝特光学"),
        ("002456", "欧菲光"),
        ("603501", "韦尔股份"),
    ],
    "白酒": [
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000568", "泸州老窖"),
        ("002304", "洋河股份"),
        ("600809", "山西汾酒"),
    ],
    "半导体": [
        ("688981", "中芯国际"),
        ("603986", "兆易创新"),
        ("002371", "北方华创"),
        ("688012", "中微公司"),
        ("688008", "澜起科技"),
        ("002129", "TCL中环"),
    ],
    "电池": [
        ("300750", "宁德时代"),
        ("300014", "亿纬锂能"),
        ("002460", "赣锋锂业"),
        ("002812", "恩捷股份"),
        ("300207", "欣旺达"),
    ],
    "医药生物": [
        ("300760", "迈瑞医疗"),
        ("600276", "恒瑞医药"),
        ("603259", "药明康德"),
        ("600196", "复星医药"),
        ("300122", "智飞生物"),
    ],
    "银行": [
        ("601398", "工商银行"),
        ("600036", "招商银行"),
        ("601939", "建设银行"),
        ("601288", "农业银行"),
        ("601166", "兴业银行"),
    ],
    "家电": [
        ("000333", "美的集团"),
        ("000651", "格力电器"),
        ("600690", "海尔智家"),
        ("002032", "苏泊尔"),
    ],
    "光模块": [
        ("300308", "中际旭创"),
        ("300394", "天孚通信"),
        ("300502", "新易盛"),
        ("002463", "沪电股份"),
    ],
    "消费电子": [
        ("002475", "立讯精密"),
        ("002241", "歌尔股份"),
        ("002938", "鹏鼎控股"),
    ],
    "钢铁": [
        ("600019", "宝钢股份"),
        ("600808", "马钢股份"),
        ("000898", "鞍钢股份"),
    ],
    "保险": [
        ("601318", "中国平安"),
        ("601601", "中国太保"),
        ("601628", "中国人寿"),
    ],
    "证券": [
        ("600030", "中信证券"),
        ("601688", "华泰证券"),
        ("000776", "广发证券"),
    ],
    "房地产": [
        ("000002", "万科A"),
        ("001979", "招商蛇口"),
        ("600048", "保利发展"),
    ],
    "食品饮料": [
        ("600887", "伊利股份"),
        ("603288", "海天味业"),
    ],
}


def _fetch_peer_basics(peers: list[tuple[str, str]], self_code: str, top_n: int) -> list[dict]:
    results = []
    for code, known_name in peers:
        if code == self_code:
            continue
        if len(results) >= top_n:
            break
        try:
            ti = parse_ticker(code)
            basic = ds.fetch_basic(ti)
            if not basic or not basic.get("price"):
                continue
            name = basic.get("name") or known_name
            results.append({
                "name": name,
                "code": ti.full,
                "price": basic.get("price"),
                "pe_ttm": basic.get("pe_ttm"),
                "pb": basic.get("pb"),
                "market_cap": basic.get("market_cap"),
                "change_pct": basic.get("change_pct"),
                "url": f"https://xueqiu.com/S/SZ{code}" if ti.full.endswith("SZ") else f"https://xueqiu.com/S/SH{code}",
            })
        except Exception:
            continue
    return results


def main(ticker: str, top_n: int = 4) -> dict:
    ti = parse_ticker(ticker)
    if ti.market != "A":
        return {"ticker": ti.full, "data": {"similar_stocks": []}, "source": "n/a", "fallback": True}

    basic = ds.fetch_basic(ti)
    industry = basic.get("industry") or ""

    # Find peers from hardcoded industry map (direct + fuzzy)
    peers = INDUSTRY_PEERS.get(industry, [])
    if not peers:
        for key, val in INDUSTRY_PEERS.items():
            if key in industry or industry in key or (len(industry) >= 2 and industry[:2] in key):
                peers = val
                break

    if not peers:
        return {
            "ticker": ti.full,
            "data": {"similar_stocks": [], "industry": industry, "_note": "industry 未在同行映射表里"},
            "source": "INDUSTRY_PEERS (missing)",
            "fallback": True,
        }

    peer_basics = _fetch_peer_basics(peers, ti.code, top_n)

    # Build similar_stocks output with similarity score + reason
    similar = []
    self_pe = basic.get("pe_ttm") or 0
    for p in peer_basics:
        # Similarity = PE proximity (normalized)
        pe_sim = 0
        if self_pe and p.get("pe_ttm"):
            pe_ratio = min(self_pe, p["pe_ttm"]) / max(self_pe, p["pe_ttm"])
            pe_sim = pe_ratio * 100
        similarity_score = int(max(75, min(98, pe_sim if pe_sim > 0 else 85)))

        similar.append({
            "name": p["name"],
            "code": p["code"],
            "price": p.get("price"),
            "pe_ttm": p.get("pe_ttm"),
            "market_cap": p.get("market_cap"),
            "change_pct": p.get("change_pct"),
            "similarity": f"{similarity_score}%",
            "reason": f"同属{industry} · PE {p.get('pe_ttm', '—')} · 市值 {p.get('market_cap', '—')}",
            "url": p.get("url"),
        })

    return {
        "ticker": ti.full,
        "data": {
            "similar_stocks": similar,
            "industry": industry,
            "peers_attempted": len(peers),
        },
        "source": "INDUSTRY_PEERS + fetch_basic (XueQiu / baidu / sina)",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))
