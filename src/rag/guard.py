# -*- coding: utf-8 -*-
"""防呆自检：确认词法构造走的是 Q-1 修复版（不造伪词）。"""
import re

from . import bm25


def check():
    expr, kept, skipped = bm25.build_match("验证 一个 数值 模型 网格无关 性")
    bad = [t for t in kept if len(t) == 3 and t[0] == t[2]]
    ok = (expr == '"网格无关"') and (not bad) and ("一个一" not in expr)
    return {"ok": bool(ok), "probe_expr": expr, "kept": kept, "skipped": skipped,
            "note": "断言：表达式必须为 \"网格无关\"；kept 不得含首尾同字的 3 字词；不得出现 \"一个一\""}
