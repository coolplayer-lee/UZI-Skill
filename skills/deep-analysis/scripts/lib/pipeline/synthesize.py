"""pipeline.synthesize · stage2 merge · Phase 4 stub.

未来 session（Phase 6）：
- render 循环调 RENDERER_REGISTRY 里的 section renderer
- agent_analysis.json merge 逻辑
- HTML 组装

Phase 4 本文件 · thin wrapper 调 legacy assemble_report.
"""
from __future__ import annotations

from typing import Any


def synthesize(raw: dict, dimensions: dict, panel: dict, agent: dict | None = None) -> dict:
    """调 legacy stage2 merge · 返老格式 synthesis dict."""
    import run_real_test as rrt
    return rrt.generate_synthesis(raw, dimensions, panel, agent_analysis=agent)
