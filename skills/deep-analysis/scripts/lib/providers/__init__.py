"""Data Provider Framework · v2.10.3.

统一接入多个数据源做 **自动 failover**。目的：

  · 主源 akshare 挂了不至于整个 fetcher 返空
  · 用户有 Tushare/FMP 等可选 key 时自动启用更稳定源
  · 下游 fetcher 不关心具体从哪拉，只要拿到数据

## 架构

```
fetcher (e.g. fetch_financials)
    ↓
get_provider_chain("financials", market="A")   ← 按偏好+可用性排序的 providers
    ↓
for p in chain:
    try:
        return p.fetch_financials(ti)
    except ProviderError:
        continue
```

## 内置 providers（v2.10.3）

  · akshare    (主 · 0 key · 默认)
  · efinance   (冗余 · 0 key · 需 pip install efinance)
  · tushare    (opt-in · 需 TUSHARE_TOKEN)
  · baostock   (低层 · 0 key · 已装)

## 环境变量

  TUSHARE_TOKEN     · Tushare Pro token
  UZI_PROVIDERS_<DIM>  · 单维度覆盖偏好，如 UZI_PROVIDERS_FINANCIALS=tushare,akshare
"""
from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable


class ProviderError(Exception):
    """统一错误类型，让 fetch chain 能优雅 failover."""


@runtime_checkable
class Provider(Protocol):
    """所有 provider 必须实现的协议."""
    name: str
    requires_key: bool
    markets: tuple[str, ...]  # ("A",) / ("A", "H") / ("U",)

    def is_available(self) -> bool:
        """能否用（环境变量/依赖/网络都检查）."""
        ...


# ═══════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════

_REGISTRY: dict[str, Provider] = {}


def register(provider: Provider) -> None:
    """Provider 类模块内自动调用注册."""
    _REGISTRY[provider.name] = provider


def get(name: str) -> Provider | None:
    return _REGISTRY.get(name)


def list_providers(market: str | None = None, available_only: bool = False) -> list[Provider]:
    """列出 provider · 可按 market 过滤 · 可只返回当前可用的."""
    out = list(_REGISTRY.values())
    if market:
        out = [p for p in out if market in p.markets]
    if available_only:
        out = [p for p in out if p.is_available()]
    return out


def get_provider_chain(dim: str, market: str = "A") -> list[Provider]:
    """返回一个给定维度+市场的 provider 优先级链.

    优先级 = UZI_PROVIDERS_<DIM> env （逗号分隔 id）> 内置默认顺序
    默认顺序：akshare → efinance → tushare → baostock
    """
    default_order = ["akshare", "efinance", "tushare", "baostock"]
    env_key = f"UZI_PROVIDERS_{dim.upper()}"
    env_val = os.environ.get(env_key)
    if env_val:
        order = [x.strip() for x in env_val.split(",") if x.strip()]
    else:
        order = default_order

    chain: list[Provider] = []
    for name in order:
        p = _REGISTRY.get(name)
        if p and market in p.markets and p.is_available():
            chain.append(p)
    return chain


def health_check() -> dict[str, dict]:
    """返回每个 provider 的健康度 + 诊断信息."""
    out = {}
    for name, p in _REGISTRY.items():
        try:
            avail = p.is_available()
            out[name] = {
                "available": avail,
                "markets": list(p.markets),
                "requires_key": p.requires_key,
                "status": "ok" if avail else "unavailable",
            }
        except Exception as e:
            out[name] = {"available": False, "status": f"error: {type(e).__name__}"}
    return out


# Auto-register built-in providers on import
def _auto_register():
    """import 时自动装所有内置 providers（失败的静默跳过）."""
    try:
        from . import akshare_provider  # noqa
    except Exception:
        pass
    try:
        from . import efinance_provider  # noqa
    except Exception:
        pass
    try:
        from . import tushare_provider  # noqa
    except Exception:
        pass
    try:
        from . import baostock_provider  # noqa
    except Exception:
        pass


_auto_register()
