"""Renderer 注册表 · dim_key → SectionRenderer."""
from __future__ import annotations

from .basic_header import BasicHeaderRenderer
from .events import EventsRenderer
from .financials import FinancialsRenderer
from .fund import FundRenderer
from .industry import IndustryRenderer
from .moat import MoatRenderer
from .peers import PeersRenderer
from .sentiment import SentimentRenderer

# Phase 3 已迁移 8 个
RENDERER_REGISTRY: dict[str, type] = {
    "0_basic": BasicHeaderRenderer,
    "1_financials": FinancialsRenderer,
    "4_peers": PeersRenderer,
    "6_fund_holders": FundRenderer,
    "7_industry": IndustryRenderer,
    "14_moat": MoatRenderer,
    "15_events": EventsRenderer,
    "17_sentiment": SentimentRenderer,
    # Phase 4+ 待迁：2_kline / 3_macro / 5_chain / 6_research / 8_materials / 9_futures
    #                10_valuation / 11_governance / 12_capital_flow / 13_policy / 16_lhb
    #                18_trap / 19_contests
}


def get_renderer(dim_key: str):
    """根据 dim_key 取 renderer 实例 · 未注册返 None."""
    cls = RENDERER_REGISTRY.get(dim_key)
    return cls() if cls else None


def list_renderers() -> list[str]:
    return sorted(RENDERER_REGISTRY.keys())
