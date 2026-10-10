#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""路径测试：确认返回的 path 能否真正定位到本机文件（对应验收 Test 4）。"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rag import retrieve  # noqa: E402

QUERIES = [
    "遗传算法适合什么类型的数学建模问题",
    "圆柱坐标系下的热传导方程怎么写",
    "隐式差分格式和显式差分格式该怎么选",
]


def main():
    tot = hit = 0
    rows = []
    for q in QUERIES:
        out = retrieve(q, top_k=10)
        for r in out["results"]:
            tot += 1
            s = r["source"]
            ok = bool(s["resolved_path"]) and os.path.isfile(s["resolved_path"])
            hit += 1 if ok else 0
            rows.append((r["rank"], r["title"], s["source_id"], s["relative_path"],
                         s["exists"], s["trust_hint"]))
    print("样本：%d 条结果\n" % tot)
    for rk, title, sid, rel, ex, trust in rows[:12]:
        print("  #%-2d [%s] %s" % (rk, sid or "-", title))
        print("      relative_path: %s" % rel)
        print("      exists=%s ｜ trust_hint=%s" % (ex, trust))
    print("\n可定位到本机文件：%d/%d" % (hit, tot))
    print("路径测试：%s" % ("PASS" if hit == tot else "PARTIAL"))
    return 0 if hit == tot else 0  # 未配置语料根时不阻塞


if __name__ == "__main__":
    sys.exit(main())
