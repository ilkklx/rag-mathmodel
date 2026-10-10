#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""基础检索测试：五类各取一题，检查结果非空、带 path+chunk_id、JSON 可序列化、耗时。"""
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rag import retrieve  # noqa: E402

GT = os.path.join(ROOT, "data", "ground_truth", "eval_set_v2.json")


def main():
    items = json.load(open(GT, encoding="utf-8"))["items"]
    picked, seen = [], set()
    for it in items:
        c = it["category"]
        if c not in seen:
            seen.add(c)
            picked.append(it)
    print("五类各取一题，共 %d 题\n" % len(picked))
    ok = 0
    for it in picked:
        t0 = time.time()
        out = retrieve(it["question"], top_k=5)
        dt = time.time() - t0
        good = len(out["results"]) > 0 and all(
            r.get("path") and r.get("chunk_id") for r in out["results"])
        json.dumps(out, ensure_ascii=False)
        ok += 1 if good else 0
        print("[%s] %s" % ("PASS" if good else "FAIL", it["category"]))
        print("   Q: %s" % it["question"])
        tops = " | ".join("%s#%s" % (r["title"], r["chunk_id"].split("#")[-1]) for r in out["results"])
        print("   Top5: %s" % tops)
        print("   耗时 %.3fs ｜ 词法 %s ｜ 向量 %d / BM25 %d"
              % (dt, out["meta"]["bm25_match"] or "(空→回退向量)",
                 out["meta"]["n_vector"], out["meta"]["n_bm25"]))
        print()
    print("基础检索：%d/%d PASS" % (ok, len(picked)))
    return 0 if ok == len(picked) else 1


if __name__ == "__main__":
    sys.exit(main())
