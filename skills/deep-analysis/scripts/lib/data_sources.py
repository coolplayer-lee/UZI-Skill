"""Unified data source layer.

Wraps akshare / yfinance / direct HTTP endpoints with caching + retry.
All fetcher scripts in scripts/ should use this module instead of touching libs directly.

Install: pip install akshare yfinance pandas requests
"""
from __future__ import annotations

import time
from typing import Any

from .cache import (
    cached,
    TTL_REALTIME,
    TTL_INTRADAY,
    TTL_HOURLY,
    TTL_DAILY,
    TTL_QUARTERLY,
    TTL_STATIC,
)
from .market_router import Market, TickerInfo, parse_ticker

try:
    import akshare as ak
except ImportError:
    ak = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import baostock as bs
    _bs_logged_in = False
except ImportError:
    bs = None
    _bs_logged_in = False

try:
    import requests
except ImportError:
    requests = None


def _retry(fn, attempts: int = 3, sleep: float = 0.8):
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(sleep * (i + 1))
    raise last_err


# ─────────────────────────────────────────────────────────────
# 0. Basic info (name, industry, price, mcap, PE, PB)
# ─────────────────────────────────────────────────────────────
def fetch_basic(ti: TickerInfo) -> dict:
    """Returns a dict with: code, name, industry, price, change_pct, market_cap, pe_ttm, pb.

    TTL = 60s (real-time quote). Use STOCK_NO_CACHE=1 to bypass entirely.
    """
    if ti.market == "A":
        return cached(ti.full, f"basic__{ti.code}", lambda: _fetch_basic_a(ti), ttl=TTL_REALTIME)
    if ti.market == "H":
        return cached(ti.full, f"basic__{ti.code}", lambda: _fetch_basic_hk(ti), ttl=TTL_REALTIME)
    return cached(ti.full, f"basic__{ti.code}", lambda: _fetch_basic_us(ti), ttl=TTL_REALTIME)


def _fetch_basic_a(ti: TickerInfo) -> dict:
    if ak is None:
        raise RuntimeError("akshare not installed")
    out = {"code": ti.full}
    xq_symbol = ("SH" if ti.full.endswith("SH") else "SZ") + ti.code

    # PRIMARY: stock_individual_basic_info_xq (XueQiu backend, bypasses eastmoney push2)
    # Aggressive retry: 4 attempts with 2s base delay because XueQiu SSL sometimes flakes
    try:
        df = _retry(lambda: ak.stock_individual_basic_info_xq(symbol=xq_symbol), attempts=4, sleep=2.0)
        if df is not None and not df.empty:
            info = dict(zip(df["item"], df["value"]))
            industry_field = info.get("affiliate_industry")
            industry_name = None
            if isinstance(industry_field, dict):
                industry_name = industry_field.get("ind_name")
            out.update({
                "name": info.get("org_short_name_cn") or info.get("name"),
                "full_name": info.get("org_name_cn"),
                "name_en": info.get("org_short_name_en"),
                "industry": industry_name,
                "main_business": info.get("main_operation_business"),
                "intro": info.get("org_cn_introduction"),
                "staff_num": info.get("staff_num"),
                "legal_rep": info.get("legal_representative"),
                "chairman": info.get("chairman"),
                "actual_controller": info.get("actual_controller"),
                "reg_asset": info.get("reg_asset"),
                "listed_date": info.get("listed_date"),
                "website": info.get("org_website"),
                "office_address": info.get("office_address_cn"),
                "province": info.get("provincial_name"),
            })
    except Exception as e:
        out["_xq_basic_err"] = str(e)

    # PRIMARY: stock_individual_spot_xq (XueQiu realtime quote, bypasses push2)
    try:
        df = _retry(lambda: ak.stock_individual_spot_xq(symbol=xq_symbol), attempts=4, sleep=2.0)
        if df is not None and not df.empty:
            info = dict(zip(df["item"], df["value"]))

            def _getf(*keys):
                for k in keys:
                    v = info.get(k)
                    if v is not None and v != "":
                        try:
                            return float(v)
                        except (ValueError, TypeError):
                            pass
                return None

            price = _getf("现价")
            mcap = _getf("资产净值/总市值")  # XueQiu's weird key name for total 市值
            circ = _getf("流通值")

            out.update({
                "price": price or out.get("price"),
                "change_pct": _getf("涨幅"),  # real intraday pct change
                "open": _getf("今开"),
                "prev_close": _getf("昨收"),
                "high": _getf("最高"),
                "low": _getf("最低"),
                "high_52w": _getf("52周最高"),
                "low_52w": _getf("52周最低"),
                "volume": _getf("成交量"),
                "turnover": _getf("成交额"),
                "turnover_rate": _getf("周转率"),  # XueQiu calls 换手率 → 周转率
                "market_cap": f"{round(mcap/1e8, 1)}亿" if mcap else out.get("market_cap"),
                "market_cap_raw": mcap,
                "circulating_cap": f"{round(circ/1e8, 1)}亿" if circ else out.get("circulating_cap"),
                "circulating_cap_raw": circ,
                "pe_ttm": _getf("市盈率(TTM)"),
                "pe_static": _getf("市盈率(静)"),
                "pe_dynamic": _getf("市盈率(动)"),
                "pb": _getf("市净率"),
                "eps": _getf("每股收益"),
                "bps": _getf("每股净资产"),
                "dividend_yield_ttm": _getf("股息率(TTM)"),
                "ytd_return_pct": _getf("今年以来涨幅"),
                "amplitude": _getf("振幅"),
                "total_shares": _getf("基金份额/总股本"),
                "float_shares": _getf("流通股"),
                "listed_date": str(info.get("发行日期", "")),
            })
            out["_fallback_snap"] = "xueqiu-spot"
            return out
    except Exception as e:
        out["_xq_spot_err"] = str(e)

    # FALLBACK 1: old stock_individual_info_em (push2 — usually blocked)
    try:
        df = _retry(lambda: ak.stock_individual_info_em(symbol=ti.code), attempts=2)
        info = dict(zip(df["item"], df["value"]))
        out.update({
            "name": out.get("name") or info.get("股票简称"),
            "industry": out.get("industry") or info.get("行业"),
            "market_cap": out.get("market_cap") or info.get("总市值"),
            "circulating_cap": out.get("circulating_cap") or info.get("流通市值"),
            "list_date": out.get("list_date") or info.get("上市时间"),
        })
    except Exception as e:
        out["_info_err"] = str(e)

    # FALLBACK 2: stock_zh_a_spot_em (push2 bulk — usually blocked)
    try:
        snap = _retry(lambda: ak.stock_zh_a_spot_em(), attempts=2)
        row = snap[snap["代码"] == ti.code]
        if not row.empty and not out.get("price"):
            out.update({
                "price": float(row["最新价"].iloc[0]),
                "change_pct": float(row["涨跌幅"].iloc[0]),
                "pe_ttm": float(row["市盈率-动态"].iloc[0]) if row["市盈率-动态"].iloc[0] not in ("", "-", None) else out.get("pe_ttm"),
                "pb": float(row["市净率"].iloc[0]) if row["市净率"].iloc[0] not in ("", "-", None) else out.get("pb"),
            })
            return out
    except Exception as e:
        out["_snap_err"] = str(e)

    def _needs_pe_or_mcap() -> bool:
        return not out.get("pe_ttm") or not out.get("market_cap")

    # Fallback 1: direct push2 HTTP for single ticker (bypass spot_em bulk)
    if requests and (not out.get("price") or _needs_pe_or_mcap()):
        try:
            secid = f"1.{ti.code}" if ti.full.endswith("SH") else f"0.{ti.code}"
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f50,f57,f58,f116,f117,f162,f164",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            }
            r = requests.get(url, params=params, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            data = (r.json() or {}).get("data") or {}
            if data:
                scale = 100.0
                price = (data.get("f43") or 0) / scale
                chg = (data.get("f170") or data.get("f47") or 0) / scale if data.get("f47") else None
                out.update({
                    "price": price if price else out.get("price"),
                    "change_pct": chg,
                    "pe_ttm": (data.get("f162") or 0) / 100 if data.get("f162") else out.get("pe_ttm"),
                    "pb": (data.get("f167") or 0) / 100 if data.get("f167") else out.get("pb"),
                    "market_cap": data.get("f116") or out.get("market_cap"),
                })
                out["_fallback_snap"] = "em-direct"
        except Exception as e:
            out["_em_direct_err"] = str(e)

    # Fallback 2: 腾讯 qt.gtimg.cn (完全独立的 host, 不走 eastmoney)
    # Always try if we're missing PE/PB/market_cap, even if price is set
    if requests and (not out.get("price") or _needs_pe_or_mcap()):
        try:
            prefix = "sh" if ti.full.endswith("SH") else "sz"
            url = f"http://qt.gtimg.cn/q={prefix}{ti.code}"
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            # Response: v_sz002273="51~水晶光电~002273~29.93~29.18~29.20~...";
            text = r.text
            if "~" in text:
                start = text.find('"') + 1
                end = text.rfind('"')
                payload = text[start:end]
                parts = payload.split("~")
                if len(parts) > 45:
                    name = parts[1]
                    try:
                        price = float(parts[3]) if parts[3] else 0
                        prev_close = float(parts[4]) if parts[4] else 0
                        chg_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                    except (ValueError, IndexError):
                        price = prev_close = chg_pct = 0
                    try:
                        total_mcap_yi = float(parts[45]) if len(parts) > 45 and parts[45] else 0
                    except (ValueError, IndexError):
                        total_mcap_yi = 0
                    try:
                        circ_mcap_yi = float(parts[44]) if len(parts) > 44 and parts[44] else 0
                    except (ValueError, IndexError):
                        circ_mcap_yi = 0
                    try:
                        pe_ttm = float(parts[39]) if len(parts) > 39 and parts[39] else None
                    except (ValueError, IndexError):
                        pe_ttm = None
                    try:
                        pb_val = float(parts[46]) if len(parts) > 46 and parts[46] else None
                    except (ValueError, IndexError):
                        pb_val = None
                    # Accumulate, don't overwrite existing populated fields
                    if not out.get("name"):
                        out["name"] = name
                    if not out.get("price") and price:
                        out["price"] = price
                        out["change_pct"] = round(chg_pct, 2)
                    if not out.get("pe_ttm") and pe_ttm:
                        out["pe_ttm"] = pe_ttm
                    if not out.get("pb") and pb_val:
                        out["pb"] = pb_val
                    if not out.get("market_cap") and total_mcap_yi:
                        out["market_cap"] = f"{total_mcap_yi}亿"
                        out["market_cap_raw"] = total_mcap_yi * 1e8
                    if not out.get("circulating_cap") and circ_mcap_yi:
                        out["circulating_cap"] = f"{circ_mcap_yi}亿"
                    out["_fallback_snap"] = out.get("_fallback_snap") or "tencent-qt"
        except Exception as e:
            out["_tencent_err"] = str(e)

    # Fallback 3: 新浪 hq.sinajs.cn (另一个完全独立的 host)
    if requests and not out.get("price"):
        try:
            prefix = "sh" if ti.full.endswith("SH") else "sz"
            url = f"http://hq.sinajs.cn/list={prefix}{ti.code}"
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"})
            text = r.text
            start = text.find('"') + 1
            end = text.rfind('"')
            payload = text[start:end]
            parts = payload.split(",")
            if len(parts) > 30:
                name = parts[0]
                open_p = float(parts[1]) if parts[1] else 0
                prev_close = float(parts[2]) if parts[2] else 0
                price = float(parts[3]) if parts[3] else 0
                chg_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                out.update({
                    "name": out.get("name") or name,
                    "price": price,
                    "change_pct": round(chg_pct, 2),
                })
                out["_fallback_snap"] = "sina-hq"
        except Exception as e:
            out["_sina_err"] = str(e)

    # LAST RESORT 1: industry lookup from known map (critical for downstream fetchers)
    # This covers the case where ALL realtime APIs failed but we still need to know
    # the industry to make industry/materials/futures fetchers work.
    if not out.get("industry"):
        out["industry"] = _known_stock_industry(ti.code)

    # LAST RESORT 2: PE/PB from baidu gushitong (works when xueqiu/tencent/eastmoney all blocked)
    if not out.get("pe_ttm"):
        try:
            df_pe = ak.stock_zh_valuation_baidu(symbol=ti.code, indicator="市盈率(TTM)", period="近一年")
            if df_pe is not None and not df_pe.empty and "value" in df_pe.columns:
                # Take the latest non-null value
                for v in reversed(df_pe["value"].tolist()):
                    if v and float(v) > 0:
                        out["pe_ttm"] = round(float(v), 3)
                        break
        except Exception as e:
            out["_baidu_pe_err"] = str(e)[:80]

    if not out.get("pb"):
        try:
            df_pb = ak.stock_zh_valuation_baidu(symbol=ti.code, indicator="市净率", period="近一年")
            if df_pb is not None and not df_pb.empty and "value" in df_pb.columns:
                for v in reversed(df_pb["value"].tolist()):
                    if v and float(v) > 0:
                        out["pb"] = round(float(v), 3)
                        break
        except Exception as e:
            out["_baidu_pb_err"] = str(e)[:80]

    # LAST RESORT 3: market cap from baidu 总市值 (baidu returns in 亿 directly)
    if not out.get("market_cap"):
        try:
            df_mc = ak.stock_zh_valuation_baidu(symbol=ti.code, indicator="总市值", period="近一年")
            if df_mc is not None and not df_mc.empty and "value" in df_mc.columns:
                for v in reversed(df_mc["value"].tolist()):
                    if v and float(v) > 0:
                        mc = float(v)
                        # Baidu 返回已经是亿为单位
                        out["market_cap"] = f"{round(mc, 1)}亿"
                        out["market_cap_raw"] = mc * 1e8
                        break
        except Exception as e:
            out["_baidu_mcap_err"] = str(e)[:80]

    return out


# Hardcoded industry map for common A-share stocks (used as last-resort fallback
# when all realtime APIs fail). Updated periodically from 申万/中证 classifications.
_STOCK_INDUSTRY_MAP: dict[str, str] = {
    # 光学光电子
    "002273": "光学光电子", "002281": "光学光电子", "300433": "光学光电子",
    "688127": "光学光电子", "002456": "光学光电子", "603501": "光学光电子",
    # 白酒
    "600519": "白酒", "000858": "白酒", "000568": "白酒", "002304": "白酒",
    "600809": "白酒", "600779": "白酒", "000799": "白酒",
    # 半导体
    "688981": "半导体", "603986": "半导体", "002371": "半导体", "002129": "半导体",
    "300782": "半导体", "688012": "半导体", "688008": "半导体", "688536": "半导体",
    # 新能源 / 电池
    "300750": "电池", "002594": "汽车整车", "300014": "电池", "002460": "电池",
    "300207": "电池", "300124": "电池", "300919": "电池",
    # AI / 算力
    "300308": "光模块", "300394": "光模块", "300502": "光模块", "002463": "光模块",
    # 医药生物
    "300760": "医药生物", "600276": "医药生物", "603259": "医药生物", "600196": "医药生物",
    # 消费电子
    "002475": "消费电子", "002241": "消费电子", "002938": "消费电子",
    # 银行
    "601398": "银行", "601939": "银行", "601288": "银行", "600036": "银行",
    "601166": "银行", "000001": "银行",
    # 保险
    "601318": "保险", "601601": "保险", "601628": "保险", "601336": "保险",
    # 证券
    "600030": "证券", "601688": "证券", "000776": "证券",
    # 房地产
    "000002": "房地产", "600048": "房地产", "001979": "房地产",
    # 钢铁
    "600019": "钢铁", "600808": "钢铁", "000898": "钢铁",
    # 家电
    "000333": "家电", "000651": "家电", "600690": "家电",
    # 食品饮料
    "600887": "食品饮料", "603288": "食品饮料",
}


def _known_stock_industry(code: str) -> str | None:
    return _STOCK_INDUSTRY_MAP.get(code)


def _fetch_basic_hk(ti: TickerInfo) -> dict:
    if ak is None:
        raise RuntimeError("akshare not installed")
    df = _retry(lambda: ak.stock_hk_spot_em())
    row = df[df["代码"] == ti.code.zfill(5)]
    if row.empty:
        return {"code": ti.full, "name": None}
    r = row.iloc[0]
    return {
        "code": ti.full,
        "name": r.get("名称"),
        "price": float(r.get("最新价", 0)),
        "change_pct": float(r.get("涨跌幅", 0)),
        "market_cap": r.get("总市值"),
    }


def _fetch_basic_us(ti: TickerInfo) -> dict:
    if yf is None:
        raise RuntimeError("yfinance not installed")
    t = yf.Ticker(ti.code)
    info = _retry(lambda: t.info)
    return {
        "code": ti.full,
        "name": info.get("longName") or info.get("shortName"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "change_pct": info.get("regularMarketChangePercent"),
        "pe_ttm": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
    }


# ─────────────────────────────────────────────────────────────
# 1. K-line (OHLCV)
# ─────────────────────────────────────────────────────────────
def fetch_kline(ti: TickerInfo, period: str = "daily", start: str = "20240101", adjust: str = "qfq") -> list[dict]:
    """K-line OHLCV. TTL = 5min during day, naturally serves stale-OK after close."""
    key = f"kline__{ti.code}__{period}__{start}__{adjust}"
    return cached(ti.full, key, lambda: _fetch_kline_impl(ti, period, start, adjust), ttl=TTL_INTRADAY)


def _fetch_kline_impl(ti: TickerInfo, period: str, start: str, adjust: str) -> list[dict]:
    """K-line with multi-source fallback chain.

    A-share fallback order:
      1. akshare.stock_zh_a_hist  (东财, primary)
      2. akshare.stock_zh_a_daily (新浪, secondary)
      3. baostock                  (官方接口)
      4. 东财直连 push2his HTTP    (no lib)
      5. 新浪直连 quotes HTTP      (no lib)
      6. 腾讯直连 ifzq HTTP        (no lib)
    """
    if ti.market == "A":
        return _kline_a_share_chain(ti, period, start, adjust)
    if ti.market == "H" and ak:
        try:
            df = _retry(lambda: ak.stock_hk_hist(symbol=ti.code.zfill(5), period=period, start_date=start, adjust=adjust))
            return df.to_dict("records") if df is not None else []
        except Exception:
            pass
    if ti.market == "U":
        return _kline_us_chain(ti)
    return []


def _kline_a_share_chain(ti: TickerInfo, period: str, start: str, adjust: str) -> list[dict]:
    code = ti.code
    errors: list[str] = []

    # ── 1. akshare 东财
    if ak:
        try:
            df = _retry(lambda: ak.stock_zh_a_hist(symbol=code, period=period, start_date=start, adjust=adjust), attempts=2)
            if df is not None and len(df) > 0:
                return df.to_dict("records")
        except Exception as e:
            errors.append(f"akshare-em: {e}")

    # ── 2. akshare 新浪
    if ak:
        try:
            sina_symbol = ("sh" if ti.full.endswith("SH") else "sz") + code
            df = _retry(lambda: ak.stock_zh_a_daily(symbol=sina_symbol, start_date=start, adjust="qfq" if adjust == "qfq" else ""), attempts=2)
            if df is not None and len(df) > 0:
                # Normalize column names to match em format (中文)
                rename = {"date": "日期", "open": "开盘", "close": "收盘", "high": "最高", "low": "最低", "volume": "成交量", "amount": "成交额"}
                df = df.rename(columns=rename)
                return df.to_dict("records")
        except Exception as e:
            errors.append(f"akshare-sina: {e}")

    # ── 3. baostock
    if bs:
        try:
            global _bs_logged_in
            if not _bs_logged_in:
                bs.login()
                _bs_logged_in = True
            bs_code = ("sh." if ti.full.endswith("SH") else "sz.") + code
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=f"{start[:4]}-{start[4:6]}-{start[6:8]}",
                frequency="d",
                adjustflag="2" if adjust == "qfq" else "3",
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                row = rs.get_row_data()
                rows.append({
                    "日期": row[0], "开盘": float(row[1] or 0), "最高": float(row[2] or 0),
                    "最低": float(row[3] or 0), "收盘": float(row[4] or 0),
                    "成交量": float(row[5] or 0), "成交额": float(row[6] or 0),
                    "换手率": float(row[7] or 0), "涨跌幅": float(row[8] or 0),
                })
            if rows:
                return rows
        except Exception as e:
            errors.append(f"baostock: {e}")

    # ── 4. 东财直连 HTTP
    if requests:
        try:
            secid = f"1.{code}" if ti.full.endswith("SH") else f"0.{code}"
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid, "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": "101", "fqt": "1" if adjust == "qfq" else "0", "lmt": "500",
            }
            r = requests.get(url, params=params, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json().get("data") or {}
            klines = data.get("klines") or []
            rows = []
            for line in klines:
                parts = line.split(",")
                if len(parts) >= 7:
                    rows.append({
                        "日期": parts[0], "开盘": float(parts[1]), "收盘": float(parts[2]),
                        "最高": float(parts[3]), "最低": float(parts[4]),
                        "成交量": float(parts[5]), "成交额": float(parts[6]),
                    })
            if rows:
                return rows
        except Exception as e:
            errors.append(f"em-direct: {e}")

    # ── 5. 新浪直连 HTTP
    if requests:
        try:
            sina_sym = ("sh" if ti.full.endswith("SH") else "sz") + code
            url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
            params = {"symbol": sina_sym, "scale": "240", "ma": "no", "datalen": "500"}
            r = requests.get(url, params=params, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json() if r.text and r.text != "null" else []
            rows = []
            for d in data:
                rows.append({
                    "日期": d.get("day"), "开盘": float(d.get("open", 0)), "最高": float(d.get("high", 0)),
                    "最低": float(d.get("low", 0)), "收盘": float(d.get("close", 0)),
                    "成交量": float(d.get("volume", 0)),
                })
            if rows:
                return rows
        except Exception as e:
            errors.append(f"sina-direct: {e}")

    # ── 6. 腾讯直连 HTTP
    if requests:
        try:
            tx_sym = ("sh" if ti.full.endswith("SH") else "sz") + code
            url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {"param": f"{tx_sym},day,,,500,qfq"}
            r = requests.get(url, params=params, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            payload = r.json().get("data", {}).get(tx_sym, {})
            klines = payload.get("qfqday") or payload.get("day") or []
            rows = []
            for line in klines:
                if len(line) >= 6:
                    rows.append({
                        "日期": line[0], "开盘": float(line[1]), "收盘": float(line[2]),
                        "最高": float(line[3]), "最低": float(line[4]), "成交量": float(line[5]),
                    })
            if rows:
                return rows
        except Exception as e:
            errors.append(f"tencent-direct: {e}")

    # ── All failed
    return [{"_kline_fetch_error": "; ".join(errors) or "no source available"}]


def _kline_us_chain(ti: TickerInfo) -> list[dict]:
    """US K-line: yfinance → akshare → stooq HTTP fallback."""
    if yf:
        try:
            t = yf.Ticker(ti.code)
            df = _retry(lambda: t.history(period="2y", interval="1d"), attempts=2)
            if df is not None and len(df) > 0:
                df = df.reset_index()
                return df.to_dict("records")
        except Exception:
            pass
    if ak:
        try:
            df = ak.stock_us_hist(symbol=ti.code, period="daily", start_date="20240101", adjust="qfq")
            if df is not None and len(df) > 0:
                return df.to_dict("records")
        except Exception:
            pass
    if requests:
        try:
            url = f"https://stooq.com/q/d/l/?s={ti.code.lower()}.us&i=d"
            r = requests.get(url, timeout=12)
            lines = r.text.strip().splitlines()
            if len(lines) > 1:
                rows = []
                for line in lines[1:]:
                    parts = line.split(",")
                    if len(parts) >= 6:
                        rows.append({
                            "Date": parts[0], "Open": float(parts[1]), "High": float(parts[2]),
                            "Low": float(parts[3]), "Close": float(parts[4]), "Volume": float(parts[5]),
                        })
                return rows
        except Exception:
            pass
    return []


# ─────────────────────────────────────────────────────────────
# 2. Financials (3 statements)
# ─────────────────────────────────────────────────────────────
def fetch_financials(ti: TickerInfo) -> dict:
    """Quarterly financials. TTL = 24h (季报频率)."""
    return cached(ti.full, f"fin__{ti.code}", lambda: _fetch_financials_impl(ti), ttl=TTL_QUARTERLY)


def _fetch_financials_impl(ti: TickerInfo) -> dict:
    if ti.market == "A" and ak:
        try:
            abstract = ak.stock_financial_abstract(symbol=ti.code)
            indicator = ak.stock_financial_analysis_indicator(symbol=ti.code)
            return {
                "abstract": abstract.head(20).to_dict("records") if abstract is not None else [],
                "indicator": indicator.head(20).to_dict("records") if indicator is not None else [],
            }
        except Exception as e:
            return {"error": str(e)}
    if ti.market == "U" and yf:
        t = yf.Ticker(ti.code)
        return {
            "income": t.financials.to_dict() if t.financials is not None else {},
            "balance": t.balance_sheet.to_dict() if t.balance_sheet is not None else {},
            "cashflow": t.cashflow.to_dict() if t.cashflow is not None else {},
        }
    return {}


# ─────────────────────────────────────────────────────────────
# 3. 龙虎榜 (A only)
# ─────────────────────────────────────────────────────────────
def fetch_lhb_recent(ti: TickerInfo, days: int = 30) -> list[dict]:
    """LHB updates daily after market close. TTL = 2h (cover the window after close)."""
    if ti.market != "A" or ak is None:
        return []
    key = f"lhb__{ti.code}__{days}"
    return cached(ti.full, key, lambda: _fetch_lhb_impl(ti, days), ttl=TTL_DAILY)


def _fetch_lhb_impl(ti: TickerInfo, days: int) -> list[dict]:
    try:
        df = ak.stock_lhb_stock_detail_em(symbol=ti.code, date="近一月" if days <= 30 else "近三月")
        return df.to_dict("records") if df is not None else []
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# 4. News / Telegraph (财联社)
# ─────────────────────────────────────────────────────────────
def fetch_news(ti: TickerInfo, limit: int = 30) -> list[dict]:
    """News TTL = 1h (hot news shouldn't be stale)."""
    if ak is None:
        return []
    key = f"news__{ti.code}__{limit}"
    return cached(ti.full, key, lambda: _fetch_news_impl(ti, limit), ttl=TTL_HOURLY)


def _fetch_news_impl(ti: TickerInfo, limit: int) -> list[dict]:
    try:
        if ti.market == "A":
            df = ak.stock_news_em(symbol=ti.code)
            return df.head(limit).to_dict("records") if df is not None else []
    except Exception:
        return []
    return []


# ─────────────────────────────────────────────────────────────
# 5. Sentiment / hot rank
# ─────────────────────────────────────────────────────────────
def fetch_hot_rank(ti: TickerInfo) -> dict:
    """Sentiment hot rank. TTL = 5min (changes intraday)."""
    if ak is None or ti.market != "A":
        return {}
    key = f"hot__{ti.code}"
    return cached(ti.full, key, lambda: _fetch_hot_impl(ti), ttl=TTL_INTRADAY)


def _fetch_hot_impl(ti: TickerInfo) -> dict:
    try:
        df = ak.stock_hot_rank_detail_em(symbol=ti.code)
        return {"rank_history": df.head(30).to_dict("records") if df is not None else []}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────
# 6. North-bound capital (A only)
# ─────────────────────────────────────────────────────────────
def fetch_northbound(ti: TickerInfo) -> dict:
    """North-bound capital. TTL = 2h (daily aggregate)."""
    if ak is None or ti.market != "A":
        return {}
    key = f"hsgt__{ti.code}"
    return cached(ti.full, key, lambda: _fetch_north_impl(ti), ttl=TTL_DAILY)


def _fetch_north_impl(ti: TickerInfo) -> dict:
    try:
        df = ak.stock_hsgt_individual_em(stock=ti.code)
        return {"flow_history": df.tail(60).to_dict("records") if df is not None else []}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────
# 7. Research reports
# ─────────────────────────────────────────────────────────────
def fetch_research_reports(ti: TickerInfo) -> list[dict]:
    """Research reports. TTL = 24h (mostly stable)."""
    if ak is None or ti.market != "A":
        return []
    key = f"research__{ti.code}"
    return cached(ti.full, key, lambda: _fetch_research_impl(ti), ttl=TTL_QUARTERLY)


def _fetch_research_impl(ti: TickerInfo) -> list[dict]:
    try:
        df = ak.stock_research_report_em(symbol=ti.code)
        return df.head(20).to_dict("records") if df is not None else []
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# Top-level: resolve Chinese name → ticker (uses akshare a-share spot table)
# ─────────────────────────────────────────────────────────────
def resolve_chinese_name(name: str) -> TickerInfo | None:
    if ak is None:
        return None
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["名称"].str.contains(name, na=False)]
        if row.empty:
            return None
        code = str(row.iloc[0]["代码"])
        return parse_ticker(code)
    except Exception:
        return None


if __name__ == "__main__":
    import json
    ti = parse_ticker("002273")
    print(json.dumps(fetch_basic(ti), ensure_ascii=False, indent=2, default=str))
