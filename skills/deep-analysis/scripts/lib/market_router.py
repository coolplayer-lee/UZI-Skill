"""Identify market (A / H / U) from a ticker or stock name and normalize the code."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Market = Literal["A", "H", "U"]


@dataclass
class TickerInfo:
    raw: str            # original user input
    code: str           # numeric/letter code without exchange suffix
    full: str           # canonical: 002273.SZ / 00700.HK / AAPL
    market: Market      # A / H / U


_RE_A_NUMERIC = re.compile(r"^\d{6}$")
_RE_A_FULL = re.compile(r"^(\d{6})\.(SZ|SH|BJ)$", re.I)
_RE_HK = re.compile(r"^(\d{4,5})(?:\.HK)?$", re.I)
_RE_US = re.compile(r"^[A-Z][A-Z\.\-]{0,5}$")


def _a_share_suffix(code6: str) -> str:
    """Decide SZ/SH/BJ for a 6-digit A-share code."""
    if code6.startswith(("60", "688", "900")):
        return "SH"
    if code6.startswith(("83", "87", "88", "92")):
        return "BJ"
    return "SZ"  # 000/001/002/003/300


def parse_ticker(raw: str) -> TickerInfo:
    """Best-effort parse. For Chinese names (e.g. '水晶光电'), caller must resolve via fetch_basic first."""
    s = raw.strip().upper().replace(" ", "")

    m = _RE_A_FULL.match(s)
    if m:
        return TickerInfo(raw=raw, code=m.group(1), full=f"{m.group(1)}.{m.group(2).upper()}", market="A")

    if _RE_A_NUMERIC.match(s):
        suffix = _a_share_suffix(s)
        return TickerInfo(raw=raw, code=s, full=f"{s}.{suffix}", market="A")

    if s.endswith(".HK"):
        code = s.removesuffix(".HK").lstrip("0") or "0"
        return TickerInfo(raw=raw, code=code, full=f"{code.zfill(5)}.HK", market="H")

    if _RE_HK.match(s) and not _RE_US.match(s):
        return TickerInfo(raw=raw, code=s.lstrip("0") or "0", full=f"{s.zfill(5)}.HK", market="H")

    if _RE_US.match(s):
        return TickerInfo(raw=raw, code=s, full=s, market="U")

    # Unrecognized — likely a Chinese name. Caller must resolve.
    return TickerInfo(raw=raw, code=raw, full=raw, market="A")


def is_chinese_name(raw: str) -> bool:
    """True if input contains CJK chars (needs name→code resolution)."""
    return any("\u4e00" <= ch <= "\u9fff" for ch in raw)


if __name__ == "__main__":
    for t in ["002273", "002273.SZ", "600519", "00700.HK", "00700", "AAPL", "BRK.B", "水晶光电"]:
        print(t, "->", parse_ticker(t))
