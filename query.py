#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI：python query.py "你的问题" --top-k 10 [--json] [--no-content]"""
import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rag import retrieve  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="RAG-MathModel 检索 CLI")
    ap.add_argument("query")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="输出合法 JSON（Agent 首选）")
    ap.add_argument("--no-content", action="store_true", help="不输出正文，仅出处")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()

    out = retrieve(a.query, top_k=a.top_k, config_path=a.config)
    if a.no_content:
        for r in out["results"]:
            r.pop("content", None)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    print("查询：%s" % out["query"])
    m = out["meta"]
    print("词法：%s ｜ 向量条数 %d ｜ BM25 条数 %d ｜ 耗时 %.3fs"
          % (m["bm25_match"] or "(空→回退向量)", m["n_vector"], m["n_bm25"], m["latency_s"]))
    for r in out["results"]:
        src = r["source"]
        print("\n%d) [%s] %s题 %s" % (r["rank"], r["section"] or "-", r["problem"] or "-", r["year"] or "?"))
        print("   出处: %s#%s" % (r["title"], r["chunk_id"].split("#")[-1]))
        print("   原文: %s" % (src["resolved_path"] or "（未配置 library_roots，无法定位）"))
        print("   摘录: %s" % r["content_preview"].replace("\n", " ")[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
