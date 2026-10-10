#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最小 Python 调用示例（Agent 可直接照抄）。"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rag import retrieve  # noqa: E402

out = retrieve("遗传算法适合什么数学建模问题？", top_k=5)

# 1) 完整结构（含 meta 与 source 映射）
print(json.dumps({"query": out["query"], "meta": out["meta"]}, ensure_ascii=False, indent=1))

# 2) 只要「结论 + 出处」时，必须保留 path + chunk_id
for r in out["results"]:
    print("%d) %s" % (r["rank"], r["title"]))
    print("    chunk_id : %s" % r["chunk_id"])
    print("    path     : %s" % r["path"])
    print("    本地原文 : %s" % (r["source"]["resolved_path"] or "（未配置 library_roots）"))
    print("    片段     : %s" % r["content_preview"].replace("\n", " ")[:120])
