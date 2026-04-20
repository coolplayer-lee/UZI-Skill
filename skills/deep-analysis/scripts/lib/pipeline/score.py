"""pipeline.score · Rules 引擎 + 51 评委打分骨架 · Phase 4 stub.

Phase 4：thin wrapper · 内部直接调 legacy run_real_test 的 scoring 函数.
未来 session（Phase 5）：把 run_real_test 里的 build_dimensions/build_panel/compute_institutional
一步步挪进来.
"""
from __future__ import annotations

from typing import Any


def score_skeleton(raw: dict) -> tuple[dict, dict]:
    """调 legacy scoring · 返 (dimensions, panel) dict.

    输入：raw (pipeline.collect 的输出 · 老格式兼容)
    输出：(dimensions_dict, panel_dict) · 与 run_real_test 原流程一致
    """
    # 调老代码 · 未来 session 会把这部分逻辑挪进来
    import run_real_test as rrt
    # run_real_test 的 scoring 路径在 stage1 里面 · 本 stub 只返 placeholder
    raise NotImplementedError("Phase 5 TODO · 目前走 legacy stage1 · UZI_PIPELINE=1 只到 collect 阶段")
