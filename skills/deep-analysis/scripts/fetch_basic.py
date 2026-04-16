"""Dimension 0 · 基础信息 (name, code, industry, price, mcap, PE, PB)."""
import json
import sys

from lib import data_sources as ds
from lib.market_router import is_chinese_name, parse_ticker


def main(user_input: str) -> dict:
    if is_chinese_name(user_input):
        ti = ds.resolve_chinese_name(user_input) or parse_ticker(user_input)
    else:
        ti = parse_ticker(user_input)
    data = ds.fetch_basic(ti)
    return {
        "ticker": ti.full,
        "market": ti.market,
        "data": data,
        "source": f"akshare:{ti.market}",
        "fallback": False,
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "002273"
    print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))
