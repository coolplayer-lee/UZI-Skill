"""Dimension 5 · 上下游产业链 — 产出 main_business_breakdown (viz 需要的饼图数据)."""
from __future__ import annotations

import json
import sys

import akshare as ak  # type: ignore
from lib.market_router import parse_ticker


def _float(v) -> float:
    try:
        s = str(v).replace("%", "").replace(",", "")
        return float(s) if s and s not in ("nan", "-") else 0.0
    except (ValueError, TypeError):
        return 0.0


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    main_business: list = []
    breakdown_top: list = []
    ths_zyjs: dict = {}

    if ti.market == "A":
        # Source A · 同花顺 主营介绍 (bypasses eastmoney push2)
        try:
            df = ak.stock_zyjs_ths(symbol=ti.code)
            if df is not None and not df.empty:
                row = df.iloc[0]
                ths_zyjs = {
                    "主营业务": str(row.get("主营业务", "")),
                    "产品类型": str(row.get("产品类型", "")),
                    "产品名称": str(row.get("产品名称", "")),
                    "经营范围": str(row.get("经营范围", ""))[:200],
                }
        except Exception as e:
            ths_zyjs = {"error": str(e)[:80]}

        try:
            # stock_zygc_em 需要带前缀的 symbol，例如 SZ002273
            sym_with_prefix = f"{'SZ' if ti.full.endswith('SZ') else 'SH'}{ti.code}"
            df = ak.stock_zygc_em(symbol=sym_with_prefix)
            if df is not None and not df.empty:
                main_business = df.head(50).to_dict("records")

                # 抽最新报告期 × 按"分产品" 聚合
                if "报告日期" in df.columns:
                    latest_date = df["报告日期"].iloc[0]
                    df_latest = df[df["报告日期"] == latest_date]
                else:
                    df_latest = df.head(20)

                # 优先"分产品"，其次"分行业"，最后全部
                product_col = None
                for kw in ["分产品", "分行业", "按产品", "主营构成"]:
                    if "分类" in df_latest.columns:
                        sub = df_latest[df_latest["分类"].astype(str).str.contains(kw, na=False)]
                        if not sub.empty:
                            df_latest = sub
                            product_col = kw
                            break

                # 聚合
                name_col = next((c for c in ["项目", "分项", "名称", "主营构成"] if c in df_latest.columns), None)
                value_col = next((c for c in ["主营收入-同比增长(%)", "收入-金额", "营业收入", "主营收入"] if c in df_latest.columns), None)
                pct_col = next((c for c in ["主营收入-收入比例(%)", "收入比例", "占比"] if c in df_latest.columns), None)

                if name_col and (value_col or pct_col):
                    items = []
                    for _, row in df_latest.iterrows():
                        name = str(row.get(name_col, ""))
                        if not name or name in ("nan", "合计", "总计"):
                            continue
                        if pct_col:
                            v = _float(row.get(pct_col))
                        else:
                            v = _float(row.get(value_col)) / 1e8
                        if v > 0:
                            items.append({"name": name[:12], "value": round(v, 1)})
                    items.sort(key=lambda x: -x["value"])
                    breakdown_top = items[:6]
        except Exception as e:
            main_business = [{"error": str(e)}]

    # Derive upstream/downstream qualitatively from 同花顺 主营
    upstream = "—"
    downstream = "—"
    if ths_zyjs and "error" not in ths_zyjs:
        biz = ths_zyjs.get("主营业务", "")
        if biz:
            downstream = f"(从主营反推) {biz[:60]}..."

    return {
        "ticker": ti.full,
        "data": {
            "main_business_breakdown": breakdown_top,
            "main_business_raw": main_business[:20],
            "ths_zyjs": ths_zyjs,
            "upstream": upstream,
            "downstream": downstream,
            "client_concentration": "—",
            "supplier_concentration": "—",
            "_note": "上下游 specifics 需年报附注 scrape；已从同花顺拿到主营/产品/经营范围",
        },
        "source": "akshare:stock_zygc_em + stock_zyjs_ths",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))
